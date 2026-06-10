"""
robinhoodGateway — the execution service boundary.

This is the ONLY entry point for trade execution.
It enforces:
  1. Global kill switch (EXECUTION_ENABLED=false blocks everything)
  2. Mode check (READ_ONLY vs EXECUTE)
  3. Trade plan verification (every intent must reference a real plan)
  4. Approval status check
  5. Immutable audit logging at every step
  6. Structured response — never raw broker data

Nothing outside this module calls the broker directly.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.scan import ScanCandidate
from app.models.trade import TradePlan, TradeOrder
from app.services.execution.models import (
    TradeIntent, GatewayResponse, GatewayMode,
    ExecutionStatus, ApprovalStatus, OrderSide,
)
from app.services.execution.audit import (
    log_intent_received, log_gateway_blocked,
    log_intent_submitted, log_broker_response, log_simulated,
)

logger = logging.getLogger(__name__)


class ExecutionGateway:
    """
    robinhoodGateway — structured execution boundary.

    Instantiate once per request/session with an AsyncSession.
    Never share across requests.
    """

    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._mode: GatewayMode = self._resolve_mode()

    def _resolve_mode(self) -> GatewayMode:
        from app.core.config import settings
        if not settings.execution_enabled:
            return GatewayMode.READ_ONLY
        if settings.execution_mode == "EXECUTE":
            return GatewayMode.EXECUTE
        return GatewayMode.READ_ONLY

    @property
    def mode(self) -> GatewayMode:
        return self._mode

    @property
    def is_live(self) -> bool:
        return self._mode == GatewayMode.EXECUTE

    # ── Pre-flight checks ────────────────────────────────────────────────

    async def _verify_trade_plan(self, trade_plan_id: uuid.UUID) -> TradePlan | None:
        result = await self._db.execute(
            select(TradePlan).where(TradePlan.id == trade_plan_id)
        )
        return result.scalar_one_or_none()

    def _check_kill_switch(self) -> str | None:
        from app.core.config import settings
        if not settings.execution_enabled:
            return "EXECUTION_ENABLED=false — global kill switch active"
        return None

    def _check_approval(self, intent: TradeIntent) -> str | None:
        if intent.approval_status not in (ApprovalStatus.APPROVED, ApprovalStatus.AUTO_APPROVED):
            return f"ApprovalStatus is {intent.approval_status.value} — APPROVED required"
        return None

    # ── Public interface ─────────────────────────────────────────────────

    async def submit(self, intent: TradeIntent) -> GatewayResponse:
        """
        Process a trade intent through the full gateway pipeline.

        Steps:
        1. Log receipt
        2. Kill switch check
        3. Trade plan verification
        4. Approval check
        5. Mode branch (READ_ONLY → simulate | EXECUTE → broker)
        6. Persist order record
        7. Log response
        """
        # Step 1: Audit inbound
        await log_intent_received(intent, self._db)

        def _blocked(reason: str) -> GatewayResponse:
            return GatewayResponse(
                intent_id=intent.intent_id,
                trade_plan_id=intent.trade_plan_id,
                status=ExecutionStatus.BLOCKED,
                mode=self._mode,
                message=reason,
                blocked_reason=reason,
            )

        # Step 2: Kill switch
        kill = self._check_kill_switch()
        if kill:
            await log_gateway_blocked(intent, kill, self._db)
            return _blocked(kill)

        # Step 3: Trade plan must exist
        plan = await self._verify_trade_plan(intent.trade_plan_id)
        if plan is None:
            reason = f"TradePlan {intent.trade_plan_id} not found in database"
            await log_gateway_blocked(intent, reason, self._db)
            return _blocked(reason)

        if plan.status not in ("DRAFT", "ACTIVE"):
            reason = f"TradePlan status is '{plan.status}' — only DRAFT or ACTIVE plans can execute"
            await log_gateway_blocked(intent, reason, self._db)
            return _blocked(reason)

        if plan.symbol != intent.symbol:
            reason = f"Symbol mismatch: intent={intent.symbol}, plan={plan.symbol}"
            await log_gateway_blocked(intent, reason, self._db)
            return _blocked(reason)

        # Step 4: Approval check
        approval_err = self._check_approval(intent)
        if approval_err:
            await log_gateway_blocked(intent, approval_err, self._db)
            return _blocked(approval_err)

        # Step 5: Mode branch
        if self._mode == GatewayMode.READ_ONLY:
            return await self._simulate(intent, plan)
        else:
            return await self._execute(intent, plan)

    async def _simulate(self, intent: TradeIntent, plan: TradePlan) -> GatewayResponse:
        """READ_ONLY mode — validate and log, but never touch the broker."""
        await log_simulated(intent, self._db)
        response = GatewayResponse(
            intent_id=intent.intent_id,
            trade_plan_id=intent.trade_plan_id,
            status=ExecutionStatus.SIMULATED,
            mode=GatewayMode.READ_ONLY,
            message=f"READ_ONLY: {intent.side.value} {intent.symbol} simulated — no order placed",
        )
        logger.info("Gateway [READ_ONLY]: %s", response.message)
        return response

    async def _execute(self, intent: TradeIntent, plan: TradePlan) -> GatewayResponse:
        """EXECUTE mode — submit to broker and persist result."""
        from app.services.execution.robinhood_client import get_robinhood_client

        client = get_robinhood_client()
        if client is None:
            reason = "Robinhood credentials not configured (ROBINHOOD_API_KEY / ROBINHOOD_ACCOUNT_ID)"
            await log_gateway_blocked(intent, reason, self._db)
            return GatewayResponse(
                intent_id=intent.intent_id,
                trade_plan_id=intent.trade_plan_id,
                status=ExecutionStatus.BLOCKED,
                mode=self._mode,
                message=reason,
                blocked_reason=reason,
            )

        # Build and log the outbound payload BEFORE sending
        broker_payload = {
            "symbol": intent.symbol,
            "side": intent.side.value,
            "order_type": intent.order_type.value,
            "quantity": intent.quantity,
            "dollar_amount": intent.dollar_amount,
            "limit_price": intent.limit_price,
            "stop_price": intent.stop_price,
        }
        await log_intent_submitted(intent, broker_payload, self._db)

        # Submit to broker
        result = await client.submit_order(intent)

        status = ExecutionStatus.SUBMITTED if result.success else ExecutionStatus.REJECTED

        response = GatewayResponse(
            intent_id=intent.intent_id,
            trade_plan_id=intent.trade_plan_id,
            status=status,
            mode=self._mode,
            broker_order_id=result.broker_order_id,
            filled_price=result.filled_price,
            filled_quantity=result.filled_quantity,
            message=result.error_message or f"Order {status.value}: {result.broker_order_id}",
        )

        # Log broker response (with raw data — never returned to caller)
        await log_broker_response(intent, response, result.raw_response, self._db)

        # Persist TradeOrder record
        if result.success:
            order = TradeOrder(
                id=uuid.uuid4(),
                plan_id=intent.trade_plan_id,
                symbol=intent.symbol,
                order_type=intent.order_type.value,
                side=intent.side.value,
                quantity=result.filled_quantity or intent.quantity or 0,
                limit_price=intent.limit_price,
                stop_price=intent.stop_price,
                filled_price=result.filled_price,
                filled_quantity=result.filled_quantity,
                status=status.value,
                broker_order_id=result.broker_order_id,
                submitted_at=datetime.now(timezone.utc),
                raw_response=result.raw_response,
            )
            self._db.add(order)
            # Update plan status
            plan.status = "FILLED" if status == ExecutionStatus.SUBMITTED else plan.status
            await self._db.flush()

        return response

    async def get_positions(self) -> list[dict]:
        """Read-only position snapshot — no execution path."""
        from app.services.execution.robinhood_client import get_robinhood_client
        client = get_robinhood_client()
        if not client:
            return []
        return await client.get_positions()

    async def get_account(self) -> dict:
        """Read-only account info."""
        from app.services.execution.robinhood_client import get_robinhood_client
        client = get_robinhood_client()
        if not client:
            return {}
        return await client.get_account()
