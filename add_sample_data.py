"""
add_sample_data.py - Insert sample expert profiles into MongoDB for testing.
"""

import asyncio
import json
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient

# Sample expert profiles
SAMPLE_PROFILES = [
    {
        "profile_url": "https://www.mywastesolution.com/experts/profile/jane-smith",
        "name": "Jane Smith",
        "description": "15 years in hazardous waste management and compliance.",
        "location": "London, UK",
        "skills": ["Waste Auditing", "Regulatory Compliance", "Environmental Planning"],
        "expertise": ["Hazardous Waste", "Circular Economy", "Waste Reduction"],
        "experience": [
            "Senior Consultant at EcoWaste Corp (2015–2023)",
            "Environmental Manager at GreenTech Ltd (2010–2015)",
        ],
        "education": [
            "M.Sc. Environmental Management, LSE (2010)",
            "B.Sc. Environmental Science, UCL (2009)",
        ],
        "certifications": ["ISO 14001", "WAMITAB"],
        "contact_email": "jane.smith@example.com",
        "phone": "+44 20 1234 5678",
        "website": "https://example.com/jane",
        "social_links": {
            "linkedin": "https://linkedin.com/in/janesmith",
            "twitter": "https://twitter.com/janesmith",
        },
        "scraped_at": datetime.now(timezone.utc),
        "scrape_status": "success",
    },
    {
        "profile_url": "https://www.mywastesolution.com/experts/profile/john-doe",
        "name": "John Doe",
        "description": "Expert in waste-to-energy solutions and sustainability.",
        "location": "Berlin, Germany",
        "skills": ["Energy Recovery", "Sustainability", "Process Optimization"],
        "expertise": ["Waste-to-Energy", "Industrial Waste", "Climate Action"],
        "experience": [
            "Chief Sustainability Officer at RenewTech GmbH (2018–2024)",
            "Waste Engineering Manager at EuroWaste Solutions (2012–2018)",
        ],
        "education": [
            "Ph.D. Environmental Engineering, TU Berlin (2012)",
            "B.Eng. Chemical Engineering, TU Berlin (2008)",
        ],
        "certifications": ["ISO 50001", "Green Engineering"],
        "contact_email": "john.doe@example.com",
        "phone": "+49 30 1234 5678",
        "website": "https://example.com/john",
        "social_links": {
            "linkedin": "https://linkedin.com/in/johndoe",
        },
        "scraped_at": datetime.now(timezone.utc),
        "scrape_status": "success",
    },
    {
        "profile_url": "https://www.mywastesolution.com/experts/profile/maria-garcia",
        "name": "Maria Garcia",
        "description": "Specialized in plastic recycling and circular economy models.",
        "location": "Barcelona, Spain",
        "skills": ["Plastic Recycling", "Circular Economy", "Market Analysis"],
        "expertise": ["Plastic Waste", "Recycling Innovation", "Supply Chain"],
        "experience": [
            "Director of Recycling at PlasticCircle SA (2016–2024)",
            "Research Scientist at LEITAT (2011–2016)",
        ],
        "education": [
            "M.Sc. Materials Science, UPC Barcelona (2011)",
            "B.Sc. Chemistry, UB Barcelona (2009)",
        ],
        "certifications": ["ISO 14001", "Circular Economy Expert"],
        "contact_email": "maria.garcia@example.com",
        "phone": "+34 93 1234 5678",
        "website": "https://example.com/maria",
        "social_links": {
            "linkedin": "https://linkedin.com/in/mariagarcia",
            "twitter": "https://twitter.com/mariagarcia",
        },
        "scraped_at": datetime.now(timezone.utc),
        "scrape_status": "success",
    },
]


async def add_sample_data():
    """Connect to MongoDB and insert sample profiles."""
    mongo_uri = "mongodb://localhost:27017"
    db_name = "mywastesolution"
    collection_name = "profiles"

    client = AsyncIOMotorClient(mongo_uri)
    db = client[db_name]
    collection = db[collection_name]

    try:
        # Create unique index on profile_url (skip if exists)
        try:
            await collection.create_index("profile_url", unique=True)
        except Exception:
            pass  # Index likely already exists

        # Insert profiles (upsert to avoid duplicates)
        result = await collection.insert_many(SAMPLE_PROFILES, ordered=False)
        print(f"✓ Inserted {len(result.inserted_ids)} sample profiles")

        # Show inserted data
        count = await collection.count_documents({})
        print(f"✓ Total profiles in database: {count}")

    except Exception as e:
        print(f"✗ Error: {e}")
    finally:
        client.close()


if __name__ == "__main__":
    asyncio.run(add_sample_data())
