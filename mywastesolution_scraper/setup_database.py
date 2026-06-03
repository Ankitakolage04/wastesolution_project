#!/usr/bin/env python3
"""
setup_database.py - Setup MongoDB indexes for optimal performance

Indexes created:
  1. Unique index on profile_url (prevents duplicates)
  2. Text index on name + description (enables full-text search)
  3. Index on scraped_at (for sorting recent profiles)
  4. Index on scrape_status (for filtering by status)
  5. Index on location (for location filtering)
"""

import logging
from pymongo import ASCENDING, TEXT
from dotenv import load_dotenv
from db import MongoDB

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
)
logger = logging.getLogger(__name__)

load_dotenv()


def setup_indexes():
    """Create MongoDB indexes for profiles collection."""
    db = MongoDB()
    db.connect()
    
    logger.info("Setting up MongoDB indexes...")
    
    try:
        # 1. Unique index on profile_url
        db.collection.create_index(
            [("profile_url", ASCENDING)],
            unique=True,
            name="profile_url_unique"
        )
        logger.info("✓ Created unique index on profile_url")
    except Exception as e:
        logger.warning(f"Index profile_url_unique already exists or error: {e}")
    
    try:
        # 2. Text index for full-text search
        db.collection.create_index(
            [("name", TEXT), ("description", TEXT)],
            name="name_description_text"
        )
        logger.info("✓ Created text index on name + description")
    except Exception as e:
        logger.warning(f"Index name_description_text already exists or error: {e}")
    
    try:
        # 3. Index on scraped_at for sorting
        db.collection.create_index(
            [("scraped_at", ASCENDING)],
            name="scraped_at_asc"
        )
        logger.info("✓ Created index on scraped_at")
    except Exception as e:
        logger.warning(f"Index scraped_at_asc already exists or error: {e}")
    
    try:
        # 4. Index on scrape_status for filtering
        db.collection.create_index(
            [("scrape_status", ASCENDING)],
            name="scrape_status_asc"
        )
        logger.info("✓ Created index on scrape_status")
    except Exception as e:
        logger.warning(f"Index scrape_status_asc already exists or error: {e}")
    
    try:
        # 5. Index on location for filtering
        db.collection.create_index(
            [("location", ASCENDING)],
            name="location_asc"
        )
        logger.info("✓ Created index on location")
    except Exception as e:
        logger.warning(f"Index location_asc already exists or error: {e}")
    
    # List all indexes
    logger.info("\nCurrent indexes:")
    for index in db.collection.list_indexes():
        logger.info(f"  • {index['name']}: {index['key']}")
    
    db.disconnect()
    logger.info("\n✓ Database setup completed!")


if __name__ == "__main__":
    setup_indexes()
