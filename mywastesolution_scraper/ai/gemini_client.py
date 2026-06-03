"""
gemini_client.py - Gemini API client for structuring extracted profile data

Uses Google Gemini to:
  1. Validate extracted data
  2. Structure messy text into clean fields
  3. Extract missing information when possible (from context only)
  4. Never generate/hallucinate information not in the source
"""

import asyncio
import json
import logging
import os
from typing import Any, Optional

# Try to import google.generativeai, but gracefully fail if not installed
try:
    import google.generativeai as genai
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False
    logging.warning("google.generativeai not installed - skipping Gemini processing")

logger = logging.getLogger(__name__)

# Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-pro")
GEMINI_ENABLED = os.getenv("GEMINI_ENABLED", "true").lower() == "true"


class GeminiClient:
    """Client for Gemini API interactions."""
    
    def __init__(self):
        self.enabled = GEMINI_ENABLED and HAS_GEMINI and bool(GEMINI_API_KEY)
        if self.enabled:
            try:
                genai.configure(api_key=GEMINI_API_KEY)
                self.model = genai.GenerativeModel(GEMINI_MODEL)
                logger.info("✓ Gemini API configured")
            except Exception as e:
                logger.warning(f"Failed to configure Gemini: {e}")
                self.enabled = False
    
    async def structure_profile(self, raw_profile: dict[str, Any]) -> dict[str, Any]:
        """
        Use Gemini to structure and validate profile data.
        Only uses visible information - never generates missing data.
        """
        if not self.enabled:
            logger.debug("Gemini disabled - returning raw profile")
            return raw_profile
        
        try:
            profile_text = self._format_profile_text(raw_profile)
            
            prompt = f"""Analyze this extracted profile data and return ONLY information visible in the source.
            
DO NOT:
  - Generate missing information
  - Make assumptions
  - Fill in unspecified fields
  
DO:
  - Validate existing information
  - Clean up messy text
  - Parse dates and durations
  - Return null for missing fields

Profile data:
{profile_text}

Return JSON with these fields (null if not found):
{{
    "name": "...",
    "description": "...",
    "location": "...",
    "company": "...",
    "skills": ["..."],
    "expertise": ["..."],
    "certifications": ["..."],
    "experience": [
        {{
            "title": "...",
            "company": "...",
            "duration": "..."
        }}
    ],
    "education": [
        {{
            "degree": "...",
            "institution": "...",
            "year": "..."
        }}
    ]
}}
"""
            
            response = await asyncio.to_thread(
                self.model.generate_content,
                prompt
            )
            
            # Extract JSON from response
            response_text = response.text
            
            # Try to find JSON in response
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                structured = json.loads(json_str)
                
                # Merge with original, preferring non-null Gemini values
                return self._merge_profiles(raw_profile, structured)
            else:
                logger.warning("No JSON found in Gemini response")
                return raw_profile
                
        except Exception as e:
            logger.warning(f"Gemini processing failed: {e}")
            return raw_profile
    
    def _format_profile_text(self, profile: dict[str, Any]) -> str:
        """Format profile dict as text for Gemini processing."""
        lines = []
        
        if profile.get("name"):
            lines.append(f"Name: {profile['name']}")
        if profile.get("description"):
            lines.append(f"Description: {profile['description']}")
        if profile.get("location"):
            lines.append(f"Location: {profile['location']}")
        if profile.get("company"):
            lines.append(f"Company: {profile['company']}")
        if profile.get("skills"):
            lines.append(f"Skills: {', '.join(profile['skills'])}")
        if profile.get("expertise"):
            lines.append(f"Expertise: {', '.join(profile['expertise'])}")
        if profile.get("certifications"):
            lines.append(f"Certifications: {', '.join(profile['certifications'])}")
        if profile.get("experience"):
            for exp in profile.get("experience", []):
                if isinstance(exp, dict):
                    lines.append(f"Experience: {exp.get('raw', str(exp))}")
        if profile.get("education"):
            for edu in profile.get("education", []):
                if isinstance(edu, dict):
                    lines.append(f"Education: {edu.get('raw', str(edu))}")
        if profile.get("additional_info"):
            for key, val in profile["additional_info"].items():
                lines.append(f"{key}: {val}")
        
        return "\n".join(lines)
    
    def _merge_profiles(
        self,
        original: dict[str, Any],
        gemini: dict[str, Any]
    ) -> dict[str, Any]:
        """
        Merge Gemini-structured data with original, preferring Gemini
        where it provides non-null, non-empty values.
        """
        result = original.copy()
        
        # String fields - prefer Gemini if non-empty
        for field in ["name", "description", "location", "company"]:
            gemini_val = gemini.get(field)
            if gemini_val and isinstance(gemini_val, str) and gemini_val.strip():
                result[field] = gemini_val.strip()
        
        # List fields - prefer Gemini if non-empty
        for field in ["skills", "expertise", "certifications"]:
            gemini_val = gemini.get(field)
            if gemini_val and isinstance(gemini_val, list) and len(gemini_val) > 0:
                result[field] = [str(v).strip() for v in gemini_val if v]
        
        # Complex fields - prefer Gemini if provided
        for field in ["experience", "education"]:
            gemini_val = gemini.get(field)
            if gemini_val and isinstance(gemini_val, list):
                result[field] = gemini_val
        
        return result


# Singleton instance
_gemini_client: Optional[GeminiClient] = None


def get_gemini_client() -> GeminiClient:
    """Get or create Gemini client singleton."""
    global _gemini_client
    if _gemini_client is None:
        _gemini_client = GeminiClient()
    return _gemini_client


async def structure_with_gemini(profile: dict[str, Any]) -> dict[str, Any]:
    """Convenience function to structure a profile using Gemini."""
    client = get_gemini_client()
    return await client.structure_profile(profile)
