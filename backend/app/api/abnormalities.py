"""
Abnormalities API Endpoints - PROPERLY FIXED
Replace backend/api/abnormalities.py with this file

Key fixes:
1. Store UTC in database (PostgreSQL best practice)
2. Accept any timezone from clients, convert to UTC before storing
3. Use timezone_utils consistently
4. No more double timezone conversions
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc, func
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
import uuid

from ..core.database import get_db
from ..core.security import get_current_user_id, RoleChecker
from ..core.timezone_utils import now_utc, to_utc, to_ist, format_ist
from ..models.abnormality import Abnormality, AdminAction

router = APIRouter()


# Schemas
class AbnormalityCreate(BaseModel):
    """Create abnormality report"""
    session_id: str
    abnormality_type: str
    confidence_score: float
    detected_at: datetime
    metadata: Optional[dict] = None


class AbnormalityReview(BaseModel):
    """Review abnormality"""
    review_decision: str  # dismissed, warning_issued, escalated
    notes: Optional[str] = None


class AdminActionCreate(BaseModel):
    """Create admin action"""
    employee_id: str
    session_id: Optional[str] = None
    action_type: str
    justification: str
    metadata: Optional[dict] = None


@router.post("/")
async def report_abnormality(
    data: AbnormalityCreate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Report a detected abnormality from desktop app
    Converts any timezone to UTC for storage
    """
    # Convert detected_at to UTC for storage
    detected_at_utc = to_utc(data.detected_at)
    
    print(f"📊 Abnormality detected:")
    print(f"   Type: {data.abnormality_type}")
    print(f"   Confidence: {data.confidence_score:.2%}")
    print(f"   Time (UTC): {detected_at_utc}")
    print(f"   Time (IST): {format_ist(to_ist(detected_at_utc))}")
    
    # Create abnormality record with UTC time
    abnormality = Abnormality(
        session_id=uuid.UUID(data.session_id),
        employee_id=uuid.UUID(user_id),
        abnormality_type=data.abnormality_type,
        confidence_score=data.confidence_score,
        detected_at=detected_at_utc,  # Store UTC
        detection_metadata=data.metadata,
        reviewed=False
    )
    
    db.add(abnormality)
    await db.commit()
    await db.refresh(abnormality)
    
    # Update session risk score
    from ..models.session import Session
    result = await db.execute(
        select(Session).where(Session.id == data.session_id)
    )
    session = result.scalar_one_or_none()
    
    if session:
        # Calculate new risk score (simple average for now)
        abn_result = await db.execute(
            select(func.avg(Abnormality.confidence_score))
            .where(Abnormality.session_id == data.session_id)
        )
        avg_score = abn_result.scalar()
        session.risk_score = float(avg_score) if avg_score else 0
        await db.commit()
    
    return {
        "message": "Abnormality reported successfully",
        "abnormality": abnormality.to_dict()
    }


@router.get("/")
async def get_abnormalities(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    session_id: Optional[str] = None,
    reviewed: Optional[bool] = None
):
    """Get abnormalities for current user"""
    query = select(Abnormality).where(Abnormality.employee_id == user_id)
    
    if session_id:
        query = query.where(Abnormality.session_id == session_id)
    if reviewed is not None:
        query = query.where(Abnormality.reviewed == reviewed)
    
    query = query.order_by(desc(Abnormality.detected_at)).limit(limit).offset(offset)
    
    result = await db.execute(query)
    abnormalities = result.scalars().all()
    
    return {
        "abnormalities": [a.to_dict() for a in abnormalities],
        "total": len(abnormalities)
    }


@router.get("/{abnormality_id}")
async def get_abnormality(
    abnormality_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get abnormality details"""
    result = await db.execute(
        select(Abnormality).where(
            and_(
                Abnormality.id == abnormality_id,
                Abnormality.employee_id == user_id
            )
        )
    )
    abnormality = result.scalar_one_or_none()
    
    if not abnormality:
        raise HTTPException(
            status_code=404,
            detail="Abnormality not found"
        )
    
    return abnormality.to_dict()


# Admin endpoints
@router.get("/all/unreviewed", dependencies=[Depends(RoleChecker(["admin"]))])
async def get_unreviewed_abnormalities(
    db: AsyncSession = Depends(get_db),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    min_confidence: Optional[float] = Query(None, ge=0, le=100)
):
    """Get all unreviewed abnormalities (Admin only)"""
    query = select(Abnormality).where(Abnormality.reviewed == False)
    
    if min_confidence:
        query = query.where(Abnormality.confidence_score >= min_confidence)
    
    query = query.order_by(desc(Abnormality.confidence_score), desc(Abnormality.detected_at))
    query = query.limit(limit).offset(offset)
    
    result = await db.execute(query)
    abnormalities = result.scalars().all()
    
    return {
        "abnormalities": [a.to_dict() for a in abnormalities],
        "total": len(abnormalities)
    }


@router.post("/{abnormality_id}/review", dependencies=[Depends(RoleChecker(["admin"]))])
async def review_abnormality(
    abnormality_id: str,
    review_data: AbnormalityReview,
    admin_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Review an abnormality (Admin only)
    Stores review timestamp in UTC
    """
    # Get abnormality
    result = await db.execute(
        select(Abnormality).where(Abnormality.id == abnormality_id)
    )
    abnormality = result.scalar_one_or_none()
    
    if not abnormality:
        raise HTTPException(
            status_code=404,
            detail="Abnormality not found"
        )
    
    # Update review status with UTC time
    current_utc = now_utc()
    current_ist = to_ist(current_utc)
    
    print(f"👨‍💼 Admin review:")
    print(f"   Admin ID: {admin_id}")
    print(f"   Decision: {review_data.review_decision}")
    print(f"   Time (UTC): {current_utc}")
    print(f"   Time (IST): {format_ist(current_ist)}")
    
    abnormality.reviewed = True
    abnormality.reviewed_by = uuid.UUID(admin_id)
    abnormality.reviewed_at = current_utc  # Store UTC
    abnormality.review_decision = review_data.review_decision
    
    # Create admin action if warning issued or escalated
    if review_data.review_decision in ['warning_issued', 'escalated']:
        admin_action = AdminAction(
            admin_id=uuid.UUID(admin_id),
            employee_id=abnormality.employee_id,
            session_id=abnormality.session_id,
            action_type=review_data.review_decision,
            justification=review_data.notes or f"Abnormality reviewed: {abnormality.abnormality_type}",
            action_metadata={
                "abnormality_id": str(abnormality.id),
                "abnormality_type": abnormality.abnormality_type,
                "confidence_score": float(abnormality.confidence_score)
            }
        )
        db.add(admin_action)
    
    await db.commit()
    await db.refresh(abnormality)
    
    return {
        "message": "Abnormality reviewed successfully",
        "abnormality": abnormality.to_dict(),
        "reviewed_at_utc": current_utc.isoformat(),
        "reviewed_at_ist": current_ist.isoformat()
    }


@router.get("/stats/summary", dependencies=[Depends(RoleChecker(["admin"]))])
async def get_abnormality_stats(
    db: AsyncSession = Depends(get_db),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
):
    """
    Get abnormality statistics (Admin only)
    Accepts dates in any timezone, converts to UTC for querying
    """
    query = select(Abnormality)
    
    # Convert date filters to UTC
    if start_date:
        start_date_utc = to_utc(start_date)
        query = query.where(Abnormality.detected_at >= start_date_utc)
        print(f"📅 Start date filter: {format_ist(to_ist(start_date_utc))}")
    
    if end_date:
        end_date_utc = to_utc(end_date)
        query = query.where(Abnormality.detected_at <= end_date_utc)
        print(f"📅 End date filter: {format_ist(to_ist(end_date_utc))}")
    
    result = await db.execute(query)
    all_abnormalities = result.scalars().all()
    
    # Calculate statistics
    total = len(all_abnormalities)
    reviewed = len([a for a in all_abnormalities if a.reviewed])
    unreviewed = total - reviewed
    
    by_type = {}
    for abn in all_abnormalities:
        by_type[abn.abnormality_type] = by_type.get(abn.abnormality_type, 0) + 1
    
    avg_confidence = sum(float(a.confidence_score) for a in all_abnormalities) / total if total > 0 else 0
    
    return {
        "total_abnormalities": total,
        "reviewed": reviewed,
        "unreviewed": unreviewed,
        "by_type": by_type,
        "average_confidence_score": round(avg_confidence, 2),
        "period": {
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None
        }
    }


# Admin Actions endpoints
@router.post("/admin-actions", dependencies=[Depends(RoleChecker(["admin"]))])
async def create_admin_action(
    action_data: AdminActionCreate,
    admin_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Create an admin action (Admin only)
    Timestamp stored in UTC
    """
    current_utc = now_utc()
    
    print(f"⚖️ Admin action created:")
    print(f"   Type: {action_data.action_type}")
    print(f"   Employee: {action_data.employee_id}")
    print(f"   Time (UTC): {current_utc}")
    
    admin_action = AdminAction(
        admin_id=uuid.UUID(admin_id),
        employee_id=uuid.UUID(action_data.employee_id),
        session_id=uuid.UUID(action_data.session_id) if action_data.session_id else None,
        action_type=action_data.action_type,
        justification=action_data.justification,
        action_metadata=action_data.metadata
        # created_at will be set by server_default to current UTC
    )
    
    db.add(admin_action)
    await db.commit()
    await db.refresh(admin_action)
    
    return {
        "message": "Admin action created successfully",
        "action": admin_action.to_dict(),
        "created_at_utc": current_utc.isoformat(),
        "created_at_ist": to_ist(current_utc).isoformat()
    }


@router.get("/admin-actions", dependencies=[Depends(RoleChecker(["admin"]))])
async def get_admin_actions(
    db: AsyncSession = Depends(get_db),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    employee_id: Optional[str] = None,
    action_type: Optional[str] = None
):
    """Get admin actions (Admin only)"""
    query = select(AdminAction)
    
    if employee_id:
        query = query.where(AdminAction.employee_id == employee_id)
    if action_type:
        query = query.where(AdminAction.action_type == action_type)
    
    query = query.order_by(desc(AdminAction.created_at)).limit(limit).offset(offset)
    
    result = await db.execute(query)
    actions = result.scalars().all()
    
    return {
        "actions": [a.to_dict() for a in actions],
        "total": len(actions)
    }


@router.get("/debug/time")
async def debug_time():
    """Debug endpoint to check current time in abnormalities context"""
    utc_now = now_utc()
    ist_now = to_ist(utc_now)
    
    return {
        "utc_time": utc_now.isoformat(),
        "ist_time": ist_now.isoformat(),
        "ist_formatted": format_ist(ist_now),
        "timezone_utc": str(utc_now.tzinfo),
        "timezone_ist": str(ist_now.tzinfo),
        "timestamp": utc_now.timestamp(),
        "message": "All times stored in database are in UTC"
    }