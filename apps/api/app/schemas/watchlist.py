import uuid
from datetime import datetime
from app.schemas.base import APIModel


class WatchlistItemCreate(APIModel):
    symbol: str
    notes: str | None = None
    alert_price: float | None = None


class WatchlistItemRead(APIModel):
    id: uuid.UUID
    symbol: str
    notes: str | None
    alert_price: float | None
    created_at: datetime


class WatchlistCreate(APIModel):
    name: str
    description: str | None = None
    is_default: bool = False


class WatchlistRead(APIModel):
    id: uuid.UUID
    name: str
    description: str | None
    is_default: bool
    items: list[WatchlistItemRead] = []
    created_at: datetime
