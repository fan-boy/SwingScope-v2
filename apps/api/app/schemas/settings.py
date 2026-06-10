import uuid
from datetime import datetime
from app.schemas.base import APIModel


class AppSettingsRead(APIModel):
    id: uuid.UUID
    min_score: float
    min_rr: float
    max_candidates: int
    mock_mode: bool
    notify_on_scan: bool
    notify_on_fill: bool
    telegram_chat_id: str | None
    extra: dict | None
    updated_at: datetime


class AppSettingsUpdate(APIModel):
    min_score: float | None = None
    min_rr: float | None = None
    max_candidates: int | None = None
    mock_mode: bool | None = None
    notify_on_scan: bool | None = None
    notify_on_fill: bool | None = None
    telegram_chat_id: str | None = None
    extra: dict | None = None
