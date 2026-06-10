"""
Execution gateway — public interface.

Import from here. Do NOT import gateway.py, robinhood_client.py,
or audit.py directly from outside this package.
"""
from app.services.execution.gateway import ExecutionGateway
from app.services.execution.models import (
    TradeIntent, GatewayResponse, GatewayMode,
    OrderSide, OrderType, ApprovalStatus, RiskTag, StrategyTag,
    ExecutionStatus,
)

__all__ = [
    "ExecutionGateway",
    "TradeIntent", "GatewayResponse", "GatewayMode",
    "OrderSide", "OrderType", "ApprovalStatus", "RiskTag", "StrategyTag",
    "ExecutionStatus",
]
