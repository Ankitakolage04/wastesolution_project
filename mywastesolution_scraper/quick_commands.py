#!/usr/bin/env python3
"""
quick_commands.py - Quick reference for common commands
"""

def print_commands():
    """Print all useful commands."""
    
    commands = {
        "1. Setup": [
            "# Install Python dependencies",
            "pip install -r requirements.txt",
            "",
            "# Install Playwright browsers",
            "playwright install chromium",
        ],
        "2. Database": [
            "# Setup indexes (run once)",
            "cd mywastesolution_scraper",
            "python setup_database.py",
            "",
            "# Check profile count",
            "python -c \"from db import MongoDB; db = MongoDB(); db.connect(); print(f'Total profiles: {db.count()}'); db.disconnect()\"",
            "",
            "# View sample profile",
            "mongosh",
            "> use mywastesolution",
            "> db.profiles.findOne()",
            "> db.profiles.count()",
        ],
        "3. Scraping": [
            "# Run main scraper",
            "cd mywastesolution_scraper",
            "python main_scraper.py",
            "",
            "# Monitor logs in real-time",
            "tail -f mywastesolution_scraper/scraper.log",
            "",
            "# View profiles.json output",
            "cat mywastesolution_scraper/profiles.json",
        ],
        "4. API": [
            "# Start API server",
            "cd profiles_api",
            "python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000",
            "",
            "# Health check",
            "curl http://localhost:8000/health",
            "",
            "# API docs (interactive)",
            "http://localhost:8000/docs",
        ],
        "5. Testing": [
            "# Test MongoDB connection",
            "python -c \"from mywastesolution_scraper.db import MongoDB; db = MongoDB(); db.connect(); print('✓ MongoDB connected'); db.disconnect()\"",
            "",
            "# Fetch first 5 profiles",
            "curl 'http://localhost:8000/profiles?page=1&page_size=5'",
            "",
            "# Search by skill",
            "curl 'http://localhost:8000/profiles?skill=recycling'",
            "",
            "# Search by location",
            "curl 'http://localhost:8000/profiles?location=New+York'",
            "",
            "# Full-text search",
            "curl 'http://localhost:8000/profiles?q=waste+management'",
        ],
        "6. Monitoring": [
            "# Watch MongoDB for changes (in another terminal)",
            "mongosh",
            "> use mywastesolution",
            "> db.profiles.watch([{ $match: { operationType: 'insert' } }])",
            "",
            "# Check API logs",
            "tail -f uvicorn.log",
        ],
        "7. Cleanup & Reset": [
            "# Clear all profiles from MongoDB",
            "mongosh",
            "> use mywastesolution",
            "> db.profiles.deleteMany({})",
            "> db.profiles.countDocuments()",
            "",
            "# Delete profiles.json backup",
            "rm mywastesolution_scraper/profiles.json",
            "",
            "# Clear logs",
            "rm mywastesolution_scraper/scraper.log",
        ],
    }
    
    print("\n" + "="*80)
    print("MyWasteSolution Scraper - Quick Commands Reference")
    print("="*80 + "\n")
    
    for section, cmds in commands.items():
        print(f"\n{section}")
        print("-" * 80)
        for cmd in cmds:
            if cmd.startswith("#"):
                print(f"  {cmd}")
            elif cmd == "":
                print()
            elif cmd.startswith("http"):
                print(f"  📱 {cmd}")
            else:
                print(f"  $ {cmd}")
    
    print("\n" + "="*80)
    print("Environment Variables (.env)")
    print("="*80 + "\n")
    
    env_vars = {
        "Scraper": {
            "BASE_URL": "https://www.mywastesolution.com",
            "MAX_PROFILES": "30 (20-50 recommended)",
            "CONCURRENT_PAGES": "10 (5-15 recommended)",
            "REQUEST_DELAY_MS": "1000",
        },
        "Database": {
            "MONGO_URI": "mongodb://localhost:27017",
            "MONGO_DB_NAME": "mywastesolution",
            "MONGO_COLLECTION": "profiles",
        },
        "Gemini": {
            "GEMINI_ENABLED": "true/false",
            "GEMINI_API_KEY": "your-api-key-here",
            "GEMINI_MODEL": "gemini-pro",
        },
        "API": {
            "API_HOST": "0.0.0.0",
            "API_PORT": "8000",
            "DEBUG": "true/false",
        },
    }
    
    for section, vars in env_vars.items():
        print(f"\n{section}:")
        for key, default in vars.items():
            print(f"  {key}={default}")
    
    print("\n" + "="*80)
    print("MongoDB Text Index (for full-text search)")
    print("="*80 + "\n")
    print("  Auto-created on first scrape")
    print("  Searches across: name, description")
    print("  Usage: GET /profiles?q=waste+management")
    
    print("\n" + "="*80)
    print("Project Structure")
    print("="*80 + "\n")
    print("""
  mywastesolution_scraper/
  ├── main_scraper.py          ← Run this to scrape
  ├── setup_database.py        ← Run once for indexes
  ├── scraper/
  │   ├── crawler.py           (discover URLs)
  │   ├── extractor.py         (scrape pages)
  │   └── parser.py            (structure data)
  ├── ai/
  │   └── gemini_client.py     (optional: enhance data)
  ├── db.py                    (MongoDB client)
  └── requirements.txt
  
  profiles_api/
  ├── app/
  │   ├── main.py              ← Start API here
  │   ├── routers/profiles.py  (endpoints)
  │   ├── models/profile.py    (Pydantic models)
  │   └── core/
  │       ├── config.py        (settings)
  │       └── database.py      (async MongoDB)
  └── requirements.txt
  
  .env                         ← Configuration (create from template)
  SCRAPING_GUIDE.md           ← Full documentation
  """)
    
    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    print_commands()
