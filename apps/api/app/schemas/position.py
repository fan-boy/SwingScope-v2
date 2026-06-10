import uuid
from datetime import date, datetime
from app.schemas.base import APIModel


class PositionCreate(APIModel):
    symbol: str
    direction: str = "LONG"
    quantity: float
    avg_entry_price: float
    stop_price: float | None = None
    target_price: float | None = None
    opened_at: date


class PositionRead(APIModel):
    id: uuid.UUID
    symbol: str
    status: str
    direction: str
    quantity: float
    avg_entry_price: float
    stop_price: float | None
    target_price: float | None
    avg_exit_price: float | None
    realized_pnl: float | None
    opened_at: date
    closed_at: date | None
    notes: str | None
    created_at: datetime
