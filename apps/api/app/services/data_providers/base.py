"""
Abstract base interfaces for market data providers.

Any new provider (Polygon, Yahoo, etc.) must implement these interfaces.
Calling code depends only on these types — never on a concrete adapter.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Literal


# ─── Normalised value types ────────────────────────────────────────────────

@dataclass(frozen=True)
class OHLCVBar:
    """One daily OHLCV bar."""
    symbol: str
    date: date
    open: float
    high: float
    low: float
    close: float
    volume: float
    vwap: float | None = None
    source: str = ""


@dataclass(frozen=True)
class Quote:
    """Latest bid/ask/last for a symbol."""
    symbol: str
    bid: float | None
    ask: float | None
    last: float | None
    timestamp: datetime
    source: str = ""


@dataclass(frozen=True)
class NewsItem:
    """A single news article with sentiment."""
    symbol: str
    headline: str
    summary: str
    url: str
    published_at: datetime
    sentiment_score: float | None = None   # -1.0 to 1.0
    sentiment_label: str | None = None     # POSITIVE | NEUTRAL | NEGATIVE
    source: str = ""


@dataclass(frozen=True)
class TechnicalIndicator:
    """A named technical indicator value at a point in time."""
    symbol: str
    indicator: str   # e.g. "RSI", "EMA_20", "MACD"
    value: float
    timestamp: datetime
    meta: dict = field(default_factory=dict)
    source: str = ""


TimeFrame = Literal["1d", "1h", "15m", "5m"]


# ─── Abstract provider interfaces ──────────────────────────────────────────

class MarketDataProvider(ABC):
    """
    Fetch historical and real-time price data.
    Implement this for Alpaca, Polygon, Yahoo, etc.
    """

    @abstractmethod
    async def get_bars(
        self,
        symbol: str,
        timeframe: TimeFrame = "1d",
        limit: int = 60,
        start: date | None = None,
        end: date | None = None,
    ) -> list[OHLCVBar]:
        """Return OHLCV bars sorted oldest-first."""
        ...

    @abstractmethod
    async def get_quotes(self, symbols: list[str]) -> dict[str, Quote]:
        """Return latest quote keyed by symbol."""
        ...

    @abstractmethod
    async def get_tradable_symbols(self) -> list[str]:
        """Return symbols available for trading on this provider."""
        ...


class NewsProvider(ABC):
    """
    Fetch news and sentiment for symbols.
    Implement this for Finnhub, Marketaux, Benzinga, etc.
    """

    @abstractmethod
    async def get_news(
        self,
        symbol: str,
        limit: int = 10,
        from_date: date | None = None,
    ) -> list[NewsItem]:
        ...

    @abstractmethod
    async def get_sentiment(self, symbol: str) -> float | None:
        """Return aggregate sentiment score -1.0 to 1.0, or None if unavailable."""
        ...


class IndicatorProvider(ABC):
    """
    Fetch pre-computed technical indicators.
    Implement this for Finnhub, Polygon, Taapi, etc.
    """

    @abstractmethod
    async def get_indicator(
        self,
        symbol: str,
        indicator: str,
        timeframe: TimeFrame = "1d",
        **kwargs,
    ) -> TechnicalIndicator | None:
        ...
