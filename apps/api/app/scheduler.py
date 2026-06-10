"""
APScheduler — daily scan + alert job.
Started with the FastAPI app, runs in-process.

Schedule: configurable via SCAN_CRON_SCHEDULE env var.
Default: 30 23 * * 1-5  (11:30 PM UTC = ~6:30 PM ET, after market close)
"""
import logging
from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.core.config import settings

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler(timezone="UTC")


async def _daily_scan_job() -> None:
    """Run scan → send alert. Runs inside its own DB session."""
    logger.info("Scheduled scan starting at %s", datetime.now(timezone.utc).isoformat())
    try:
        from app.db.session import AsyncSessionLocal
        from app.services.scanner.service import run_scan
        from app.services.alerts.service import send_scan_summary

        async with AsyncSessionLocal() as db:
            scan = await run_scan(db=db, mock_mode=settings.mock_mode)
            await db.commit()

        if settings.alert_email_enabled and settings.alert_email_to:
            async with AsyncSessionLocal() as db:
                result = await send_scan_summary(scan.id, db)
                await db.commit()
                logger.info("Alert result: %s", result)
        else:
            logger.info("Email alerts disabled — skipping")

    except Exception as e:
        logger.error("Scheduled scan job failed: %s", e)


def start_scheduler() -> None:
    if not settings.scheduler_enabled:
        logger.info("Scheduler disabled (SCHEDULER_ENABLED=false)")
        return

    # Parse cron: "30 23 * * 1-5"
    parts = settings.scan_cron_schedule.split()
    if len(parts) != 5:
        logger.error("Invalid SCAN_CRON_SCHEDULE: %s — scheduler not started", settings.scan_cron_schedule)
        return

    minute, hour, day, month, day_of_week = parts
    trigger = CronTrigger(
        minute=minute, hour=hour,
        day=day, month=month, day_of_week=day_of_week,
    )

    scheduler.add_job(_daily_scan_job, trigger=trigger, id="daily_scan", replace_existing=True)
    scheduler.start()
    logger.info("Scheduler started — daily scan at cron '%s' UTC", settings.scan_cron_schedule)


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
