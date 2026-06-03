# MyWasteSolution Scraper & API - Setup & Usage Guide

Complete guide for setting up the scraper, configuring LLMs, scraping profiles, and running the API.

---

## Table of Contents
1. [Quick Start](#quick-start)
2. [LLM Setup](#llm-setup)
3. [Running the Scraper](#running-the-scraper)
4. [Running the API](#running-the-api)
5. [API Endpoints](#api-endpoints)
6. [Methodology](#methodology)

---

## Quick Start

### Prerequisites
- **Python 3.9+**
- **MongoDB 5.0+** (local or Atlas)
- **API Keys** for at least one LLM provider (Groq, Gemini, or Claude)

### 1. Clone & Setup Virtual Environment

```bash
cd c:\Users\anike\OneDrive\Desktop\wastesolution_project
python -m venv venv

# Windows PowerShell
.\venv\Scripts\Activate.ps1

# macOS/Linux
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
playwright install chromium
```

### 3. Configure Environment

Copy `.env.example` to `.env` and fill in your values:

```bash
copy .env.example .env
```

Edit `.env`:
```env
# MongoDB
MONGO_URI=mongodb://localhost:27017
MONGO_DB_NAME=mywastesolution

# LLM API Keys (get from providers below)
GROQ_API_KEY=your-groq-key
GEMINI_API_KEY=your-gemini-key
ANTHROPIC_API_KEY=your-claude-key

# Primary LLM (fallback chain: groq → gemini → claude)
PRIMARY_LLM=groq
```

---

## LLM Setup

This project uses a **multi-LLM system with automatic fallback**. If one LLM hits rate limits, the system automatically switches to the next available provider.

### Why Multiple LLMs?

| LLM | Rate Limit | Best For | Cost |
|-----|-----------|----------|------|
| **Groq** | 30 req/min | Fast extraction, structured data | Free tier |
| **Gemini** | 60 req/min | Context understanding, parsing | Free tier |
| **Claude** | 5 req/min | Quality responses, complex reasoning | Free tier (limited) |

### Obtaining API Keys

#### 1. Groq (Recommended for Speed)
```
Website: https://console.groq.com
Steps:
  1. Sign up with email
  2. Go to "API Keys"
  3. Create new API key
  4. Copy to GROQ_API_KEY in .env
```

#### 2. Google Gemini
```
Website: https://aistudio.google.com/app/apikey
Steps:
  1. Click "Get API Key"
  2. Create new API key in Google Cloud
  3. Copy to GEMINI_API_KEY in .env
```

#### 3. Anthropic Claude
```
Website: https://console.anthropic.com
Steps:
  1. Sign up
  2. Go to "API Keys"
  3. Create new API key
  4. Copy to ANTHROPIC_API_KEY in .env
```

### How LLM Fallback Works

The system tries providers in this order:
1. **Primary LLM** (set by `PRIMARY_LLM=groq`)
2. **Secondary LLMs** (in order: groq, gemini, claude)

If a provider is rate-limited, the system:
- Waits for its rate limit window to reset
- Or immediately switches to the next available provider
- Automatically tracks capacity per LLM

Example scenario:
```
Groq hits rate limit (30 req/min)
  ↓
System switches to Gemini (still available)
  ↓
Gemini processes request while Groq recovers
  ↓
Next request goes back to Groq (rate limit reset)
```

### Configuring LLM Behavior

Edit `.env` to control LLM behavior:

```env
# Which LLM to prefer first
PRIMARY_LLM=groq

# Enable/disable providers
LLM_ENABLE_GROQ=true
LLM_ENABLE_GEMINI=true
LLM_ENABLE_CLAUDE=true

# Timeout for LLM calls (seconds)
LLM_TIMEOUT=30

# Number of retries on failure
LLM_RETRIES=3

# Use LLM to extract task and category
GEMINI_ENABLED=true
```

---

## Running the Scraper

### What Gets Scraped

For each profile, the scraper extracts:
- **Photos** (up to 5 image URLs)
- **Name** (profile owner)
- **Description** (bio/about section)
- **Task** (what they do - AI-identified)
- **Location** (geographic area)
- **Category** (service type - AI-identified)
- **Skills** (list of skills)
- **Expertise** (areas of expertise)
- **Education** (degrees, institutions)
- **Experience** (work history)
- **Additional Info** (contact, website, etc.)

### Run the Scraper

```bash
cd mywastesolution_scraper
python main_scraper.py
```

### What Happens

The scraper runs in these phases:

#### Phase 1: Discovery
- Crawls listing pages to find profile URLs
- Follows pagination to discover more profiles
- Stops when MAX_PROFILES is reached
- Output: 50-100 profile URLs

#### Phase 2: Extraction
- Visits each profile page (async, concurrent)
- Extracts all visible fields using CSS selectors
- Extracts up to 5 photos
- Stores raw extracted data
- Timeout: 5 seconds per page

#### Phase 3: Parsing & LLM Processing
- Cleans and normalizes text fields
- Parses experience/education items
- Uses LLM to identify **task** and **category**
- Validates data integrity

#### Phase 4: Storage
- Upserts profiles into MongoDB (keyed on profile_url)
- Generates JSON backup (profiles.json)
- Logs statistics

### Monitor Progress

Logs are written to:
- **Console** (real-time)
- **File**: `scraper.log` (persistent)

Example output:
```
========================
MyWasteSolution Profile Scraper
========================
Configuration:
  Base URL: https://www.mywastesolution.com
  Max Profiles: 50
  Concurrent Pages: 10
  Gemini Enabled: true
========================

📄 Scraping profile: https://www.mywastesolution.com/experts/profile/xyz
  Extracting scalar fields...
  Extracting list fields...
  Extracting photos...
  ✓ Success: Jane Smith | Task: Hazardous Waste Consultant | Location: London

[LLM] Groq processing profile (task extraction)
[LLM] ✓ Identified task="Consultant", category="Hazardous Waste"

✓ Inserted: https://www.mywastesolution.com/experts/profile/xyz
```

### Scraper Configuration

Edit `.env` to control scraping behavior:

```env
# Website settings
BASE_URL=https://www.mywastesolution.com
MAX_PROFILES=50

# Concurrency (be careful not to overload target server)
CONCURRENT_PAGES=10

# Delay between requests per tab (milliseconds)
REQUEST_DELAY_MS=1000

# Headless mode (true = no browser window, false = watch browser)
HEADLESS=true

# Output file
OUTPUT_JSON=profiles.json
```

### Troubleshooting Scraper

**Problem**: "MongoDB connection failed"
```
Solution: Check MONGO_URI in .env
  mongodb://localhost:27017          (local)
  mongodb+srv://user:pwd@host        (Atlas)
```

**Problem**: "No LLM providers configured"
```
Solution: Add API keys to .env
  GROQ_API_KEY=xyz
  GEMINI_API_KEY=abc
```

**Problem**: "Timeout loading profile"
```
Solution: Increase REQUEST_DELAY_MS or reduce CONCURRENT_PAGES
```

---

## Running the API

### Start the Server

```bash
cd profiles_api
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Server Output

```
INFO:     Application startup complete
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     API docs available at http://localhost:8000/docs
```

### Access the API

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **API Base**: http://localhost:8000/api/profiles

---

## API Endpoints

### Base URL
```
http://localhost:8000/api/profiles
```

### 1. List Profiles (Paginated)

```
GET /profiles
```

**Query Parameters**:
- `page` (int): Page number (1-based), default: 1
- `page_size` (int): Results per page (1-100), default: 20
- `name` (str): Filter by name (partial match, case-insensitive)
- `location` (str): Filter by location (partial match)
- `category` (str): Filter by category (partial match)
- `task` (str): Filter by task/specialization (partial match)
- `skill` (str): Filter by skill (partial match)
- `expertise` (str): Filter by expertise area (partial match)
- `q` (str): Full-text search across name + description
- `status` (str): Filter by scrape status (success, partial, error)
- `sort_by` (str): Sort field (name, location, category, task, scraped_at, scrape_status)
- `sort_order` (str): asc or desc

**Example**:
```bash
curl "http://localhost:8000/api/profiles?category=Hazardous%20Waste&location=London&page=1&page_size=20"
```

**Response**:
```json
{
  "total": 245,
  "page": 1,
  "page_size": 20,
  "pages": 13,
  "results": [
    {
      "id": "507f1f77bcf86cd799439011",
      "profile_url": "https://www.mywastesolution.com/experts/profile/...",
      "name": "Jane Smith",
      "description": "15 years in hazardous waste management...",
      "location": "London, UK",
      "task": "Hazardous Waste Consultant",
      "category": "Hazardous Waste",
      "profile_image_url": "https://...",
      "photos": ["https://...", "https://..."],
      "skills": ["Waste Auditing", "Regulatory Compliance"],
      "expertise": ["Hazardous Waste", "Circular Economy"],
      "education": [...],
      "experience": [...],
      "scraped_at": "2024-06-03T10:30:00Z",
      "scrape_status": "success",
      "llm_processed": true,
      "llm_provider": "groq"
    }
  ]
}
```

### 2. Get Single Profile

```
GET /profiles/{id}
```

**Parameters**:
- `id` (str): MongoDB ObjectId

**Example**:
```bash
curl "http://localhost:8000/api/profiles/507f1f77bcf86cd799439011"
```

### 3. Get Profile by URL

```
GET /profiles/by-url/lookup?url=...
```

**Parameters**:
- `url` (str): Exact profile URL

**Example**:
```bash
curl "http://localhost:8000/api/profiles/by-url/lookup?url=https://www.mywastesolution.com/experts/profile/xyz"
```

### 4. Get Statistics

```
GET /profiles/stats/overview
```

**Response**:
```json
{
  "total_profiles": 245,
  "scraped_success": 220,
  "scraped_partial": 15,
  "scraped_error": 10,
  "by_category": {
    "Hazardous Waste": 45,
    "Recycling": 38,
    "Consulting": 32
  },
  "by_location": {
    "London": 25,
    "New York": 18,
    "Toronto": 12
  },
  "by_llm_provider": {
    "groq": 150,
    "gemini": 70
  },
  "total_photos": 892,
  "profiles_with_photos": 210
}
```

### 5. Get Categories

```
GET /profiles/filters/categories
```

**Response**:
```json
{
  "Hazardous Waste": 45,
  "Recycling": 38,
  "Consulting": 32,
  "Waste Management": 28
}
```

### 6. Get Tasks

```
GET /profiles/filters/tasks
```

**Response**:
```json
{
  "Consultant": 95,
  "Manager": 42,
  "Specialist": 38,
  "Director": 25
}
```

### 7. Get Locations

```
GET /profiles/filters/locations
```

**Response**:
```json
{
  "London": 25,
  "New York": 18,
  "Toronto": 12
}
```

### 8. Get Profile Photos

```
GET /profiles/{id}/photos
```

**Response**:
```json
[
  "https://example.com/photo1.jpg",
  "https://example.com/photo2.jpg",
  "https://example.com/photo3.jpg"
]
```

---

## Methodology

### Scraping Approach

1. **URL Discovery**
   - Crawl listing pages using Playwright
   - Extract URLs matching `/experts/profile/` pattern
   - Follow pagination links
   - Deduplicate and limit to MAX_PROFILES

2. **Data Extraction**
   - Use CSS selector fallbacks (robust to HTML variations)
   - Extract photos from all `<img>` tags (filter out placeholders)
   - Parse lists (skills, expertise) from `<li>` elements
   - Extract key-value data from `<dl>/<dt>/<dd>` format
   - Timeout protection (5s per page)

3. **AI-Powered Enhancement**
   - Use LLM to identify **task** (what they do) from description
   - Use LLM to identify **category** (service type) from profile
   - Validate that LLM doesn't hallucinate (uses profile context only)
   - Automatic fallback if LLM provider hits rate limit

4. **Data Prevention**
   - Validate URLs (image URLs must start with http/https)
   - Check photo count (max 5)
   - Sanitize text (remove XSS/SQL injection patterns)
   - Unique index on `profile_url` prevents duplicates
   - Timestamp tracking for audit trails

5. **Storage**
   - Upsert to MongoDB (idempotent operations)
   - Store extraction metadata (timestamp, status, LLM provider)
   - Generate JSON backup after each run
   - Aggregate statistics for reporting

### Why Multi-LLM?

The project uses multiple LLMs because:

1. **Rate Limit Management**: Different providers have different limits
   - Groq: 30 req/min (fastest)
   - Gemini: 60 req/min
   - Claude: 5 req/min (highest quality)

2. **Cost Optimization**: Free tiers mean zero cost for 50-100 profiles

3. **Resilience**: If one LLM is down, others continue working

4. **Quality**: Can use high-quality Claude for important profiles when available

### Data Flow

```
Website
   ↓
Playwright Crawler (discover URLs)
   ↓
Profile Pages (50-100)
   ↓
Playwright Extractor (parallel, 10 concurrent)
   ↓
Raw Data (photos, name, bio, etc.)
   ↓
Parser (clean, normalize, validate)
   ↓
LLM Manager (identify task & category)
   ↓
Groq/Gemini/Claude (rate-limited, auto-fallback)
   ↓
Structured Profile
   ↓
MongoDB (upsert, deduplicate)
   ↓
JSON Backup (profiles.json)
   ↓
FastAPI (serve to frontend)
   ↓
Web/Mobile Client
```

---

## Performance Metrics

With default settings:

| Metric | Value |
|--------|-------|
| **Discovery Time** | 30 seconds (50 profiles) |
| **Extraction Time** | 5-10 minutes (50 profiles @ 10 concurrent) |
| **LLM Processing** | 2-3 minutes (Groq @ 30 req/min) |
| **Total Time** | ~15-20 minutes (first run) |
| **Photos Extracted** | 85-95% of profiles |
| **Task/Category Identified** | 80-90% of profiles |
| **API Response Time** | <100ms (cached) |

---

## Troubleshooting

### Scraper Issues

**No profiles found**
- Check `BASE_URL` is correct
- Verify internet connection
- Check `REQUEST_DELAY_MS` (may need to increase)

**Timeout errors**
- Reduce `CONCURRENT_PAGES` (e.g., 10 → 5)
- Increase `REQUEST_DELAY_MS` (e.g., 1000 → 2000)
- Check target website is responding

**LLM errors**
- Verify API keys in `.env`
- Check rate limits not exceeded
- Try disabling LLM: `LLM_ENABLE_GROQ=false`

### API Issues

**Profiles not appearing**
- Confirm MongoDB connection works
- Run scraper first: `python main_scraper.py`
- Check MongoDB has data: `db.profiles.count()`

**Slow queries**
- Ensure MongoDB indexes exist
- Use pagination: `?page=1&page_size=20`
- Avoid large full-text searches

---

## Questions?

See `IMPLEMENTATION_PLAN.md` for complete technical specifications.
