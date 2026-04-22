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
    notification_preferences, productivity_metrics, leaves, tasks,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


from .core.websocket import manager


import asyncio
from .tasks.demo_reset import hourly_demo_reset_task, revert_demo_admin_changes

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Step 1: Initialize DB tables (may fail if already exist — that's fine)
    try:
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.warning(f"Database initialization skipped (tables likely exist): {e}")

    # Step 2: Ensure demo accounts exist — MUST run independently of init_db
    try:
        await revert_demo_admin_changes()
        logger.info("Demo accounts initialized successfully")
    except Exception as e:
        logger.error(f"Demo account setup failed: {e}", exc_info=True)

    # Step 3: Start hourly background cleanup loop
    try:
        demo_reset_task = asyncio.create_task(hourly_demo_reset_task())
        logger.info("Hourly demo reset task started")
    except Exception as e:
        logger.error(f"Failed to start demo reset task: {e}")
    
    yield
    
    logger.info("Shutting down SENTINEL Backend...")
    if demo_reset_task:
        demo_reset_task.cancel()
        
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


@app.websocket("/ws/admin-feed")
async def admin_feed_endpoint(websocket: WebSocket):
    """
    Dedicated WebSocket endpoint for the admin dashboard Live Feed.
    Must be declared BEFORE /ws/{user_id} so FastAPI matches the literal
    path instead of capturing 'admin-feed' as a user_id parameter.

    Connects under the reserved key 'admin-feed' so manager.broadcast()
    fans all real-time events (sessions, abnormalities, tasks) to every
    connected admin dashboard tab automatically.
    """
    ADMIN_FEED_KEY = "admin-feed"
    await manager.connect(websocket, ADMIN_FEED_KEY)
    try:
        while True:
            # Keep connection alive; dashboard only listens, never sends
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, ADMIN_FEED_KEY)
    except Exception as e:
        logger.error(f"Admin feed WebSocket error: {e}")
        manager.disconnect(websocket, ADMIN_FEED_KEY)


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


app.include_router(auth.router,          prefix=f"{settings.API_V1_PREFIX}/auth",          tags=["Authentication"])
app.include_router(sessions.router,      prefix=f"{settings.API_V1_PREFIX}/sessions",       tags=["Sessions"])
app.include_router(employees.router,     prefix=f"{settings.API_V1_PREFIX}/employees",      tags=["Employees"])
app.include_router(abnormalities.router, prefix=f"{settings.API_V1_PREFIX}/abnormalities",  tags=["Abnormalities"])
app.include_router(reports.router,       prefix=f"{settings.API_V1_PREFIX}/reports",        tags=["Reports"])
app.include_router(appeals.router,                  prefix=f"{settings.API_V1_PREFIX}/appeals",               tags=["Appeals"])
app.include_router(audit_log.router,                prefix=f"{settings.API_V1_PREFIX}/audit",                 tags=["Audit Log"])
app.include_router(work_rules.router,               prefix=f"{settings.API_V1_PREFIX}/work-rules",            tags=["Work Rules"])
app.include_router(notification_preferences.router, prefix=f"{settings.API_V1_PREFIX}/notification-prefs",    tags=["Notification Preferences"])
app.include_router(productivity_metrics.router,     prefix=f"{settings.API_V1_PREFIX}/productivity-metrics",  tags=["Productivity Metrics"])
app.include_router(leaves.router, prefix=f"{settings.API_V1_PREFIX}/leaves", tags=["Leaves"])
app.include_router(tasks.router,  prefix=f"{settings.API_V1_PREFIX}/tasks",  tags=["Tasks"])

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