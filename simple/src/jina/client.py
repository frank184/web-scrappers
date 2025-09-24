import os
import httpx
from typing import Iterable, List, Optional, Dict, Any
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from dotenv import load_dotenv
from datetime import datetime, timezone
from .models import ReadResult

load_dotenv()

JINA_API_KEY = os.getenv("JINA_API_KEY")
JINA_BROWSER = os.getenv("JINA_BROWSER")  # optional

# Base endpoints:
# - Reader: prepend r.jina.ai to the target URL
# - Search+Read (SERP -> top URLs -> content): s.jina.ai?q=YOUR+QUERY
# Notes:
#   Reader needs no key; adding a key via Authorization header boosts limits.
#   We'll send Authorization if present.
#   Response is the cleaned, main content (LLM-friendly).
# Docs: https://jina.ai/reader  (see "The best part? It's free!" & rate limits)
AUTH_HEADERS = {}
if JINA_API_KEY:
    AUTH_HEADERS["Authorization"] = f"Bearer {JINA_API_KEY}"

class JinaReaderClient:
    def __init__(self, timeout: float = 45.0):
        self.timeout = timeout

    @retry(
        reraise=True,
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        retry=retry_if_exception_type(httpx.HTTPError),
    )
    def read_url(
        self,
        url: str,
        format_: str = "markdown",  # or "text" (Jina can vary), markdown is most common
        browser: Optional[str] = None,  # e.g., "auto" | "fast" | "quality"; Jina-controlled
        extra_params: Optional[Dict[str, Any]] = None,
    ) -> ReadResult:
        """
        Fetches LLM-ready content using Jina Reader by prepending r.jina.ai to the URL.
        """
        # Build the r.jina.ai URL:
        # You literally prefix r.jina.ai/ to the target URL.
        # Example: https://r.jina.ai/https://example.com
        r_url = f"https://r.jina.ai/{url}"

        params: Dict[str, Any] = {}
        if format_:
            params["format"] = format_  # if supported by Jina at the time; safe to include
        if browser or JINA_BROWSER:
            params["browser"] = browser or JINA_BROWSER
        if extra_params:
            params.update(extra_params)

        try:
            with httpx.Client(timeout=self.timeout, headers=AUTH_HEADERS) as client:
                resp = client.get(r_url, params=params, follow_redirects=True)
                content = resp.text if resp.status_code == 200 else None
                return ReadResult(
                    url=url,
                    status=resp.status_code,
                    fetched_at=datetime.now(timezone.utc),
                    content=content,
                    meta={"requested_url": r_url, "params": params},
                    error=None if resp.status_code == 200 else resp.text[:500],
                )
        except httpx.HTTPError as e:
            return ReadResult(
                url=url,
                status=0,
                fetched_at=datetime.now(timezone.utc),
                error=str(e),
            )

    def read_bulk(self, urls: Iterable[str]) -> List[ReadResult]:
        return [self.read_url(u) for u in urls]

    @retry(
        reraise=True,
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        retry=retry_if_exception_type(httpx.HTTPError),
    )
    def search_and_read(
        self,
        query: str,
        top_k: int = 5,
        extra_params: Optional[Dict[str, Any]] = None,
    ) -> ReadResult:
        """
        Uses s.jina.ai to perform a search and returns aggregated, cleaned content
        from the top results (Jina handles crawling/cleaning under the hood).
        """
        # Jina s.jina.ai does the web search and returns LLM-friendly content.
        # Rate-limited; benefits from an API key. Every request has a fixed token cost.
        # Docs mention 100 RPM free-IP, 1000 RPM with key (exact values may change).
        # https://jina.ai/reader  (rate limit table lists s.jina.ai row)
        params: Dict[str, Any] = {"q": query, "top_k": top_k}
        if extra_params:
            params.update(extra_params)

        s_url = "https://s.jina.ai/"
        try:
            with httpx.Client(timeout=self.timeout, headers=AUTH_HEADERS) as client:
                resp = client.get(s_url, params=params, follow_redirects=True)
                content = resp.text if resp.status_code == 200 else None
                return ReadResult(
                    url=f"s.jina.ai?q={query}",
                    status=resp.status_code,
                    fetched_at=datetime.now(timezone.utc),
                    content=content,
                    meta={"params": params},
                    error=None if resp.status_code == 200 else resp.text[:500],
                )
        except httpx.HTTPError as e:
            return ReadResult(
                url=f"s.jina.ai?q={query}",
                status=0,
                fetched_at=datetime.now(timezone.utc),
                error=str(e),
            )
