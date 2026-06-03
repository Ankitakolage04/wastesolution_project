"""
crawler.py - Discover profile URLs from mywastesolution.com

Flow:
  1. Start from seed URLs (search pages, directories)
  2. Crawl listing pages to find profile URLs matching /experts/profile/ pattern
  3. Follow pagination links to discover more profiles
  4. Stop when MAX_PROFILES limit is reached
  5. Return deduplicated set of profile URLs
"""

import asyncio
import logging
import re
import os
from typing import Set
from playwright.async_api import BrowserContext, Page, TimeoutError as PWTimeout

logger = logging.getLogger(__name__)

# Configuration
BASE_URL = os.getenv("BASE_URL", "https://www.mywastesolution.com")
MAX_PROFILES = int(os.getenv("MAX_PROFILES", "50"))
REQUEST_DELAY_MS = int(os.getenv("REQUEST_DELAY_MS", "1000"))
PROFILE_URL_PATTERN = re.compile(r"/experts?/profile/", re.IGNORECASE)
PAGINATION_SELECTORS = [
    "a[rel='next']",
    "a.next",
    ".pagination a[aria-label*='next']",
    ".pagination li:last-child a",
    "a[href*='page']",
]


async def discover_profile_urls(context: BrowserContext) -> Set[str]:
    """
    Crawl the site to find profile URLs, respecting MAX_PROFILES limit.
    Returns a set of unique profile URLs (up to MAX_PROFILES items).
    """
    discovered: Set[str] = set()
    visited_pages: Set[str] = set()
    queue: list[str] = []
    
    # Query MongoDB for existing URLs to skip
    existing_urls = set()
    try:
        from db import MongoDB
        db = MongoDB()
        db.connect()
        existing_urls = {doc["profile_url"] for doc in db.collection.find({}, {"profile_url": 1})}
        db.disconnect()
        logger.info(f"Loaded {len(existing_urls)} existing URLs from MongoDB to skip.")
    except Exception as e:
        logger.warning(f"Could not load existing URLs from DB: {e}")

    # Seed URLs - pages that list experts/consultants
    seed_urls = [
        f"{BASE_URL}/search-consultants/waste-consultants",
        f"{BASE_URL}/search-consultants",
        f"{BASE_URL}/find-an-expert",
        f"{BASE_URL}/experts",
        f"{BASE_URL}/directory",
        BASE_URL,
    ]
    queue.extend(seed_urls)

    page = await context.new_page()
    await page.set_extra_http_headers({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    })

    async def harvest_links(url: str):
        """Visit a page and extract profile links + pagination links."""
        if url in visited_pages:
            return
        
        if len(discovered) >= MAX_PROFILES:
            logger.info(f"✓ Reached MAX_PROFILES limit ({MAX_PROFILES}). Stopping crawl.")
            return

        visited_pages.add(url)
        logger.info(f"🕷️  Crawling listing page: {url}")
        
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(REQUEST_DELAY_MS)

            # Extract all links from the page
            links = await page.eval_on_selector_all(
                "a[href]",
                "els => els.map(e => e.href)"
            )
            logger.debug(f"   Found {len(links)} total links on page")

            # Extract profile URLs
            profile_links_found = 0
            for link in links:
                if len(discovered) >= MAX_PROFILES:
                    break

                link = link.split("?")[0].rstrip("/")  # Normalize URL
                
                if PROFILE_URL_PATTERN.search(link):
                    if link in existing_urls or link in discovered:
                        logger.info(f"[PROFILE SKIPPED] {link}")
                        continue
                    discovered.add(link)
                    profile_links_found += 1
                    logger.info(f"[URL FOUND] {link}")

            logger.info(f"   Found {profile_links_found} new profile links on this page")

            # Queue up next pagination page
            if len(discovered) < MAX_PROFILES:
                for selector in PAGINATION_SELECTORS:
                    try:
                        next_link = await page.locator(selector).first.get_attribute("href")
                        if next_link:
                            next_url = next_link.split("?")[0].rstrip("/")
                            if next_url.startswith("http"):
                                full_url = next_url
                            else:
                                full_url = BASE_URL.rstrip("/") + "/" + next_url.lstrip("/")
                            
                            if full_url not in visited_pages:
                                queue.append(full_url)
                                logger.debug(f"   → Queued pagination: {full_url}")
                            break
                    except Exception:
                        continue

        except PWTimeout:
            logger.warning(f"[ERROR] Timeout loading {url}")
        except Exception as e:
            logger.error(f"[ERROR] crawling {url}: {e}")

    # Process queue until we have enough profiles
    while queue and len(discovered) < MAX_PROFILES:
        url = queue.pop(0)
        if url not in visited_pages:
            await harvest_links(url)

    await page.close()
    
    logger.info(f"\n{'='*70}")
    logger.info(f"✓ Crawler finished")
    logger.info(f"  Total profile URLs discovered: {len(discovered)}")
    logger.info(f"  Pages crawled: {len(visited_pages)}")
    logger.info(f"{'='*70}\n")
    
    return discovered
