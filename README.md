# MyWasteSolution Expert Profile Scraper

Async Playwright scraper that collects all `/experts/profile/` pages from
[mywastesolution.com](https://www.mywastesolution.com), stores profiles in
MongoDB, and writes a JSON backup.

---

## Project Structure

```
mywastesolution_scraper/
├── scraper.py        # Main scraper (discovery + extraction + persistence)
├── db.py             # MongoDB connection & upsert logic
├── requirements.txt  # Python dependencies
├── .env              # Environment config (copy from .env.example)
├── profiles.json     # Auto-generated JSON backup (after first run)
└── scraper.log       # Auto-generated log file (after first run)
```

---

## Prerequisites

| Requirement | Version |
|---|---|
| Python | 3.9 + |
| MongoDB | 5.0 + (local or Atlas) |

---

## Setup

### 1 — Clone / copy the project

```bash
cd mywastesolution_scraper
```

### 2 — Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
```

### 3 — Install dependencies

```bash
pip install -r requirements.txt
```

### 4 — Install Playwright browsers

```bash
playwright install chromium
```

### 5 — Configure environment

Edit `.env` to match your setup:

```dotenv
MONGO_URI=mongodb://localhost:27017   # or mongodb+srv://... for Atlas
MONGO_DB_NAME=mywastesolution
MONGO_COLLECTION=profiles

BASE_URL=https://www.mywastesolution.com
HEADLESS=true          # set false to watch the browser
CONCURRENT_PAGES=3     # parallel tabs; increase carefully
REQUEST_DELAY_MS=1000  # ms between requests per tab

OUTPUT_JSON=profiles.json
```

---

## Run

```bash
python scraper.py
```

Progress is logged to both the terminal and `scraper.log`.

---

## Output

### MongoDB document shape

```json
{
  "profile_url":       "https://www.mywastesolution.com/experts/profile/...",
  "name":              "Jane Smith",
  "description":       "15 years in hazardous waste management...",
  "skills":            ["Waste Auditing", "Regulatory Compliance"],
  "expertise":         ["Hazardous Waste", "Circular Economy"],
  "experience":        ["Senior Consultant at XYZ Corp (2015–2023)", "..."],
  "education":         ["B.Sc. Environmental Science, UCL (2009)"],
  "location":          "London, UK",
  "profile_image_url": "https://cdn.mywastesolution.com/avatars/jane.jpg",
  "additional_info":   { "Languages": "English, French" },
  "scraped_at":        "2024-06-01T10:23:45+00:00",
  "scrape_status":     "success"
}
```

Missing fields are stored as `null` (scalars) or `[]` (lists).

### profiles.json

A full array of every scraped profile written after each run.

---

## Duplicate Prevention

A **unique index** on `profile_url` is created automatically on first run.
Re-running the scraper is safe — existing profiles are skipped (`$setOnInsert`
semantics), so no data is overwritten or duplicated.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `0 profile URLs found` | Site structure changed | Open `BASE_URL/experts` manually; update `PROFILE_PATH_RE` and seed URLs in `scraper.py` |
| `MongoDB connection failed` | Mongo not running | `mongod --dbpath /data/db` or check Atlas URI |
| Fields all `null` | CSS selectors changed | Add the new selectors to `FIELD_SELECTORS` / `LIST_FIELD_SELECTORS` in `scraper.py` |
| `TimeoutError` on profiles | Slow network or JS-heavy pages | Increase `REQUEST_DELAY_MS`; set `HEADLESS=false` to inspect |
| Rate-limited / blocked | Too many concurrent requests | Reduce `CONCURRENT_PAGES` to `1` and increase `REQUEST_DELAY_MS` |
