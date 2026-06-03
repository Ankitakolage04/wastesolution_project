"""
llm_manager.py - Multi-LLM orchestrator with fallback support

Manages multiple LLM providers (Groq, Gemini, Claude) with:
- Capacity-aware fallback switching
- Rate limit tracking
- Unified async interface
- Request queuing

Environment Variables:
    GROQ_API_KEY: API key for Groq
    GEMINI_API_KEY: API key for Google Gemini
    ANTHROPIC_API_KEY: API key for Anthropic Claude
    
    PRIMARY_LLM: Which LLM to use first (groq, gemini, or claude)
    LLM_TIMEOUT: Timeout in seconds for LLM calls (default: 30)
    LLM_RETRIES: Number of retries on failure (default: 3)
    LLM_ENABLE_GROQ: Enable Groq provider (default: true)
    LLM_ENABLE_GEMINI: Enable Gemini provider (default: true)
    LLM_ENABLE_CLAUDE: Enable Claude provider (default: true)
"""

import asyncio
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Optional, Literal
from collections import defaultdict

try:
    import litellm
    HAS_LITELLM = True
except ImportError:
    HAS_LITELLM = False

from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)


# ── Constants ──────────────────────────────────────────────────────────────────

ProviderName = Literal["groq", "gemini", "claude"]

RATE_LIMITS = {
    "groq": {"requests_per_minute": 30, "tokens_per_minute": 6000},
    "gemini": {"requests_per_minute": 60, "tokens_per_minute": 4000},
    "claude": {"requests_per_minute": 5, "tokens_per_minute": 1000},
}

LLM_MODELS = {
    "groq": "groq/mixtral-8x7b-32768",
    "gemini": "gemini-pro",
    "claude": "claude-3-5-sonnet-20241022",
}


# ── Capacity Tracker ───────────────────────────────────────────────────────────

class CapacityTracker:
    """Track request capacity per LLM provider."""
    
    def __init__(self, provider: ProviderName):
        self.provider = provider
        self.request_window: defaultdict[str, list[float]] = defaultdict(list)
        self.limits = RATE_LIMITS.get(provider, {})
        self.rpm_limit = self.limits.get("requests_per_minute", 60)
    
    def _cleanup_window(self, window_key: str, cutoff_seconds: int = 60) -> None:
        """Remove timestamps older than cutoff_seconds."""
        cutoff = datetime.now().timestamp() - cutoff_seconds
        self.request_window[window_key] = [
            ts for ts in self.request_window[window_key] if ts > cutoff
        ]
    
    def is_available(self) -> bool:
        """Check if provider can accept new requests."""
        window_key = "minute"
        self._cleanup_window(window_key)
        return len(self.request_window[window_key]) < self.rpm_limit
    
    def get_wait_time(self) -> float:
        """Get seconds to wait before next request is available."""
        window_key = "minute"
        self._cleanup_window(window_key)
        if self.is_available():
            return 0.0
        
        oldest = min(self.request_window[window_key]) if self.request_window[window_key] else 0
        wait = 60 - (datetime.now().timestamp() - oldest)
        return max(0, wait)
    
    def record_request(self) -> None:
        """Record a request timestamp."""
        self.request_window["minute"].append(datetime.now().timestamp())


# ── LLM Manager ────────────────────────────────────────────────────────────────

class LLMManager:
    """
    Unified interface for multiple LLM providers with automatic fallback.
    
    Usage:
        manager = LLMManager()
        response = await manager.call(prompt="Classify this text: ...", task="classify")
    """
    
    def __init__(self):
        """Initialize LLM manager with available providers."""
        # Load configuration
        self.enabled_providers: list[ProviderName] = self._detect_enabled_providers()
        self.primary_llm: ProviderName = self._get_primary_llm()
        self.timeout = int(os.getenv("LLM_TIMEOUT", "30"))
        self.retries = int(os.getenv("LLM_RETRIES", "3"))
        
        # Initialize LiteLLM
        if HAS_LITELLM:
            litellm.drop_params = True
            litellm.api_timeout = self.timeout
            logger.info(f"✓ LiteLLM initialized (timeout={self.timeout}s)")
        
        # Capacity trackers
        self.trackers = {
            provider: CapacityTracker(provider)
            for provider in self.enabled_providers
        }
        
        logger.info(f"LLM Manager initialized")
        logger.info(f"  Enabled providers: {self.enabled_providers}")
        logger.info(f"  Primary LLM: {self.primary_llm}")
        logger.info(f"  Fallback chain: {self._get_fallback_chain()}")
    
    def _detect_enabled_providers(self) -> list[ProviderName]:
        """Detect which LLM providers have API keys configured."""
        providers: list[ProviderName] = []
        
        if os.getenv("LLM_ENABLE_GROQ", "true").lower() == "true" and os.getenv("GROQ_API_KEY"):
            providers.append("groq")
        
        if os.getenv("LLM_ENABLE_GEMINI", "true").lower() == "true" and os.getenv("GEMINI_API_KEY"):
            providers.append("gemini")
        
        if os.getenv("LLM_ENABLE_CLAUDE", "true").lower() == "true" and os.getenv("ANTHROPIC_API_KEY"):
            providers.append("claude")
        
        if not providers:
            logger.warning("⚠ No LLM providers configured! Check API keys in .env")
        
        return providers
    
    def _get_primary_llm(self) -> ProviderName:
        """Get the primary LLM from environment or default."""
        primary = os.getenv("PRIMARY_LLM", "groq").lower()
        if primary in self.enabled_providers:
            return primary  # type: ignore
        elif self.enabled_providers:
            return self.enabled_providers[0]
        else:
            return "groq"  # fallback, will fail later if not available
    
    def _get_fallback_chain(self) -> list[ProviderName]:
        """Get ordered list of providers to try (primary first)."""
        chain = [self.primary_llm]
        for provider in self.enabled_providers:
            if provider not in chain:
                chain.append(provider)
        return chain  # type: ignore
    
    async def call(
        self,
        prompt: str,
        task: str = "general",
        max_tokens: int = 1000,
        temperature: float = 0.7,
        json_mode: bool = False,
        retries: Optional[int] = None,
    ) -> dict[str, Any]:
        """
        Call an LLM with automatic fallback.
        
        Args:
            prompt: The prompt to send
            task: Task name for logging (e.g., "structure_profile")
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature
            json_mode: Request JSON output
            retries: Number of retries (uses default if None)
        
        Returns:
            {
                "content": str,           # Response text
                "provider": ProviderName, # Which LLM was used
                "tokens_used": int,
                "task": str,
                "timestamp": str,
            }
        """
        if retries is None:
            retries = self.retries
        
        fallback_chain = self._get_fallback_chain()
        last_error = None
        
        for attempt in range(retries):
            for provider in fallback_chain:
                try:
                    # Check capacity
                    tracker = self.trackers.get(provider)
                    if tracker and not tracker.is_available():
                        wait_time = tracker.get_wait_time()
                        logger.debug(
                            f"[{task}] {provider} at capacity, waiting {wait_time:.1f}s"
                        )
                        await asyncio.sleep(min(wait_time + 0.1, 5))
                        continue
                    
                    # Build message
                    messages = [{"role": "user", "content": prompt}]
                    
                    # Call LLM
                    logger.debug(f"[{task}] Calling {provider} (attempt {attempt+1}/{retries})")
                    
                    if not HAS_LITELLM:
                        raise ImportError("litellm not installed")
                    
                    # Use litellm completion
                    response = await asyncio.to_thread(
                        litellm.completion,
                        model=LLM_MODELS[provider],
                        messages=messages,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        timeout=self.timeout,
                        api_key=self._get_api_key(provider),
                    )
                    
                    # Record successful request
                    if tracker:
                        tracker.record_request()
                    
                    # Extract content
                    content = response.choices[0].message.content.strip()
                    usage = getattr(response, "usage", None)
                    tokens_used = getattr(usage, "total_tokens", -1) if usage else -1
                    
                    logger.info(
                        f"✓ [{task}] {provider} succeeded ({tokens_used} tokens)"
                    )
                    
                    return {
                        "content": content,
                        "provider": provider,
                        "tokens_used": tokens_used,
                        "task": task,
                        "timestamp": datetime.now().isoformat(),
                    }
                
                except asyncio.TimeoutError:
                    logger.warning(f"[{task}] {provider} timeout, trying next...")
                    last_error = f"Timeout from {provider}"
                
                except Exception as e:
                    logger.warning(f"[{task}] {provider} error: {e}")
                    last_error = str(e)
        
        # All providers and retries exhausted
        error_msg = f"All LLM providers exhausted. Last error: {last_error}"
        logger.error(error_msg)
        return {
            "content": "",
            "provider": "none",
            "tokens_used": 0,
            "task": task,
            "error": error_msg,
            "timestamp": datetime.now().isoformat(),
        }
    
    def _get_api_key(self, provider: ProviderName) -> str:
        """Get API key for provider."""
        key_map = {
            "groq": "GROQ_API_KEY",
            "gemini": "GEMINI_API_KEY",
            "claude": "ANTHROPIC_API_KEY",
        }
        return os.getenv(key_map.get(provider, ""), "")
    
    async def parse_json(
        self,
        prompt: str,
        task: str = "parse",
        schema: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """
        Call LLM and parse JSON response.
        
        Args:
            prompt: Prompt ending with JSON instructions
            task: Task name for logging
            schema: Optional Pydantic schema for validation
        
        Returns:
            Parsed JSON dict or empty dict on failure
        """
        response = await self.call(
            prompt=prompt,
            task=task,
            json_mode=True,
        )
        
        if response.get("error"):
            logger.error(f"[{task}] LLM error: {response['error']}")
            return {}
        
        try:
            content = response.get("content", "")
            # Try to extract JSON from response (handles markdown code blocks)
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            data = json.loads(content)
            logger.debug(f"[{task}] Parsed JSON from {response['provider']}")
            return data
        except json.JSONDecodeError as e:
            logger.error(f"[{task}] JSON parse error: {e}")
            return {}
    
    def get_status(self) -> dict[str, Any]:
        """Get current status of all LLM providers."""
        status = {}
        for provider in self.enabled_providers:
            tracker = self.trackers.get(provider)
            if tracker:
                status[provider] = {
                    "available": tracker.is_available(),
                    "wait_time_seconds": tracker.get_wait_time(),
                    "recent_requests": len(tracker.request_window.get("minute", [])),
                }
        return status


# ── Singleton Instance ─────────────────────────────────────────────────────────

_llm_manager: Optional[LLMManager] = None


async def get_llm_manager() -> LLMManager:
    """Get or create the singleton LLM manager."""
    global _llm_manager
    if _llm_manager is None:
        _llm_manager = LLMManager()
    return _llm_manager


def get_llm_manager_sync() -> LLMManager:
    """Get or create the singleton LLM manager (sync version)."""
    global _llm_manager
    if _llm_manager is None:
        _llm_manager = LLMManager()
    return _llm_manager
