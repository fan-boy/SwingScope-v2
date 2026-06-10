"""
Unit tests for data provider adapters.
All tests use mock providers — no API keys required.
"""
import asyncio
from datetime import date, datetime, timezone

import pytest

from app.services.data_providers.mock import (
    MockMarketDataProvider,
    MockNewsProvider,
    MockIndicatorProvider,
)
from app.services.data_providers.base import OHLCVBar, Quote, NewsItem, TechnicalIndicator


# ─── MockMarketDataProvider ────────────────────────────────────────────────

class TestMockMarketDataProvider:
    def setup_method(self):
        self.provider = MockMarketDataProvider()

    def test_get_bars_returns_list(self):
        bars = asyncio.run(self.provider.get_bars("AAPL", limit=30))
        assert isinstance(bars, list)
        assert len(bars) > 0

    def test_get_bars_are_ohlcv(self):
        bars = asyncio.run(self.provider.get_bars("NVDA", limit=10))
        for bar in bars:
            assert isinstance(bar, OHLCVBar)
            assert bar.symbol == "NVDA"
            assert bar.high >= bar.low
            assert bar.high >= bar.open
            assert bar.high >= bar.close
            assert bar.volume > 0

    def test_get_bars_sorted_oldest_first(self):
        bars = asyncio.run(self.provider.get_bars("AAPL", limit=20))
        dates = [b.date for b in bars]
        assert dates == sorted(dates)

    def test_get_bars_excludes_weekends(self):
        bars = asyncio.run(self.provider.get_bars("MSFT", limit=60))
        for bar in bars:
            assert bar.date.weekday() < 5, f"Weekend bar found: {bar.date}"

    def test_get_bars_source_is_mock(self):
        bars = asyncio.run(self.provider.get_bars("AAPL", limit=5))
        assert all(b.source == "mock" for b in bars)

    def test_get_quotes_returns_dict(self):
        quotes = asyncio.run(self.provider.get_quotes(["AAPL", "NVDA"]))
        assert isinstance(quotes, dict)
        assert "AAPL" in quotes
        assert "NVDA" in quotes

    def test_get_quotes_are_typed(self):
        quotes = asyncio.run(self.provider.get_quotes(["MSFT"]))
        q = quotes["MSFT"]
        assert isinstance(q, Quote)
        assert q.bid < q.ask
        assert q.symbol == "MSFT"

    def test_get_tradable_symbols(self):
        symbols = asyncio.run(self.provider.get_tradable_symbols())
        assert isinstance(symbols, list)
        assert "AAPL" in symbols


# ─── MockNewsProvider ──────────────────────────────────────────────────────

class TestMockNewsProvider:
    def setup_method(self):
        self.provider = MockNewsProvider()

    def test_get_news_returns_list(self):
        news = asyncio.run(self.provider.get_news("AAPL"))
        assert isinstance(news, list)
        assert len(news) > 0

    def test_news_items_typed(self):
        news = asyncio.run(self.provider.get_news("NVDA", limit=3))
        for item in news:
            assert isinstance(item, NewsItem)
            assert item.symbol == "NVDA"
            assert len(item.headline) > 0
            assert isinstance(item.published_at, datetime)

    def test_news_respects_limit(self):
        news = asyncio.run(self.provider.get_news("MSFT", limit=2))
        assert len(news) <= 2

    def test_get_sentiment_returns_float(self):
        score = asyncio.run(self.provider.get_sentiment("AAPL"))
        assert score is not None
        assert -1.0 <= score <= 1.0


# ─── MockIndicatorProvider ─────────────────────────────────────────────────

class TestMockIndicatorProvider:
    def setup_method(self):
        self.provider = MockIndicatorProvider()

    def test_get_rsi(self):
        result = asyncio.run(self.provider.get_indicator("AAPL", "RSI"))
        assert isinstance(result, TechnicalIndicator)
        assert result.indicator == "RSI"
        assert 0 <= result.value <= 100

    def test_get_ema(self):
        result = asyncio.run(self.provider.get_indicator("NVDA", "EMA_20"))
        assert result is not None
        assert result.value > 0

    def test_indicator_has_timestamp(self):
        result = asyncio.run(self.provider.get_indicator("MSFT", "MACD"))
        assert isinstance(result.timestamp, datetime)
        assert result.timestamp.tzinfo is not None


# ─── Interface contract tests ──────────────────────────────────────────────

class TestProviderInterface:
    """
    Ensure all mock providers satisfy the abstract interface.
    These tests will catch regressions if interfaces change.
    """
    def test_mock_market_implements_interface(self):
        from app.services.data_providers.base import MarketDataProvider
        assert isinstance(MockMarketDataProvider(), MarketDataProvider)

    def test_mock_news_implements_interface(self):
        from app.services.data_providers.base import NewsProvider
        assert isinstance(MockNewsProvider(), NewsProvider)

    def test_mock_indicator_implements_interface(self):
        from app.services.data_providers.base import IndicatorProvider
        assert isinstance(MockIndicatorProvider(), IndicatorProvider)
