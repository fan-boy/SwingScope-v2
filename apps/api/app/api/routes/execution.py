"""
Execution gateway API — INTERNAL USE ONLY.

This route is NOT included in the OpenAPI docs by default.
It is NOT accessible to the frontend.
It accepts ONLY structured TradeIntent payloads from the backend.

Access pattern:
  Backend service → POST /api/internal/execute
  Frontend         → NEVER

Any attempt to call this from a user-facing client should be
treated as a security incident.
"""
import logging

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.execution import ExecutionGateway, TradeIntent, GatewayResponse, GatewayMode
from app.core.config import settings

# Hidden from Swagger — include_in_schema=False on the router
router = APIRouter(
    prefix="/internal",
    tags=["internal"],
    include_in_schema=False,   # ← not visible in /docs
)

logger = logging.getLogger(__name__)

INTERNAL_API_KEY_HEADER = "X-Internal-Key"


def _verify_internal_key(x_internal_key: str = Header(..., alias=INTERNAL_API_KEY_HEADER)) -> str:
    """
    Simple shared-secret check. Only backend services know this key.
    Replace with mTLS or signed JWTs for production hardening.
    """
    if not settings.internal_api_key:
        raise HTTPException(status_code=503, detail="Internal API key not configured")
    if x_internal_key != settings.internal_api_key:
        logger.warning("Rejected execution request — invalid internal key")
        raise HTTPException(status_code=403, detail="Forbidden")
    return x_internal_key


@router.post("/execute", response_model=GatewayResponse)
async def execute_trade(
    intent: TradeIntent,
    _key: str = Depends(_verify_internal_key),
    db: AsyncSession = Depends(get_db),
) -> GatewayResponse:
    """
    Submit a structured trade intent through the execution gateway.

    - Validates input model (Pydantic)
    - Verifies trade_plan_id exists in DB
    - Checks approval_status
    - Respects global kill switch and READ_ONLY mode
    - Logs everything immutably to execution_logs
    - Returns structured response — never raw broker data
    """
    gateway = ExecutionGateway(db=db)
    logger.info(
        "Execution request received [mode=%s]: %s %s plan=%s",
        gateway.mode.value, intent.side.value, intent.symbol, intent.trade_plan_id,
    )
    return await gateway.submit(intent)


@router.get("/gateway/status")
async def gateway_status(_key: str = Depends(_verify_internal_key)) -> dict:
    """Return current gateway mode and feature flag state."""
    return {
        "execution_enabled": settings.execution_enabled,
        "execution_mode": settings.execution_mode,
        "robinhood_configured": bool(settings.robinhood_api_key and settings.robinhood_account_id),
        "effective_mode": GatewayMode.EXECUTE.value
            if settings.execution_enabled and settings.execution_mode == "EXECUTE"
            else GatewayMode.READ_ONLY.value,
    }
