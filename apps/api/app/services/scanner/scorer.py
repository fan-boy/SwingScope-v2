"""
Deterministic scoring engine — returns 0-100 float.
Three sub-scores: trend, volume, breakout.
All inputs are normalised so weights always sum correctly.
"""
from dataclasses import dataclass

from app.services.scanner.config import ScannerConfig
from app.services.scanner.indicators import IndicatorSet


@dataclass(frozen=True)
class ScoreBreakdown:
    symbol: str
    total: float             # 0-100
    trend_score: float       # 0-100 before weighting
    volume_score: float      # 0-100 before weighting
    breakout_score: float    # 0-100 before weighting
    weighted_trend: float
    weighted_volume: float
    weighted_breakout: float
    confidence: str          # HIGH | MEDIUM | LOW


def _clamp(v: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, v))


def score_trend(ind: IndicatorSet, cfg: ScannerConfig) -> float:
    """
    Score 0-100 based on moving average alignment.
    - Close above MA20            → +40
    - Close above MA50            → +30
    - MA20 above MA50             → +20
    - MA50 above MA200            → +10
    """
    score = 0.0
    if ind.ma20 is not None and ind.close > ind.ma20:
        score += 40
        margin = (ind.close - ind.ma20) / ind.ma20
        score += _clamp(margin * 200, 0, 10)   # bonus up to 10 for strong gap

    if ind.ma50 is not None and ind.close > ind.ma50:
        score += 30

    if ind.ma20 is not None and ind.ma50 is not None and ind.ma20 > ind.ma50:
        score += 20

    if ind.ma50 is not None and ind.ma200 is not None and ind.ma50 > ind.ma200:
        score += 10

    return _clamp(score)


def score_volume(ind: IndicatorSet, cfg: ScannerConfig) -> float:
    """
    Score 0-100 based on relative volume.
    1.0x = 0 points, 2.0x = 50, 3.0x+ = 100.
    """
    rv = ind.relative_volume
    if rv <= 1.0:
        return 0.0
    # linear interpolation 1x → 0, 3x+ → 100
    raw = (rv - 1.0) / 2.0 * 100.0
    return _clamp(raw)


def score_breakout(ind: IndicatorSet, cfg: ScannerConfig) -> float:
    """
    Score 0-100 based on proximity to recent highs.
    - Within breakout_pct % of 20-day high → 50-100
    - Above 20-day high → 100
    - Between 20-day and 50-day zone → 25-50
    """
    pct_20 = ind.pct_from_high_20   # 0 = at high, negative = below
    pct_50 = ind.pct_from_high_50

    if pct_20 >= 0:
        # Above 20-day high = full breakout
        return 100.0

    dist = abs(pct_20)
    if dist <= cfg.breakout_pct:
        # In breakout zone
        return _clamp(100.0 - (dist / cfg.breakout_pct) * 50.0)

    # Score based on 50-day proximity as secondary signal
    if pct_50 >= 0:
        return 40.0
    dist_50 = abs(pct_50)
    return _clamp(30.0 - (dist_50 / (cfg.breakout_pct * 3)) * 30.0)


def score_candidate(ind: IndicatorSet, cfg: ScannerConfig) -> ScoreBreakdown:
    trend = score_trend(ind, cfg)
    volume = score_volume(ind, cfg)
    breakout = score_breakout(ind, cfg)

    w_trend = (cfg.weight_trend / 100.0) * trend
    w_volume = (cfg.weight_volume / 100.0) * volume
    w_breakout = (cfg.weight_breakout / 100.0) * breakout
    total = _clamp(w_trend + w_volume + w_breakout)

    if total >= 75:
        confidence = "HIGH"
    elif total >= 55:
        confidence = "MEDIUM"
    else:
        confidence = "LOW"

    return ScoreBreakdown(
        symbol=ind.symbol,
        total=round(total, 2),
        trend_score=round(trend, 2),
        volume_score=round(volume, 2),
        breakout_score=round(breakout, 2),
        weighted_trend=round(w_trend, 2),
        weighted_volume=round(w_volume, 2),
        weighted_breakout=round(w_breakout, 2),
        confidence=confidence,
    )
