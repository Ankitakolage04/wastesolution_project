from __future__ import annotations
from typing import Any
from pydantic import BaseModel, Field, field_validator
from bson import ObjectId


# ── helpers ───────────────────────────────────────────────────────────────────

def _str_objectid(v: Any) -> str:
    """Coerce ObjectId → str so JSON serialisation works."""
    return str(v) if isinstance(v, ObjectId) else v


# ── sub-documents ─────────────────────────────────────────────────────────────

class ExperienceItem(BaseModel):
    title: str | None = None
    company: str | None = None
    duration: str | None = None
    raw: str | None = None          # original scraped string if not yet parsed


class EducationItem(BaseModel):
    degree: str | None = None
    institution: str | None = None
    year: str | None = None
    raw: str | None = None


# ── profile response (outbound) ───────────────────────────────────────────────

class ProfileOut(BaseModel):
    id: str = Field(alias="_id")
    profile_url: str | None = None
    name: str | None = None
    description: str | None = None
    location: str | None = None
    task: str | None = None
    category: str | None = None
    profile_image_url: str | None = None
    photos: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    expertise: list[str] = Field(default_factory=list)
    experience: list[Any] = Field(default_factory=list)
    education: list[Any] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    company: str | None = None
    social_links: list[str] = Field(default_factory=list)
    website_links: list[str] = Field(default_factory=list)
    images: list[str] = Field(default_factory=list)
    contact_email: str | None = None
    contact_phone: str | None = None
    website: str | None = None
    additional_info: dict[str, Any] = Field(default_factory=dict)
    scraped_at: str | None = None
    scrape_status: str | None = None
    llm_processed: bool = False
    llm_provider: str | None = None

    @field_validator("id", mode="before")
    @classmethod
    def coerce_id(cls, v: Any) -> str:
        return _str_objectid(v)

    model_config = {"populate_by_name": True}


# ── paginated envelope ────────────────────────────────────────────────────────

class PaginatedProfiles(BaseModel):
    total: int
    page: int
    page_size: int
    pages: int
    results: list[ProfileOut]


# ── query params (shared) ─────────────────────────────────────────────────────

class ProfileFilters(BaseModel):
    """All optional query-string filters for the list/search endpoints."""
    skill: str | None = None
    expertise: str | None = None
    location: str | None = None
    category: str | None = None
    task: str | None = None
    name: str | None = None
    q: str | None = None            # full-text search (requires text index)
    status: str | None = None       # scrape_status filter
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
    sort_by: str = "scraped_at"
    sort_order: str = "desc"        # "asc" | "desc"


# ── statistics response ───────────────────────────────────────────────────────

class ProfileStatsResponse(BaseModel):
    """Statistics about the profile collection."""
    total_profiles: int
    scraped_success: int
    scraped_partial: int
    scraped_error: int
    by_category: dict[str, int] = Field(default_factory=dict)
    by_location: dict[str, int] = Field(default_factory=dict)
    by_llm_provider: dict[str, int] = Field(default_factory=dict)
    total_photos: int
    profiles_with_photos: int
