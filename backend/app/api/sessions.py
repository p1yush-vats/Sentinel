from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
import uuid

from ..core.database import get_db
from ..core.security import get_current_user_id, RoleChecker
from ..core.timezone_utils import now_utc, to_utc, to_ist, format_ist
from ..models.session import Session, WorkTimeLog
from .audit_log import write_audit

router = APIRouter()


class SessionStart(BaseModel):
    pass

class SessionUpdate(BaseModel):
    total_work_minutes:  Optional[int]   = None
    total_break_minutes: Optional[int]   = None
    lunch_taken:         Optional[bool]  = None
    status:              Optional[str]   = None

class SessionEnd(BaseModel):
    total_work_minutes:    int
    total_break_minutes:   int
    lunch_taken:           bool
    session_quality_score: Optional[float] = None

class WorkLogCreate(BaseModel):
    log_type:         str
    start_time:       datetime
    end_time:         Optional[datetime] = None
    duration_minutes: Optional[int]      = None
    break_token_used: bool = False


def calculate_session_status(total_work_minutes: int, target_minutes: int = 400) -> str:
    if target_minutes == 0:
        return 'incomplete'
    pct = (total_work_minutes / target_minutes) * 100
    if pct >= 75:   return 'completed'   # 300+ minutes = completed
    elif pct >= 30: return 'partial'     # 120+ minutes = partial
    else:           return 'incomplete'


@router.post("/start")
async def start_session(
    force_end_existing: bool = False,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Session).where(and_(Session.employee_id == user_id, Session.status == 'active'))
    )
    existing = result.scalar_one_or_none()

    if existing:
        if not force_end_existing:
            return {
                "conflict": True,
                "existing_session": existing.to_dict(),
                "message": "Active session already exists"
            }
        existing.status   = 'completed'
        existing.end_time = now_utc()
        await db.commit()

        await write_audit(db, "session_force_ended", "force_end_session",
            actor_id=user_id, target_id=str(existing.id), target_type="session",
            metadata={"reason": "force_end_existing_on_start"})
        await db.commit()

    session = Session(
        employee_id = uuid.UUID(user_id),
        start_time  = now_utc(),
        status      = 'active'
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)

    await write_audit(db, "session_started", "start_session",
        actor_id=user_id, target_id=str(session.id), target_type="session",
        metadata={"start_time": session.start_time.isoformat()})
    await db.commit()

    return {
        "conflict": False,
        "session":  session.to_dict(),
        "message":  "Session started successfully"
    }


@router.patch("/{session_id}")
async def update_session(
    session_id:  str,
    update_data: SessionUpdate,
    user_id:     str = Depends(get_current_user_id),
    db:          AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Session).where(and_(Session.id == session_id, Session.employee_id == user_id))
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if update_data.total_work_minutes  is not None: session.total_work_minutes  = update_data.total_work_minutes
    if update_data.total_break_minutes is not None: session.total_break_minutes = update_data.total_break_minutes
    if update_data.lunch_taken         is not None: session.lunch_taken         = update_data.lunch_taken
    if update_data.status              is not None: session.status              = update_data.status

    await db.commit()
    await db.refresh(session)
    return {"message": "Session updated", "session": session.to_dict()}


@router.post("/{session_id}/end")
async def end_session(
    session_id: str,
    end_data:   SessionEnd,
    user_id:    str = Depends(get_current_user_id),
    db:         AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Session).where(and_(Session.id == session_id, Session.employee_id == user_id))
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    session.end_time              = now_utc()
    session.total_work_minutes    = end_data.total_work_minutes
    session.total_break_minutes   = end_data.total_break_minutes
    session.lunch_taken           = end_data.lunch_taken
    session.session_quality_score = end_data.session_quality_score
    session.status                = calculate_session_status(end_data.total_work_minutes)

    await db.commit()
    await db.refresh(session)

    await write_audit(db, "session_ended", "end_session",
        actor_id=user_id, target_id=str(session.id), target_type="session",
        metadata={
            "work_minutes":  end_data.total_work_minutes,
            "break_minutes": end_data.total_break_minutes,
            "lunch_taken":   end_data.lunch_taken,
            "status":        session.status
        })
    await db.commit()

    return {"message": "Session ended", "session": session.to_dict()}


@router.delete("/{session_id}")
async def delete_session(
    session_id: str,
    user_id:    str = Depends(get_current_user_id),
    db:         AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Session).where(and_(Session.id == session_id, Session.employee_id == user_id))
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    await db.delete(session)
    await db.commit()

    await write_audit(db, "session_deleted", "delete_session",
        actor_id=user_id, target_id=session_id, target_type="session",
        metadata={"deleted_at": now_utc().isoformat()})
    await db.commit()

    return {"message": "Session deleted"}


@router.get("/active")
async def get_active_session(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Session).where(and_(Session.employee_id == user_id, Session.status == 'active'))
    )
    session = result.scalar_one_or_none()
    if not session:
        return {"session": None, "message": "No active session"}
    return {"session": session.to_dict()}


@router.get("/")
async def get_sessions(
    user_id: str = Depends(get_current_user_id),
    db:      AsyncSession = Depends(get_db),
    limit:   int = Query(50, ge=1, le=200),
    offset:  int = Query(0, ge=0),
    status:  Optional[str] = None
):
    query = select(Session).where(Session.employee_id == user_id)
    if status:
        query = query.where(Session.status == status)
    query = query.order_by(desc(Session.start_time)).limit(limit).offset(offset)
    result = await db.execute(query)
    sessions = result.scalars().all()
    return {"sessions": [s.to_dict() for s in sessions], "total": len(sessions)}


@router.get("/all", dependencies=[Depends(RoleChecker(["admin"]))])
async def get_all_sessions(
    db:          AsyncSession = Depends(get_db),
    limit:       int = Query(100, ge=1, le=500),
    offset:      int = Query(0, ge=0),
    status:      Optional[str] = None,
    employee_id: Optional[str] = None
):
    query = select(Session)
    if status:
        query = query.where(Session.status == status)
    if employee_id:
        query = query.where(Session.employee_id == employee_id)
    query = query.order_by(desc(Session.start_time)).limit(limit).offset(offset)
    result = await db.execute(query)
    sessions = result.scalars().all()
    return {"sessions": [s.to_dict() for s in sessions], "total": len(sessions)}


@router.get("/{session_id}")
async def get_session(
    session_id: str,
    user_id:    str = Depends(get_current_user_id),
    db:         AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Session).where(and_(Session.id == session_id, Session.employee_id == user_id))
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session.to_dict()


@router.post("/{session_id}/logs")
async def create_work_log(
    session_id: str,
    log_data:   WorkLogCreate,
    user_id:    str = Depends(get_current_user_id),
    db:         AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Session).where(and_(Session.id == session_id, Session.employee_id == user_id))
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    start_time = to_utc(log_data.start_time)
    end_time   = to_utc(log_data.end_time) if log_data.end_time else None

    work_log = WorkTimeLog(
        session_id       = uuid.UUID(session_id),
        log_type         = log_data.log_type,
        start_time       = start_time,
        end_time         = end_time,
        duration_minutes = log_data.duration_minutes,
        break_token_used = log_data.break_token_used
    )
    db.add(work_log)
    await db.commit()
    await db.refresh(work_log)

    return {"message": "Work log created successfully", "log": work_log.to_dict()}


@router.get("/{session_id}/logs")
async def get_work_logs(
    session_id: str,
    user_id:    str = Depends(get_current_user_id),
    db:         AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Session).where(and_(Session.id == session_id, Session.employee_id == user_id))
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Session not found")

    result = await db.execute(
        select(WorkTimeLog).where(WorkTimeLog.session_id == session_id).order_by(WorkTimeLog.start_time)
    )
    logs = result.scalars().all()
    return {"logs": [log.to_dict() for log in logs], "total": len(logs)}


@router.get("/debug/time")
async def debug_time():
    utc_now = now_utc()
    ist_now = to_ist(utc_now)
    return {
        "utc_time":       utc_now.isoformat(),
        "ist_time":       ist_now.isoformat(),
        "ist_formatted":  format_ist(ist_now),
    }