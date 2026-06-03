"""
db.py - MongoDB connection and operations for profile storage.

Handles:
- Connection management
- Profile upsert (keyed on profile_url)
- Schema validation
- Aggregation queries for statistics
"""

import logging
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import ConnectionFailure, DuplicateKeyError
from dotenv import load_dotenv
from datetime import datetime
import os

load_dotenv()
logger = logging.getLogger(__name__)


class MongoDB:
    def __init__(self):
        self.uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
        self.db_name = os.getenv("MONGO_DB_NAME", "mywastesolution")
        self.collection_name = os.getenv("MONGO_COLLECTION", "profiles")
        self.client = None
        self.db = None
        self.collection = None

    def connect(self):
        """Establish MongoDB connection and set up indexes."""
        try:
            self.client = MongoClient(self.uri, serverSelectionTimeoutMS=5000)
            # Verify connection
            self.client.admin.command("ping")
            self.db = self.client[self.db_name]
            self.collection = self.db[self.collection_name]

            # Create indexes for efficient queries
            self.collection.create_index(
                [("profile_url", ASCENDING)], unique=True, name="profile_url_unique"
            )
            self.collection.create_index(
                [("name", ASCENDING)], name="name_index"
            )
            self.collection.create_index(
                [("category", ASCENDING)], name="category_index"
            )
            self.collection.create_index(
                [("location", ASCENDING)], name="location_index"
            )
            self.collection.create_index(
                [("task", ASCENDING)], name="task_index"
            )
            self.collection.create_index(
                [("scraped_at", DESCENDING)], name="scraped_at_index"
            )
            
            # Text index for full-text search
            try:
                self.collection.create_index(
                    [("name", "text"), ("description", "text"), ("skills", "text"), ("expertise", "text")],
                    name="text_search_index"
                )
            except Exception as e:
                logger.warning(f"Could not create text index: {e}")

            logger.info(
                f"✓ Connected to MongoDB: {self.db_name}.{self.collection_name}"
            )
        except ConnectionFailure as e:
            logger.error(f"MongoDB connection failed: {e}")
            raise

    def disconnect(self):
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed.")

    def upsert_profile(self, profile: dict) -> str:
        """
        Insert or update profile (keyed on profile_url).
        
        Returns:
            'inserted' - new profile inserted
            'updated' - existing profile updated
            'error' - something went wrong
        """
        if not profile.get("profile_url"):
            logger.warning("Profile missing URL — skipping.")
            return "error"

        try:
            # Prepare profile for storage
            profile_to_store = profile.copy()
            profile_to_store["updated_at"] = datetime.utcnow()
            
            result = self.collection.update_one(
                {"profile_url": profile["profile_url"]},
                {"$set": profile_to_store},
                upsert=True,
            )
            
            if result.upserted_id:
                logger.info(f"✓ Inserted: {profile['profile_url']}")
                return "inserted"
            elif result.modified_count > 0:
                logger.info(f"✓ Updated: {profile['profile_url']}")
                return "updated"
            else:
                logger.debug(f"⊘ Already exists: {profile['profile_url']}")
                return "updated"
                
        except DuplicateKeyError:
            logger.debug(f"Duplicate (race condition): {profile['profile_url']}")
            return "updated"
        except Exception as e:
            logger.error(f"DB error for {profile['profile_url']}: {e}")
            return "error"

    def count(self) -> int:
        """Count total profiles in collection."""
        return self.collection.count_documents({})
    
    def count_by_status(self) -> dict:
        """Count profiles by scrape_status."""
        pipeline = [
            {"$group": {"_id": "$scrape_status", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        result = {}
        for doc in self.collection.aggregate(pipeline):
            result[doc["_id"]] = doc["count"]
        return result
    
    def count_by_category(self) -> dict:
        """Count profiles by category."""
        pipeline = [
            {"$match": {"category": {"$exists": True, "$ne": None}}},
            {"$group": {"_id": "$category", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]
        result = {}
        for doc in self.collection.aggregate(pipeline):
            result[doc["_id"]] = doc["count"]
        return result
    
    def count_by_location(self) -> dict:
        """Count profiles by location."""
        pipeline = [
            {"$match": {"location": {"$exists": True, "$ne": None}}},
            {"$group": {"_id": "$location", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": 20}  # Top 20 locations
        ]
        result = {}
        for doc in self.collection.aggregate(pipeline):
            result[doc["_id"]] = doc["count"]
        return result
    
    def count_with_photos(self) -> int:
        """Count profiles that have photos."""
        return self.collection.count_documents({"photos": {"$exists": True, "$ne": []}})
    
    def get_stats(self) -> dict:
        """Get comprehensive statistics about the profile collection."""
        total = self.count()
        by_status = self.count_by_status()
        by_category = self.count_by_category()
        by_location = self.count_by_location()
        with_photos = self.count_with_photos()
        
        return {
            "total_profiles": total,
            "by_status": by_status,
            "by_category": by_category,
            "by_location": by_location,
            "profiles_with_photos": with_photos,
            "photo_coverage_percent": round((with_photos / total * 100) if total > 0 else 0, 1),
        }
