"""
Alert API routes.

POST /alerts/resend         resend last scan summary
GET  /alerts/history        list alert log entries
GET  /alerts/settings       get current alert settings
PATCH /alerts/settings      update alert settings
"""
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.alerts.service import send_last_summary, get_alert_history
from app.core.config import settings

router = APIRouter(prefix="/alerts", tags=["alerts"])
logger = logging.getLogger(__name__)


class AlertSettingsOut(BaseModel):
    email_enabled: bool
    email_to: str
    smtp_configured: bool
    scheduler_enabled: bool
    scan_cron_schedule: str


class AlertSettingsUpdate(BaseModel):
    email_enabled: bool | None = None
    email_to: str | None = None
    scheduler_enabled: bool | None = None
    scan_cron_schedule: str | None = None


class AlertLogOut(BaseModel):
    id: str
    level: str
    event: str
    message: str
    meta: dict | None
    created_at: datetime


class ResendOut(BaseModel):
    sent: bool
    reason: str | None = None
    to: str | None = None
    candidates: int | None = None


@router.post("/resend", response_model=ResendOut)
async def resend_last_summary(db: AsyncSession = Depends(get_db)):
    """Resend the email summary for the most recent completed scan."""
    try:
        result = await send_last_summary(db)
        return ResendOut(**result)
    except Exception as e:
        logger.error("Resend failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history", response_model=list[AlertLogOut])
async def list_alert_history(limit: int = 20, db: AsyncSession = Depends(get_db)):
    logs = await get_alert_history(db, limit=min(limit, 100))
    return [
        AlertLogOut(
            id=str(log.id),
            level=log.level,
            event=log.event,
            message=log.message,
            meta=log.meta,
            created_at=log.created_at,
        )
        for log in logs
    ]


@router.get("/settings", response_model=AlertSettingsOut)
async def get_alert_settings():
    from app.services.alerts.email import get_email_sender
    return AlertSettingsOut(
        email_enabled=settings.alert_email_enabled,
        email_to=settings.alert_email_to,
        smtp_configured=get_email_sender() is not None,
        scheduler_enabled=settings.scheduler_enabled,
        scan_cron_schedule=settings.scan_cron_schedule,
    )


@router.patch("/settings", response_model=AlertSettingsOut)
async def update_alert_settings(body: AlertSettingsUpdate):
    """
    Update alert settings at runtime.
    Note: changes are in-memory only — update .env for persistence.
    """
    if body.email_enabled is not None:
        settings.alert_email_enabled = body.email_enabled
    if body.email_to is not None:
        settings.alert_email_to = body.email_to
    if body.scan_cron_schedule is not None:
        settings.scan_cron_schedule = body.scan_cron_schedule
        # Reschedule if running
        from app.scheduler import scheduler, _daily_scan_job
        from apscheduler.triggers.cron import CronTrigger
        if scheduler.running:
            parts = settings.scan_cron_schedule.split()
            if len(parts) == 5:
                minute, hour, day, month, dow = parts
                scheduler.reschedule_job(
                    "daily_scan",
                    trigger=CronTrigger(minute=minute, hour=hour, day=day, month=month, day_of_week=dow),
                )

    from app.services.alerts.email import get_email_sender
    return AlertSettingsOut(
        email_enabled=settings.alert_email_enabled,
        email_to=settings.alert_email_to,
        smtp_configured=get_email_sender() is not None,
        scheduler_enabled=settings.scheduler_enabled,
        scan_cron_schedule=settings.scan_cron_schedule,
    )
