"""
parser.py - Parse and structure extracted profile data

Flow:
  1. Take raw extracted data
  2. Clean and validate fields
  3. Parse experience/education items
  4. Normalize list fields
  5. Use LLM to identify task and category
  6. Return clean structured profile
"""

import logging
import re
import asyncio
from typing import Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


def parse_experience(items: list[str]) -> list[dict[str, Any]]:
    """
    Parse experience items into structured format.
    Handles various formats like:
      - "Job Title at Company (2020-2023)"
      - "Company: 2 years"
      - "Position | Organization"
    """
    parsed = []
    for item in items:
        exp = {
            "title": None,
            "company": None,
            "duration": None,
            "raw": item,
        }
        
        # Try to extract duration (years, date ranges, etc.)
        duration_match = re.search(
            r"(\d{4}-\d{4}|\d+\s*years?|\d+\s*months?)",
            item,
            re.IGNORECASE
        )
        if duration_match:
            exp["duration"] = duration_match.group(1)
        
        # Try to split by common separators
        if " at " in item:
            parts = item.split(" at ")
            exp["title"] = parts[0].strip()
            exp["company"] = parts[1].strip()
        elif " | " in item:
            parts = item.split(" | ")
            exp["title"] = parts[0].strip()
            exp["company"] = parts[1].strip()
        elif ":" in item:
            parts = item.split(":")
            if len(parts[0]) < 50:  # Likely a label
                exp["title"] = parts[0].strip()
                exp["company"] = parts[1].strip()
        else:
            exp["title"] = item.strip()
        
        parsed.append(exp)
    
    return parsed


def parse_education(items: list[str]) -> list[dict[str, Any]]:
    """
    Parse education items into structured format.
    Handles formats like:
      - "Bachelor of Science in Computer Science, University of X"
      - "MBA | Harvard University (2020)"
      - "Degree: Institution (Year)"
    """
    parsed = []
    for item in items:
        edu = {
            "degree": None,
            "institution": None,
            "year": None,
            "raw": item,
        }
        
        # Extract year
        year_match = re.search(r"\(?(19|20)\d{2}\)?", item)
        if year_match:
            edu["year"] = year_match.group(0).strip("()")
        
        # Try to split by common separators
        if ", " in item:
            parts = item.split(", ", 1)
            edu["degree"] = parts[0].strip()
            edu["institution"] = parts[1].replace(f"({edu['year']})", "").strip()
        elif " | " in item:
            parts = item.split(" | ")
            edu["degree"] = parts[0].strip()
            edu["institution"] = parts[1].strip()
        elif ":" in item and len(item.split(":")[0]) < 50:
            parts = item.split(":", 1)
            edu["degree"] = parts[0].strip()
            edu["institution"] = parts[1].strip()
        else:
            edu["degree"] = item.strip()
        
        parsed.append(edu)
    
    return parsed


def normalize_list_field(items: Optional[list[str]]) -> list[str]:
    """
    Normalize list fields:
      - Remove None values
      - Remove duplicates
      - Remove empty strings
      - Limit to reasonable length
    """
    if not items:
        return []
    
    cleaned = []
    for item in items:
        if isinstance(item, str):
            item = item.strip()
            if item and item not in cleaned and len(item) < 200:
                cleaned.append(item)
    
    return cleaned[:50]  # Limit to 50 items


async def extract_task_and_category_with_llm(profile: dict[str, Any]) -> tuple[Optional[str], Optional[str]]:
    """
    Use LLM to identify task and category from profile data.
    
    Returns: (task, category) tuple
    """
    try:
        from ai.llm_manager import get_llm_manager
        manager = await get_llm_manager()
    except Exception as e:
        logger.warning(f"Could not load LLM manager: {e}")
        return None, None
    
    # Build context for LLM
    context_parts = []
    if profile.get("description"):
        context_parts.append(f"Bio: {profile['description'][:500]}")
    if profile.get("skills"):
        context_parts.append(f"Skills: {', '.join(profile['skills'][:5])}")
    if profile.get("expertise"):
        context_parts.append(f"Expertise: {', '.join(profile['expertise'][:5])}")
    if profile.get("additional_info"):
        context_parts.append(f"Info: {str(profile['additional_info'])[:200]}")
    
    context = "\n".join(context_parts)
    if not context:
        return None, None
    
    # Prompt for LLM
    prompt = f"""Based on this professional profile, identify:
1. TASK: What does this person do? (e.g., "Hazardous Waste Consultant", "Recycling Specialist")
2. CATEGORY: What service/industry category? (e.g., "Hazardous Waste", "Recycling", "Consulting")

Profile:
{context}

Respond as JSON:
{{"task": "...", "category": "..."}}

Only use information from the profile. If uncertain, use null.
"""
    
    try:
        result = await manager.parse_json(prompt, task="extract_task_category")
        task = result.get("task")
        category = result.get("category")
        
        # Validate extracted values
        if task and len(str(task)) > 100:
            task = None
        if category and len(str(category)) > 100:
            category = None
        
        if task or category:
            logger.debug(f"  LLM extracted task='{task}', category='{category}'")
        
        return task, category
    except Exception as e:
        logger.warning(f"  LLM extraction failed: {e}")
        return None, None


def parse_profile(raw_profile: dict[str, Any]) -> dict[str, Any]:
    """
    Parse and clean a raw extracted profile (synchronous version).
    For async version with LLM, use parse_profile_async.
    """
    profile = raw_profile.copy()
    
    # Normalize string fields
    for field in ["name", "description", "location", "task", "category", "company"]:
        if field in profile and profile[field]:
            profile[field] = str(profile[field]).strip()[:1000]  # Max 1000 chars
        else:
            profile[field] = None
    
    # Normalize list fields
    for field in ["skills", "expertise", "certifications", "social_links", "website_links", "images"]:
        if field in profile:
            profile[field] = normalize_list_field(profile[field])
            if not profile[field]:
                del profile[field]
    
    # Parse complex fields
    if "experience" in profile:
        profile["experience"] = parse_experience(profile.get("experience", []))
        if not profile["experience"]:
            del profile["experience"]
    
    if "education" in profile:
        profile["education"] = parse_education(profile.get("education", []))
        if not profile["education"]:
            del profile["education"]
    
    # Normalize photos
    if "photos" in profile:
        profile["photos"] = [
            url for url in profile.get("photos", [])
            if url and isinstance(url, str) and (url.startswith("http") or url.startswith("//"))
        ][:5]  # Max 5 photos
        if not profile["photos"]:
            del profile["photos"]
    
    # Validate URL
    if "profile_url" in profile:
        profile["profile_url"] = str(profile["profile_url"]).strip()
    
    # Ensure required fields exist
    profile.setdefault("scraped_at", None)
    profile.setdefault("scrape_status", "unknown")
    
    return profile


async def parse_profile_async(raw_profile: dict[str, Any], use_llm: bool = True) -> dict[str, Any]:
    """
    Parse and clean a raw extracted profile with optional LLM enhancement.
    Async version for task/category extraction via LLM.
    
    Args:
        raw_profile: Raw extracted profile dict
        use_llm: Whether to use LLM for task/category extraction
    
    Returns:
        Clean structured profile dict
    """
    profile = parse_profile(raw_profile)
    
    # Use LLM to extract task and category if not already present
    if use_llm and not profile.get("task") and not profile.get("category"):
        try:
            task, category = await extract_task_and_category_with_llm(profile)
            if task:
                profile["task"] = task
            if category:
                profile["category"] = category
            profile["llm_processed"] = True
        except Exception as e:
            logger.warning(f"  LLM processing failed: {e}")
            profile["llm_processed"] = False
    
    return profile


def validate_profile(profile: dict[str, Any]) -> tuple[bool, str]:
    """
    Validate that profile has minimum required data.
    Returns (is_valid, reason).
    """
    # Must have profile URL
    if not profile.get("profile_url"):
        return False, "Missing profile_url"
    
    # Must have at least one of: name or description
    if not profile.get("name") and not profile.get("description"):
        return False, "Missing both name and description"
    
    return True, "Valid"
