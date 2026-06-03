"""
main_scraper.py - Main orchestrator for the complete scraping pipeline

Pipeline:
  1. Crawl website to discover profile URLs (max 20-50)
  2. Scrape each profile page (async with concurrency limit)
  3. Parse extracted data into structured format
  4. Optionally structure with Gemini
  5. Upsert into MongoDB
  6. Generate report

Usage:
  python main_scraper.py
  
Environment variables:
  BASE_URL: Website to scrape (default: https://www.mywastesolution.com)
  MAX_PROFILES: Max profiles to scrape (default: 30)
  CONCURRENT_PAGES: Concurrent browser pages (default: 10)
  MONGO_URI: MongoDB connection string
  MONGO_DB_NAME: MongoDB database name
  MONGO_COLLECTION: MongoDB collection name
  GEMINI_ENABLED: Enable Gemini processing (default: true)
  GEMINI_API_KEY: Google Gemini API key
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from playwright.async_api import async_playwright, Browser, BrowserContext

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scraper.crawler import discover_profile_urls
from scraper.extractor import scrape_profile_worker
from scraper.parser import parse_profile, validate_profile
from ai.gemini_client import structure_with_gemini
from db import MongoDB

# Load environment
load_dotenv()

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("scraper.log", encoding="utf-8", mode="a"),
    ],
)
logger = logging.getLogger(__name__)

# Configuration
BASE_URL = os.getenv("BASE_URL", "https://www.mywastesolution.com")
MAX_PROFILES = int(os.getenv("MAX_PROFILES", "30"))
CONCURRENT_PAGES = int(os.getenv("CONCURRENT_PAGES", "10"))
REQUEST_DELAY_MS = int(os.getenv("REQUEST_DELAY_MS", "1000"))
OUTPUT_JSON = os.getenv("OUTPUT_JSON", "profiles.json")
USE_GEMINI = os.getenv("GEMINI_ENABLED", "true").lower() == "true"


class ScraperOrchestrator:
    """Manages the complete scraping workflow."""
    
    def __init__(self):
        self.db = MongoDB()
        self.profiles: list[dict[str, Any]] = []
        self.stats = {
            "crawled_urls": 0,
            "scraped_profiles": 0,
            "inserted_profiles": 0,
            "skipped_profiles": 0,
            "errors": 0,
            "gemini_processed": 0,
        }
    
    async def run(self):
        """Execute the complete scraping pipeline."""
        try:
            logger.info(f"\n{'='*80}")
            logger.info(f"MyWasteSolution Profile Scraper")
            logger.info(f"{'='*80}")
            logger.info(f"Configuration:")
            logger.info(f"  Base URL: {BASE_URL}")
            logger.info(f"  Max Profiles: {MAX_PROFILES}")
            logger.info(f"  Concurrent Pages: {CONCURRENT_PAGES}")
            logger.info(f"  Gemini Enabled: {USE_GEMINI}")
            logger.info(f"{'='*80}\n")
            
            # Connect to MongoDB
            self.db.connect()
            
            # Start browser
            async with async_playwright() as playwright:
                browser = await playwright.chromium.launch(headless=True)
                
                # Phase 1: Discover profile URLs
                logger.info("PHASE 1: Crawling website to discover profile URLs")
                logger.info(f"{'-'*80}")
                urls = await self._crawl(browser)
                self.stats["crawled_urls"] = len(urls)
                
                if not urls:
                    logger.error("❌ No profile URLs discovered!")
                    return False
                
                # Phase 2: Scrape profiles
                logger.info(f"\nPHASE 2: Scraping {len(urls)} profiles")
                logger.info(f"{'-'*80}")
                await self._scrape(browser, urls)
                
                # Phase 3: Save to MongoDB
                logger.info(f"\nPHASE 3: Saving profiles to MongoDB")
                logger.info(f"{'-'*80}")
                await self._save_to_mongodb()
                
                # Close browser
                await browser.close()
            
            # Phase 4: Generate report
            logger.info(f"\nPHASE 4: Generating report")
            logger.info(f"{'-'*80}")
            self._generate_report()
            
            logger.info(f"\n{'='*80}")
            logger.info(f"✓ Scraping completed successfully!")
            logger.info(f"{'='*80}\n")
            
            return True
            
        except Exception as e:
            logger.exception(f"❌ Fatal error: {e}")
            return False
        finally:
            # Cleanup
            self.db.disconnect()
    
    async def _crawl(self, browser: Browser) -> set[str]:
        """Phase 1: Discover profile URLs."""
        context = await browser.new_context()
        try:
            urls = await discover_profile_urls(context)
            logger.info(f"\n✓ Discovered {len(urls)} profile URLs\n")
            return urls
        finally:
            await context.close()
    
    async def _scrape(self, browser: Browser, urls: set[str]):
        """Phase 2: Scrape profile content."""
        context = await browser.new_context()
        try:
            # Create semaphore to limit concurrent pages
            sem = asyncio.Semaphore(CONCURRENT_PAGES)
            
            # Create tasks for all profiles
            tasks = [
                scrape_profile_worker(sem, context, url)
                for url in urls
            ]
            
            # Execute with progress
            completed = 0
            for task in asyncio.as_completed(tasks):
                try:
                    profile = await task
                    completed += 1
                    
                    # Parse the profile
                    parsed = parse_profile(profile)
                    
                    # Validate
                    is_valid, reason = validate_profile(parsed)
                    if not is_valid:
                        logger.warning(f"⚠️  Invalid profile ({reason}): {profile.get('profile_url')}")
                        self.stats["errors"] += 1
                        continue
                    
                    # Optionally process with Gemini
                    if USE_GEMINI:
                        try:
                            parsed = await structure_with_gemini(parsed)
                            self.stats["gemini_processed"] += 1
                        except Exception as e:
                            logger.warning(f"Gemini processing failed: {e}")
                    
                    self.profiles.append(parsed)
                    self.stats["scraped_profiles"] += 1
                    
                    logger.info(f"[{completed}/{len(urls)}] ✓ Scraped: {parsed.get('name', 'Unknown')}")
                    
                except Exception as e:
                    logger.error(f"❌ Error processing profile: {e}")
                    self.stats["errors"] += 1
            
            logger.info(f"\n✓ Scraped {self.stats['scraped_profiles']} profiles")
            
        finally:
            await context.close()
    
    async def _save_to_mongodb(self):
        """Phase 3: Save profiles to MongoDB."""
        for i, profile in enumerate(self.profiles, 1):
            result = self.db.upsert_profile(profile)
            
            if result == "inserted":
                self.stats["inserted_profiles"] += 1
                logger.info(f"[{i}/{len(self.profiles)}] ➕ Inserted: {profile.get('name', 'Unknown')}")
            elif result == "skipped":
                self.stats["skipped_profiles"] += 1
                logger.debug(f"[{i}/{len(self.profiles)}] ⏭️  Already exists: {profile.get('profile_url')}")
            else:
                self.stats["errors"] += 1
                logger.error(f"[{i}/{len(self.profiles)}] ❌ Error: {profile.get('profile_url')}")
        
        # Save JSON backup
        with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
            json.dump(self.profiles, f, indent=2, ensure_ascii=False)
        logger.info(f"✓ Saved JSON backup: {OUTPUT_JSON}")
    
    def _generate_report(self):
        """Phase 4: Generate summary report."""
        total_in_db = self.db.count()
        
        logger.info(f"\n{'='*80}")
        logger.info(f"SCRAPING REPORT")
        logger.info(f"{'='*80}")
        logger.info(f"Crawling:")
        logger.info(f"  URLs discovered: {self.stats['crawled_urls']}")
        logger.info(f"\nScraping:")
        logger.info(f"  Profiles scraped: {self.stats['scraped_profiles']}")
        logger.info(f"  Gemini processed: {self.stats['gemini_processed']}")
        logger.info(f"  Errors: {self.stats['errors']}")
        logger.info(f"\nDatabase:")
        logger.info(f"  Inserted: {self.stats['inserted_profiles']}")
        logger.info(f"  Skipped (already existed): {self.stats['skipped_profiles']}")
        logger.info(f"  Total in MongoDB: {total_in_db}")
        logger.info(f"\nOutput:")
        logger.info(f"  JSON backup: {OUTPUT_JSON}")
        logger.info(f"  Log file: scraper.log")
        logger.info(f"{'='*80}\n")


async def main():
    """Main entry point."""
    orchestrator = ScraperOrchestrator()
    success = await orchestrator.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
