"""
models/profile.py - Pydantic models for profile data

Defines database schema and API response schemas.
"""

from __future__ import annotations
from typing import Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from bson import ObjectId


# ── Helpers ────────────────────────────────────────────────────────────────────

def _str_objectid(v: Any) -> str:
    """Coerce ObjectId → str for JSON serialization."""
    return str(v) if isinstance(v, ObjectId) else v


# ── Sub-documents ──────────────────────────────────────────────────────────────

class ExperienceItem(BaseModel):
    """Single experience entry."""
    title: str | None = None
    company: str | None = None
    duration: str | None = None
    raw: str | None = None  # original scraped string if not yet parsed


class EducationItem(BaseModel):
    """Single education entry."""
    degree: str | None = None
    institution: str | None = None
    year: str | None = None
    raw: str | None = None


class ExtractionMetadata(BaseModel):
    """Metadata about the extraction process."""
    scraped_at: datetime | None = None
    scrape_status: str = "pending"  # pending, success, partial, error
    error_message: str | None = None
    llm_processed: bool = False
    llm_provider: str | None = None  # groq, gemini, claude
    extraction_confidence: float = 0.0  # 0.0 to 1.0


# ── MongoDB Document ───────────────────────────────────────────────────────────

class ProfileDB(BaseModel):
    """MongoDB document schema (stored in DB)."""
    
    # Required fields
    profile_url: str = Field(..., description="Unique profile URL")
    
    # Contact & Basic Info
    name: str | None = None
    description: str | None = None  # Bio/about section
    location: str | None = None
    
    # Professional Info
    task: str | None = None  # What they do / specialization
    category: str | None = None  # Service category / waste type
    skills: list[str] = Field(default_factory=list)
    expertise: list[str] = Field(default_factory=list)
    
    # Education & Experience
    experience: list[ExperienceItem] = Field(default_factory=list)
    education: list[EducationItem] = Field(default_factory=list)
    
    # Media
    photos: list[str] = Field(default_factory=list)  # Image URLs
    profile_image_url: str | None = None  # Primary profile photo
    
    # Additional Info
    certifications: list[str] = Field(default_factory=list)
    company: str | None = None
    social_links: list[str] = Field(default_factory=list)
    website_links: list[str] = Field(default_factory=list)
    images: list[str] = Field(default_factory=list)
    contact_email: str | None = None
    contact_phone: str | None = None
    website: str | None = None
    additional_info: dict[str, Any] = Field(default_factory=dict)
    
    # Metadata
    metadata: ExtractionMetadata = Field(default_factory=ExtractionMetadata)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None,
        }


# ── API Response Models ────────────────────────────────────────────────────────

class ProfileOut(BaseModel):
    """Response model for API (outbound)."""
    
    id: str = Field(alias="_id", description="MongoDB ObjectId as string")
    profile_url: str
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
    
    # Metadata
    scraped_at: str | None = None
    scrape_status: str = "pending"
    llm_processed: bool = False
    llm_provider: str | None = None
    
    @field_validator("id", mode="before")
    @classmethod
    def coerce_id(cls, v: Any) -> str:
        return _str_objectid(v)
    
    @field_validator("scraped_at", mode="before")
    @classmethod
    def coerce_datetime(cls, v: Any) -> str | None:
        if isinstance(v, datetime):
            return v.isoformat()
        return v


class ProfileCreate(BaseModel):
    """Input model for creating profiles (admin API)."""
    profile_url: str
    name: str | None = None
    description: str | None = None
    location: str | None = None
    task: str | None = None
    category: str | None = None


class ProfileUpdate(BaseModel):
    """Input model for updating profiles."""
    name: str | None = None
    description: str | None = None
    location: str | None = None
    task: str | None = None
    category: str | None = None
    skills: list[str] | None = None
    expertise: list[str] | None = None
    photos: list[str] | None = None


class ProfileListResponse(BaseModel):
    """Response model for paginated profile lists."""
    items: list[ProfileOut]
    total: int
    page: int
    page_size: int
    total_pages: int


class ProfileStatsResponse(BaseModel):
    """Response for profile statistics."""
    total_profiles: int
    scraped_success: int
    scraped_partial: int
    scraped_error: int
    by_category: dict[str, int] = Field(default_factory=dict)
    by_location: dict[str, int] = Field(default_factory=dict)
    by_llm_provider: dict[str, int] = Field(default_factory=dict)
    total_photos: int
    profiles_with_photos: int
