# MyWasteSolution Scraper - Implementation Plan

## Overview
Complete scraping pipeline for mywastesolution.com profile data with multi-LLM support, data persistence, and API delivery.

---

## Part 1: LLM Management & Initialization

### Architecture
```
LLMManager (main orchestrator)
├── GroqClient (free tier: 30 req/min)
├── GeminiClient (free tier: 60 req/min)
├── ClaudeClient (free tier: 5 req/min)
└── FallbackStrategy (capacity-aware switching)
```

### Key Decisions
1. **Which LLMs?**
   - **Groq (Mixtral)**: Fastest, free tier, good for structured extraction
   - **Gemini 1.5**: Good for context understanding, free tier
   - **Claude 3.5 Sonnet**: Best quality but limited free tier
   - **Fallback**: If primary LLM hits rate limit, switch to next available

2. **Rate Limits Management**
   - Track call counts per LLM per minute
   - Implement queuing and prioritization
   - Log capacity events

3. **Configuration**
   ```env
   # LiteLLM provider keys
   GROQ_API_KEY=xxx
   GEMINI_API_KEY=xxx
   ANTHROPIC_API_KEY=xxx
   
   # Rate limit settings
   LLM_TIMEOUT=30
   LLM_RETRIES=3
   PRIMARY_LLM=groq  # fallback order: groq→gemini→claude
   ```

### Implementation Files
- `mywastesolution_scraper/ai/llm_manager.py` — orchestrator + fallback logic
- `mywastesolution_scraper/ai/providers/` — provider-specific clients
- `.env.example` — API keys and configuration

---

## Part 2: Enhanced Scraper

### Fields to Extract
| Field | Source | Type | Notes |
|-------|--------|------|-------|
| profile_url | URL | string | Unique identifier |
| photos | Profile page | list[str] | Up to 5 image URLs |
| name | h1/title | string | Profile owner name |
| description | Bio section | string | Long-form bio |
| task | ? | string | What they do / specialization |
| location | Address block | string | Geographic location |
| category | Tags/badges | string | Waste type, service type |
| skills | List section | list[str] | Technical/domain skills |
| expertise | List section | list[str] | Areas of expertise |
| education | Edu section | list | Degrees, institutions, years |

### Scraping Methodology
1. **Discovery Phase**
   - Crawl listing pages → find `/experts/profile/` URLs
   - Pagination support for all pages
   - Deduplicate URLs

2. **Extraction Phase** (async, concurrent)
   - Playwright + multiple CSS selector fallbacks
   - Photo extraction: all `<img>` tags with filtering
   - List parsing: `<ul>/<li>` and badge-based extraction
   - Timeout handling (5s per page)

3. **Enrichment Phase**
   - Use LLM to parse/validate extracted data
   - Identify task and category from description/bio
   - Clean and normalize text fields

4. **Storage Phase**
   - Upsert to MongoDB (keyed on `profile_url`)
   - Store extraction metadata (timestamps, scrape status)
   - Generate backup JSON

### Implementation Files
- `mywastesolution_scraper/scraper/extractor.py` — update for photos, task, category
- `mywastesolution_scraper/scraper/parser.py` — LLM-assisted parsing
- Configuration in `.env`

---

## Part 3: Data Prevention & Storage

### Prevention Strategy
1. **Input Validation**
   - Validate URLs (image, profile)
   - Check image existence (HEAD request)
   - Sanitize text fields (no XSS, SQL injection)

2. **Data Integrity**
   - Unique index on `profile_url`
   - Required fields validation
   - Timestamp tracking for audits

3. **Rate Limiting**
   - Respect site robots.txt
   - 1s delay between requests per tab
   - Concurrent page limit (default 10)

### MongoDB Schema
```javascript
{
  _id: ObjectId,
  profile_url: String (unique),
  photos: [String],  // URLs to profile images
  name: String,
  description: String,
  task: String,      // e.g. "Hazardous Waste Consultant"
  location: String,
  category: String,  // e.g. "Hazardous Waste, Recycling"
  skills: [String],
  expertise: [String],
  education: [
    {
      degree: String,
      institution: String,
      year: String
    }
  ],
  scraped_at: Date,
  scrape_status: "success" | "partial" | "error",
  error_message: String (optional),
  llm_processed: Boolean,
  llm_provider: String (optional)
}
```

### Implementation Files
- `mywastesolution_scraper/db.py` — schema validation
- `profiles_api/app/models/profile.py` — response models
- MongoDB indexes setup script

---

## Part 4: API for Displaying Data

### Endpoints
```
GET /profiles
  - Query: page, page_size, sort_by, sort_order
  - Filter: skill=, expertise=, location=, category=, task=, name=
  - Returns: paginated ProfileOut[]

GET /profiles/{id}
  - Returns: complete ProfileOut with all fields

GET /profiles/by-url?url=...
  - Returns: ProfileOut

GET /profiles/count
  - Returns: { total: int, by_category: {...}, by_location: {...} }

GET /profiles/{id}/photos
  - Returns: list of photo URLs

POST /profiles/search
  - Full-text search across name, description, skills
```

### Implementation Files
- `profiles_api/app/routers/profiles.py` — route handlers
- `profiles_api/app/core/database.py` — async MongoDB ops

---

## Execution Timeline

| Phase | Task | Duration | Owner |
|-------|------|----------|-------|
| 1a | Create LLM manager + providers | 2h | Backend |
| 1b | Environment setup, testing | 1h | Backend |
| 2a | Update extractor for photos/task/category | 2.5h | Backend |
| 2b | Parser + LLM integration | 1.5h | Backend |
| 3a | Update MongoDB schema and validation | 1h | Backend |
| 3b | Profile counting logic | 0.5h | Backend |
| 4a | Update API models | 1h | Backend |
| 4b | Add new endpoints | 2h | Backend |
| 5 | Integration testing, docs | 3h | QA |
| **Total** | | **15h** | |

---

## Success Criteria
- [ ] Scrape 50+ profiles with all fields populated
- [ ] Multi-LLM fallback working (one LLM always available)
- [ ] Photos extracted for 90%+ of profiles
- [ ] Task and category identified for 85%+ of profiles
- [ ] API returns all fields correctly
- [ ] Profile count endpoint working
- [ ] Data validation prevents corrupt entries
- [ ] Rate limiting working (no 429 errors from site)

---

## Key Files Summary
```
mywastesolution_scraper/
├── ai/
│   ├── llm_manager.py          ← CREATE (orchestrator)
│   ├── providers/
│   │   ├── groq_client.py       ← CREATE
│   │   ├── gemini_client.py     ← UPDATE
│   │   └── claude_client.py     ← CREATE
│   └── __init__.py
├── scraper/
│   ├── crawler.py               ← UPDATE (photo handling)
│   ├── extractor.py             ← UPDATE (photos, task, category)
│   ├── parser.py                ← UPDATE (LLM integration)
│   └── __init__.py
├── main_scraper.py              ← UPDATE (logging, reporting)
├── db.py                        ← UPDATE (schema validation)
└── models/profile.py            ← CREATE (Pydantic models)

profiles_api/
├── app/
│   ├── models/
│   │   └── profile.py           ← UPDATE
│   ├── routers/
│   │   └── profiles.py          ← UPDATE (new endpoints)
│   ├── core/
│   │   └── database.py          ← UPDATE (async ops)
│   └── main.py                  ← UPDATE (new routes)
└── run.py

Root:
├── requirements.txt             ← UPDATE (add litellm, etc.)
├── .env.example                 ← CREATE (with new keys)
└── IMPLEMENTATION_PLAN.md       ← THIS FILE
```
