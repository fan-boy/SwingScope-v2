import uuid
from datetime import datetime
from app.schemas.base import APIModel


class TradePlanCreate(APIModel):
    symbol: str
    direction: str = "LONG"
    entry: float
    stop: float
    target1: float
    target2: float | None = None
    quantity: float | None = None
    rr_ratio: float | None = None
    candidate_id: uuid.UUID | None = None
    notes: str | None = None


class TradePlanRead(APIModel):
    id: uuid.UUID
    symbol: str
    direction: str
    status: str
    entry: float
    stop: float
    target1: float
    target2: float | None
    quantity: float | None
    rr_ratio: float | None
    notes: str | None
    approved_at: datetime | None
    created_at: datetime


class TradeOrderRead(APIModel):
    id: uuid.UUID
    plan_id: uuid.UUID
    symbol: str
    order_type: str
    side: str
    quantity: float
    limit_price: float | None
    stop_price: float | None
    filled_price: float | None
    filled_quantity: float | None
    status: str
    broker_order_id: str | None
    submitted_at: datetime | None
    filled_at: datetime | None
    created_at: datetime
