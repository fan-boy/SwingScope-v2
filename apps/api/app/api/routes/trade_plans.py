"""
Trade plan workflow API.

POST   /trade-plans/                   create plan (from candidate or manual)
GET    /trade-plans/                   list plans (filter by status)
GET    /trade-plans/{id}               get single plan with orders
PATCH  /trade-plans/{id}               update draft
POST   /trade-plans/{id}/approve       approve plan
POST   /trade-plans/{id}/reject        reject plan
POST   /trade-plans/{id}/submit        send approved plan to execution gateway
"""
import uuid
import logging
from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.trade import TradePlan, TradeOrder
from app.models.log import ExecutionLog
from app.core.config import settings

router = APIRouter(prefix="/trade-plans", tags=["trade-plans"])
logger = logging.getLogger(__name__)

# Stub user — replace with real auth
STUB_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")

VALID_STATUSES = ("DRAFT", "APPROVED", "SENT", "FILLED", "CANCELLED", "REJECTED")


# ── Request / response models ──────────────────────────────────────────────

class CreatePlanRequest(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=5)
    direction: Literal["LONG", "SHORT"] = "LONG"
    entry: float = Field(..., gt=0)
    stop: float = Field(..., gt=0)
    target1: float = Field(..., gt=0)
    target2: float | None = Field(None, gt=0)
    quantity: float | None = Field(None, gt=0)
    risk_amount: float | None = Field(None, gt=0, description="Max dollar risk on this trade")
    notes: str | None = Field(None, max_length=1000)
    candidate_id: uuid.UUID | None = None


class UpdatePlanRequest(BaseModel):
    entry: float | None = Field(None, gt=0)
    stop: float | None = Field(None, gt=0)
    target1: float | None = Field(None, gt=0)
    target2: float | None = Field(None, gt=0)
    quantity: float | None = Field(None, gt=0)
    risk_amount: float | None = Field(None, gt=0)
    notes: str | None = Field(None, max_length=1000)


class ApproveRequest(BaseModel):
    notes: str | None = Field(None, max_length=500)


class RejectRequest(BaseModel):
    reason: str = Field(..., min_length=1, max_length=500)


class SubmitRequest(BaseModel):
    order_type: Literal["MARKET", "LIMIT", "STOP_LIMIT"] = "LIMIT"
    strategy_tag: str = "SWING_ENTRY"


class OrderOut(BaseModel):
    id: uuid.UUID
    order_type: str
    side: str
    quantity: float
    limit_price: float | None
    stop_price: float | None
    filled_price: float | None
    status: str
    broker_order_id: str | None
    submitted_at: datetime | None
    model_config = {"from_attributes": True}


class PlanOut(BaseModel):
    id: uuid.UUID
    symbol: str
    direction: str
    status: str
    entry: float
    stop: float
    target1: float
    target2: float | None
    quantity: float | None
    risk_amount: float | None
    rr_ratio: float | None
    notes: str | None
    candidate_id: uuid.UUID | None
    approved_at: datetime | None
    created_at: datetime
    updated_at: datetime
    orders: list[OrderOut] = []
    model_config = {"from_attributes": True}


# ── Helpers ────────────────────────────────────────────────────────────────

def _calc_rr(entry: float, stop: float, target: float, direction: str) -> float | None:
    try:
        risk = abs(entry - stop)
        reward = abs(target - entry)
        if risk == 0:
            return None
        return round(reward / risk, 2)
    except Exception:
        return None


async def _get_plan_or_404(plan_id: uuid.UUID, db: AsyncSession) -> TradePlan:
    result = await db.execute(
        select(TradePlan)
        .where(TradePlan.id == plan_id, TradePlan.user_id == STUB_USER_ID)
        .options(selectinload(TradePlan.orders))
    )
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(404, "Trade plan not found")
    return plan


async def _log(db: AsyncSession, level: str, event: str, message: str, plan_id: uuid.UUID, meta: dict | None = None):
    db.add(ExecutionLog(
        id=uuid.uuid4(), level=level, event=event, message=message,
        entity_type="trade_plan", entity_id=plan_id,
        meta=meta, created_at=datetime.now(timezone.utc),
    ))
    await db.flush()


# ── Routes ─────────────────────────────────────────────────────────────────

@router.post("/", response_model=PlanOut, status_code=201)
async def create_plan(body: CreatePlanRequest, db: AsyncSession = Depends(get_db)):
    symbol = body.symbol.upper().strip()
    rr = _calc_rr(body.entry, body.stop, body.target1, body.direction)

    plan = TradePlan(
        id=uuid.uuid4(),
        user_id=STUB_USER_ID,
        candidate_id=body.candidate_id,
        symbol=symbol,
        direction=body.direction,
        status="DRAFT",
        entry=body.entry,
        stop=body.stop,
        target1=body.target1,
        target2=body.target2,
        quantity=body.quantity,
        rr_ratio=rr,
        notes=body.notes,
    )
    # Store risk_amount in notes as metadata until schema migration
    if body.risk_amount:
        plan.notes = (plan.notes or "") + f"\n[risk_amount: {body.risk_amount}]"

    db.add(plan)
    await db.flush()
    await _log(db, "INFO", "plan.created", f"Trade plan created: {symbol} {body.direction}", plan.id,
               {"entry": body.entry, "stop": body.stop, "rr": rr})
    return plan


@router.get("/", response_model=list[PlanOut])
async def list_plans(
    status: str | None = Query(None, description="Filter by status"),
    limit: int = Query(50, le=200),
    db: AsyncSession = Depends(get_db),
):
    q = select(TradePlan).where(TradePlan.user_id == STUB_USER_ID)
    if status:
        statuses = [s.strip().upper() for s in status.split(",")]
        q = q.where(TradePlan.status.in_(statuses))
    q = q.order_by(desc(TradePlan.created_at)).limit(limit)
    result = await db.execute(q)
    return list(result.scalars().all())


@router.get("/{plan_id}", response_model=PlanOut)
async def get_plan(plan_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    return await _get_plan_or_404(plan_id, db)


@router.patch("/{plan_id}", response_model=PlanOut)
async def update_plan(plan_id: uuid.UUID, body: UpdatePlanRequest, db: AsyncSession = Depends(get_db)):
    plan = await _get_plan_or_404(plan_id, db)
    if plan.status != "DRAFT":
        raise HTTPException(400, f"Only DRAFT plans can be edited (current: {plan.status})")
    for field, val in body.model_dump(exclude_none=True).items():
        setattr(plan, field, val)
    if plan.entry and plan.stop and plan.target1:
        plan.rr_ratio = _calc_rr(plan.entry, plan.stop, plan.target1, plan.direction)
    await db.flush()
    return plan


@router.post("/{plan_id}/approve", response_model=PlanOut)
async def approve_plan(plan_id: uuid.UUID, body: ApproveRequest, db: AsyncSession = Depends(get_db)):
    plan = await _get_plan_or_404(plan_id, db)
    if plan.status not in ("DRAFT",):
        raise HTTPException(400, f"Only DRAFT plans can be approved (current: {plan.status})")
    plan.status = "APPROVED"
    plan.approved_at = datetime.now(timezone.utc)
    if body.notes:
        plan.notes = (plan.notes or "") + f"\n[approved: {body.notes}]"
    await db.flush()
    await _log(db, "INFO", "plan.approved", f"{plan.symbol} plan approved", plan.id)
    return plan


@router.post("/{plan_id}/reject", response_model=PlanOut)
async def reject_plan(plan_id: uuid.UUID, body: RejectRequest, db: AsyncSession = Depends(get_db)):
    plan = await _get_plan_or_404(plan_id, db)
    if plan.status not in ("DRAFT", "APPROVED"):
        raise HTTPException(400, f"Cannot reject plan with status {plan.status}")
    plan.status = "REJECTED"
    plan.notes = (plan.notes or "") + f"\n[rejected: {body.reason}]"
    await db.flush()
    await _log(db, "INFO", "plan.rejected", f"{plan.symbol} plan rejected: {body.reason}", plan.id)
    return plan


@router.post("/{plan_id}/submit", response_model=dict)
async def submit_plan(plan_id: uuid.UUID, body: SubmitRequest, db: AsyncSession = Depends(get_db)):
    """
    Send an APPROVED plan to the execution gateway.
    Hard-blocked if:
    - plan is not APPROVED
    - global kill switch is off
    - plan is already SENT/FILLED
    """
    plan = await _get_plan_or_404(plan_id, db)

    # Safety check 1: must be APPROVED
    if plan.status != "APPROVED":
        raise HTTPException(400, f"Plan must be APPROVED before submitting (current: {plan.status})")

    # Safety check 2: kill switch
    if not settings.execution_enabled:
        await _log(db, "WARN", "plan.submit_blocked",
                   "Submission blocked — EXECUTION_ENABLED=false", plan.id)
        raise HTTPException(403, "Execution is globally disabled. Enable EXECUTION_ENABLED in settings.")

    # Build trade intent
    from app.services.execution import (
        ExecutionGateway, TradeIntent,
        OrderSide, OrderType, ApprovalStatus, RiskTag, StrategyTag,
    )

    side = OrderSide.BUY if plan.direction == "LONG" else OrderSide.SELL
    order_type = OrderType[body.order_type]
    strategy = StrategyTag[body.strategy_tag] if body.strategy_tag in StrategyTag.__members__ else StrategyTag.SWING_ENTRY

    intent = TradeIntent(
        trade_plan_id=plan.id,
        symbol=plan.symbol,
        side=side,
        order_type=order_type,
        quantity=plan.quantity,
        limit_price=plan.entry if order_type == OrderType.LIMIT else None,
        stop_price=plan.stop if order_type in (OrderType.STOP, OrderType.STOP_LIMIT) else None,
        strategy_tag=strategy,
        risk_tag=RiskTag.MEDIUM,
        approval_status=ApprovalStatus.APPROVED,
        note=f"Submitted via trade plan {plan.id}",
    )

    gateway = ExecutionGateway(db=db)
    response = await gateway.submit(intent)

    # Update plan status based on result
    if response.status.value in ("SUBMITTED", "SIMULATED"):
        plan.status = "SENT"
        await _log(db, "INFO", "plan.sent",
                   f"Plan submitted to gateway [{response.mode.value}]: {response.status.value}",
                   plan.id, {"gateway_response": response.status.value, "mode": response.mode.value})
    else:
        await _log(db, "WARN", "plan.submit_failed",
                   f"Gateway blocked: {response.blocked_reason}", plan.id)

    await db.flush()
    return {
        "plan_id": str(plan.id),
        "plan_status": plan.status,
        "gateway_status": response.status.value,
        "mode": response.mode.value,
        "broker_order_id": response.broker_order_id,
        "message": response.message,
        "blocked_reason": response.blocked_reason,
    }
