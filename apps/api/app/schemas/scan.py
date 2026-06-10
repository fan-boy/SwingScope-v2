import uuid
from datetime import date, datetime
from app.schemas.base import APIModel


class ScanCandidateSummary(APIModel):
    """Lightweight version for table views."""
    id: uuid.UUID
    symbol: str
    score: float
    confidence: str
    entry: float
    stop: float
    target1: float
    rr_ratio: float
    direction: str
    status: str
    generated_by_llm: bool


class ScanCandidateRead(APIModel):
    id: uuid.UUID
    scan_run_id: uuid.UUID
    run_date: date
    symbol: str
    score: float
    technical_score: float
    sentiment_score: float
    regime_modifier: float
    squeeze_score: float | None
    confidence: str
    entry: float
    stop: float
    target1: float
    target2: float | None
    rr_ratio: float
    atr14: float | None
    direction: str
    strategy: str | None
    regime: str | None
    thesis: str | None
    technical_setup: str | None
    catalyst_summary: str | None
    invalidation: str | None
    generated_by_llm: bool
    status: str
    created_at: datetime


class ScanRunRead(APIModel):
    id: uuid.UUID
    run_date: date
    status: str
    market_regime: str | None
    tickers_scanned: int
    candidates_found: int
    duration_ms: int | None
    is_mocked: bool
    created_at: datetime
    candidates: list[ScanCandidateSummary] = []
