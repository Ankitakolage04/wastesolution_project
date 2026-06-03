import logging
from typing import Annotated
from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, Depends, HTTPException, Query
from pymongo import ASCENDING, DESCENDING

from app.core.database import get_collection
from app.core.config import settings
from app.models.profile import (
    ProfileFilters, 
    ProfileOut, 
    PaginatedProfiles,
    ProfileStatsResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/profiles", tags=["profiles"])

# ── allowed sort fields (whitelist to prevent injection) ──────────────────────
SORTABLE_FIELDS = {"name", "location", "scraped_at", "scrape_status", "category", "task"}
FILTERABLE_FIELDS = {"category", "task", "location", "name", "skill", "expertise"}


# ── dependency: parse + validate all query params ─────────────────────────────

def parse_filters(
    skill: Annotated[str | None, Query(description="Filter by skill (case-insensitive, partial match)")] = None,
    expertise: Annotated[str | None, Query(description="Filter by expertise area")] = None,
    location: Annotated[str | None, Query(description="Filter by location (partial match)")] = None,
    category: Annotated[str | None, Query(description="Filter by category")] = None,
    task: Annotated[str | None, Query(description="Filter by task/specialization")] = None,
    name: Annotated[str | None, Query(description="Filter by name (partial match)")] = None,
    q: Annotated[str | None, Query(description="Full-text search across name + description")] = None,
    status: Annotated[str | None, Query(description="Filter by scrape_status")] = None,
    page: Annotated[int, Query(ge=1, description="Page number (1-based)")] = 1,
    page_size: Annotated[int, Query(ge=1, le=100, alias="page_size", description="Results per page")] = settings.default_page_size,
    sort_by: Annotated[str, Query(description="Field to sort by")] = "scraped_at",
    sort_order: Annotated[str, Query(description="'asc' or 'desc'")] = "desc",
) -> ProfileFilters:
    if sort_by not in SORTABLE_FIELDS:
        sort_by = "scraped_at"
    if sort_order not in ("asc", "desc"):
        sort_order = "desc"
    return ProfileFilters(
        skill=skill,
        expertise=expertise,
        location=location,
        category=category,
        task=task,
        name=name,
        q=q,
        status=status,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order,
    )


# ── query builder ─────────────────────────────────────────────────────────────

def build_query(f: ProfileFilters) -> dict:
    query: dict = {}

    # Full-text search (requires text index on name + description)
    if f.q:
        query["$text"] = {"$search": f.q}

    # Array-field case-insensitive partial matches
    if f.skill:
        query["skills"] = {"$elemMatch": {"$regex": f.skill, "$options": "i"}}

    if f.expertise:
        query["expertise"] = {"$elemMatch": {"$regex": f.expertise, "$options": "i"}}

    # String-field partial matches
    if f.location:
        query["location"] = {"$regex": f.location, "$options": "i"}

    if f.category:
        query["category"] = {"$regex": f.category, "$options": "i"}
    
    if f.task:
        query["task"] = {"$regex": f.task, "$options": "i"}

    if f.name:
        query["name"] = {"$regex": f.name, "$options": "i"}

    if f.status:
        query["scrape_status"] = f.status

    return query


def _serialize(doc: dict) -> dict:
    """Convert ObjectId → str so Pydantic can parse the doc."""
    doc["_id"] = str(doc["_id"])
    return doc


# ── GET /profiles ─────────────────────────────────────────────────────────────

@router.get(
    "",
    response_model=PaginatedProfiles,
    summary="List profiles with optional filtering and pagination",
)
async def list_profiles(
    filters: ProfileFilters = Depends(parse_filters),
):
    collection = get_collection()
    query = build_query(filters)

    sort_dir = ASCENDING if filters.sort_order == "asc" else DESCENDING
    skip = (filters.page - 1) * filters.page_size

    # Run count + fetch in parallel using the same query
    total = await collection.count_documents(query)
    pages = max(1, -(-total // filters.page_size))  # ceiling division

    cursor = (
        collection.find(query)
        .sort(filters.sort_by, sort_dir)
        .skip(skip)
        .limit(filters.page_size)
    )
    docs = [_serialize(doc) async for doc in cursor]

    return PaginatedProfiles(
        total=total,
        page=filters.page,
        page_size=filters.page_size,
        pages=pages,
        results=docs,
    )


# ── GET /profiles/{id} ────────────────────────────────────────────────────────

@router.get(
    "/{profile_id}",
    response_model=ProfileOut,
    summary="Fetch a single profile by MongoDB ObjectId",
)
async def get_profile(profile_id: str):
    try:
        oid = ObjectId(profile_id)
    except InvalidId:
        raise HTTPException(status_code=422, detail=f"'{profile_id}' is not a valid ObjectId")

    collection = get_collection()
    doc = await collection.find_one({"_id": oid})

    if doc is None:
        raise HTTPException(status_code=404, detail=f"Profile '{profile_id}' not found")

    return _serialize(doc)


# ── GET /profiles/by-url ──────────────────────────────────────────────────────

@router.get(
    "/by-url/lookup",
    response_model=ProfileOut,
    summary="Fetch a profile by its scraped URL",
)
async def get_profile_by_url(
    url: Annotated[str, Query(description="Exact profile URL")]
):
    collection = get_collection()
    doc = await collection.find_one({"profile_url": url})
    if doc is None:
        raise HTTPException(status_code=404, detail="No profile found for that URL")
    return _serialize(doc)


# ── GET /profiles/stats ───────────────────────────────────────────────────────

@router.get(
    "/stats/overview",
    response_model=ProfileStatsResponse,
    summary="Get profile collection statistics",
)
async def get_stats():
    """
    Return overall statistics about the profile collection:
    - Total profiles
    - Breakdown by scrape status
    - Breakdown by category
    - Breakdown by location
    - Photo coverage
    """
    collection = get_collection()
    
    total = await collection.count_documents({})
    
    # Count by status
    status_pipeline = [
        {"$group": {"_id": "$scrape_status", "count": {"$sum": 1}}}
    ]
    by_status = {}
    async for doc in collection.aggregate(status_pipeline):
        by_status[doc["_id"]] = doc["count"]
    
    # Count by category
    category_pipeline = [
        {"$match": {"category": {"$exists": True, "$ne": None}}},
        {"$group": {"_id": "$category", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 20}
    ]
    by_category = {}
    async for doc in collection.aggregate(category_pipeline):
        by_category[doc["_id"]] = doc["count"]
    
    # Count by location
    location_pipeline = [
        {"$match": {"location": {"$exists": True, "$ne": None}}},
        {"$group": {"_id": "$location", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 20}
    ]
    by_location = {}
    async for doc in collection.aggregate(location_pipeline):
        by_location[doc["_id"]] = doc["count"]
    
    # Count by LLM provider
    llm_pipeline = [
        {"$match": {"llm_provider": {"$exists": True, "$ne": None}}},
        {"$group": {"_id": "$llm_provider", "count": {"$sum": 1}}}
    ]
    by_llm = {}
    async for doc in collection.aggregate(llm_pipeline):
        by_llm[doc["_id"]] = doc["count"]
    
    # Count with photos
    with_photos = await collection.count_documents({"photos": {"$exists": True, "$ne": []}})
    
    # Count total photos
    total_photos_pipeline = [
        {"$project": {"photos": {"$cond": [{"$isArray": "$photos"}, {"$size": "$photos"}, 0]}}},
        {"$group": {"_id": None, "total": {"$sum": "$photos"}}}
    ]
    total_photos = 0
    async for doc in collection.aggregate(total_photos_pipeline):
        total_photos = doc["total"]
    
    return ProfileStatsResponse(
        total_profiles=total,
        scraped_success=by_status.get("success", 0),
        scraped_partial=by_status.get("partial", 0),
        scraped_error=by_status.get("error", 0),
        by_category=by_category,
        by_location=by_location,
        by_llm_provider=by_llm,
        total_photos=total_photos,
        profiles_with_photos=with_photos,
    )


@router.get(
    "/stats",
    response_model=ProfileStatsResponse,
    summary="Get stats details alias",
)
async def get_stats_alias():
    return await get_stats()


@router.get(
    "/search",
    response_model=PaginatedProfiles,
    summary="Search profile collection",
)
async def search_profiles(
    filters: ProfileFilters = Depends(parse_filters),
):
    return await list_profiles(filters)


# ── GET /profiles/categories ──────────────────────────────────────────────────

@router.get(
    "/filters/categories",
    response_model=dict[str, int],
    summary="List all categories and profile counts",
)
async def get_categories():
    """Get all unique categories with their profile counts."""
    collection = get_collection()
    pipeline = [
        {"$match": {"category": {"$exists": True, "$ne": None}}},
        {"$group": {"_id": "$category", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
    ]
    result = {}
    async for doc in collection.aggregate(pipeline):
        result[doc["_id"]] = doc["count"]
    return result


# ── GET /profiles/tasks ───────────────────────────────────────────────────────

@router.get(
    "/filters/tasks",
    response_model=dict[str, int],
    summary="List all tasks and profile counts",
)
async def get_tasks():
    """Get all unique tasks with their profile counts."""
    collection = get_collection()
    pipeline = [
        {"$match": {"task": {"$exists": True, "$ne": None}}},
        {"$group": {"_id": "$task", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
    ]
    result = {}
    async for doc in collection.aggregate(pipeline):
        result[doc["_id"]] = doc["count"]
    return result


# ── GET /profiles/locations ───────────────────────────────────────────────────

@router.get(
    "/filters/locations",
    response_model=dict[str, int],
    summary="List all locations and profile counts",
)
async def get_locations():
    """Get all unique locations with their profile counts."""
    collection = get_collection()
    pipeline = [
        {"$match": {"location": {"$exists": True, "$ne": None}}},
        {"$group": {"_id": "$location", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 50}
    ]
    result = {}
    async for doc in collection.aggregate(pipeline):
        result[doc["_id"]] = doc["count"]
    return result


# ── GET /profiles/{id}/photos ────────────────────────────────────────────────

@router.get(
    "/{profile_id}/photos",
    response_model=list[str],
    summary="Get all photos for a profile",
)
async def get_profile_photos(profile_id: str):
    """Fetch all photo URLs for a specific profile."""
    try:
        oid = ObjectId(profile_id)
    except InvalidId:
        raise HTTPException(status_code=422, detail=f"'{profile_id}' is not a valid ObjectId")
    
    collection = get_collection()
    doc = await collection.find_one(
        {"_id": oid},
        {"photos": 1, "_id": 0}
    )
    
    if doc is None:
        raise HTTPException(status_code=404, detail=f"Profile '{profile_id}' not found")
    
    return doc.get("photos", [])
