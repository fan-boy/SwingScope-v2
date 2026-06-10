"""
Seed a default watchlist with stub user.
Run: python scripts/seed_watchlist.py
"""
import asyncio, uuid, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv()

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.core.config import settings
from app.models.watchlist import Watchlist, WatchlistItem
from app.models.user import User

STUB_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")

DEFAULT_TICKERS = ["AAPL", "NVDA", "MSFT", "TSLA", "AMZN", "META"]

async def seed():
    engine = create_async_engine(settings.database_url)
    Session = async_sessionmaker(engine, expire_on_commit=False)

    async with Session() as db:
        # Ensure stub user exists
        from sqlalchemy import select
        result = await db.execute(select(User).where(User.id == STUB_USER_ID))
        if not result.scalar_one_or_none():
            db.add(User(id=STUB_USER_ID, email="admin@swingscope.local", name="Admin"))

        # Check for existing watchlist
        result = await db.execute(
            select(Watchlist).where(Watchlist.user_id == STUB_USER_ID, Watchlist.is_default == True)
        )
        if result.scalar_one_or_none():
            print("Default watchlist already exists — skipping")
            return

        wl = Watchlist(
            id=uuid.uuid4(), user_id=STUB_USER_ID,
            name="Main Watchlist", is_default=True,
        )
        db.add(wl)
        await db.flush()

        for sym in DEFAULT_TICKERS:
            db.add(WatchlistItem(id=uuid.uuid4(), watchlist_id=wl.id, symbol=sym))

        await db.commit()
        print(f"Seeded watchlist {wl.id} with {len(DEFAULT_TICKERS)} tickers")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(seed())
