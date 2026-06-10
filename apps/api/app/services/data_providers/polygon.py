"""
Polygon.io adapter — stub ready for implementation.

Drop in: implement the same interface as AlpacaAdapter.
Docs: https://polygon.io/docs/stocks
"""
import logging
from datetime import date

from app.services.data_providers.base import (
    MarketDataProvider, OHLCVBar, Quote, TimeFrame
)

logger = logging.getLogger(__name__)


class PolygonAdapter(MarketDataProvider):
    """
    Polygon.io market data provider.
    Not yet implemented — stub preserves the interface.
    """

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key
        # TODO: init httpx client
        # self._client = build_client("https://api.polygon.io", {"Authorization": f"Bearer {api_key}"})

    async def get_bars(
        self,
        symbol: str,
        timeframe: TimeFrame = "1d",
        limit: int = 60,
        start: date | None = None,
        end: date | None = None,
    ) -> list[OHLCVBar]:
        # TODO: GET /v2/aggs/ticker/{symbol}/range/1/day/{start}/{end}
        raise NotImplementedError("PolygonAdapter.get_bars not yet implemented")

    async def get_quotes(self, symbols: list[str]) -> dict[str, Quote]:
        # TODO: GET /v2/last/trade/{symbol}
        raise NotImplementedError("PolygonAdapter.get_quotes not yet implemented")

    async def get_tradable_symbols(self) -> list[str]:
        # TODO: GET /v3/reference/tickers
        raise NotImplementedError("PolygonAdapter.get_tradable_symbols not yet implemented")
