import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from ..core.database import get_db
from ..core.security import get_current_user_id, RoleChecker
from ..models.appeal import Appeal
from ..models.session import Session
from .audit_log import write_audit

router = APIRouter()


def now_utc():
    return datetime.now(timezone.utc)


class AppealCreate(BaseModel):
    session_id:     str
    abnormality_id: Optional[str] = None
    reason:         str


class AppealReview(BaseModel):
    status:         str
    admin_response: str


@router.post("/")
async def submit_appeal(
    data:    AppealCreate,
    user_id: str = Depends(get_current_user_id),
    db:      AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Session).where(Session.id == data.session_id))
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if str(session.employee_id) != user_id:
        raise HTTPException(status_code=403, detail="Not your session")

    existing = await db.execute(
        select(Appeal).where(
            Appeal.session_id  == uuid.UUID(data.session_id),
            Appeal.employee_id == uuid.UUID(user_id),
            Appeal.status      == 'pending'
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Pending appeal already exists for this session")

    appeal = Appeal(
        employee_id    = uuid.UUID(user_id),
        session_id     = uuid.UUID(data.session_id),
        abnormality_id = uuid.UUID(data.abnormality_id) if data.abnormality_id else None,
        reason         = data.reason,
        status         = 'pending',
    )
    db.add(appeal)
    await db.commit()
    await db.refresh(appeal)

    await write_audit(db, "appeal_submitted", "submit_appeal",
        actor_id=user_id, target_id=str(appeal.id), target_type="appeal",
        metadata={"session_id": data.session_id, "reason_preview": data.reason[:100]})
    await db.commit()

    return {"message": "Appeal submitted successfully", "appeal": appeal.to_dict()}


@router.get("/")
async def get_my_appeals(
    user_id: str = Depends(get_current_user_id),
    db:      AsyncSession = Depends(get_db),
    status:  Optional[str] = None,
    limit:   int = Query(50, ge=1, le=200),
    offset:  int = Query(0, ge=0),
):
    query = select(Appeal).where(Appeal.employee_id == uuid.UUID(user_id))
    if status:
        query = query.where(Appeal.status == status)
    query = query.order_by(desc(Appeal.created_at)).limit(limit).offset(offset)
    result = await db.execute(query)
    appeals = result.scalars().all()
    return {"appeals": [a.to_dict() for a in appeals], "total": len(appeals)}


@router.get("/all", dependencies=[Depends(RoleChecker(["admin"]))])
async def get_all_appeals(
    db:     AsyncSession = Depends(get_db),
    status: Optional[str] = None,
    limit:  int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    query = select(Appeal)
    if status:
        query = query.where(Appeal.status == status)
    query = query.order_by(desc(Appeal.created_at)).limit(limit).offset(offset)
    result = await db.execute(query)
    appeals = result.scalars().all()
    return {"appeals": [a.to_dict() for a in appeals], "total": len(appeals)}


@router.post("/{appeal_id}/review", dependencies=[Depends(RoleChecker(["admin"]))])
async def review_appeal(
    appeal_id: str,
    review:    AppealReview,
    admin_id:  str = Depends(get_current_user_id),
    db:        AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Appeal).where(Appeal.id == appeal_id))
    appeal = result.scalar_one_or_none()
    if not appeal:
        raise HTTPException(status_code=404, detail="Appeal not found")
    if appeal.status != 'pending':
        raise HTTPException(status_code=400, detail="Appeal already reviewed")
    if review.status not in ('approved', 'rejected'):
        raise HTTPException(status_code=400, detail="Status must be approved or rejected")

    appeal.status         = review.status
    appeal.admin_response = review.admin_response
    appeal.reviewed_by    = uuid.UUID(admin_id)
    appeal.reviewed_at    = now_utc()

    await db.commit()
    await db.refresh(appeal)

    await write_audit(db, "appeal_reviewed", f"appeal_{review.status}",
        actor_id=admin_id, target_id=str(appeal.employee_id), target_type="appeal",
        metadata={"appeal_id": appeal_id, "decision": review.status,
                  "session_id": str(appeal.session_id)})
    await db.commit()

    return {"message": "Appeal reviewed", "appeal": appeal.to_dict()}


@router.get("/{appeal_id}")
async def get_appeal(
    appeal_id: str,
    user_id:   str = Depends(get_current_user_id),
    db:        AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Appeal).where(Appeal.id == appeal_id))
    appeal = result.scalar_one_or_none()
    if not appeal:
        raise HTTPException(status_code=404, detail="Appeal not found")
    return appeal.to_dict()
