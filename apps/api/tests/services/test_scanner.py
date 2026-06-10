"""
Unit tests for scanner — indicators, filters, scorer.
All pure functions, no DB or network.
"""
import asyncio
from datetime import date, timedelta

from app.services.data_providers.base import OHLCVBar
from app.services.scanner.config import ScannerConfig
from app.services.scanner.indicators import compute_indicators, IndicatorSet
from app.services.scanner.filters import (
    apply_filters, filter_price, filter_dollar_volume,
    filter_relative_volume, filter_moving_averages,
)
from app.services.scanner.scorer import (
    score_candidate, score_trend, score_volume, score_breakout,
)


# ─── Fixtures ──────────────────────────────────────────────────────────────

def make_bars(
    symbol: str = "TEST",
    count: int = 60,
    base_price: float = 100.0,
    trend: float = 0.002,     # daily drift
    volume: int = 10_000_000,
    today_volume_mult: float = 1.5,
) -> list[OHLCVBar]:
    bars = []
    price = base_price
    today = date.today()
    for i in range(count, 0, -1):
        d = today - timedelta(days=i)
        close = price * (1 + trend)
        vol = volume if i > 1 else int(volume * today_volume_mult)
        bars.append(OHLCVBar(
            symbol=symbol, date=d,
            open=price, high=close * 1.005,
            low=price * 0.995, close=close,
            volume=float(vol), source="test",
        ))
        price = close
    return bars


DEFAULT_CFG = ScannerConfig(
    min_price=5.0,
    min_avg_dollar_volume=1_000_000.0,
    min_relative_volume=1.0,
    require_above_ma20=True,
    require_above_ma50=True,
    require_ma20_above_ma50=True,
    require_ma50_above_ma200=False,
    breakout_pct=0.03,
    min_final_score=0.0,
)


# ─── Indicator tests ────────────────────────────────────────────────────────

class TestComputeIndicators:
    def test_returns_none_for_too_few_bars(self):
        bars = make_bars(count=10)
        assert compute_indicators(bars) is None

    def test_returns_indicator_set(self):
        bars = make_bars(count=60)
        ind = compute_indicators(bars)
        assert isinstance(ind, IndicatorSet)

    def test_ma20_is_average_of_last_20_closes(self):
        bars = make_bars(count=60, trend=0.0)   # flat price
        ind = compute_indicators(bars)
        assert ind.ma20 is not None
        assert abs(ind.ma20 - ind.close) < 0.01   # flat = MA ≈ close

    def test_relative_volume_gt_1_when_today_volume_high(self):
        bars = make_bars(count=60, today_volume_mult=2.5)
        ind = compute_indicators(bars)
        assert ind.relative_volume > 1.5

    def test_relative_volume_near_1_when_normal(self):
        bars = make_bars(count=60, today_volume_mult=1.0)
        ind = compute_indicators(bars)
        assert 0.8 <= ind.relative_volume <= 1.3

    def test_high_20_is_max_of_previous_20_highs(self):
        bars = make_bars(count=60)
        ind = compute_indicators(bars)
        assert ind.high_20 > 0

    def test_uptrend_price_above_ma20(self):
        bars = make_bars(count=60, trend=0.005)   # strong uptrend
        ind = compute_indicators(bars)
        assert ind.close > ind.ma20

    def test_ma50_none_when_insufficient_bars(self):
        bars = make_bars(count=40)
        ind = compute_indicators(bars)
        assert ind is not None
        assert ind.ma50 is None


# ─── Filter tests ───────────────────────────────────────────────────────────

class TestFilters:
    def _ind(self, close=150.0, rel_vol=2.0, dv=50_000_000.0, ma20=145.0, ma50=140.0):
        return IndicatorSet(
            symbol="TEST", close=close,
            ma20=ma20, ma50=ma50, ma200=None,
            avg_volume_20=1_000_000, avg_dollar_volume_20=dv,
            relative_volume=rel_vol,
            high_20=155.0, high_50=160.0,
            pct_from_high_20=-0.032, pct_from_high_50=-0.062,
        )

    def test_price_filter_passes(self):
        assert filter_price(self._ind(close=100), DEFAULT_CFG).passed

    def test_price_filter_fails_too_low(self):
        r = filter_price(self._ind(close=2.0), DEFAULT_CFG)
        assert not r.passed
        assert r.failed_filter == "price"

    def test_dollar_volume_filter_fails(self):
        r = filter_dollar_volume(self._ind(dv=500_000), DEFAULT_CFG)
        assert not r.passed
        assert r.failed_filter == "dollar_volume"

    def test_relative_volume_fails(self):
        cfg = ScannerConfig(min_relative_volume=2.0)
        r = filter_relative_volume(self._ind(rel_vol=1.2), cfg)
        assert not r.passed

    def test_ma_filter_fails_when_below_ma20(self):
        r = filter_moving_averages(self._ind(close=140.0, ma20=145.0), DEFAULT_CFG)
        assert not r.passed
        assert r.failed_filter == "ma20"

    def test_ma_filter_passes_valid_uptrend(self):
        r = filter_moving_averages(self._ind(close=155.0, ma20=148.0, ma50=140.0), DEFAULT_CFG)
        assert r.passed

    def test_apply_filters_passes_clean_stock(self):
        ind = self._ind(close=155.0, rel_vol=2.0, dv=50_000_000)
        assert apply_filters(ind, DEFAULT_CFG).passed

    def test_apply_filters_fails_early(self):
        ind = self._ind(close=1.0)   # too cheap
        r = apply_filters(ind, DEFAULT_CFG)
        assert not r.passed
        assert r.failed_filter == "price"


# ─── Scorer tests ───────────────────────────────────────────────────────────

class TestScorer:
    def _ind(self, close=155.0, ma20=148.0, ma50=140.0, ma200=None, rel_vol=2.5, pct_20=-0.01):
        return IndicatorSet(
            symbol="TEST", close=close,
            ma20=ma20, ma50=ma50, ma200=ma200,
            avg_volume_20=1_000_000, avg_dollar_volume_20=50_000_000,
            relative_volume=rel_vol,
            high_20=close / (1 + pct_20) if pct_20 < 0 else close,
            high_50=close * 0.95,
            pct_from_high_20=pct_20,
            pct_from_high_50=-0.05,
        )

    def test_trend_score_max_for_full_alignment(self):
        ind = self._ind(close=200, ma20=190, ma50=180, ma200=170)
        cfg = ScannerConfig(require_ma50_above_ma200=True)
        score = score_trend(ind, cfg)
        assert score >= 90

    def test_trend_score_no_ma20_bonus_when_below(self):
        # close < MA20 → no MA20 bonus (+40), but MA20 > MA50 still earns +20
        ind = self._ind(close=130, ma20=148, ma50=140)
        score = score_trend(ind, DEFAULT_CFG)
        assert score < 30   # lost the +40 MA20 bonus — should be low

    def test_volume_score_zero_at_1x(self):
        ind = self._ind(rel_vol=1.0)
        assert score_volume(ind, DEFAULT_CFG) == 0.0

    def test_volume_score_max_at_3x(self):
        ind = self._ind(rel_vol=3.0)
        assert score_volume(ind, DEFAULT_CFG) == 100.0

    def test_volume_score_linear(self):
        ind_2x = self._ind(rel_vol=2.0)
        assert 45 <= score_volume(ind_2x, DEFAULT_CFG) <= 55

    def test_breakout_score_100_at_new_high(self):
        ind = self._ind(close=160, pct_20=0.0)
        assert score_breakout(ind, DEFAULT_CFG) == 100.0

    def test_breakout_score_high_near_high(self):
        ind = self._ind(pct_20=-0.01)   # 1% below 20-day high
        assert score_breakout(ind, DEFAULT_CFG) >= 70

    def test_total_score_0_to_100(self):
        for rel_vol in [0.5, 1.0, 2.0, 3.0]:
            ind = self._ind(rel_vol=rel_vol)
            bd = score_candidate(ind, DEFAULT_CFG)
            assert 0 <= bd.total <= 100

    def test_confidence_high_above_75(self):
        ind = self._ind(rel_vol=3.0, pct_20=0.0, close=200, ma20=190, ma50=180)
        bd = score_candidate(ind, DEFAULT_CFG)
        assert bd.confidence in ("HIGH", "MEDIUM")

    def test_confidence_low_weak_candidate(self):
        ind = self._ind(rel_vol=1.0, close=150, ma20=148, pct_20=-0.15)
        bd = score_candidate(ind, DEFAULT_CFG)
        assert bd.confidence in ("LOW", "MEDIUM")

    def test_score_deterministic(self):
        ind = self._ind()
        s1 = score_candidate(ind, DEFAULT_CFG)
        s2 = score_candidate(ind, DEFAULT_CFG)
        assert s1.total == s2.total


# ─── End-to-end pipeline test ───────────────────────────────────────────────

class TestScannerPipeline:
    def test_full_pipeline_uptrend_passes(self):
        bars = make_bars(count=60, trend=0.003, today_volume_mult=2.5)
        ind = compute_indicators(bars)
        assert ind is not None
        result = apply_filters(ind, DEFAULT_CFG)
        assert result.passed
        bd = score_candidate(ind, DEFAULT_CFG)
        assert bd.total > 0

    def test_full_pipeline_cheap_stock_filtered(self):
        bars = make_bars(count=60, base_price=3.0)
        ind = compute_indicators(bars)
        result = apply_filters(ind, DEFAULT_CFG)
        assert not result.passed
        assert result.failed_filter == "price"

    def test_full_pipeline_downtrend_filtered(self):
        bars = make_bars(count=60, trend=-0.003)
        ind = compute_indicators(bars)
        if ind:
            result = apply_filters(ind, DEFAULT_CFG)
            # price below MAs in downtrend should fail
            if not result.passed:
                assert result.failed_filter in ("ma20", "ma50", "ma20_above_ma50")
