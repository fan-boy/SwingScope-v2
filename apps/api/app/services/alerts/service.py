"""
Alert service — send scan summary email + log to execution_logs.
"""
import uuid
import logging
from datetime import datetime, timezone

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.scan import ScanRun, ScanCandidate
from app.models.log import ExecutionLog
from app.services.alerts.email import get_email_sender, EmailMessage
from app.services.alerts.templates import render_scan_summary, CandidateSummary
from app.core.config import settings

logger = logging.getLogger(__name__)


async def _log_event(
    db: AsyncSession,
    level: str,
    event: str,
    message: str,
    entity_id: uuid.UUID | None = None,
    meta: dict | None = None,
) -> None:
    db.add(ExecutionLog(
        id=uuid.uuid4(),
        level=level,
        event=event,
        message=message,
        entity_type="scan_run",
        entity_id=entity_id,
        meta=meta,
        created_at=datetime.now(timezone.utc),
    ))
    await db.flush()


async def send_scan_summary(scan_run_id: uuid.UUID, db: AsyncSession) -> dict:
    """
    Build and send a scan summary email for the given scan run.
    Returns a status dict.
    """
    # Load scan run with candidates
    result = await db.execute(
        select(ScanRun).where(ScanRun.id == scan_run_id)
    )
    scan = result.scalar_one_or_none()
    if not scan:
        raise ValueError(f"Scan run {scan_run_id} not found")

    result = await db.execute(
        select(ScanCandidate)
        .where(ScanCandidate.scan_run_id == scan_run_id)
        .order_by(desc(ScanCandidate.score))
        .limit(10)
    )
    candidates_raw = list(result.scalars().all())

    if not candidates_raw:
        await _log_event(db, "INFO", "alert.skipped", "No candidates — alert not sent", scan_run_id)
        return {"sent": False, "reason": "no_candidates"}

    candidates = [
        CandidateSummary(
            symbol=c.symbol,
            score=c.score,
            confidence=c.confidence,
            entry=c.entry,
            stop=c.stop,
            target1=c.target1,
            rr_ratio=c.rr_ratio,
            technical_setup=c.technical_setup,
        )
        for c in candidates_raw
    ]

    html, text = render_scan_summary(
        candidates=candidates,
        run_date=scan.run_date,
        tickers_scanned=scan.tickers_scanned,
        regime=scan.market_regime,
    )

    sender = get_email_sender()
    if not sender:
        await _log_event(
            db, "WARN", "alert.not_configured",
            "SMTP not configured — email skipped",
            scan_run_id,
            {"candidates": len(candidates)},
        )
        return {"sent": False, "reason": "smtp_not_configured", "candidates": len(candidates)}

    try:
        msg = EmailMessage(
            to=settings.alert_email_to,
            subject=f"SwingScope — {len(candidates)} candidates for {scan.run_date}",
            html=html,
            text=text,
        )
        await sender.send(msg)

        await _log_event(
            db, "INFO", "alert.sent",
            f"Scan summary email sent to {settings.alert_email_to} with {len(candidates)} candidates",
            scan_run_id,
            {"to": settings.alert_email_to, "candidates": len(candidates), "top": candidates[0].symbol},
        )
        return {"sent": True, "to": settings.alert_email_to, "candidates": len(candidates)}

    except Exception as e:
        logger.error("Failed to send alert email: %s", e)
        await _log_event(
            db, "ERROR", "alert.failed",
            f"Email send failed: {e}",
            scan_run_id,
            {"error": str(e)},
        )
        raise


async def send_last_summary(db: AsyncSession) -> dict:
    """Resend the summary for the most recent completed scan run."""
    result = await db.execute(
        select(ScanRun)
        .where(ScanRun.status == "COMPLETED")
        .order_by(desc(ScanRun.run_date), desc(ScanRun.created_at))
        .limit(1)
    )
    scan = result.scalar_one_or_none()
    if not scan:
        return {"sent": False, "reason": "no_completed_scans"}
    return await send_scan_summary(scan.id, db)


async def get_alert_history(db: AsyncSession, limit: int = 20) -> list[ExecutionLog]:
    result = await db.execute(
        select(ExecutionLog)
        .where(ExecutionLog.event.in_(["alert.sent", "alert.failed", "alert.skipped", "alert.not_configured"]))
        .order_by(desc(ExecutionLog.created_at))
        .limit(limit)
    )
    return list(result.scalars().all())
