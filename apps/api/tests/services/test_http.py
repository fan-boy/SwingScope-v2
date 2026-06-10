"""
Unit tests for the shared HTTP client — uses httpx mock transport.
No real network calls.
"""
import asyncio
import pytest
import httpx

from app.services.data_providers.http import _request, RateLimitError, ProviderError


def _make_client(responses: list[httpx.Response]) -> httpx.AsyncClient:
    """Build an httpx client backed by a sequence of mock responses."""
    call_count = {"n": 0}
    def transport_handler(request):
        idx = min(call_count["n"], len(responses) - 1)
        call_count["n"] += 1
        return responses[idx]

    transport = httpx.MockTransport(transport_handler)
    return httpx.AsyncClient(transport=transport, base_url="https://test.example")


class TestRequestHelper:
    def test_success_returns_json(self):
        client = _make_client([
            httpx.Response(200, json={"ok": True}),
        ])
        result = asyncio.run(_request(client, "GET", "/test"))
        assert result == {"ok": True}

    def test_retries_on_500(self):
        client = _make_client([
            httpx.Response(500),
            httpx.Response(500),
            httpx.Response(200, json={"recovered": True}),
        ])
        result = asyncio.run(_request(client, "GET", "/test", retries=3))
        assert result["recovered"] is True

    def test_raises_after_max_retries(self):
        client = _make_client([httpx.Response(500)] * 5)
        with pytest.raises(ProviderError):
            asyncio.run(_request(client, "GET", "/test", retries=2))

    def test_raises_rate_limit_after_retries(self):
        client = _make_client([httpx.Response(429)] * 5)
        with pytest.raises(RateLimitError):
            asyncio.run(_request(client, "GET", "/test", retries=2))
