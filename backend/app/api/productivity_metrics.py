import uuid
from datetime import datetime, timezone
from typing import Optional, List

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from ..core.database import get_db
from ..core.security import get_current_user_id, RoleChecker
from ..models.productivity_metric import ProductivityMetric

router = APIRouter()


def now_utc():
    return datetime.now(timezone.utc).replace(tzinfo=None)  # naive UTC for DB


def to_naive_utc(dt: Optional[datetime]) -> Optional[datetime]:
    """Strip timezone info → naive UTC datetime suitable for TIMESTAMP WITHOUT TIME ZONE."""
    if dt is None:
        return None
    if dt.tzinfo is not None:
        # Convert to UTC then drop the tzinfo so asyncpg is happy with TIMESTAMP WITHOUT TIME ZONE
        from datetime import timedelta
        utc_offset = dt.utcoffset()
        if utc_offset is not None:
            dt = dt - utc_offset
        return dt.replace(tzinfo=None)
    return dt


class MetricCreate(BaseModel):
    session_id:                str
    hour_of_day:               Optional[int]      = None
    activity_intensity:        Optional[float]    = None
    break_effectiveness_score: Optional[float]    = None
    keystroke_count:           Optional[int]      = None
    mouse_movement_count:      Optional[int]      = None
    paste_count:               Optional[int]      = None
    recorded_at:               Optional[datetime] = None


class MetricBulkCreate(BaseModel):
    metrics: List[MetricCreate]


@router.post("/")
async def record_metric(
    data:    MetricCreate,
    user_id: str = Depends(get_current_user_id),
    db:      AsyncSession = Depends(get_db),
):
    metric = ProductivityMetric(
        session_id                = uuid.UUID(data.session_id),
        employee_id               = uuid.UUID(user_id),
        hour_of_day               = data.hour_of_day,
        activity_intensity        = data.activity_intensity,
        break_effectiveness_score = data.break_effectiveness_score,
        keystroke_count           = data.keystroke_count,
        mouse_movement_count      = data.mouse_movement_count,
        paste_count               = data.paste_count,
        recorded_at               = data.recorded_at or now_utc(),
    )
    db.add(metric)
    await db.commit()
    await db.refresh(metric)
    return {"message": "Metric recorded", "metric": metric.to_dict()}


@router.post("/bulk")
async def record_metrics_bulk(
    data:    MetricBulkCreate,
    user_id: str = Depends(get_current_user_id),
    db:      AsyncSession = Depends(get_db),
):
    metrics = []
    for m in data.metrics:
        metric = ProductivityMetric(
            session_id                = uuid.UUID(m.session_id),
            employee_id               = uuid.UUID(user_id),
            hour_of_day               = m.hour_of_day,
            activity_intensity        = m.activity_intensity,
            break_effectiveness_score = m.break_effectiveness_score,
            keystroke_count           = m.keystroke_count,
            mouse_movement_count      = m.mouse_movement_count,
            paste_count               = m.paste_count,
            recorded_at               = to_naive_utc(m.recorded_at) or now_utc(),
        )
        db.add(metric)
        metrics.append(metric)

    await db.commit()
    return {"message": f"{len(metrics)} metrics recorded", "count": len(metrics)}


@router.get("/session/{session_id}")
async def get_session_metrics(
    session_id: str,
    user_id:    str = Depends(get_current_user_id),
    db:         AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ProductivityMetric)
        .where(ProductivityMetric.session_id == uuid.UUID(session_id))
        .order_by(ProductivityMetric.recorded_at)
    )
    metrics = result.scalars().all()
    return {"metrics": [m.to_dict() for m in metrics], "total": len(metrics)}


@router.get("/employee/{employee_id}", dependencies=[Depends(RoleChecker(["admin"]))])
async def get_employee_metrics(
    employee_id: str,
    db:          AsyncSession = Depends(get_db),
    limit:       int = Query(200, ge=1, le=1000),
    offset:      int = Query(0, ge=0),
):
    result = await db.execute(
        select(ProductivityMetric)
        .where(ProductivityMetric.employee_id == uuid.UUID(employee_id))
        .order_by(desc(ProductivityMetric.recorded_at))
        .limit(limit).offset(offset)
    )
    metrics = result.scalars().all()
    return {"metrics": [m.to_dict() for m in metrics], "total": len(metrics)}
