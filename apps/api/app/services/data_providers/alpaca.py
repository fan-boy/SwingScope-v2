"""
Alpaca Markets adapter — MarketDataProvider implementation.

Docs: https://docs.alpaca.markets/reference/stockbars
"""
import logging
from datetime import date, datetime, timedelta, timezone

import httpx

from app.services.data_providers.base import (
    MarketDataProvider, OHLCVBar, Quote, TimeFrame
)
from app.services.data_providers.http import _request, build_client, ProviderError

logger = logging.getLogger(__name__)

ALPACA_DATA_BASE = "https://data.alpaca.markets"
ALPACA_TRADE_BASE = "https://api.alpaca.markets"

_TIMEFRAME_MAP: dict[TimeFrame, str] = {
    "1d": "1Day",
    "1h": "1Hour",
    "15m": "15Min",
    "5m": "5Min",
}


class AlpacaAdapter(MarketDataProvider):
    def __init__(self, api_key: str, api_secret: str) -> None:
        self._headers = {
            "APCA-API-KEY-ID": api_key,
            "APCA-API-SECRET-KEY": api_secret,
        }
        self._data_client = build_client(ALPACA_DATA_BASE, self._headers)
        self._trade_client = build_client(ALPACA_TRADE_BASE, self._headers)

    async def get_bars(
        self,
        symbol: str,
        timeframe: TimeFrame = "1d",
        limit: int = 60,
        start: date | None = None,
        end: date | None = None,
    ) -> list[OHLCVBar]:
        tf = _TIMEFRAME_MAP.get(timeframe, "1Day")
        # Always set start date to ensure we get enough history for indicators
        from datetime import timedelta
        default_start = date.today() - timedelta(days=limit * 2)
        params: dict = {
            "timeframe": tf,
            "limit": limit,
            "adjustment": "split",
            "feed": "sip",
            "start": (start or default_start).isoformat(),
        }
        if end:
            params["end"] = end.isoformat()

        try:
            data = await _request(
                self._data_client, "GET",
                f"/v2/stocks/{symbol}/bars",
                params=params,
            )
        except ProviderError as e:
            logger.error("Alpaca bars error for %s: %s", symbol, e)
            return []

        bars = data.get("bars") or []
        return [
            OHLCVBar(
                symbol=symbol,
                date=datetime.fromisoformat(b["t"].replace("Z", "+00:00")).date(),
                open=float(b["o"]),
                high=float(b["h"]),
                low=float(b["l"]),
                close=float(b["c"]),
                volume=float(b["v"]),
                vwap=float(b["vw"]) if b.get("vw") else None,
                source="alpaca",
            )
            for b in bars
        ]

    async def get_multi_bars(
        self,
        symbols: list[str],
        timeframe: TimeFrame = "1d",
        limit: int = 60,
    ) -> dict[str, list[OHLCVBar]]:
        """Batch endpoint — fetch bars for multiple symbols in one call."""
        from datetime import timedelta
        default_start = date.today() - timedelta(days=limit * 2)
        params = {
            "symbols": ",".join(symbols),
            "timeframe": _TIMEFRAME_MAP.get(timeframe, "1Day"),
            "limit": limit,
            "adjustment": "split",
            "feed": "sip",
            "start": default_start.isoformat(),
        }
        try:
            data = await _request(
                self._data_client, "GET",
                "/v2/stocks/bars",
                params=params,
            )
        except ProviderError as e:
            logger.error("Alpaca multi-bars error: %s", e)
            return {}

        result: dict[str, list[OHLCVBar]] = {}
        for sym, bars in (data.get("bars") or {}).items():
            result[sym] = [
                OHLCVBar(
                    symbol=sym,
                    date=datetime.fromisoformat(b["t"].replace("Z", "+00:00")).date(),
                    open=float(b["o"]),
                    high=float(b["h"]),
                    low=float(b["l"]),
                    close=float(b["c"]),
                    volume=float(b["v"]),
                    vwap=float(b["vw"]) if b.get("vw") else None,
                    source="alpaca",
                )
                for b in bars
            ]
        return result

    async def get_quotes(self, symbols: list[str]) -> dict[str, Quote]:
        params = {"symbols": ",".join(symbols), "feed": "iex"}
        try:
            data = await _request(
                self._data_client, "GET",
                "/v2/stocks/quotes/latest",
                params=params,
            )
        except ProviderError as e:
            logger.error("Alpaca quotes error: %s", e)
            return {}

        result: dict[str, Quote] = {}
        for sym, q in (data.get("quotes") or {}).items():
            result[sym] = Quote(
                symbol=sym,
                bid=float(q["bp"]) if q.get("bp") else None,
                ask=float(q["ap"]) if q.get("ap") else None,
                last=None,  # use trades endpoint for last price
                timestamp=datetime.fromisoformat(q["t"].replace("Z", "+00:00")),
                source="alpaca",
            )
        return result

    async def get_tradable_symbols(self) -> list[str]:
        """Return all active, tradable US equity symbols."""
        try:
            data = await _request(
                self._trade_client, "GET",
                "/v2/assets",
                params={"status": "active", "asset_class": "us_equity", "tradable": "true"},
            )
        except ProviderError as e:
            logger.error("Alpaca assets error: %s", e)
            return []

        return [a["symbol"] for a in data if a.get("tradable") and a.get("fractionable") is not False]

    async def close(self) -> None:
        await self._data_client.aclose()
        await self._trade_client.aclose()
