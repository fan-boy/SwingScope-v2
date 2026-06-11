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
    # ─── Risk Controls ───────────────────────────────────────
    kill_switch_active: bool
    max_risk_per_trade_pct: float
    max_daily_loss_pct: float
    max_concurrent_positions: int
    max_new_positions_per_day: int
    block_trades_near_earnings: bool
    account_size_usd: float


class AppSettingsUpdate(APIModel):
    min_score: float | None = None
    min_rr: float | None = None
    max_candidates: int | None = None
    mock_mode: bool | None = None
    notify_on_scan: bool | None = None
    notify_on_fill: bool | None = None
    telegram_chat_id: str | None = None
    extra: dict | None = None
    # ─── Risk Controls ───────────────────────────────────────
    kill_switch_active: bool | None = None
    max_risk_per_trade_pct: float | None = None
    max_daily_loss_pct: float | None = None
    max_concurrent_positions: int | None = None
    max_new_positions_per_day: int | None = None
    block_trades_near_earnings: bool | None = None
    account_size_usd: float | None = None
