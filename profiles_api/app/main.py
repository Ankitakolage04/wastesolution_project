import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.database import connect, disconnect
from app.routers import profiles

logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


# ── lifespan (replaces on_event) ──────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect()
    yield
    await disconnect()


# ── app ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="MyWasteSolution Profiles API",
    description=(
        "REST API for querying expert profiles scraped from mywastesolution.com.\n\n"
        "**Filtering** — use `skill=`, `expertise=`, `location=`, `name=` for "
        "case-insensitive partial matches. Use `q=` for full-text search "
        "(requires MongoDB text index).\n\n"
        "**Pagination** — `page` (1-based) and `page_size` (max 100).\n\n"
        "**Sorting** — `sort_by` ∈ {name, location, scraped_at, scrape_status} "
        "and `sort_order` ∈ {asc, desc}."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ──────────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # tighten in production
    allow_methods=["GET"],
    allow_headers=["*"],
)


# ── global error handlers ─────────────────────────────────────────────────────

@app.exception_handler(Exception)
async def unhandled_exception(request: Request, exc: Exception):
    logger.exception("Unhandled error: %s", exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "type": type(exc).__name__},
    )


# ── routes ────────────────────────────────────────────────────────────────────

app.include_router(profiles.router)


@app.get("/search", tags=["profiles"], summary="Search expert profiles")
async def search_root(
    filters: profiles.ProfileFilters = profiles.Depends(profiles.parse_filters)
):
    """Search profiles from MongoDB (delegates to profiles endpoint)."""
    return await profiles.list_profiles(filters)


@app.get("/stats", tags=["profiles"], summary="Get profile statistics")
async def stats_root():
    """Get scraper and profile metrics from MongoDB."""
    return await profiles.get_stats()


@app.get("/", tags=["health"], summary="Health check")
async def health():
    return {"status": "ok", "version": app.version}


@app.get("/health", tags=["health"], summary="Detailed health check")
async def health_detail():
    from app.core.database import get_client
    try:
        await get_client().admin.command("ping")
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {e}"
    return {"api": "ok", "mongodb": db_status}
