"""
POST /scans/run   — trigger a scan
GET  /scans/latest — get the most recent scan run with candidates
GET  /scans/{id}  — get a specific scan run
"""
import uuid
import logging

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.scan import ScanRun, ScanCandidate
from app.schemas.scan_run import ScanRunOut, ScanRequest
from app.services.scanner.service import run_scan
from app.services.scanner.config import DEFAULT_CONFIG
from app.core.config import settings

router = APIRouter(prefix="/scans", tags=["scans"])
logger = logging.getLogger(__name__)


@router.post("/run", response_model=ScanRunOut, status_code=201)
async def trigger_scan(
    body: ScanRequest | None = None,
    db: AsyncSession = Depends(get_db),
) -> ScanRun:
    """
    Trigger a full scan run synchronously.
    Optionally override config and/or universe via request body.
    """
    cfg = (body.config if body and body.config else None) or DEFAULT_CONFIG
    universe = (body.universe if body and body.universe else None) or None

    kwargs = {"db": db, "config": cfg, "mock_mode": settings.mock_mode}
    if universe:
        kwargs["universe"] = universe

    scan_run = await run_scan(**kwargs)

    # Reload with candidates eagerly
    result = await db.execute(
        select(ScanRun)
        .where(ScanRun.id == scan_run.id)
        .options(selectinload(ScanRun.candidates))
    )
    return result.scalar_one()


@router.get("/latest", response_model=ScanRunOut)
async def get_latest_scan(db: AsyncSession = Depends(get_db)) -> ScanRun:
    """Return the most recent completed scan run with all candidates."""
    result = await db.execute(
        select(ScanRun)
        .where(ScanRun.status == "COMPLETED")
        .order_by(desc(ScanRun.created_at))
        .limit(1)
        .options(selectinload(ScanRun.candidates))
    )
    scan = result.scalar_one_or_none()
    if not scan:
        raise HTTPException(status_code=404, detail="No completed scan runs found")
    return scan


@router.get("/{scan_id}", response_model=ScanRunOut)
async def get_scan(
    scan_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> ScanRun:
    result = await db.execute(
        select(ScanRun)
        .where(ScanRun.id == scan_id)
        .options(selectinload(ScanRun.candidates))
    )
    scan = result.scalar_one_or_none()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan run not found")
    return scan


@router.get("/", response_model=list[ScanRunOut])
async def list_scans(
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
) -> list[ScanRun]:
    """List recent scan runs (without candidates for brevity)."""
    result = await db.execute(
        select(ScanRun)
        .order_by(desc(ScanRun.created_at))
        .limit(min(limit, 50))
    )
    return list(result.scalars().all())
