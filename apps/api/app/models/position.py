import uuid
from datetime import date, datetime
from sqlalchemy import String, ForeignKey, Date, Text, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base, TimestampMixin


class Position(Base, TimestampMixin):
    """An open or closed position."""
    __tablename__ = "positions"
    __table_args__ = (
        Index("ix_positions_symbol_status", "symbol", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    symbol: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(10), default="OPEN", nullable=False, index=True)
    # OPEN | CLOSED

    direction: Mapped[str] = mapped_column(String(5), default="LONG", nullable=False)
    quantity: Mapped[float] = mapped_column(nullable=False)
    avg_entry_price: Mapped[float] = mapped_column(nullable=False)
    stop_price: Mapped[float | None] = mapped_column(nullable=True)
    target_price: Mapped[float | None] = mapped_column(nullable=True)

    # Close info
    avg_exit_price: Mapped[float | None] = mapped_column(nullable=True)
    realized_pnl: Mapped[float | None] = mapped_column(nullable=True)
    opened_at: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    closed_at: Mapped[date | None] = mapped_column(Date, nullable=True)

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    orders: Mapped[list["TradeOrder"]] = relationship(back_populates="position", cascade="all, delete-orphan")
