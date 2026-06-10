"""
Filter chain — each filter returns (passes: bool, reason: str).
All filters are pure functions; easy to unit test independently.
"""
from dataclasses import dataclass

from app.services.scanner.config import ScannerConfig
from app.services.scanner.indicators import IndicatorSet


@dataclass(frozen=True)
class FilterResult:
    passed: bool
    failed_filter: str | None = None
    reason: str | None = None


def _fail(name: str, reason: str) -> FilterResult:
    return FilterResult(passed=False, failed_filter=name, reason=reason)


def _pass() -> FilterResult:
    return FilterResult(passed=True)


def filter_price(ind: IndicatorSet, cfg: ScannerConfig) -> FilterResult:
    if ind.close < cfg.min_price:
        return _fail("price", f"${ind.close:.2f} < min ${cfg.min_price}")
    if ind.close > cfg.max_price:
        return _fail("price", f"${ind.close:.2f} > max ${cfg.max_price}")
    return _pass()


def filter_dollar_volume(ind: IndicatorSet, cfg: ScannerConfig) -> FilterResult:
    if ind.avg_dollar_volume_20 < cfg.min_avg_dollar_volume:
        return _fail(
            "dollar_volume",
            f"avg DV ${ind.avg_dollar_volume_20:,.0f} < min ${cfg.min_avg_dollar_volume:,.0f}",
        )
    return _pass()


def filter_relative_volume(ind: IndicatorSet, cfg: ScannerConfig) -> FilterResult:
    if ind.relative_volume < cfg.min_relative_volume:
        return _fail(
            "relative_volume",
            f"rel vol {ind.relative_volume:.2f}x < min {cfg.min_relative_volume:.2f}x",
        )
    return _pass()


def filter_moving_averages(ind: IndicatorSet, cfg: ScannerConfig) -> FilterResult:
    if cfg.require_above_ma20:
        if ind.ma20 is None:
            return _fail("ma20", "insufficient data for MA20")
        if ind.close < ind.ma20:
            return _fail("ma20", f"close ${ind.close:.2f} < MA20 ${ind.ma20:.2f}")

    if cfg.require_above_ma50:
        if ind.ma50 is None:
            return _fail("ma50", "insufficient data for MA50")
        if ind.close < ind.ma50:
            return _fail("ma50", f"close ${ind.close:.2f} < MA50 ${ind.ma50:.2f}")

    if cfg.require_ma20_above_ma50:
        if ind.ma20 is None or ind.ma50 is None:
            return _fail("ma20_above_ma50", "insufficient data")
        if ind.ma20 <= ind.ma50:
            return _fail("ma20_above_ma50", f"MA20 ${ind.ma20:.2f} <= MA50 ${ind.ma50:.2f}")

    if cfg.require_ma50_above_ma200:
        if ind.ma50 is None or ind.ma200 is None:
            return _fail("ma50_above_ma200", "insufficient data for MA200")
        if ind.ma50 <= ind.ma200:
            return _fail("ma50_above_ma200", f"MA50 ${ind.ma50:.2f} <= MA200 ${ind.ma200:.2f}")

    return _pass()


# All filters in order — fail fast
FILTER_CHAIN = [
    filter_price,
    filter_dollar_volume,
    filter_relative_volume,
    filter_moving_averages,
]


def apply_filters(ind: IndicatorSet, cfg: ScannerConfig) -> FilterResult:
    """Run all filters; return first failure or pass."""
    for fn in FILTER_CHAIN:
        result = fn(ind, cfg)
        if not result.passed:
            return result
    return _pass()
