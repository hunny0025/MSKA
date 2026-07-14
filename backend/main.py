"""
Maruti Suzuki Knowledge Assistant — FastAPI Application Entry Point.

Creates the FastAPI app, mounts routers, configures middleware.
All business logic lives in services/; this file is intentionally thin.
"""

from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import get_settings
from core.logging import get_logger

from api.v1.auth import router as auth_router
from api.v1.departments import router as departments_router
from api.v1.projects import router as projects_router
from api.v1.documents import router as documents_router
from api.v1.chat import router as chat_router
from api.v1.search import router as search_router
from api.v1.analytics import router as analytics_router
from api.v1.notifications import router as notifications_router
from api.v1.admin import router as admin_router
from api.v1.ingestion import router as ingestion_router
from api.v1.trace import router as trace_router
from api.v1.explorer import router as explorer_router

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(application: FastAPI):
    """Application lifespan handler for startup/shutdown events."""
    settings = get_settings()
    logger.info(
        "Starting %s (env=%s, debug=%s)",
        settings.app_name, settings.app_env, settings.app_debug,
    )
    
    # Initialize database tables (Alembic-free startup creation)
    from core.database import engine
    from core.init_db import init_tables
    logger.info("Initializing database tables...")
    await init_tables(engine)
    logger.info("Database tables initialized successfully.")
    
    # Seed core data (automatic setup for deployments)
    from seed_db import seed_core_data
    logger.info("Auto-seeding database core tables...")
    await seed_core_data()
    logger.info("Database auto-seeding completed.")
    
    yield
    logger.info("Shutting down %s", settings.app_name)



settings = get_settings()

app = FastAPI(
    title="Maruti Suzuki Knowledge Assistant",
    description="Enterprise AI-powered knowledge management platform",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routers
app.include_router(auth_router, prefix="/api/v1")
app.include_router(departments_router, prefix="/api/v1")
app.include_router(projects_router, prefix="/api/v1")
app.include_router(documents_router, prefix="/api/v1")
app.include_router(ingestion_router, prefix="/api/v1")  # A3 – upload + SSE progress
app.include_router(trace_router, prefix="/api/v1")       # C1 – retrieval trace
app.include_router(explorer_router, prefix="/api/v1")    # D1 – document explorer
app.include_router(chat_router, prefix="/api/v1")
app.include_router(search_router, prefix="/api/v1")
app.include_router(analytics_router, prefix="/api/v1")
app.include_router(notifications_router, prefix="/api/v1")
app.include_router(admin_router, prefix="/api/v1")









@app.get("/health", tags=["Infrastructure"])
async def health_check() -> dict:
    """
    Health check endpoint.

    Returns 200 with status and timestamp. Used by Docker health checks
    and monitoring.
    """
    return {
        "status": "ok",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "0.1.0",
    }

