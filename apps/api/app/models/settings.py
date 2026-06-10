import uuid
from sqlalchemy import String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.db.base import Base, TimestampMixin


class AppSettings(Base, TimestampMixin):
    """Per-user configuration store."""
    __tablename__ = "app_settings"
    __table_args__ = (UniqueConstraint("user_id", name="uq_app_settings_user"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)

    # Scanner settings
    min_score: Mapped[float] = mapped_column(default=55.0, nullable=False)
    min_rr: Mapped[float] = mapped_column(default=2.0, nullable=False)
    max_candidates: Mapped[int] = mapped_column(default=10, nullable=False)
    mock_mode: Mapped[bool] = mapped_column(default=False, nullable=False)

    # Notification settings
    notify_on_scan: Mapped[bool] = mapped_column(default=True, nullable=False)
    notify_on_fill: Mapped[bool] = mapped_column(default=True, nullable=False)
    telegram_chat_id: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Arbitrary key-value overrides
    extra: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    user: Mapped["User"] = relationship(back_populates="app_settings")
