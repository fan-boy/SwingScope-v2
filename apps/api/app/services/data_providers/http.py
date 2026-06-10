"""
Shared rate-limit-safe HTTP client with retry + backoff.
All provider adapters use this instead of raw httpx.
"""
import asyncio
import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 15.0
MAX_RETRIES = 3
RETRY_BACKOFF_BASE = 1.5   # seconds — doubles each attempt


class RateLimitError(Exception):
    """Raised on HTTP 429."""


class ProviderError(Exception):
    """Raised on unrecoverable provider errors."""


async def _request(
    client: httpx.AsyncClient,
    method: str,
    url: str,
    *,
    params: dict | None = None,
    headers: dict | None = None,
    json: dict | None = None,
    retries: int = MAX_RETRIES,
) -> Any:
    """
    Execute an HTTP request with automatic retry + exponential backoff.
    Raises RateLimitError on 429, ProviderError on 4xx/5xx after retries.
    """
    attempt = 0
    last_exc: Exception | None = None

    while attempt <= retries:
        try:
            resp = await client.request(
                method, url, params=params, headers=headers, json=json,
                timeout=DEFAULT_TIMEOUT,
            )

            if resp.status_code == 429:
                wait = RETRY_BACKOFF_BASE ** (attempt + 1)
                logger.warning("Rate limited by %s — waiting %.1fs (attempt %d/%d)", url, wait, attempt + 1, retries)
                if attempt == retries:
                    raise RateLimitError(f"Rate limited after {retries} retries: {url}")
                await asyncio.sleep(wait)
                attempt += 1
                continue

            if resp.status_code >= 500:
                wait = RETRY_BACKOFF_BASE ** attempt
                logger.warning("Server error %d from %s — retrying in %.1fs", resp.status_code, url, wait)
                await asyncio.sleep(wait)
                attempt += 1
                last_exc = ProviderError(f"HTTP {resp.status_code} from {url}")
                continue

            resp.raise_for_status()
            return resp.json()

        except (httpx.TimeoutException, httpx.ConnectError) as exc:
            wait = RETRY_BACKOFF_BASE ** attempt
            logger.warning("Network error on %s: %s — retrying in %.1fs", url, exc, wait)
            await asyncio.sleep(wait)
            attempt += 1
            last_exc = exc

    raise ProviderError(f"Request failed after {retries} retries: {url}") from last_exc


def build_client(base_url: str, headers: dict | None = None) -> httpx.AsyncClient:
    return httpx.AsyncClient(base_url=base_url, headers=headers or {}, timeout=DEFAULT_TIMEOUT)
