"""
Execution gateway models.

All trade intents must be explicitly typed — no free-form strings
that could be forwarded to a broker without validation.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Annotated

from pydantic import BaseModel, Field, field_validator, model_validator


# ── Enumerations — exhaustive, no "OTHER" catch-alls ─────────────────────

class OrderSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderType(str, Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    STOP_LIMIT = "STOP_LIMIT"


class ApprovalStatus(str, Enum):
    APPROVED = "APPROVED"       # human explicitly approved
    AUTO_APPROVED = "AUTO_APPROVED"   # within pre-set risk limits (future)


class RiskTag(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class StrategyTag(str, Enum):
    SWING_ENTRY = "SWING_ENTRY"
    SWING_EXIT = "SWING_EXIT"
    STOP_LOSS = "STOP_LOSS"
    TAKE_PROFIT_1 = "TAKE_PROFIT_1"
    TAKE_PROFIT_2 = "TAKE_PROFIT_2"
    MANUAL = "MANUAL"


class GatewayMode(str, Enum):
    READ_ONLY = "READ_ONLY"     # safe default — never submits
    EXECUTE = "EXECUTE"         # live submission — requires feature flag


class ExecutionStatus(str, Enum):
    ACCEPTED = "ACCEPTED"       # passed validation
    SUBMITTED = "SUBMITTED"     # sent to broker
    FILLED = "FILLED"
    PARTIAL = "PARTIAL"
    REJECTED = "REJECTED"       # broker refused
    BLOCKED = "BLOCKED"         # gateway refused before broker call
    SIMULATED = "SIMULATED"     # read-only mode dry run


# ── Trade intent ─────────────────────────────────────────────────────────

TICKER_RE = __import__("re").compile(r"^[A-Z]{1,5}$")


class TradeIntent(BaseModel):
    """
    Structured trade intent — the ONLY input this gateway accepts.
    No free-form fields. All values are validated before the gateway
    forwards anything to a broker.
    """

    # Identity
    intent_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    trade_plan_id: uuid.UUID = Field(..., description="Must reference an existing TradePlan record")

    # Symbol
    symbol: str = Field(..., min_length=1, max_length=5)

    # Order parameters
    side: OrderSide
    order_type: OrderType
    quantity: float | None = Field(None, gt=0, description="Share quantity")
    dollar_amount: float | None = Field(None, gt=0, description="Dollar-notional (converted to qty at execution)")
    limit_price: float | None = Field(None, gt=0)
    stop_price: float | None = Field(None, gt=0)

    # Context
    strategy_tag: StrategyTag
    risk_tag: RiskTag
    approval_status: ApprovalStatus

    # Optional override note — stored in audit log only, never forwarded
    note: str | None = Field(None, max_length=300)

    @field_validator("symbol")
    @classmethod
    def validate_symbol(cls, v: str) -> str:
        v = v.upper().strip()
        if not TICKER_RE.match(v):
            raise ValueError("Symbol must be 1-5 uppercase letters")
        return v

    @model_validator(mode="after")
    def validate_qty_or_dollar(self) -> "TradeIntent":
        if self.quantity is None and self.dollar_amount is None:
            raise ValueError("Provide either quantity or dollar_amount")
        if self.quantity is not None and self.dollar_amount is not None:
            raise ValueError("Provide quantity OR dollar_amount, not both")
        return self

    @model_validator(mode="after")
    def validate_prices(self) -> "TradeIntent":
        if self.order_type == OrderType.LIMIT and self.limit_price is None:
            raise ValueError("limit_price required for LIMIT orders")
        if self.order_type == OrderType.STOP and self.stop_price is None:
            raise ValueError("stop_price required for STOP orders")
        if self.order_type == OrderType.STOP_LIMIT:
            if self.stop_price is None or self.limit_price is None:
                raise ValueError("stop_price and limit_price both required for STOP_LIMIT")
        return self


# ── Gateway response ──────────────────────────────────────────────────────

class GatewayResponse(BaseModel):
    intent_id: uuid.UUID
    trade_plan_id: uuid.UUID
    status: ExecutionStatus
    mode: GatewayMode
    broker_order_id: str | None = None
    filled_price: float | None = None
    filled_quantity: float | None = None
    message: str
    blocked_reason: str | None = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Raw broker response — stored in audit log, never returned to frontend
    _raw_broker_response: dict | None = None
