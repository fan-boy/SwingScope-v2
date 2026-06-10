import uuid
from datetime import datetime
from sqlalchemy import String, Text, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.db.base import Base


class ExecutionLog(Base):
    """Append-only audit log for all significant system events."""
    __tablename__ = "execution_logs"
    __table_args__ = (
        Index("ix_execution_logs_entity", "entity_type", "entity_id"),
        Index("ix_execution_logs_level", "level"),
        Index("ix_execution_logs_created_at", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    level: Mapped[str] = mapped_column(String(10), nullable=False, default="INFO", index=True)
    # INFO | WARN | ERROR
    event: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)

    entity_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    # scan_run | trade_plan | trade_order | position
    entity_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)

    meta: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False, index=True)
