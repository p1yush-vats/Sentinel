from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging

from .core.config import settings
from .core.database import init_db, close_db
from .api import (
    auth, sessions, employees, abnormalities, reports,
    appeals, audit_log, work_rules,
    notification_preferences, productivity_metrics,leaves,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


from .core.websocket import manager


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting SENTINEL Backend...")
    try:
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.warning(f"Database initialization failed: {e}")
        logger.warning("Server will start but database features may not work")
        logger.warning("Check your DATABASE_URL in .env file")
    yield
    logger.info("Shutting down SENTINEL Backend...")
    try:
        await close_db()
        logger.info("Database connections closed")
    except Exception as e:
        logger.warning(f"Database cleanup failed: {e}")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    redirect_slashes=False,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION
    }


@app.get("/")
async def root():
    return {
        "message": "SENTINEL Work Integrity System API",
        "version": settings.APP_VERSION,
        "docs": "/docs"
    }


@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_json()
            await manager.send_personal_message(
                {"type": "echo", "data": data},
                user_id
            )
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket, user_id)


# Original routers
app.include_router(auth.router,          prefix=f"{settings.API_V1_PREFIX}/auth",          tags=["Authentication"])
app.include_router(sessions.router,      prefix=f"{settings.API_V1_PREFIX}/sessions",       tags=["Sessions"])
app.include_router(employees.router,     prefix=f"{settings.API_V1_PREFIX}/employees",      tags=["Employees"])
app.include_router(abnormalities.router, prefix=f"{settings.API_V1_PREFIX}/abnormalities",  tags=["Abnormalities"])
app.include_router(reports.router,       prefix=f"{settings.API_V1_PREFIX}/reports",        tags=["Reports"])

# New routers — all tables now wired
app.include_router(appeals.router,                  prefix=f"{settings.API_V1_PREFIX}/appeals",               tags=["Appeals"])
app.include_router(audit_log.router,                prefix=f"{settings.API_V1_PREFIX}/audit",                 tags=["Audit Log"])
app.include_router(work_rules.router,               prefix=f"{settings.API_V1_PREFIX}/work-rules",            tags=["Work Rules"])
app.include_router(notification_preferences.router, prefix=f"{settings.API_V1_PREFIX}/notification-prefs",    tags=["Notification Preferences"])
app.include_router(productivity_metrics.router,     prefix=f"{settings.API_V1_PREFIX}/productivity-metrics",  tags=["Productivity Metrics"])
app.include_router(leaves.router, prefix=f"{settings.API_V1_PREFIX}/leaves", tags=["Leaves"])

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "type": str(type(exc).__name__)
        }
    )


__all__ = ["app", "manager"]