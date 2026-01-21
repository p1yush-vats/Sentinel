"""
Sessions API Endpoints - FIXED STATUS LOGIC
Replace backend/api/sessions.py with this file

Key fixes:
1. Status based on work completion percentage
2. incomplete (<40%), partial (40-89%), completed (90%+)
3. active sessions stay active
"""
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

router = APIRouter()


# Schemas
class SessionStart(BaseModel):
    """Session start request"""
    pass


class SessionUpdate(BaseModel):
    """Session update request"""
    total_work_minutes: Optional[int] = None
    total_break_minutes: Optional[int] = None
    lunch_taken: Optional[bool] = None
    status: Optional[str] = None


class SessionEnd(BaseModel):
    """Session end request"""
    total_work_minutes: int
    total_break_minutes: int
    lunch_taken: bool
    session_quality_score: Optional[float] = None


class WorkLogCreate(BaseModel):
    """Work log creation"""
    log_type: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    break_token_used: bool = False


def calculate_session_status(total_work_minutes: int, target_minutes: int = 400) -> str:
    
    if target_minutes == 0:
        return 'incomplete'
    
    completion_percentage = (total_work_minutes / target_minutes) * 100
    
    if completion_percentage >= 90:
        return 'completed'
    elif completion_percentage >= 40:
        return 'partial'
    else:
        return 'incomplete'


@router.post("/start")
async def start_session(
    force_end_existing: bool = False,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Start a new work session
    Stores UTC in database, returns IST to client
    """
    # Check for active session
    result = await db.execute(
        select(Session).where(
            and_(
                Session.employee_id == user_id,
                Session.status == 'active'
            )
        )
    )
    active_session = result.scalar_one_or_none()
    
    if active_session:
        if force_end_existing:
            # End existing session with current UTC time
            current_utc = now_utc()
            active_session.status = calculate_session_status(active_session.total_work_minutes)
            active_session.end_time = current_utc
            await db.commit()
            
            print(f"✅ Auto-ended existing session: {active_session.id}")
        else:
            # Return conflict
            raise HTTPException(
                status_code=409,
                detail={
                    "error": "active_session_exists",
                    "message": "You already have an active session. Choose to continue or end it.",
                    "active_session": active_session.to_dict()
                }
            )
    
    # Get current UTC time for database
    current_utc = now_utc()
    current_ist = to_ist(current_utc)
    
    print(f"🕐 Creating session at UTC: {current_utc}")
    print(f"🕐 IST equivalent: {format_ist(current_ist)}")
    
    # Create new session with UTC time
    new_session = Session(
        employee_id=uuid.UUID(user_id),
        start_time=current_utc,  # Store UTC
        status='active',  # Always start as active
        total_work_minutes=0,
        total_break_minutes=0,
        lunch_taken=False,
        risk_score=0
    )
    
    db.add(new_session)
    await db.commit()
    await db.refresh(new_session)
    
    return {
        "message": "Session started successfully",
        "session": new_session.to_dict(),
        "current_time_utc": current_utc.isoformat(),
        "current_time_ist": current_ist.isoformat()
    }


@router.post("/{session_id}/end")
async def end_session(
    session_id: str,
    data: SessionEnd,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    End a work session
    Calculates status based on work completion
    """
    # Get session
    result = await db.execute(
        select(Session).where(
            and_(
                Session.id == session_id,
                Session.employee_id == user_id
            )
        )
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session.status != 'active':
        raise HTTPException(status_code=400, detail="Session is not active")
    
    # Get current UTC time
    current_utc = now_utc()
    current_ist = to_ist(current_utc)
    
    print(f"🕐 Ending session at UTC: {current_utc}")
    print(f"🕐 IST equivalent: {format_ist(current_ist)}")
    
    # Calculate status based on work completion
    calculated_status = calculate_session_status(data.total_work_minutes)
    
    print(f"📊 Work minutes: {data.total_work_minutes}/400")
    print(f"📊 Calculated status: {calculated_status}")
    
    # Update session with UTC time and calculated status
    session.end_time = current_utc  # Store UTC
    session.total_work_minutes = data.total_work_minutes
    session.total_break_minutes = data.total_break_minutes
    session.lunch_taken = data.lunch_taken
    session.status = calculated_status  # Use calculated status
    session.session_quality_score = data.session_quality_score
    
    await db.commit()
    await db.refresh(session)
    
    return {
        "message": "Session ended successfully",
        "session": session.to_dict(),
        "completion_percentage": round((data.total_work_minutes / 400) * 100, 1),
        "current_time_utc": current_utc.isoformat(),
        "current_time_ist": current_ist.isoformat()
    }


@router.patch("/{session_id}")
async def update_session(
    session_id: str,
    data: SessionUpdate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Update session details"""
    result = await db.execute(
        select(Session).where(
            and_(
                Session.id == session_id,
                Session.employee_id == user_id
            )
        )
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Update fields
    if data.total_work_minutes is not None:
        session.total_work_minutes = data.total_work_minutes
    if data.total_break_minutes is not None:
        session.total_break_minutes = data.total_break_minutes
    if data.lunch_taken is not None:
        session.lunch_taken = data.lunch_taken
    if data.status is not None:
        # Only allow manual status override if explicitly provided
        session.status = data.status
    
    await db.commit()
    await db.refresh(session)
    
    return {
        "message": "Session updated successfully",
        "session": session.to_dict()
    }


@router.get("/")
async def get_sessions(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status: Optional[str] = None
):
    """Get all sessions for current user"""
    query = select(Session).where(Session.employee_id == user_id)
    
    if status:
        query = query.where(Session.status == status)
    
    query = query.order_by(desc(Session.start_time)).limit(limit).offset(offset)
    
    result = await db.execute(query)
    sessions = result.scalars().all()
    
    return {
        "sessions": [s.to_dict() for s in sessions],
        "total": len(sessions),
        "limit": limit,
        "offset": offset,
        "current_time_utc": now_utc().isoformat(),
        "current_time_ist": to_ist(now_utc()).isoformat()
    }


@router.get("/active")
async def get_active_session(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get current active session if any"""
    result = await db.execute(
        select(Session).where(
            and_(
                Session.employee_id == user_id,
                Session.status == 'active'
            )
        )
    )
    session = result.scalar_one_or_none()
    
    return {
        "active_session": session.to_dict() if session else None,
        "current_time_utc": now_utc().isoformat(),
        "current_time_ist": to_ist(now_utc()).isoformat()
    }


@router.get("/{session_id}")
async def get_session(
    session_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get session details"""
    result = await db.execute(
        select(Session).where(
            and_(
                Session.id == session_id,
                Session.employee_id == user_id
            )
        )
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return session.to_dict()


@router.post("/{session_id}/logs")
async def create_work_log(
    session_id: str,
    log_data: WorkLogCreate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Create a work time log entry"""
    # Verify session exists
    result = await db.execute(
        select(Session).where(
            and_(
                Session.id == session_id,
                Session.employee_id == user_id
            )
        )
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Convert times to UTC for storage
    start_time = to_utc(log_data.start_time)
    end_time = to_utc(log_data.end_time) if log_data.end_time else None
    
    # Create work log
    work_log = WorkTimeLog(
        session_id=uuid.UUID(session_id),
        log_type=log_data.log_type,
        start_time=start_time,  # Store UTC
        end_time=end_time,  # Store UTC
        duration_minutes=log_data.duration_minutes,
        break_token_used=log_data.break_token_used
    )
    
    db.add(work_log)
    await db.commit()
    await db.refresh(work_log)
    
    return {
        "message": "Work log created successfully",
        "log": work_log.to_dict()
    }


@router.get("/{session_id}/logs")
async def get_work_logs(
    session_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get all work logs for a session"""
    # Verify session access
    result = await db.execute(
        select(Session).where(
            and_(
                Session.id == session_id,
                Session.employee_id == user_id
            )
        )
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Get logs
    result = await db.execute(
        select(WorkTimeLog).where(WorkTimeLog.session_id == session_id)
        .order_by(WorkTimeLog.start_time)
    )
    logs = result.scalars().all()
    
    return {
        "logs": [log.to_dict() for log in logs],
        "total": len(logs)
    }


@router.get("/debug/time")
async def debug_time():
    """Debug endpoint to check current time"""
    utc_now = now_utc()
    ist_now = to_ist(utc_now)
    
    return {
        "utc_time": utc_now.isoformat(),
        "ist_time": ist_now.isoformat(),
        "ist_formatted": format_ist(ist_now),
        "timezone_utc": str(utc_now.tzinfo),
        "timezone_ist": str(ist_now.tzinfo),
        "timestamp": utc_now.timestamp()
    }