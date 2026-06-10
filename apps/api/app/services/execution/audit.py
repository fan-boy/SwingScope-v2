"""
Immutable execution audit log.

Every inbound intent and outbound response is written here.
Rows are never updated — only inserted.
Use execution_logs table (entity_type = "execution_gateway").
"""
import uuid
import logging
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.log import ExecutionLog
from app.services.execution.models import TradeIntent, GatewayResponse, GatewayMode

logger = logging.getLogger(__name__)


async def log_intent_received(intent: TradeIntent, db: AsyncSession) -> None:
    """Log an incoming trade intent before any processing."""
    db.add(ExecutionLog(
        id=uuid.uuid4(),
        level="INFO",
        event="gateway.intent_received",
        message=f"Trade intent received: {intent.side.value} {intent.symbol} via {intent.strategy_tag.value}",
        entity_type="execution_gateway",
        entity_id=intent.trade_plan_id,
        meta={
            "intent_id": str(intent.intent_id),
            "trade_plan_id": str(intent.trade_plan_id),
            "symbol": intent.symbol,
            "side": intent.side.value,
            "order_type": intent.order_type.value,
            "quantity": intent.quantity,
            "dollar_amount": intent.dollar_amount,
            "limit_price": intent.limit_price,
            "stop_price": intent.stop_price,
            "strategy_tag": intent.strategy_tag.value,
            "risk_tag": intent.risk_tag.value,
            "approval_status": intent.approval_status.value,
            # note is intentionally included — it's already stored only in audit
        },
        created_at=datetime.now(timezone.utc),
    ))
    await db.flush()


async def log_gateway_blocked(
    intent: TradeIntent,
    reason: str,
    db: AsyncSession,
) -> None:
    db.add(ExecutionLog(
        id=uuid.uuid4(),
        level="WARN",
        event="gateway.blocked",
        message=f"Execution blocked — {reason}",
        entity_type="execution_gateway",
        entity_id=intent.trade_plan_id,
        meta={
            "intent_id": str(intent.intent_id),
            "symbol": intent.symbol,
            "blocked_reason": reason,
        },
        created_at=datetime.now(timezone.utc),
    ))
    await db.flush()


async def log_intent_submitted(
    intent: TradeIntent,
    broker_payload: dict,
    db: AsyncSession,
) -> None:
    """Log the exact payload being sent to the broker."""
    db.add(ExecutionLog(
        id=uuid.uuid4(),
        level="INFO",
        event="gateway.submitted",
        message=f"Order submitted to broker: {intent.side.value} {intent.quantity or intent.dollar_amount} {intent.symbol}",
        entity_type="execution_gateway",
        entity_id=intent.trade_plan_id,
        meta={
            "intent_id": str(intent.intent_id),
            "broker_payload": broker_payload,  # exact outbound payload
        },
        created_at=datetime.now(timezone.utc),
    ))
    await db.flush()


async def log_broker_response(
    intent: TradeIntent,
    response: GatewayResponse,
    raw_response: dict | None,
    db: AsyncSession,
) -> None:
    level = "ERROR" if response.status.value in ("REJECTED",) else "INFO"
    db.add(ExecutionLog(
        id=uuid.uuid4(),
        level=level,
        event=f"gateway.{response.status.value.lower()}",
        message=response.message,
        entity_type="execution_gateway",
        entity_id=intent.trade_plan_id,
        meta={
            "intent_id": str(intent.intent_id),
            "status": response.status.value,
            "broker_order_id": response.broker_order_id,
            "filled_price": response.filled_price,
            "filled_quantity": response.filled_quantity,
            "raw_broker_response": raw_response,  # full broker payload archived
        },
        created_at=datetime.now(timezone.utc),
    ))
    await db.flush()


async def log_simulated(intent: TradeIntent, db: AsyncSession) -> None:
    """Log a read-only mode dry run — no broker call made."""
    db.add(ExecutionLog(
        id=uuid.uuid4(),
        level="INFO",
        event="gateway.simulated",
        message=f"READ_ONLY mode — {intent.side.value} {intent.symbol} simulated, no order sent",
        entity_type="execution_gateway",
        entity_id=intent.trade_plan_id,
        meta={
            "intent_id": str(intent.intent_id),
            "symbol": intent.symbol,
            "side": intent.side.value,
            "quantity": intent.quantity,
            "dollar_amount": intent.dollar_amount,
            "order_type": intent.order_type.value,
        },
        created_at=datetime.now(timezone.utc),
    ))
    await db.flush()
