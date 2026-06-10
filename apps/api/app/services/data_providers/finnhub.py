"""
Finnhub adapter — NewsProvider + IndicatorProvider implementation.

Docs: https://finnhub.io/docs/api
Free tier: 60 req/min
"""
import logging
from datetime import date, datetime, timezone
from typing import Any

from app.services.data_providers.base import (
    NewsProvider, IndicatorProvider,
    NewsItem, TechnicalIndicator, TimeFrame
)
from app.services.data_providers.http import _request, build_client, ProviderError

logger = logging.getLogger(__name__)

FINNHUB_BASE = "https://finnhub.io/api/v1"

_RESOLUTION_MAP: dict[TimeFrame, str] = {
    "1d": "D",
    "1h": "60",
    "15m": "15",
    "5m": "5",
}


class FinnhubAdapter(NewsProvider, IndicatorProvider):
    def __init__(self, api_key: str) -> None:
        self._client = build_client(FINNHUB_BASE, {"X-Finnhub-Token": api_key})

    # ── NewsProvider ────────────────────────────────────────────────────────

    async def get_news(
        self,
        symbol: str,
        limit: int = 10,
        from_date: date | None = None,
    ) -> list[NewsItem]:
        from_dt = from_date or (datetime.now(timezone.utc).date().__class__.today() - __import__("datetime").timedelta(days=7))
        to_dt = datetime.now(timezone.utc).date()

        try:
            data = await _request(
                self._client, "GET",
                "/company-news",
                params={
                    "symbol": symbol,
                    "from": from_dt.isoformat(),
                    "to": to_dt.isoformat(),
                },
            )
        except ProviderError as e:
            logger.error("Finnhub news error for %s: %s", symbol, e)
            return []

        items = []
        for a in (data or [])[:limit]:
            published = datetime.fromtimestamp(a.get("datetime", 0), tz=timezone.utc)
            items.append(NewsItem(
                symbol=symbol,
                headline=a.get("headline", ""),
                summary=a.get("summary", ""),
                url=a.get("url", ""),
                published_at=published,
                source="finnhub",
            ))
        return items

    async def get_sentiment(self, symbol: str) -> float | None:
        """Use Finnhub news sentiment endpoint."""
        try:
            data = await _request(
                self._client, "GET",
                "/news-sentiment",
                params={"symbol": symbol},
            )
        except ProviderError as e:
            logger.error("Finnhub sentiment error for %s: %s", symbol, e)
            return None

        buzz = data.get("buzz", {})
        sentiment = data.get("sentiment", {})
        score = sentiment.get("bearishPercent", None)
        bullish = sentiment.get("bullishPercent", None)

        if bullish is not None and score is not None:
            # normalise to -1.0 .. 1.0
            return round(bullish - score, 4)
        return None

    # ── IndicatorProvider ───────────────────────────────────────────────────

    async def get_indicator(
        self,
        symbol: str,
        indicator: str,
        timeframe: TimeFrame = "1d",
        **kwargs,
    ) -> TechnicalIndicator | None:
        """
        Fetch a single technical indicator from Finnhub.

        Supported indicators (Finnhub names):
          rsi, macd, ema, sma, adx, aroon, stoch, cci, obv, williams

        kwargs are passed as additional query params (e.g. timeperiod=14).
        """
        resolution = _RESOLUTION_MAP.get(timeframe, "D")
        params: dict[str, Any] = {
            "symbol": symbol,
            "resolution": resolution,
            "indicator": indicator.lower(),
            **kwargs,
        }
        # Finnhub requires unix timestamps
        import time
        params["from"] = int(time.time()) - 86400 * 60  # 60 days back
        params["to"] = int(time.time())

        try:
            data = await _request(self._client, "GET", "/indicator", params=params)
        except ProviderError as e:
            logger.error("Finnhub indicator error for %s %s: %s", symbol, indicator, e)
            return None

        # Response has varying keys per indicator — extract the last value
        # e.g. RSI → data["rsi"], EMA → data["ema"]
        key = indicator.lower()
        values = data.get(key) or data.get(key.upper())
        timestamps = data.get("t")

        if not values or not timestamps:
            return None

        return TechnicalIndicator(
            symbol=symbol,
            indicator=indicator.upper(),
            value=float(values[-1]),
            timestamp=datetime.fromtimestamp(timestamps[-1], tz=timezone.utc),
            meta={"resolution": resolution, **kwargs},
            source="finnhub",
        )

    async def get_quote(self, symbol: str) -> dict | None:
        """Lightweight quote (last price, change %) from Finnhub."""
        try:
            return await _request(self._client, "GET", "/quote", params={"symbol": symbol})
        except ProviderError:
            return None

    async def close(self) -> None:
        await self._client.aclose()
