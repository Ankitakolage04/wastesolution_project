"""
scraper.py - Async Playwright scraper for mywastesolution.com expert profiles.

Flow:
  1. Crawl the site to discover all /experts/profile/ URLs.
  2. Visit each profile page and extract structured data.
  3. Upsert every profile into MongoDB (duplicate-safe via unique index).
  4. Write a full backup to profiles.json.
"""

import asyncio
import json
import logging
import os
import re
from datetime import datetime, timezone
from typing import Optional

from dotenv import load_dotenv
from playwright.async_api import (
    async_playwright,
    Browser,
    BrowserContext,
    Page,
    TimeoutError as PWTimeout,
)

from db import MongoDB

load_dotenv()

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("scraper.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────────────────────
BASE_URL = os.getenv("BASE_URL", "https://www.mywastesolution.com")
HEADLESS = os.getenv("HEADLESS", "true").lower() == "true"
CONCURRENT_PAGES = int(os.getenv("CONCURRENT_PAGES", 3))
DELAY_MS = int(os.getenv("REQUEST_DELAY_MS", 1000))
OUTPUT_JSON = os.getenv("OUTPUT_JSON", "profiles.json")

PROFILE_PATH_RE = re.compile(r"/experts/profile/", re.IGNORECASE)

# Selectors to try for each field (first match wins)
FIELD_SELECTORS = {
    "name": [
        "h1.profile-name",
        "h1[class*='name']",
        ".expert-name h1",
        ".profile-header h1",
        "h1",
    ],
    "description": [
        ".profile-about",
        ".about-section p",
        "[class*='about'] p",
        ".bio",
        ".description",
        "[class*='description']",
        ".profile-bio",
    ],
    "location": [
        ".profile-location",
        "[class*='location']",
        ".expert-location",
        "[data-field='location']",
    ],
    "profile_image_url": [
        ".profile-image img",
        ".expert-avatar img",
        ".avatar img",
        "[class*='profile'] img",
        ".profile-photo img",
    ],
}

LIST_FIELD_SELECTORS = {
    "skills": [
        ".skills-list li",
        "[class*='skill'] li",
        ".tags li",
        "[class*='skill']",
        ".expertise-tags span",
    ],
    "expertise": [
        ".expertise-list li",
        "[class*='expertise'] li",
        ".areas-of-expertise li",
        "[class*='expertise']",
    ],
    "experience": [
        ".experience-section .item",
        "[class*='experience'] .item",
        ".work-history li",
        ".timeline-item",
        "[class*='experience'] li",
        ".work-experience .entry",
    ],
    "education": [
        ".education-section .item",
        "[class*='education'] .item",
        ".education li",
        "[class*='education'] li",
        ".academic-history .entry",
    ],
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def clean(text: Optional[str]) -> Optional[str]:
    if text is None:
        return None
    text = re.sub(r"\s+", " ", text).strip()
    return text if text else None


async def try_selectors(page: Page, selectors: list[str], attr: str = "innerText") -> Optional[str]:
    for sel in selectors:
        try:
            el = page.locator(sel).first
            if await el.count() == 0:
                continue
            if attr == "innerText":
                val = await el.inner_text(timeout=3000)
            else:
                val = await el.get_attribute(attr, timeout=3000)
            if val and val.strip():
                return clean(val)
        except Exception:
            continue
    return None


async def try_list_selectors(page: Page, selectors: list[str]) -> list[str]:
    for sel in selectors:
        try:
            els = page.locator(sel)
            count = await els.count()
            if count == 0:
                continue
            items = []
            for i in range(count):
                text = await els.nth(i).inner_text(timeout=3000)
                if text and text.strip():
                    items.append(clean(text))
            if items:
                return items
        except Exception:
            continue
    return []


# ── Profile URL Discovery ─────────────────────────────────────────────────────

async def discover_profile_urls(context: BrowserContext) -> set[str]:
    """
    Crawl the site to find all /experts/profile/ URLs.
    Strategy:
      1. Start from /experts (or /experts/directory etc.)
      2. Follow pagination links.
      3. Also gather any profile links found on the homepage.
    """
    discovered: set[str] = set()
    visited_pages: set[str] = set()
    queue: list[str] = []

    # Seed URLs most likely to list experts
    seeds = [
        f"{BASE_URL}/search-consultants/waste-consultants",
        f"{BASE_URL}/search-consultants",
        f"{BASE_URL}/find-an-expert",
        BASE_URL,
    ]
    queue.extend(seeds)

    page = await context.new_page()
    await page.set_extra_http_headers({"User-Agent": "Mozilla/5.0 (compatible; ProfileScraper/1.0)"})

    async def harvest_links(url: str):
        if url in visited_pages:
            return
        visited_pages.add(url)
        logger.info(f"Crawling listing page: {url}")
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(DELAY_MS)
            links = await page.eval_on_selector_all(
                "a[href]",
                "els => els.map(e => e.href)"
            )
            
            logger.info(f"Found {len(links)} links on {url}")

            for sample in links[:20]:
                logger.info(f"LINK: {sample}")

            for link in links:
                link = link.split("?")[0].rstrip("/")   # normalise
                if PROFILE_PATH_RE.search(link):
                    if link not in discovered:
                        logger.info(f"  Found profile: {link}")
                        discovered.add(link)
                elif (
                    link.startswith(BASE_URL)
                    and link not in visited_pages
                ):
                    if any(
                        keyword in link.lower()
                        for keyword in [
                            "consultant",
                            "consultants",
                            "expert",
                            "experts",
                            "find",
                            "search",
                            "directory",
                            "profile",
                        ]
                    ):
                        queue.append(link)
        except PWTimeout:
            logger.warning(f"Timeout on listing page: {url}")
        except Exception as e:
            logger.error(f"Error crawling {url}: {e}")

    while queue:
        url = queue.pop(0)
        if url not in visited_pages:
            await harvest_links(url)

    await page.close()
    logger.info(f"Total profile URLs discovered: {len(discovered)}")
    return discovered


# ── Profile Extraction ────────────────────────────────────────────────────────

async def extract_profile(page: Page, url: str) -> dict:
    """Visit a profile page and return a structured dict."""
    profile: dict = {
        "profile_url": url,
        "name": None,
        "description": None,
        "skills": [],
        "expertise": [],
        "experience": [],
        "education": [],
        "location": None,
        "profile_image_url": None,
        "additional_info": {},
        "scraped_at": datetime.now(timezone.utc).isoformat(),
        "scrape_status": "success",
    }

    try:
        logger.info(f"Scraping profile: {url}")
        await page.goto(url, wait_until="domcontentloaded", timeout=40000)
        await page.wait_for_timeout(DELAY_MS)

        # Wait for main content (try several possible containers)
        for selector in ["main", ".profile-container", ".expert-profile", "body"]:
            try:
                await page.wait_for_selector(selector, timeout=5000)
                break
            except PWTimeout:
                continue

        # ── Scalar fields ──────────────────────────────────────────────────
        for field, selectors in FIELD_SELECTORS.items():
            if field == "profile_image_url":
                profile[field] = await try_selectors(page, selectors, attr="src")
            else:
                profile[field] = await try_selectors(page, selectors)

        # ── List fields ────────────────────────────────────────────────────
        for field, selectors in LIST_FIELD_SELECTORS.items():
            profile[field] = await try_list_selectors(page, selectors)

        # ── Additional visible info ────────────────────────────────────────
        # Grab any labelled key-value pairs (dt/dd, .label/.value patterns)
        try:
            pairs = await page.eval_on_selector_all(
                "dl dt, dl dd",
                """els => {
                    const out = {};
                    for (let i = 0; i < els.length - 1; i += 2) {
                        const k = els[i]?.innerText?.trim();
                        const v = els[i+1]?.innerText?.trim();
                        if (k && v) out[k] = v;
                    }
                    return out;
                }"""
            )
            if pairs:
                profile["additional_info"].update(pairs)
        except Exception:
            pass

        # Grab any [data-label] / [data-value] attribute pairs
        try:
            labelled = await page.eval_on_selector_all(
                "[data-label]",
                "els => els.reduce((o, e) => { o[e.dataset.label] = e.innerText.trim(); return o; }, {})"
            )
            if labelled:
                profile["additional_info"].update(labelled)
        except Exception:
            pass

        # Fallback: if name still missing, grab <title>
        if not profile["name"]:
            try:
                title = await page.title()
                profile["name"] = clean(title.split("|")[0].split("-")[0]) or None
            except Exception:
                pass

    except PWTimeout:
        logger.warning(f"Timeout loading profile: {url}")
        profile["scrape_status"] = "timeout"
    except Exception as e:
        logger.error(f"Error scraping {url}: {e}")
        profile["scrape_status"] = f"error: {e}"

    return profile


# ── Semaphore-limited worker ──────────────────────────────────────────────────

async def scrape_profile_worker(
    sem: asyncio.Semaphore,
    context: BrowserContext,
    url: str,
) -> dict:
    async with sem:
        page = await context.new_page()
        try:
            return await extract_profile(page, url)
        finally:
            await page.close()


# ── Main ──────────────────────────────────────────────────────────────────────

async def main():
    logger.info("=" * 60)
    logger.info("MyWasteSolution Expert Profile Scraper — starting")
    logger.info("=" * 60)

    db = MongoDB()
    db.connect()

    async with async_playwright() as pw:
        browser: Browser = await pw.chromium.launch(headless=HEADLESS)
        context: BrowserContext = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/124.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 900},
            java_script_enabled=True,
        )

        # ── Step 1: Discover profile URLs ─────────────────────────────────
        profile_urls = await discover_profile_urls(context)

        if not profile_urls:
            logger.warning(
                "No profile URLs found. The site structure may have changed. "
                "Inspect the site manually and update PROFILE_PATH_RE / seed URLs."
            )
            await browser.close()
            db.disconnect()
            return

        # ── Step 2: Scrape each profile concurrently ──────────────────────
        sem = asyncio.Semaphore(CONCURRENT_PAGES)
        tasks = [
            scrape_profile_worker(sem, context, url)
            for url in sorted(profile_urls)
        ]
        profiles = await asyncio.gather(*tasks)

        await browser.close()

    # ── Step 3: Persist to MongoDB ────────────────────────────────────────
    stats = {"inserted": 0, "skipped": 0, "error": 0}
    all_profiles = []

    for profile in profiles:
        result = db.upsert_profile(profile)
        stats[result] += 1
        all_profiles.append(profile)

    logger.info(
        f"MongoDB — inserted: {stats['inserted']}, "
        f"skipped (duplicate): {stats['skipped']}, "
        f"errors: {stats['error']}"
    )
    logger.info(f"Total profiles in collection: {db.count()}")
    db.disconnect()

    # ── Step 4: Save JSON backup ──────────────────────────────────────────
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(all_profiles, f, ensure_ascii=False, indent=2, default=str)
    logger.info(f"Backup saved → {OUTPUT_JSON}  ({len(all_profiles)} profiles)")
    logger.info("Scrape complete.")


if __name__ == "__main__":
    asyncio.run(main())