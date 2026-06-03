"""
extractor.py - Extract profile data from individual profile pages

Flow:
  1. Visit each profile URL
  2. Extract visible text content (name, description, location, etc.)
  3. Try multiple CSS selectors for each field
  4. Extract list fields (skills, expertise, experience, education)
  5. Extract images and links
  6. Return structured dict
"""

import asyncio
import logging
import os
import re
from datetime import datetime, timezone
from typing import Optional, Any
from playwright.async_api import Page, TimeoutError as PWTimeout

logger = logging.getLogger(__name__)

# Configuration
REQUEST_DELAY_MS = int(os.getenv("REQUEST_DELAY_MS", "1000"))

# CSS selector patterns for different fields (first match wins)
FIELD_SELECTORS = {
    "name": [
        "h1.cp-name",
        "h1.profile-name",
        "h1[class*='name']",
        ".expert-name h1",
        ".profile-header h1",
        ".profile-title h1",
        "[data-testid='profile-name'] h1",
        ".bio-section h1",
        "h1",
    ],
    "description": [
        ".cp-about",
        ".cp-tagline",
        ".profile-about",
        ".about-section p",
        "[class*='about'] p",
        ".bio",
        ".description",
        "[class*='description']",
        ".profile-bio",
        ".profile-intro p",
        ".bio-text",
        "[data-testid='profile-description']",
    ],
    "location": [
        ".profile-location",
        ".expert-location",
        "[data-field='location']",
        ".profile-address",
        ".cp-location",
    ],
    "task": [
        "[data-field='task']",
        "[class*='task']",
        ".specialization",
        ".profession",
        ".job-title",
        "[class*='specialization']",
        ".title-section",
        "h2.subtitle",
    ],
    "category": [
        "[data-field='category']",
        "[class*='category']",
        ".service-category",
        ".waste-type",
        "[class*='waste'] [class*='type']",
        ".tags.category",
        ".primary-category",
    ],
    "profile_image_url": [
        "img.cp-avatar",
        ".cp-avatar img",
        ".profile-image img",
        ".expert-avatar img",
        ".avatar img",
        "[class*='profile'] img",
        ".profile-photo img",
        "[data-testid='profile-image'] img",
        ".profile-header img",
        ".banner-section img",
    ],
    "company": [
        ".company-name",
        "[class*='company']",
        ".organization",
        "[data-field='company']",
        ".expert-company",
    ],
}

# Selectors for list fields (skills, expertise, experience, education)
LIST_FIELD_SELECTORS = {
    "skills": [
        ".skills-list li",
        "[class*='skill'] li",
        ".tags li",
        "[class*='skill'] span",
        ".expertise-tags span",
        ".skills span",
        ".skill-tag",
        "[data-testid='skills'] li",
    ],
    "expertise": [
        ".expertise-list li",
        "[class*='expertise'] li",
        ".areas-of-expertise li",
        "[class*='expertise'] span",
        ".expertise-areas",
        ".specialties li",
        "[data-testid='expertise'] li",
    ],
    "experience": [
        ".experience-section .item",
        "[class*='experience'] .item",
        ".work-history li",
        ".timeline-item",
        "[class*='experience'] li",
        ".work-experience .entry",
        ".job-item",
        "[data-testid='experience'] li",
    ],
    "education": [
        ".education-section .item",
        "[class*='education'] .item",
        ".education li",
        "[class*='education'] li",
        ".academic-history .entry",
        ".degree-item",
        "[data-testid='education'] li",
    ],
    "certifications": [
        ".certifications-list li",
        "[class*='cert'] li",
        ".credentials li",
        "[class*='credential'] span",
        ".certifications span",
        "[class*='cert'] span",
        "[data-testid='certifications'] li",
    ],
}


def clean(text: Optional[str]) -> Optional[str]:
    """Clean whitespace and return None if empty."""
    if text is None:
        return None
    text = re.sub(r"\s+", " ", text).strip()
    return text if text else None


async def try_selectors(
    page: Page,
    selectors: list[str],
    attr: str = "innerText",
    timeout: int = 3000
) -> Optional[str]:
    """Try multiple selectors and return the first match."""
    for sel in selectors:
        try:
            el = page.locator(sel).first
            count = await el.count()
            if count == 0:
                continue
                
            if attr == "innerText":
                val = await el.inner_text(timeout=timeout)
            else:
                val = await el.get_attribute(attr, timeout=timeout)
                
            if val and val.strip():
                return clean(val)
        except Exception as e:
            logger.debug(f"  Selector failed: {sel} ({type(e).__name__})")
            continue
    return None


async def try_list_selectors(
    page: Page,
    selectors: list[str],
    timeout: int = 3000
) -> list[str]:
    """Try multiple selectors and return all matches as list."""
    for sel in selectors:
        try:
            els = page.locator(sel)
            count = await els.count()
            if count == 0:
                continue
                
            items = []
            for i in range(min(count, 20)):  # Limit to 20 items per field
                text = await els.nth(i).inner_text(timeout=timeout)
                if text and text.strip():
                    cleaned = clean(text)
                    if cleaned and cleaned not in items:  # Avoid duplicates
                        items.append(cleaned)
                        
            if items:
                return items
        except Exception as e:
            logger.debug(f"  List selector failed: {sel} ({type(e).__name__})")
            continue
    return []


async def extract_images(page: Page, max_images: int = 5) -> list[str]:
    """
    Extract actual expert image URLs from profile page.
    Filters out SVGs, logos, social media icons, and placeholder assets.
    """
    images = []
    try:
        # Fetch all visible image sources with class names
        img_data = await page.eval_on_selector_all(
            "img",
            """els => els.map(e => ({
                src: e.src || e.getAttribute('data-src') || e.getAttribute('src'),
                className: e.className || ''
            })).filter(item => item.src && item.src.startsWith('http'))"""
        )
        
        # Filtering criteria
        exclude_keywords = [
            "logo", "facebook", "twitter", "linkedin", "instagram", "youtube",
            "footer", "header", "icon", "marker", "banner", 
            "1x1", "transperant", "svg_icons", "arrow", "menu", "search"
        ]
        
        filtered_srcs = []
        for item in img_data:
            src = item["src"]
            src_lower = src.lower()
            class_lower = item["className"].lower()
            
            # Skip SVGs and general UI assets
            if src_lower.endswith(".svg"):
                continue
                
            # Allow avatar class images even if they contain placeholder keyword
            is_avatar = any(c in class_lower for c in ["cp-avatar", "avatar", "profile-image"]) or "avatar" in src_lower
            
            if not is_avatar:
                if "placeholder" in src_lower:
                    continue
                if any(k in src_lower for k in exclude_keywords):
                    continue
                    
            filtered_srcs.append(src)
            
        # Prioritize images containing expert profile patterns
        priority_srcs = []
        other_srcs = []
        for src in filtered_srcs:
            src_lower = src.lower()
            if any(k in src_lower for k in ["expert-profile", "profile-image", "avatar", "expert", "uploads"]):
                priority_srcs.append(src)
            else:
                other_srcs.append(src)
                
        images = priority_srcs + other_srcs
        # Deduplicate and limit
        images = list(dict.fromkeys(images))[:max_images]
        logger.debug(f"  Extracted {len(images)} actual expert photos: {images}")
    except Exception as e:
        logger.debug(f"  Failed to extract images: {e}")
    return images


async def extract_links(page: Page) -> dict[str, list[str]]:
    """Extract social/website links from profile."""
    links = {"social": [], "website": []}
    try:
        all_links = await page.eval_on_selector_all(
            "a[href]",
            "els => els.map(e => ({ href: e.href, text: e.innerText.trim() }))"
        )
        
        for link in all_links:
            href = link.get("href", "").lower()
            text = link.get("text", "").lower()
            
            # Detect social media / websites
            if any(keyword in href for keyword in ["linkedin", "twitter", "facebook", "instagram", "github", "youtube"]):
                links["social"].append(link["href"])
            elif href.startswith("http") and len(link["href"]) > 10:
                links["website"].append(link["href"])
                
    except Exception as e:
        logger.debug(f"  Failed to extract links: {e}")
    return links


async def extract_profile(page: Page, url: str) -> dict[str, Any]:
    """
    Visit a profile page and extract all available data.
    Returns structured dict with profile information.
    """
    profile: dict[str, Any] = {
        "profile_url": url,
        "name": None,
        "description": None,
        "task": None,
        "category": None,
        "skills": [],
        "expertise": [],
        "experience": [],
        "education": [],
        "location": None,
        "profile_image_url": None,
        "photos": [],
        "certifications": [],
        "company": None,
        "social_links": [],
        "website_links": [],
        "images": [],
        "additional_info": {},
        "scraped_at": datetime.now(timezone.utc).isoformat(),
        "scrape_status": "success",
    }

    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=40000)
        await page.wait_for_timeout(REQUEST_DELAY_MS)
        logger.info(f"[PROFILE FETCHED] {url}")

        # Wait for main content
        for selector in ["main", ".profile-container", ".expert-profile", "[role='main']", "body"]:
            try:
                await page.wait_for_selector(selector, timeout=3000)
                break
            except PWTimeout:
                continue

        # Extract scalar fields
        logger.debug("  Extracting scalar fields...")
        for field, selectors in FIELD_SELECTORS.items():
            if field == "profile_image_url" or field == "photos" or field == "images":
                continue
            else:
                profile[field] = await try_selectors(page, selectors)

        # Custom extraction for mywastesolution.com elements (to bypass generic selectors)
        # 1. Avatar
        avatar_el = page.locator("img.cp-avatar").first
        if await avatar_el.count() > 0:
            avatar_url = await avatar_el.get_attribute("src")
            if avatar_url:
                profile["profile_image_url"] = avatar_url
                if "photos" not in profile:
                    profile["photos"] = []
                if avatar_url not in profile["photos"]:
                    profile["photos"].insert(0, avatar_url)
                    profile["images"] = profile["photos"]

        # 2. Tagline + About -> Description
        tagline = await try_selectors(page, [".cp-tagline", "p.cp-tagline"])
        about = await try_selectors(page, [".cp-about", "div.cp-about"])
        if tagline or about:
            desc_parts = []
            if tagline:
                desc_parts.append(tagline)
            if about:
                desc_parts.append(about)
            profile["description"] = "\n\n".join(desc_parts)

        # 3. Custom Experience Timeline items
        exp_timeline = []
        exp_header = page.locator("h2.cp-section-title:has-text('Experience')")
        if await exp_header.count() > 0:
            try:
                exp_items = await page.evaluate("""
                    () => {
                        const expHeader = Array.from(document.querySelectorAll('h2.cp-section-title')).find(el => el.textContent.trim() === 'Experience');
                        if (!expHeader) return [];
                        const section = expHeader.closest('.cp-section');
                        if (!section) return [];
                        const items = section.querySelectorAll('.cp-timeline-item');
                        return Array.from(items).map(item => {
                            const role = item.querySelector('.cp-timeline-role')?.textContent?.trim() || '';
                            const company = item.querySelector('.cp-timeline-company')?.textContent?.trim() || '';
                            const date = item.querySelector('.cp-timeline-date')?.textContent?.trim() || '';
                            return { role, company, date };
                        }).filter(x => x.role || x.company);
                    }
                """)
                for item in exp_items:
                    exp_timeline.append(f"{item['role']} at {item['company']} ({item['date']})")
            except Exception as e:
                logger.warning(f"Failed to evaluate Experience: {e}")
        if exp_timeline:
            profile["experience"] = exp_timeline

        # 4. Custom Qualifications/Education Timeline items
        edu_timeline = []
        qual_header = page.locator("h2.cp-section-title:has-text('Qualifications')")
        if await qual_header.count() > 0:
            try:
                edu_items = await page.evaluate("""
                    () => {
                        const qualHeader = Array.from(document.querySelectorAll('h2.cp-section-title')).find(el => el.textContent.trim() === 'Qualifications');
                        if (!qualHeader) return [];
                        const section = qualHeader.closest('.cp-section');
                        if (!section) return [];
                        const items = section.querySelectorAll('.cp-timeline-item');
                        return Array.from(items).map(item => {
                            const degree = item.querySelector('.cp-timeline-role')?.textContent?.trim() || '';
                            const institution = item.querySelector('.cp-timeline-company')?.textContent?.trim() || '';
                            const date = item.querySelector('.cp-timeline-date')?.textContent?.trim() || '';
                            return { degree, institution, date };
                        }).filter(x => x.degree || x.institution);
                    }
                """)
                for item in edu_items:
                    edu_timeline.append(f"{item['degree']}, {item['institution']} ({item['date']})")
            except Exception as e:
                logger.warning(f"Failed to evaluate Qualifications: {e}")
        if edu_timeline:
            profile["education"] = edu_timeline

        # 5. Skills & Expertise
        skills_header = page.locator("h2.cp-section-title:has-text('Skills')")
        if await skills_header.count() > 0:
            try:
                skills_data = await page.evaluate("""
                    () => {
                        const header = Array.from(document.querySelectorAll('h2.cp-section-title')).find(el => el.textContent.includes('Skills'));
                        if (!header) return { skills: [], expertise: [] };
                        const section = header.closest('.cp-section');
                        if (!section) return { skills: [], expertise: [] };
                        const h3s = Array.from(section.querySelectorAll('h3')).map(el => el.textContent.trim()).filter(Boolean);
                        const as_ = Array.from(section.querySelectorAll('a')).map(el => el.textContent.trim()).filter(Boolean);
                        return { skills: as_, expertise: h3s };
                    }
                """)
                if skills_data.get("skills"):
                    profile["skills"] = skills_data["skills"]
                if skills_data.get("expertise"):
                    profile["expertise"] = skills_data["expertise"]
            except Exception as e:
                logger.warning(f"Failed to evaluate Skills: {e}")

        # Extract list fields
        logger.debug("  Extracting list fields...")
        for field, selectors in LIST_FIELD_SELECTORS.items():
            if field in profile and profile[field]:
                continue
            profile[field] = await try_list_selectors(page, selectors)

        # Extract photos (up to 5)
        logger.debug("  Extracting photos...")
        profile["photos"] = await extract_images(page, max_images=5)
        profile["images"] = profile["photos"]
        
        # Set primary image URL
        if profile["photos"]:
            profile["profile_image_url"] = profile["photos"][0]
        
        # Extract links
        logger.debug("  Extracting links...")
        links_data = await extract_links(page)
        profile["social_links"] = links_data["social"]
        profile["website_links"] = links_data["website"]

        # Extract key-value pairs (dl/dt/dd format)
        logger.debug("  Extracting additional info...")
        try:
            pairs = await page.eval_on_selector_all(
                "dl dt, dl dd",
                """els => {
                    const out = {};
                    for (let i = 0; i < els.length - 1; i += 2) {
                        const k = els[i]?.innerText?.trim();
                        const v = els[i+1]?.innerText?.trim();
                        if (k && v && k.length < 50) out[k] = v;
                    }
                    return out;
                }"""
            )
            if pairs:
                profile["additional_info"].update(pairs)
        except Exception:
            pass

        # Extract [data-label] pairs
        try:
            labelled = await page.eval_on_selector_all(
                "[data-label]",
                "els => els.reduce((o, e) => { o[e.dataset.label] = e.innerText.trim(); return o; }, {})"
            )
            if labelled:
                profile["additional_info"].update(labelled)
        except Exception:
            pass

        # Fallback: extract name from title tag if not found
        if not profile["name"]:
            try:
                title = await page.title()
                profile["name"] = clean(title.split("|")[0].split("-")[0]) or None
            except Exception:
                pass

        # Clean up empty lists and dicts
        for lst_f in ["skills", "expertise", "experience", "education", "photos", "images", "certifications", "social_links", "website_links"]:
            if not profile[lst_f]:
                del profile[lst_f]
        if not profile["additional_info"]:
            del profile["additional_info"]

        logger.info(f"  ✓ Success: {profile.get('name', 'Unknown')} | Task: {profile.get('task', 'N/A')} | Location: {profile.get('location', 'Unknown location')}")

    except PWTimeout:
        logger.warning(f"[ERROR] Timeout loading profile: {url}")
        profile["scrape_status"] = "timeout"
    except Exception as e:
        logger.error(f"[ERROR] failed to scrape {url}: {e}")
        profile["scrape_status"] = f"error: {str(e)[:50]}"

    return profile


async def scrape_profile_worker(
    sem: asyncio.Semaphore,
    context,  # BrowserContext
    url: str,
) -> dict[str, Any]:
    """
    Worker that respects semaphore limit for concurrent scraping.
    """
    async with sem:
        page = await context.new_page()
        try:
            return await extract_profile(page, url)
        finally:
            await page.close()


if __name__ == "__main__":
    import sys
    import argparse
    from pathlib import Path
    
    # Enable parent imports
    parent_dir = str(Path(__file__).parent.parent)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
        
    from scraper.crawler import discover_profile_urls
    from scraper.parser import parse_profile_async, validate_profile
    from ai.gemini_client import structure_with_gemini
    from db import MongoDB
    from playwright.async_api import async_playwright
    from dotenv import load_dotenv

    load_dotenv()
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-8s  %(message)s",
    )
    
    parser = argparse.ArgumentParser(description="WasteSolution Expert Profile Scraper Runner")
    parser.add_argument("--max-profiles", type=int, default=20, help="Maximum profiles to scrape")
    args = parser.parse_args()
    
    # Override environment variable for crawler/orchestration
    os.environ["MAX_PROFILES"] = str(args.max_profiles)
    
    async def run_pipeline():
        db = MongoDB()
        db.connect()
        
        logger.info(f"Starting pipeline with MAX_PROFILES={args.max_profiles}")
        
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=True)
            context = await browser.new_context()
            
            # Step 1: Crawl
            urls = await discover_profile_urls(context)
            
            if not urls:
                logger.error("[ERROR] No profile URLs discovered.")
                await browser.close()
                db.disconnect()
                return
            
            # Step 2: Scrape
            sem = asyncio.Semaphore(10)
            tasks = [scrape_profile_worker(sem, context, url) for url in urls]
            
            scraped = []
            for task in asyncio.as_completed(tasks):
                try:
                    profile_raw = await task
                    
                    # Parse Profile
                    parsed = await parse_profile_async(profile_raw, use_llm=False)
                    logger.info(f"[PROFILE PARSED] {parsed.get('name', 'Unknown')}")
                    
                    # Validate
                    is_valid, reason = validate_profile(parsed)
                    if not is_valid:
                        logger.warning(f"[ERROR] Invalid profile: {parsed.get('profile_url')} - {reason}")
                        continue
                        
                    # Gemini Structuring
                    if os.getenv("GEMINI_ENABLED", "true").lower() == "true":
                        try:
                            parsed = await structure_with_gemini(parsed)
                            logger.info(f"[GEMINI EXTRACTION COMPLETE] {parsed.get('name', 'Unknown')}")
                        except Exception as e:
                            logger.error(f"[ERROR] Gemini processing: {e}")
                    
                    # Save
                    result = db.upsert_profile(parsed)
                    if result in ["inserted", "updated"]:
                        logger.info(f"[PROFILE SAVED] {parsed['profile_url']}")
                    else:
                        logger.error(f"[ERROR] Failed to save: {parsed['profile_url']}")
                        
                except Exception as e:
                    logger.error(f"[ERROR] Worker error: {e}")
            
            await browser.close()
        db.disconnect()
        logger.info("Pipeline Execution Completed.")

    asyncio.run(run_pipeline())
