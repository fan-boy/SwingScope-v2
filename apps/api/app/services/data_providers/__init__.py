"""
Provider registry — returns the configured provider based on env settings.
Import from here rather than instantiating adapters directly.
"""
from functools import lru_cache

from app.services.data_providers.base import (
    MarketDataProvider, NewsProvider, IndicatorProvider,
    OHLCVBar, Quote, NewsItem, TechnicalIndicator, TimeFrame,
)


def get_market_provider() -> MarketDataProvider:
    from app.core.config import settings
    if settings.mock_mode or not settings.alpaca_api_key:
        from app.services.data_providers.mock import MockMarketDataProvider
        return MockMarketDataProvider()
    from app.services.data_providers.alpaca import AlpacaAdapter
    return AlpacaAdapter(settings.alpaca_api_key, settings.alpaca_api_secret)


def get_news_provider() -> NewsProvider:
    from app.core.config import settings
    if settings.mock_mode or not settings.finnhub_api_key:
        from app.services.data_providers.mock import MockNewsProvider
        return MockNewsProvider()
    from app.services.data_providers.finnhub import FinnhubAdapter
    return FinnhubAdapter(settings.finnhub_api_key)


def get_indicator_provider() -> IndicatorProvider:
    from app.core.config import settings
    if settings.mock_mode or not settings.finnhub_api_key:
        from app.services.data_providers.mock import MockIndicatorProvider
        return MockIndicatorProvider()
    from app.services.data_providers.finnhub import FinnhubAdapter
    return FinnhubAdapter(settings.finnhub_api_key)


__all__ = [
    "get_market_provider", "get_news_provider", "get_indicator_provider",
    "MarketDataProvider", "NewsProvider", "IndicatorProvider",
    "OHLCVBar", "Quote", "NewsItem", "TechnicalIndicator", "TimeFrame",
]
