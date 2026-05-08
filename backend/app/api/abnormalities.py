import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from ..core.database import get_db
from ..core.security import get_current_user_id, RoleChecker
from ..core.websocket import manager
from ..models.abnormality import Abnormality, AdminAction, SEVERITY_RANK
from ..models.session import Session
from ..models.employee import Employee
from .audit_log import write_audit
from ..tasks.email_tasks import send_flag_warning, send_flag_escalation

router = APIRouter()


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def to_ist(dt: datetime) -> datetime:
    from datetime import timedelta
    IST = timezone(timedelta(hours=5, minutes=30))
    return dt.astimezone(IST)


class AbnormalityCreate(BaseModel):
    session_id:       str
    abnormality_type: str
    confidence_score: float
    metadata:         dict = {}

class AbnormalityReview(BaseModel):
    decision:      str
    justification: str = ""

class AdminActionCreate(BaseModel):
    employee_id:   str
    session_id:    Optional[str] = None
    action_type:   str
    justification: str
    metadata:      dict = {}


@router.post("/")
async def report_abnormality(
    data: AbnormalityCreate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    now = now_utc()

    try:
        session_id = uuid.UUID(data.session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session_id UUID")

    session_result = await db.execute(select(Session).where(Session.id == session_id))
    session = session_result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail=f"Session {data.session_id} not found")

    employee_id = session.employee_id

    detection_payload = {
        "occurrences": data.metadata.get("occurrences", 1),
        "confidence":  round(float(data.confidence_score), 4),
        "severity":    data.metadata.get("severity", "LOW"),
        "timestamps":  data.metadata.get("timestamps", []),
        "last_seen":   now.isoformat(),
    }

    result = await db.execute(select(Abnormality).where(Abnormality.session_id == session_id))
    record = result.scalar_one_or_none()

    if record:
        record.merge_detection(data.abnormality_type, detection_payload)
        record.last_updated_at = now

        # Sync session risk_score (0–100 scale) every time new data merges in
        new_risk = min(round(float(record.confidence_score) * 100, 2), 100.0)
        session.risk_score = new_risk

        await db.commit()
        await db.refresh(record)

        await write_audit(db, "abnormality_detected", "upsert_abnormality",
            actor_id=str(employee_id), target_id=str(record.id), target_type="abnormality",
            metadata={"type": data.abnormality_type, "severity": record.overall_severity,
                      "confidence": float(data.confidence_score), "session_id": data.session_id})
        await db.commit()

        payload = record.to_dict()
        await manager.broadcast({"type": "abnormality_detected", "data": payload})

        return {"message": "Abnormality merged into session record", "abnormality": payload}

    else:
        severity, confidence = Abnormality.recalculate_overall({data.abnormality_type: detection_payload})
        record = Abnormality(
            session_id        = session_id,
            employee_id       = employee_id,
            overall_severity  = severity,
            confidence_score  = confidence,
            detections        = {data.abnormality_type: detection_payload},
            first_detected_at = now,
            last_updated_at   = now,
        )
        db.add(record)
        await db.commit()
        await db.refresh(record)

        # Store on 0–100 scale to match what the desktop sync writes at session end
        session.risk_score = min(round(confidence * 100, 2), 100.0)
        await db.commit()

        await write_audit(db, "abnormality_detected", "create_abnormality",
            actor_id=str(employee_id), target_id=str(record.id), target_type="abnormality",
            metadata={"type": data.abnormality_type, "severity": severity,
                      "confidence": float(data.confidence_score), "session_id": data.session_id})
        await db.commit()

        payload = record.to_dict()
        await manager.broadcast({"type": "abnormality_detected", "data": payload})

        return {"message": "Abnormality record created", "abnormality": payload}


@router.get("/")
async def get_abnormalities(
    user_id:    str = Depends(get_current_user_id),
    db:         AsyncSession = Depends(get_db),
    limit:      int = Query(50, ge=1, le=100),
    offset:     int = Query(0, ge=0),
    session_id: Optional[str] = None,
    reviewed:   Optional[bool] = None
):
    query = select(Abnormality).where(Abnormality.employee_id == user_id)
    if session_id:
        query = query.where(Abnormality.session_id == session_id)
    if reviewed is not None:
        query = query.where(Abnormality.reviewed == reviewed)
    query = query.order_by(desc(Abnormality.last_updated_at)).limit(limit).offset(offset)
    result = await db.execute(query)
    records = result.scalars().all()
    return {"abnormalities": [r.to_dict() for r in records], "total": len(records)}


@router.get("/all/unreviewed", dependencies=[Depends(RoleChecker(["admin"]))])
async def get_unreviewed_abnormalities(
    db:             AsyncSession = Depends(get_db),
    limit:          int   = Query(100, ge=1, le=500),
    offset:         int   = Query(0, ge=0),
    min_confidence: Optional[float] = Query(None, ge=0, le=1),
    employee_id:    Optional[str] = None
):
    query = select(Abnormality).where(Abnormality.reviewed == False)
    if min_confidence is not None:
        query = query.where(Abnormality.confidence_score >= min_confidence)
    if employee_id:
        query = query.where(Abnormality.employee_id == employee_id)
    query = query.order_by(desc(Abnormality.overall_severity), desc(Abnormality.last_updated_at)).limit(limit).offset(offset)
    result = await db.execute(query)
    records = result.scalars().all()
    return {"abnormalities": [r.to_dict() for r in records], "total": len(records)}


@router.get("/{abnormality_id}")
async def get_abnormality(
    abnormality_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Abnormality).where(Abnormality.id == abnormality_id))
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="Abnormality not found")
    return record.to_dict()


@router.post("/{abnormality_id}/review", dependencies=[Depends(RoleChecker(["admin"]))])
async def review_abnormality(
    abnormality_id: str,
    review_data:    AbnormalityReview,
    background_tasks: BackgroundTasks,
    admin_id:       str = Depends(get_current_user_id),
    db:             AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Abnormality).where(Abnormality.id == abnormality_id))
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="Abnormality not found")

    record.reviewed        = True
    record.reviewed_by     = uuid.UUID(admin_id)
    record.reviewed_at     = now_utc()
    record.review_decision = review_data.decision

    await db.commit()
    await db.refresh(record)

    await write_audit(db, "flag_reviewed", f"review_{review_data.decision}",
        actor_id=admin_id, target_id=str(record.employee_id), target_type="abnormality",
        metadata={"abnormality_id": abnormality_id, "decision": review_data.decision,
                  "session_id": str(record.session_id), "severity": record.overall_severity})
    await db.commit()

    employee = await db.scalar(select(Employee).where(Employee.id == record.employee_id))
    if employee:
        note = review_data.justification if review_data.justification else f"Your activity on session {record.session_id} was reviewed."
        if review_data.decision in ("warn", "warned", "warning_issued"):
            background_tasks.add_task(send_flag_warning, employee.email, employee.full_name, note)
        elif review_data.decision in ("escalate", "escalated"):
            background_tasks.add_task(send_flag_escalation, employee.email, employee.full_name, note)

    return {"message": "Review saved", "abnormality": record.to_dict()}


@router.post("/admin-actions", dependencies=[Depends(RoleChecker(["admin"]))])
async def create_admin_action(
    action_data: AdminActionCreate,
    admin_id:    str = Depends(get_current_user_id),
    db:          AsyncSession = Depends(get_db)
):
    admin_action = AdminAction(
        admin_id        = uuid.UUID(admin_id),
        employee_id     = uuid.UUID(action_data.employee_id),
        session_id      = uuid.UUID(action_data.session_id) if action_data.session_id else None,
        action_type     = action_data.action_type,
        justification   = action_data.justification,
        action_metadata = action_data.metadata
    )
    db.add(admin_action)
    await db.commit()
    await db.refresh(admin_action)

    await write_audit(db, "admin_action", action_data.action_type,
        actor_id=admin_id, target_id=action_data.employee_id, target_type="employee",
        metadata={"action_type": action_data.action_type, "session_id": action_data.session_id,
                  "justification": action_data.justification[:100]})
    await db.commit()

    return {"message": "Admin action recorded", "action": admin_action.to_dict()}


@router.get("/admin-actions", dependencies=[Depends(RoleChecker(["admin"]))])
async def get_admin_actions(
    db:          AsyncSession = Depends(get_db),
    limit:       int = Query(100, ge=1, le=500),
    offset:      int = Query(0, ge=0),
    employee_id: Optional[str] = None,
    action_type: Optional[str] = None
):
    query = select(AdminAction)
    if employee_id:
        query = query.where(AdminAction.employee_id == employee_id)
    if action_type:
        query = query.where(AdminAction.action_type == action_type)
    query = query.order_by(desc(AdminAction.created_at)).limit(limit).offset(offset)
    result = await db.execute(query)
    actions = result.scalars().all()
    return {"actions": [a.to_dict() for a in actions], "total": len(actions)}


@router.get("/debug/time")
async def debug_time():
    utc = now_utc()
    return {"utc_time": utc.isoformat(), "ist_time": to_ist(utc).isoformat()}