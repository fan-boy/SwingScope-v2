import uuid
from datetime import datetime
from sqlalchemy import String, ForeignKey, Text, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.db.base import Base, TimestampMixin


class TradePlan(Base, TimestampMixin):
    """Human-approved plan derived from a scan candidate."""
    __tablename__ = "trade_plans"
    __table_args__ = (
        Index("ix_trade_plans_status", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    candidate_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("scan_candidates.id", ondelete="SET NULL"), nullable=True, index=True)

    symbol: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    direction: Mapped[str] = mapped_column(String(5), default="LONG", nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="DRAFT", nullable=False)
    # DRAFT | ACTIVE | FILLED | CANCELLED | EXPIRED

    entry: Mapped[float] = mapped_column(nullable=False)
    stop: Mapped[float] = mapped_column(nullable=False)
    target1: Mapped[float] = mapped_column(nullable=False)
    target2: Mapped[float | None] = mapped_column(nullable=True)
    quantity: Mapped[float | None] = mapped_column(nullable=True)
    rr_ratio: Mapped[float | None] = mapped_column(nullable=True)

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(nullable=True)

    user: Mapped["User"] = relationship(back_populates="trade_plans")
    candidate: Mapped["ScanCandidate | None"] = relationship(back_populates="trade_plan")
    orders: Mapped[list["TradeOrder"]] = relationship(back_populates="plan", cascade="all, delete-orphan")


class TradeOrder(Base, TimestampMixin):
    """An individual order (entry, stop, target) within a trade plan."""
    __tablename__ = "trade_orders"
    __table_args__ = (
        Index("ix_trade_orders_plan_id", "plan_id"),
        Index("ix_trade_orders_status", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plan_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("trade_plans.id", ondelete="CASCADE"), nullable=False, index=True)
    position_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("positions.id", ondelete="SET NULL"), nullable=True)

    symbol: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    order_type: Mapped[str] = mapped_column(String(20), nullable=False)
    # ENTRY | STOP | TARGET1 | TARGET2 | MARKET
    side: Mapped[str] = mapped_column(String(5), nullable=False)
    # BUY | SELL

    quantity: Mapped[float] = mapped_column(nullable=False)
    limit_price: Mapped[float | None] = mapped_column(nullable=True)
    stop_price: Mapped[float | None] = mapped_column(nullable=True)
    filled_price: Mapped[float | None] = mapped_column(nullable=True)
    filled_quantity: Mapped[float | None] = mapped_column(nullable=True)

    status: Mapped[str] = mapped_column(String(20), default="PENDING", nullable=False, index=True)
    # PENDING | SUBMITTED | PARTIAL | FILLED | CANCELLED | REJECTED

    broker_order_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    submitted_at: Mapped[datetime | None] = mapped_column(nullable=True)
    filled_at: Mapped[datetime | None] = mapped_column(nullable=True)
    raw_response: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    plan: Mapped["TradePlan"] = relationship(back_populates="orders")
    position: Mapped["Position | None"] = relationship(back_populates="orders")
