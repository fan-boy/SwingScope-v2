"""
Risk preflight validation service.
Called before trade plan approval and before order submission.
Pure validation — no side effects.
"""
from __future__ import annotations
import logging
from dataclasses import dataclass

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.settings import AppSettings
from app.models.trade import TradePlan, TradePlanStatus

logger = logging.getLogger(__name__)

@dataclass
class RiskCheckResult:
    passed: bool
    reasons: list[str]


async def run_risk_checks(
    db: AsyncSession,
    *,
    symbol: str,
    entry_price: float,
    stop_price: float,
    position_size: int,
    risk_amount: float,
    has_earnings: bool = False,
    user_id: str | None = None,
) -> RiskCheckResult:
    """Run all configured risk checks. Returns pass/fail with reasons."""
    reasons: list[str] = []
    passed = True

    # Load settings (first user or by user_id)
    if user_id:
        result = await db.execute(select(AppSettings).where(AppSettings.user_id == user_id))
    else:
        result = await db.execute(select(AppSettings).limit(1))
    cfg = result.scalar_one_or_none()

    kill_switch = cfg.kill_switch_active if cfg else False
    max_risk_pct = cfg.max_risk_per_trade_pct if cfg else 2.0
    max_daily_pct = cfg.max_daily_loss_pct if cfg else 5.0
    max_positions = cfg.max_concurrent_positions if cfg else 5
    max_new_day = cfg.max_new_positions_per_day if cfg else 3
    block_earnings = cfg.block_trades_near_earnings if cfg else True
    account_size = cfg.account_size_usd if cfg else 100_000.0

    # Check 1: Kill switch
    if kill_switch:
        return RiskCheckResult(passed=False, reasons=["FAIL: Kill switch is active — all trading halted"])

    # Check 2: Max risk per trade
    risk_pct = (risk_amount / account_size) * 100
    if risk_pct > max_risk_pct:
        passed = False
        reasons.append(f"FAIL: Trade risk {risk_pct:.2f}% exceeds max {max_risk_pct}% per trade")
    else:
        reasons.append(f"PASS: Trade risk {risk_pct:.2f}% within {max_risk_pct}% limit")

    # Check 3: Max daily loss
    from datetime import date
    today = date.today()
    daily_result = await db.execute(
        select(func.coalesce(func.sum(TradePlan.risk_amount), 0.0))
        .where(TradePlan.status.in_(["SENT", "FILLED"]))
        .where(func.date(TradePlan.updated_at) == today)
    )
    daily_loss = float(daily_result.scalar_one() or 0.0)
    projected_pct = ((daily_loss + risk_amount) / account_size) * 100
    if projected_pct > max_daily_pct:
        passed = False
        reasons.append(f"FAIL: Projected daily loss {projected_pct:.2f}% would exceed max {max_daily_pct}%")
    else:
        reasons.append(f"PASS: Daily loss exposure {projected_pct:.2f}% within {max_daily_pct}% limit")

    # Check 4: Max concurrent positions
    open_result = await db.execute(
        select(func.count()).select_from(TradePlan).where(TradePlan.status == "SENT")
    )
    open_positions = int(open_result.scalar_one() or 0)
    if open_positions >= max_positions:
        passed = False
        reasons.append(f"FAIL: {open_positions} open positions at max of {max_positions}")
    else:
        reasons.append(f"PASS: {open_positions} open positions (max {max_positions})")

    # Check 5: Max new positions per day
    new_result = await db.execute(
        select(func.count()).select_from(TradePlan)
        .where(func.date(TradePlan.created_at) == today)
    )
    new_today = int(new_result.scalar_one() or 0)
    if new_today >= max_new_day:
        passed = False
        reasons.append(f"FAIL: {new_today} new positions today (max {max_new_day})")
    else:
        reasons.append(f"PASS: {new_today} new positions today (max {max_new_day})")

    # Check 6: Earnings proximity
    if block_earnings and has_earnings:
        passed = False
        reasons.append(f"FAIL: Earnings event detected for {symbol} — trading blocked near earnings")
    elif block_earnings:
        reasons.append(f"PASS: No upcoming earnings event for {symbol}")

    return RiskCheckResult(passed=passed, reasons=reasons)