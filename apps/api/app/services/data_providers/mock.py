"""
Mock provider — returns realistic synthetic data.
Used in tests and when API keys are absent.
"""
import random
from datetime import date, datetime, timedelta, timezone
from typing import Any

from app.services.data_providers.base import (
    MarketDataProvider, NewsProvider, IndicatorProvider,
    OHLCVBar, Quote, NewsItem, TechnicalIndicator, TimeFrame
)

_SEED_PRICES = {
    "AAPL": 192.5, "NVDA": 875.0, "MSFT": 422.3, "TSLA": 248.0,
    "AMZN": 198.0, "META": 532.0, "GOOGL": 178.0, "V": 278.0,
}


def _generate_bars(symbol: str, limit: int, base_price: float) -> list[OHLCVBar]:
    bars = []
    price = base_price
    today = date.today()
    for i in range(limit, 0, -1):
        d = today - timedelta(days=i)
        if d.weekday() >= 5:
            continue
        change = random.gauss(0.001, 0.015)
        open_ = price * (1 + random.gauss(0, 0.003))
        close = price * (1 + change)
        high = max(open_, close) * (1 + abs(random.gauss(0, 0.005)))
        low = min(open_, close) * (1 - abs(random.gauss(0, 0.005)))
        volume = random.randint(8_000_000, 80_000_000)
        bars.append(OHLCVBar(
            symbol=symbol, date=d,
            open=round(open_, 2), high=round(high, 2),
            low=round(low, 2), close=round(close, 2),
            volume=float(volume),
            vwap=round((open_ + high + low + close) / 4, 2),
            source="mock",
        ))
        price = close
    return bars


class MockMarketDataProvider(MarketDataProvider):
    async def get_bars(self, symbol: str, timeframe: TimeFrame = "1d", limit: int = 60, **_) -> list[OHLCVBar]:
        base = _SEED_PRICES.get(symbol, random.uniform(50, 500))
        return _generate_bars(symbol, limit, base)

    async def get_quotes(self, symbols: list[str]) -> dict[str, Quote]:
        return {
            s: Quote(
                symbol=s,
                bid=round(_SEED_PRICES.get(s, 100) * 0.999, 2),
                ask=round(_SEED_PRICES.get(s, 100) * 1.001, 2),
                last=_SEED_PRICES.get(s, 100),
                timestamp=datetime.now(timezone.utc),
                source="mock",
            )
            for s in symbols
        }

    async def get_tradable_symbols(self) -> list[str]:
        return list(_SEED_PRICES.keys())


class MockNewsProvider(NewsProvider):
    _HEADLINES = [
        "{symbol} beats quarterly earnings expectations",
        "Analysts raise {symbol} price target to new high",
        "{symbol} announces strategic partnership",
        "{symbol} reports solid revenue growth",
        "Market rally lifts {symbol} shares",
    ]

    async def get_news(self, symbol: str, limit: int = 10, **_) -> list[NewsItem]:
        now = datetime.now(timezone.utc)
        return [
            NewsItem(
                symbol=symbol,
                headline=h.format(symbol=symbol),
                summary="",
                url=f"https://example.com/news/{symbol.lower()}/{i}",
                published_at=now - timedelta(hours=i * 4),
                sentiment_score=random.uniform(0.05, 0.4),
                sentiment_label="POSITIVE",
                source="mock",
            )
            for i, h in enumerate(self._HEADLINES[:limit])
        ]

    async def get_sentiment(self, symbol: str) -> float | None:
        return round(random.uniform(0.05, 0.35), 4)


class MockIndicatorProvider(IndicatorProvider):
    async def get_indicator(self, symbol: str, indicator: str, **_) -> TechnicalIndicator | None:
        defaults = {"RSI": 58.5, "EMA_20": 190.0, "EMA_50": 185.0, "ATR": 4.5, "MACD": 1.2}
        val = defaults.get(indicator.upper(), random.uniform(20, 80))
        return TechnicalIndicator(
            symbol=symbol,
            indicator=indicator.upper(),
            value=round(val + random.gauss(0, 1), 4),
            timestamp=datetime.now(timezone.utc),
            source="mock",
        )
