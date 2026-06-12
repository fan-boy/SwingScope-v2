from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import health, scans, watchlists, alerts as alerts_router, execution as execution_router
from app.api.routes.chart import router as chart_router
from app.api.routes.risk import router as risk_router
from app.scheduler import start_scheduler, stop_scheduler
from app.db.session import engine
from app.db.base import Base
# Import all models so Base knows about them
import app.models.user       # noqa: F401
import app.models.scan       # noqa: F401
import app.models.trade      # noqa: F401
import app.models.watchlist  # noqa: F401
import app.models.settings   # noqa: F401
import app.models.position   # noqa: F401
import app.models.log        # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create all tables if they don't exist (safe to run on every startup)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(title="SwingScope API", version="0.3.0", lifespan=lifespan)

import os
_origins = ["http://localhost:3000"]
if os.getenv("FRONTEND_URL"):
    _origins.append(os.getenv("FRONTEND_URL"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api")
app.include_router(scans.router, prefix="/api")
app.include_router(watchlists.router, prefix="/api")
app.include_router(alerts_router.router, prefix="/api")
app.include_router(execution_router.router, prefix="/api")
app.include_router(chart_router, prefix="/api")
app.include_router(risk_router, prefix="/api")
