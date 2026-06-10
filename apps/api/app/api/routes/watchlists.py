"""
Watchlist API routes.

GET    /watchlists/              list all watchlists for user
POST   /watchlists/              create watchlist
GET    /watchlists/{id}          get watchlist with items
DELETE /watchlists/{id}          delete watchlist

POST   /watchlists/{id}/items    add ticker
DELETE /watchlists/{id}/items/{item_id}   remove ticker
PATCH  /watchlists/{id}/items/{item_id}   update (priority, notes)
"""
import uuid
import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field, field_validator
import re

from app.db.session import get_db
from app.models.watchlist import Watchlist, WatchlistItem
from app.schemas.watchlist import WatchlistRead, WatchlistCreate, WatchlistItemRead, WatchlistItemCreate

router = APIRouter(prefix="/watchlists", tags=["watchlists"])
logger = logging.getLogger(__name__)

# ── Temporary user stub (replace with real auth later) ────────────────────
STUB_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")

TICKER_RE = re.compile(r"^[A-Z]{1,5}$")

# ── Request bodies ─────────────────────────────────────────────────────────

class AddItemRequest(BaseModel):
    symbol: str = Field(..., min_length=1, max_length=5)
    notes: str | None = Field(None, max_length=500)
    priority: bool = False

    @field_validator("symbol")
    @classmethod
    def validate_symbol(cls, v: str) -> str:
        v = v.upper().strip()
        if not TICKER_RE.match(v):
            raise ValueError("Symbol must be 1-5 uppercase letters only (e.g. AAPL)")
        return v


class UpdateItemRequest(BaseModel):
    notes: str | None = None
    priority: bool | None = None


class WatchlistItemOut(BaseModel):
    id: uuid.UUID
    symbol: str
    notes: str | None
    priority: bool
    scan_score: float | None = None      # injected from latest scan if available
    scan_confidence: str | None = None
    scan_status: str | None = None

    model_config = {"from_attributes": True}


class WatchlistOut(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    is_default: bool
    items: list[WatchlistItemOut] = []

    model_config = {"from_attributes": True}


# ── Helpers ────────────────────────────────────────────────────────────────

async def _get_watchlist_or_404(wl_id: uuid.UUID, db: AsyncSession) -> Watchlist:
    result = await db.execute(
        select(Watchlist)
        .where(Watchlist.id == wl_id, Watchlist.user_id == STUB_USER_ID)
        .options(selectinload(Watchlist.items))
    )
    wl = result.scalar_one_or_none()
    if not wl:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    return wl


async def _inject_scan_data(items: list[WatchlistItem], db: AsyncSession) -> list[WatchlistItemOut]:
    """Enrich watchlist items with latest scan scores where available."""
    from app.models.scan import ScanCandidate, ScanRun
    from sqlalchemy import desc

    symbols = [i.symbol for i in items]
    if not symbols:
        return []

    # Latest scan candidate per symbol
    subq = (
        select(ScanCandidate.symbol, ScanCandidate.score, ScanCandidate.confidence, ScanCandidate.status)
        .join(ScanRun, ScanCandidate.scan_run_id == ScanRun.id)
        .where(
            ScanCandidate.symbol.in_(symbols),
            ScanRun.status == "COMPLETED",
        )
        .order_by(desc(ScanRun.run_date), desc(ScanCandidate.score))
        .distinct(ScanCandidate.symbol)
    )
    result = await db.execute(subq)
    scan_map = {row.symbol: row for row in result}

    out = []
    for item in items:
        row = scan_map.get(item.symbol)
        out.append(WatchlistItemOut(
            id=item.id,
            symbol=item.symbol,
            notes=item.notes,
            priority=getattr(item, "priority", False),
            scan_score=float(row.score) if row else None,
            scan_confidence=row.confidence if row else None,
            scan_status=row.status if row else None,
        ))
    return out


# ── Routes ─────────────────────────────────────────────────────────────────

@router.get("/", response_model=list[WatchlistOut])
async def list_watchlists(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Watchlist)
        .where(Watchlist.user_id == STUB_USER_ID)
        .options(selectinload(Watchlist.items))
        .order_by(Watchlist.is_default.desc(), Watchlist.created_at)
    )
    watchlists = list(result.scalars().all())

    # Enrich all items
    out = []
    for wl in watchlists:
        items_out = await _inject_scan_data(list(wl.items), db)
        out.append(WatchlistOut(
            id=wl.id, name=wl.name, description=wl.description,
            is_default=wl.is_default, items=items_out,
        ))
    return out


@router.post("/", response_model=WatchlistOut, status_code=201)
async def create_watchlist(body: WatchlistCreate, db: AsyncSession = Depends(get_db)):
    wl = Watchlist(
        id=uuid.uuid4(),
        user_id=STUB_USER_ID,
        name=body.name,
        description=body.description,
        is_default=body.is_default,
    )
    db.add(wl)
    await db.flush()
    return WatchlistOut(id=wl.id, name=wl.name, description=wl.description, is_default=wl.is_default)


@router.get("/{wl_id}", response_model=WatchlistOut)
async def get_watchlist(wl_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    wl = await _get_watchlist_or_404(wl_id, db)
    items_out = await _inject_scan_data(list(wl.items), db)
    return WatchlistOut(id=wl.id, name=wl.name, description=wl.description, is_default=wl.is_default, items=items_out)


@router.delete("/{wl_id}", status_code=204)
async def delete_watchlist(wl_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    wl = await _get_watchlist_or_404(wl_id, db)
    await db.delete(wl)


@router.post("/{wl_id}/items", response_model=WatchlistItemOut, status_code=201)
async def add_item(wl_id: uuid.UUID, body: AddItemRequest, db: AsyncSession = Depends(get_db)):
    wl = await _get_watchlist_or_404(wl_id, db)

    # Duplicate check
    existing = next((i for i in wl.items if i.symbol == body.symbol), None)
    if existing:
        raise HTTPException(status_code=409, detail=f"{body.symbol} is already in this watchlist")

    item = WatchlistItem(
        id=uuid.uuid4(),
        watchlist_id=wl.id,
        symbol=body.symbol,
        notes=body.notes,
    )
    db.add(item)
    await db.flush()

    return WatchlistItemOut(
        id=item.id, symbol=item.symbol, notes=item.notes,
        priority=getattr(item, "priority", False),
    )


@router.delete("/{wl_id}/items/{item_id}", status_code=204)
async def remove_item(wl_id: uuid.UUID, item_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    wl = await _get_watchlist_or_404(wl_id, db)
    item = next((i for i in wl.items if i.id == item_id), None)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    await db.delete(item)


@router.patch("/{wl_id}/items/{item_id}", response_model=WatchlistItemOut)
async def update_item(
    wl_id: uuid.UUID, item_id: uuid.UUID,
    body: UpdateItemRequest, db: AsyncSession = Depends(get_db),
):
    wl = await _get_watchlist_or_404(wl_id, db)
    item = next((i for i in wl.items if i.id == item_id), None)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    if body.notes is not None:
        item.notes = body.notes
    await db.flush()

    return WatchlistItemOut(
        id=item.id, symbol=item.symbol, notes=item.notes,
        priority=getattr(item, "priority", False),
    )
