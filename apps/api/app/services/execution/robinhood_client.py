"""
Robinhood MCP adapter.

This is the ONLY place in the codebase that speaks to Robinhood.
It is never imported by routes, frontend, or anything outside the gateway.
The gateway calls this; nothing else does.

MCP (Market Connectivity Protocol) is Robinhood's broker API surface.
We wrap it in a minimal typed interface and never expose raw controls.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

from app.services.execution.models import TradeIntent, OrderType, OrderSide

logger = logging.getLogger(__name__)


@dataclass
class BrokerOrderResult:
    success: bool
    broker_order_id: str | None
    filled_price: float | None
    filled_quantity: float | None
    raw_response: dict
    error_message: str | None = None


def _build_payload(intent: TradeIntent, resolved_qty: float) -> dict:
    """
    Build the minimal broker payload from a validated intent.
    Only whitelisted fields are included — no pass-through of arbitrary data.
    """
    payload: dict = {
        "symbol": intent.symbol,
        "side": intent.side.value.lower(),       # "buy" / "sell"
        "type": intent.order_type.value.lower(),  # "market" / "limit" etc.
        "quantity": resolved_qty,
        "time_in_force": "day",
    }
    if intent.limit_price is not None:
        payload["limit_price"] = str(round(intent.limit_price, 2))
    if intent.stop_price is not None:
        payload["stop_price"] = str(round(intent.stop_price, 2))

    # Strategy tag is stored in our own audit log — never forwarded to broker
    return payload


class RobinhoodMCPClient:
    """
    Typed wrapper around Robinhood's MCP surface.

    Acceptance criteria:
    - Only `submit_order()` places orders — nothing else
    - Input is always a validated TradeIntent
    - Output is always a BrokerOrderResult
    - Raw MCP response is captured in full for the audit log
    """

    def __init__(self, api_key: str, account_id: str) -> None:
        self._api_key = api_key
        self._account_id = account_id
        # TODO: initialise the actual Robinhood MCP SDK client here
        # e.g. self._client = RobinhoodClient(api_key=api_key)
        logger.info("RobinhoodMCPClient initialised for account %s", account_id[:4] + "****")

    async def get_quote(self, symbol: str) -> float | None:
        """
        Fetch latest ask price for dollar→qty conversion.
        Read-only — no side effects.
        """
        # TODO: self._client.get_quote(symbol)
        logger.debug("get_quote called for %s (stub)", symbol)
        return None

    async def submit_order(self, intent: TradeIntent) -> BrokerOrderResult:
        """
        Submit a validated trade intent to Robinhood.

        This is the single execution choke point. If this method
        is not called, nothing reaches the broker.
        """
        # Resolve dollar_amount → quantity if needed
        resolved_qty = intent.quantity
        if resolved_qty is None and intent.dollar_amount is not None:
            price = await self.get_quote(intent.symbol)
            if price and price > 0:
                resolved_qty = round(intent.dollar_amount / price, 6)
            else:
                return BrokerOrderResult(
                    success=False,
                    broker_order_id=None,
                    filled_price=None,
                    filled_quantity=None,
                    raw_response={"error": "could not resolve quote for dollar_amount conversion"},
                    error_message="Quote unavailable — cannot convert dollar_amount to quantity",
                )

        payload = _build_payload(intent, resolved_qty)
        logger.info(
            "Submitting order to Robinhood: %s %s %s @ %s",
            payload["side"], payload["quantity"], payload["symbol"], payload.get("limit_price", "MARKET"),
        )

        try:
            # TODO: replace stub with actual MCP call
            # raw = await self._client.orders.create(**payload)
            raw = {"id": "stub-order-id", "state": "confirmed", "payload": payload}

            return BrokerOrderResult(
                success=True,
                broker_order_id=raw.get("id"),
                filled_price=raw.get("average_price"),
                filled_quantity=resolved_qty,
                raw_response=raw,
            )
        except Exception as e:
            logger.error("Robinhood order submission failed: %s", e)
            return BrokerOrderResult(
                success=False,
                broker_order_id=None,
                filled_price=None,
                filled_quantity=None,
                raw_response={"error": str(e)},
                error_message=str(e),
            )

    async def get_positions(self) -> list[dict]:
        """Read-only position snapshot."""
        # TODO: self._client.positions.list()
        return []

    async def get_account(self) -> dict:
        """Read-only account info."""
        # TODO: self._client.account.get()
        return {}


def get_robinhood_client() -> RobinhoodMCPClient | None:
    """Return configured client or None if credentials missing."""
    from app.core.config import settings
    if not settings.robinhood_api_key or not settings.robinhood_account_id:
        return None
    return RobinhoodMCPClient(
        api_key=settings.robinhood_api_key,
        account_id=settings.robinhood_account_id,
    )
