"""
GET /api/chart/{symbol}
Returns last 60 OHLCV bars with computed MA20/50/200, ATR14, relative volume,
and breakout level (20-day high). Uses the existing AlpacaAdapter + compute_indicators.
"""
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.data_providers.alpaca import AlpacaAdapter
from app.services.data_providers.mock import MockDataProvider
from app.services.scanner.indicators import compute_indicators
from app.core.config import settings

router = APIRouter(prefix="/chart", tags=["chart"])
logger = logging.getLogger(__name__)

BARS_TO_FETCH = 210  # need 200+ for MA200
DISPLAY_BARS = 60


class ChartCandle(BaseModel):
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    ma20: float | None
    ma50: float | None
    ma200: float | None


class ChartMetrics(BaseModel):
    rel_vol: float
    atr14: float | None
    stop_distance: float | None   # 1.5x ATR
    stop_price: float | None
    breakout_level: float
    last_close: float


class ChartResponse(BaseModel):
    symbol: str
    candles: list[ChartCandle]
    metrics: ChartMetrics


def _sma(values: list[float], period: int) -> list[float | None]:
    result: list[float | None] = []
    for i in range(len(values)):
        if i < period - 1:
            result.append(None)
        else:
            result.append(sum(values[i - period + 1 : i + 1]) / period)
    return result


def _atr14(bars) -> float | None:
    if len(bars) < 15:
        return None
    trs = []
    for i in range(1, len(bars)):
        h, l, prev_c = bars[i].high, bars[i].low, bars[i - 1].close
        tr = max(h - l, abs(h - prev_c), abs(l - prev_c))
        trs.append(tr)
    if len(trs) < 14:
        return None
    atr = sum(trs[:14]) / 14
    for tr in trs[14:]:
        atr = (atr * 13 + tr) / 14
    return atr


@router.get("/{symbol}", response_model=ChartResponse)
async def get_chart(symbol: str) -> ChartResponse:
    symbol = symbol.upper()
    try:
        if settings.mock_mode or not settings.alpaca_api_key:
            provider = MockDataProvider()
        else:
            provider = AlpacaAdapter(settings.alpaca_api_key, settings.alpaca_api_secret)

        bars = await provider.get_bars(symbol, timeframe="1d", limit=BARS_TO_FETCH)
        if not bars:
            raise HTTPException(status_code=404, detail=f"No data for {symbol}")

        closes = [b.close for b in bars]
        ma20_arr = _sma(closes, 20)
        ma50_arr = _sma(closes, 50)
        ma200_arr = _sma(closes, 200)

        atr = _atr14(bars)
        last_close = closes[-1]
        avg_vol = sum(b.volume for b in bars[-21:-1]) / 20 if len(bars) >= 21 else bars[-1].volume
        rel_vol = round(bars[-1].volume / avg_vol, 2) if avg_vol > 0 else 1.0
        breakout_level = max(b.high for b in bars[-20:])

        start = max(0, len(bars) - DISPLAY_BARS)
        candles = []
        for i, bar in enumerate(bars[start:], start=start):
            candles.append(ChartCandle(
                date=bar.date.isoformat(),
                open=round(bar.open, 2),
                high=round(bar.high, 2),
                low=round(bar.low, 2),
                close=round(bar.close, 2),
                volume=bar.volume,
                ma20=round(ma20_arr[i], 2) if ma20_arr[i] is not None else None,
                ma50=round(ma50_arr[i], 2) if ma50_arr[i] is not None else None,
                ma200=round(ma200_arr[i], 2) if ma200_arr[i] is not None else None,
            ))

        stop_dist = round(atr * 1.5, 2) if atr else None
        return ChartResponse(
            symbol=symbol,
            candles=candles,
            metrics=ChartMetrics(
                rel_vol=rel_vol,
                atr14=round(atr, 2) if atr else None,
                stop_distance=stop_dist,
                stop_price=round(last_close - stop_dist, 2) if stop_dist else None,
                breakout_level=round(breakout_level, 2),
                last_close=round(last_close, 2),
            ),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chart error for {symbol}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch chart data")