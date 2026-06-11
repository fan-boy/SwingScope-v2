"""
POST /api/risk/validate — preflight risk check, no side effects
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.risk.service import run_risk_checks

router = APIRouter(prefix="/risk", tags=["risk"])


class RiskValidateRequest(BaseModel):
    symbol: str
    entry_price: float
    stop_price: float
    position_size: int
    risk_amount: float
    has_earnings: bool = False


class RiskValidateResponse(BaseModel):
    passed: bool
    reasons: list[str]


@router.post("/validate", response_model=RiskValidateResponse)
async def validate_risk(
    body: RiskValidateRequest,
    db: AsyncSession = Depends(get_db),
) -> RiskValidateResponse:
    result = await run_risk_checks(
        db,
        symbol=body.symbol,
        entry_price=body.entry_price,
        stop_price=body.stop_price,
        position_size=body.position_size,
        risk_amount=body.risk_amount,
        has_earnings=body.has_earnings,
    )
    return RiskValidateResponse(passed=result.passed, reasons=result.reasons)