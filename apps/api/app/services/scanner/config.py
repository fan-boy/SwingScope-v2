"""
All scanner thresholds in one place.
Override via env vars or per-user AppSettings.
"""
from pydantic import BaseModel, Field


class ScannerConfig(BaseModel):
    # ── Universe filters ───────────────────────────────────────────
    min_price: float = Field(5.0, description="Minimum stock price")
    max_price: float = Field(10_000.0, description="Maximum stock price")
    min_avg_dollar_volume: float = Field(
        10_000_000.0, description="Minimum average daily dollar volume (20-day)"
    )
    min_relative_volume: float = Field(
        0.5, description="Minimum relative volume (today vs 20-day avg)"
    )

    # ── Moving average rules ───────────────────────────────────────
    require_above_ma20: bool = Field(True, description="Price must be above 20-day MA")
    require_above_ma50: bool = Field(False, description="Price must be above 50-day MA")
    require_ma20_above_ma50: bool = Field(False, description="MA20 > MA50 (uptrend)")
    require_ma50_above_ma200: bool = Field(False, description="MA50 > MA200 (optional longer trend)")
    bars_needed: int = Field(210, description="Bars to fetch for indicator calculation")

    # ── Breakout proximity ─────────────────────────────────────────
    high_window: int = Field(20, description="Days to look back for recent high")
    breakout_pct: float = Field(
        0.03, description="Price within X% of recent high = breakout zone"
    )

    # ── Scoring weights (must sum to 100) ─────────────────────────
    weight_trend: float = Field(40.0, description="Trend score weight")
    weight_volume: float = Field(30.0, description="Volume score weight")
    weight_breakout: float = Field(30.0, description="Breakout proximity weight")

    # ── Output filters ─────────────────────────────────────────────
    min_final_score: float = Field(20.0, description="Minimum score to include in results")
    max_candidates: int = Field(50, description="Maximum candidates to return")

    class Config:
        frozen = True


# Default config used by the scanner service
DEFAULT_CONFIG = ScannerConfig()
