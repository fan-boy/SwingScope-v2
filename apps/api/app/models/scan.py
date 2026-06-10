import uuid
from datetime import date, datetime
from sqlalchemy import String, ForeignKey, Date, Integer, Text, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.db.base import Base, TimestampMixin


class ScanRun(Base, TimestampMixin):
    """One execution of the nightly scanner."""
    __tablename__ = "scan_runs"
    __table_args__ = (
        Index("ix_scan_runs_run_date", "run_date"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="RUNNING")
    # RUNNING | COMPLETED | FAILED
    market_regime: Mapped[str | None] = mapped_column(String(20), nullable=True)
    # BULLISH | NEUTRAL | RISK_OFF
    tickers_scanned: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    candidates_found: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_mocked: Mapped[bool] = mapped_column(default=False, nullable=False)
    meta: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    candidates: Mapped[list["ScanCandidate"]] = relationship(
        back_populates="scan_run",
        cascade="all, delete-orphan",
        order_by="ScanCandidate.score.desc()",
    )


class ScanCandidate(Base, TimestampMixin):
    """A scored trade candidate from a scan run."""
    __tablename__ = "scan_candidates"
    __table_args__ = (
        Index("ix_scan_candidates_run_symbol", "scan_run_id", "symbol"),
        Index("ix_scan_candidates_symbol_date", "symbol", "run_date"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scan_run_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("scan_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    run_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    symbol: Mapped[str] = mapped_column(String(10), nullable=False, index=True)

    # Scores
    score: Mapped[float] = mapped_column(nullable=False, index=True)
    technical_score: Mapped[float] = mapped_column(default=0, nullable=False)
    sentiment_score: Mapped[float] = mapped_column(default=0, nullable=False)
    regime_modifier: Mapped[float] = mapped_column(default=0, nullable=False)
    squeeze_score: Mapped[float | None] = mapped_column(nullable=True)
    confidence: Mapped[str] = mapped_column(String(10), nullable=False)  # HIGH | MEDIUM | LOW

    # Levels
    entry: Mapped[float] = mapped_column(nullable=False)
    stop: Mapped[float] = mapped_column(nullable=False)
    target1: Mapped[float] = mapped_column(nullable=False)
    target2: Mapped[float | None] = mapped_column(nullable=True)
    rr_ratio: Mapped[float] = mapped_column(nullable=False)
    atr14: Mapped[float | None] = mapped_column(nullable=True)

    # Context
    direction: Mapped[str] = mapped_column(String(5), default="LONG", nullable=False)  # LONG | SHORT
    strategy: Mapped[str | None] = mapped_column(String(50), nullable=True)
    regime: Mapped[str | None] = mapped_column(String(20), nullable=True)
    thesis: Mapped[str | None] = mapped_column(Text, nullable=True)
    technical_setup: Mapped[str | None] = mapped_column(Text, nullable=True)
    catalyst_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    invalidation: Mapped[str | None] = mapped_column(Text, nullable=True)
    generated_by_llm: Mapped[bool] = mapped_column(default=False, nullable=False)

    status: Mapped[str] = mapped_column(String(20), default="NEW", nullable=False, index=True)
    # NEW | APPROVED | REJECTED | EXECUTED | EXPIRED

    scan_run: Mapped["ScanRun"] = relationship(back_populates="candidates")
    trade_plan: Mapped["TradePlan | None"] = relationship(back_populates="candidate", uselist=False)
