"""
Unit tests for the execution gateway.

Tests cover:
- Input validation
- Kill switch
- Read-only mode simulation
- Trade plan verification
- Approval status enforcement
- Symbol mismatch detection
"""
import uuid
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import date

import pytest

from app.services.execution.models import (
    TradeIntent, OrderSide, OrderType, ApprovalStatus,
    RiskTag, StrategyTag, ExecutionStatus, GatewayMode,
)
from app.services.execution.gateway import ExecutionGateway


# ── Fixtures ──────────────────────────────────────────────────────────────

def make_intent(**overrides) -> TradeIntent:
    defaults = dict(
        trade_plan_id=uuid.uuid4(),
        symbol="AAPL",
        side=OrderSide.BUY,
        order_type=OrderType.LIMIT,
        quantity=10.0,
        limit_price=190.00,
        strategy_tag=StrategyTag.SWING_ENTRY,
        risk_tag=RiskTag.MEDIUM,
        approval_status=ApprovalStatus.APPROVED,
    )
    defaults.update(overrides)
    return TradeIntent(**defaults)


def make_mock_plan(symbol="AAPL", status="ACTIVE", plan_id=None):
    plan = MagicMock()
    plan.id = plan_id or uuid.uuid4()
    plan.symbol = symbol
    plan.status = status
    return plan


def make_gateway(execution_enabled=False, execution_mode="READ_ONLY", plan=None) -> ExecutionGateway:
    """Create a gateway with a mocked DB session and settings."""
    db = AsyncMock()
    result_mock = MagicMock()
    result_mock.scalar_one_or_none.return_value = plan
    db.execute = AsyncMock(return_value=result_mock)
    db.add = MagicMock()
    db.flush = AsyncMock()

    gw = ExecutionGateway.__new__(ExecutionGateway)
    gw._db = db
    gw._mode = GatewayMode.EXECUTE if (execution_enabled and execution_mode == "EXECUTE") else GatewayMode.READ_ONLY

    # Patch _check_kill_switch to reflect execution_enabled
    if not execution_enabled:
        gw._check_kill_switch = lambda: "EXECUTION_ENABLED=false — global kill switch active"
    else:
        gw._check_kill_switch = lambda: None

    return gw


# ── TradeIntent validation ─────────────────────────────────────────────────

class TestTradeIntentValidation:
    def test_valid_intent(self):
        intent = make_intent()
        assert intent.symbol == "AAPL"
        assert intent.side == OrderSide.BUY

    def test_symbol_uppercased(self):
        intent = make_intent(symbol="aapl")
        assert intent.symbol == "AAPL"

    def test_symbol_invalid_chars_rejected(self):
        with pytest.raises(ValueError, match="Symbol must be"):
            make_intent(symbol="AA.PL")

    def test_symbol_too_long_rejected(self):
        with pytest.raises(ValueError):
            make_intent(symbol="TOOLONG")

    def test_requires_qty_or_dollar(self):
        with pytest.raises(ValueError, match="quantity or dollar_amount"):
            TradeIntent(
                trade_plan_id=uuid.uuid4(),
                symbol="AAPL", side=OrderSide.BUY,
                order_type=OrderType.MARKET,
                strategy_tag=StrategyTag.SWING_ENTRY,
                risk_tag=RiskTag.LOW,
                approval_status=ApprovalStatus.APPROVED,
                # neither quantity nor dollar_amount
            )

    def test_rejects_both_qty_and_dollar(self):
        with pytest.raises(ValueError, match="not both"):
            make_intent(quantity=10, dollar_amount=500)

    def test_limit_order_requires_limit_price(self):
        with pytest.raises(ValueError, match="limit_price required"):
            make_intent(order_type=OrderType.LIMIT, limit_price=None)

    def test_stop_order_requires_stop_price(self):
        with pytest.raises(ValueError, match="stop_price required"):
            make_intent(order_type=OrderType.STOP, stop_price=None, limit_price=None)

    def test_stop_limit_requires_both_prices(self):
        with pytest.raises(ValueError):
            make_intent(order_type=OrderType.STOP_LIMIT, stop_price=185.0, limit_price=None)

    def test_market_order_no_price_needed(self):
        intent = make_intent(order_type=OrderType.MARKET, limit_price=None)
        assert intent.order_type == OrderType.MARKET

    def test_dollar_amount_accepted(self):
        intent = make_intent(quantity=None, dollar_amount=1000.0, limit_price=None, order_type=OrderType.MARKET)
        assert intent.dollar_amount == 1000.0
        assert intent.quantity is None


# ── Gateway kill switch ────────────────────────────────────────────────────

class TestKillSwitch:
    def test_blocked_when_execution_disabled(self):
        plan = make_mock_plan()
        gw = make_gateway(execution_enabled=False, plan=plan)
        intent = make_intent(trade_plan_id=plan.id)

        with patch.object(gw, "_check_kill_switch", return_value="EXECUTION_ENABLED=false — global kill switch active"):
            with patch.object(gw, "_verify_trade_plan", return_value=plan):
                response = asyncio.run(gw.submit(intent))

        assert response.status == ExecutionStatus.BLOCKED
        assert "kill switch" in response.blocked_reason.lower()

    def test_mode_is_read_only_when_disabled(self):
        with patch("app.core.config.settings") as s:
            s.execution_enabled = False
            s.execution_mode = "READ_ONLY"
            db = AsyncMock()
            db.add = MagicMock()
            db.flush = AsyncMock()
            gw = ExecutionGateway(db=db)
        assert gw.mode == GatewayMode.READ_ONLY
        assert not gw.is_live


# ── Read-only simulation ───────────────────────────────────────────────────

class TestReadOnlyMode:
    def _make_read_only_gateway(self, plan):
        return make_gateway(execution_enabled=True, execution_mode="READ_ONLY", plan=plan)

    def test_simulated_status_in_read_only(self):
        plan = make_mock_plan()
        gw = self._make_read_only_gateway(plan)
        intent = make_intent(trade_plan_id=plan.id)
        response = asyncio.run(gw.submit(intent))
        assert response.status == ExecutionStatus.SIMULATED
        assert response.mode == GatewayMode.READ_ONLY
        assert response.broker_order_id is None

    def test_no_broker_call_in_read_only(self):
        plan = make_mock_plan()
        gw = self._make_read_only_gateway(plan)
        intent = make_intent(trade_plan_id=plan.id)

        with patch("app.services.execution.robinhood_client.get_robinhood_client") as mock_client:
            asyncio.run(gw.submit(intent))
            mock_client.assert_not_called()


# ── Trade plan verification ────────────────────────────────────────────────

class TestTradePlanVerification:
    def _gateway_with_plan(self, plan):
        return make_gateway(execution_enabled=True, execution_mode="READ_ONLY", plan=plan)

    def test_blocked_when_plan_not_found(self):
        gw = self._gateway_with_plan(None)
        intent = make_intent()
        response = asyncio.run(gw.submit(intent))
        assert response.status == ExecutionStatus.BLOCKED
        assert "not found" in response.blocked_reason

    def test_blocked_on_symbol_mismatch(self):
        plan = make_mock_plan(symbol="NVDA", status="ACTIVE")
        gw = self._gateway_with_plan(plan)
        intent = make_intent(symbol="AAPL", trade_plan_id=plan.id)
        response = asyncio.run(gw.submit(intent))
        assert response.status == ExecutionStatus.BLOCKED
        assert "mismatch" in response.blocked_reason.lower()

    def test_blocked_on_filled_plan(self):
        plan = make_mock_plan(symbol="AAPL", status="FILLED")
        gw = self._gateway_with_plan(plan)
        intent = make_intent(symbol="AAPL", trade_plan_id=plan.id)
        response = asyncio.run(gw.submit(intent))
        assert response.status == ExecutionStatus.BLOCKED
        assert "FILLED" in response.blocked_reason

    def test_passes_with_active_plan(self):
        plan = make_mock_plan(symbol="AAPL", status="ACTIVE")
        gw = self._gateway_with_plan(plan)
        intent = make_intent(symbol="AAPL", trade_plan_id=plan.id)
        response = asyncio.run(gw.submit(intent))
        assert response.status == ExecutionStatus.SIMULATED   # read-only mode


# ── Approval enforcement ───────────────────────────────────────────────────

class TestApprovalEnforcement:
    def test_non_approved_status_blocked(self):
        # ApprovalStatus only has APPROVED and AUTO_APPROVED — anything else is invalid
        # This tests the validator at model level
        with pytest.raises(Exception):
            TradeIntent(
                trade_plan_id=uuid.uuid4(),
                symbol="AAPL", side=OrderSide.BUY,
                order_type=OrderType.MARKET, quantity=10,
                strategy_tag=StrategyTag.SWING_ENTRY,
                risk_tag=RiskTag.LOW,
                approval_status="PENDING",  # not a valid enum value
            )
