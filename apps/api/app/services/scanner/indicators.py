"""
Pure functions for computing technical indicators from OHLCV bars.
No side effects — fully deterministic and testable.
"""
from dataclasses import dataclass

from app.services.data_providers.base import OHLCVBar


@dataclass(frozen=True)
class IndicatorSet:
    symbol: str
    close: float
    ma20: float | None
    ma50: float | None
    ma200: float | None
    avg_volume_20: float
    avg_dollar_volume_20: float
    relative_volume: float        # today vol / avg_vol_20
    high_20: float                # highest high over last 20 bars
    high_50: float                # highest high over last 50 bars
    pct_from_high_20: float       # (close - high_20) / high_20
    pct_from_high_50: float       # (close - high_50) / high_50


def compute_indicators(bars: list[OHLCVBar]) -> IndicatorSet | None:
    """
    Compute all indicators from a list of OHLCV bars (oldest-first).
    Returns None if there are not enough bars.
    """
    if not bars or len(bars) < 21:
        return None

    symbol = bars[-1].symbol
    closes = [b.close for b in bars]
    volumes = [b.volume for b in bars]
    highs = [b.high for b in bars]
    dollar_vols = [b.close * b.volume for b in bars]

    n = len(closes)
    close = closes[-1]
    today_vol = volumes[-1]

    def sma(series: list[float], period: int) -> float | None:
        if len(series) < period:
            return None
        return sum(series[-period:]) / period

    ma20 = sma(closes, 20)
    ma50 = sma(closes, 50) if n >= 50 else None
    ma200 = sma(closes, 200) if n >= 200 else None

    avg_vol_20 = sma(volumes[:-1], 20) or 1.0   # exclude today
    avg_dv_20 = sma(dollar_vols[:-1], 20) or 1.0

    # Use previous 20 / 50 highs (exclude today for clean signal)
    high_20 = max(highs[-21:-1]) if n >= 21 else max(highs)
    high_50 = max(highs[-51:-1]) if n >= 51 else max(highs[-21:-1])

    rel_vol = today_vol / avg_vol_20 if avg_vol_20 > 0 else 1.0
    pct_from_20 = (close - high_20) / high_20 if high_20 > 0 else -1.0
    pct_from_50 = (close - high_50) / high_50 if high_50 > 0 else -1.0

    return IndicatorSet(
        symbol=symbol,
        close=close,
        ma20=ma20,
        ma50=ma50,
        ma200=ma200,
        avg_volume_20=avg_vol_20,
        avg_dollar_volume_20=avg_dv_20,
        relative_volume=rel_vol,
        high_20=high_20,
        high_50=high_50,
        pct_from_high_20=pct_from_20,
        pct_from_high_50=pct_from_50,
    )
