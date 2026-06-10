"""
Request/response schemas for scan endpoints.
"""
import uuid
from datetime import date, datetime
from pydantic import Field
from app.schemas.base import APIModel
from app.services.scanner.config import ScannerConfig


class ScanRequest(APIModel):
    """Optional body for POST /scans/run."""
    config: ScannerConfig | None = Field(None, description="Override default scanner config")
    universe: list[str] | None = Field(None, description="Override default symbol universe")


class CandidateOut(APIModel):
    id: uuid.UUID
    symbol: str
    score: float
    confidence: str
    entry: float
    stop: float
    target1: float
    rr_ratio: float
    direction: str
    technical_score: float
    technical_setup: str | None
    status: str
    run_date: date


class ScanRunOut(APIModel):
    id: uuid.UUID
    run_date: date
    status: str
    market_regime: str | None
    tickers_scanned: int
    candidates_found: int
    duration_ms: int | None
    is_mocked: bool
    created_at: datetime
    candidates: list[CandidateOut] = []
