"""
Abnormalities API — UPSERT design

POST /abnormalities/
  - Finds existing row for this session_id
  - If found   → merges the new detection type into detections JSONB
  - If missing → creates a fresh row
  → Result: always exactly 1 row per session in the table

GET  /abnormalities/            → current user's abnormality records
GET  /abnormalities/{id}        → single record
GET  /abnormalities/all/unreviewed  → admin view

Admin:
POST /abnormalities/{id}/review
POST /abnormalities/admin-actions
GET  /abnormalities/admin-actions
"""
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from ..core.database import get_db
from ..core.security import get_current_user_id, RoleChecker
from ..models.abnormality import Abnormality, AdminAction, SEVERITY_RANK
from ..models.session import Session

router = APIRouter()


# ─── Timezone helpers ─────────────────────────────────────────
def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def to_ist(dt: datetime) -> datetime:
    from datetime import timedelta
    IST = timezone(timedelta(hours=5, minutes=30))
    return dt.astimezone(IST)


# ─── Schemas ──────────────────────────────────────────────────

class AbnormalityCreate(BaseModel):
    """
    Payload sent by the desktop app.

    abnormality_type: e.g. "rapid_paste", "long_idle"
    confidence_score: 0.0 – 1.0
    metadata: the detection detail dict built by the aggregator:
      {
        "occurrences": 5,
        "severity":    "HIGH",
        "confidence":  0.80,
        "timestamps":  [...],
        "last_seen":   "..."
      }
    """
    session_id:       str
    abnormality_type: str
    confidence_score: float
    metadata:         dict = {}


class AbnormalityReview(BaseModel):
    decision:      str        # dismissed | warning_issued | escalated
    justification: str = ""


class AdminActionCreate(BaseModel):
    employee_id:   str
    session_id:    Optional[str] = None
    action_type:   str
    justification: str
    metadata:      dict = {}


# ─── Main UPSERT endpoint ─────────────────────────────────────

@router.post("/")
async def report_abnormality(
    data: AbnormalityCreate,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """
    UPSERT abnormality for a session.

    Rules:
      - Only 1 row per session_id ever exists.
      - If a row already exists → merge the new detection type in.
      - If no row exists        → create it.
      - overall_severity and confidence_score are recalculated on every merge.
    """
    now = now_utc()

    try:
        session_id = uuid.UUID(data.session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session_id UUID")

    # 1. Verify session exists and get employee_id from it
    session_result = await db.execute(
        select(Session).where(Session.id == session_id)
    )
    session = session_result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail=f"Session {data.session_id} not found")

    employee_id = session.employee_id

    # 2. Build the detection payload for this type
    detection_payload = {
        "occurrences": data.metadata.get("occurrences", 1),
        "confidence":  round(float(data.confidence_score), 4),
        "severity":    data.metadata.get("severity", "LOW"),
        "timestamps":  data.metadata.get("timestamps", []),
        "last_seen":   now.isoformat(),
    }

    # 3. Try to find existing row for this session
    result = await db.execute(
        select(Abnormality).where(Abnormality.session_id == session_id)
    )
    record = result.scalar_one_or_none()

    if record:
        # ── MERGE into existing row ──────────────────────────
        record.merge_detection(data.abnormality_type, detection_payload)
        record.last_updated_at = now
        await db.commit()
        await db.refresh(record)

        print(f"  ✅ Merged '{data.abnormality_type}' into session record "
              f"| severity={record.overall_severity} conf={record.confidence_score}")

        return {
            "message":      "Abnormality merged into session record",
            "abnormality":  record.to_dict()
        }

    else:
        # ── CREATE new row for this session ─────────────────
        severity, confidence = Abnormality.recalculate_overall(
            {data.abnormality_type: detection_payload}
        )
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

        print(f"  🆕 Created abnormality record for session "
              f"| type='{data.abnormality_type}' severity={severity}")

        # Also update session risk score
        session.risk_score = float(confidence)
        await db.commit()

        return {
            "message":     "Abnormality record created",
            "abnormality": record.to_dict()
        }


# ─── Read endpoints ───────────────────────────────────────────

@router.get("/")
async def get_abnormalities(
    user_id:    str = Depends(get_current_user_id),
    db:         AsyncSession = Depends(get_db),
    limit:      int = Query(50, ge=1, le=100),
    offset:     int = Query(0, ge=0),
    session_id: Optional[str] = None,
    reviewed:   Optional[bool] = None
):
    """Get abnormality records for current user (one per session)."""
    query = select(Abnormality).where(Abnormality.employee_id == user_id)

    if session_id:
        query = query.where(Abnormality.session_id == session_id)
    if reviewed is not None:
        query = query.where(Abnormality.reviewed == reviewed)

    query = query.order_by(desc(Abnormality.last_updated_at)).limit(limit).offset(offset)

    result = await db.execute(query)
    records = result.scalars().all()

    return {
        "abnormalities": [r.to_dict() for r in records],
        "total": len(records)
    }


@router.get("/all/unreviewed", dependencies=[Depends(RoleChecker(["admin"]))])
async def get_unreviewed_abnormalities(
    db:             AsyncSession = Depends(get_db),
    limit:          int   = Query(100, ge=1, le=500),
    offset:         int   = Query(0, ge=0),
    min_confidence: Optional[float] = Query(None, ge=0, le=1)
):
    """Get all unreviewed abnormality records (Admin only)."""
    query = select(Abnormality).where(Abnormality.reviewed == False)

    if min_confidence is not None:
        query = query.where(Abnormality.confidence_score >= min_confidence)

    query = query.order_by(
        desc(Abnormality.overall_severity),
        desc(Abnormality.last_updated_at)
    ).limit(limit).offset(offset)

    result = await db.execute(query)
    records = result.scalars().all()

    return {
        "abnormalities": [r.to_dict() for r in records],
        "total": len(records)
    }


@router.get("/{abnormality_id}")
async def get_abnormality(
    abnormality_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get a single abnormality record."""
    result = await db.execute(
        select(Abnormality).where(Abnormality.id == abnormality_id)
    )
    record = result.scalar_one_or_none()

    if not record:
        raise HTTPException(status_code=404, detail="Abnormality not found")

    return record.to_dict()


# ─── Admin review ─────────────────────────────────────────────

@router.post("/{abnormality_id}/review", dependencies=[Depends(RoleChecker(["admin"]))])
async def review_abnormality(
    abnormality_id: str,
    review_data:    AbnormalityReview,
    admin_id:       str = Depends(get_current_user_id),
    db:             AsyncSession = Depends(get_db)
):
    """Review an abnormality record (Admin only)."""
    result = await db.execute(
        select(Abnormality).where(Abnormality.id == abnormality_id)
    )
    record = result.scalar_one_or_none()

    if not record:
        raise HTTPException(status_code=404, detail="Abnormality not found")

    record.reviewed        = True
    record.reviewed_by     = uuid.UUID(admin_id)
    record.reviewed_at     = now_utc()
    record.review_decision = review_data.decision

    await db.commit()
    await db.refresh(record)

    return {
        "message":     "Review saved",
        "abnormality": record.to_dict()
    }


# ─── Admin actions ────────────────────────────────────────────

@router.post("/admin-actions", dependencies=[Depends(RoleChecker(["admin"]))])
async def create_admin_action(
    action_data: AdminActionCreate,
    admin_id:    str = Depends(get_current_user_id),
    db:          AsyncSession = Depends(get_db)
):
    """Log an admin action (warning, flag, escalation)."""
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

    return {
        "message": "Admin action recorded",
        "action":  admin_action.to_dict()
    }


@router.get("/admin-actions", dependencies=[Depends(RoleChecker(["admin"]))])
async def get_admin_actions(
    db:          AsyncSession = Depends(get_db),
    limit:       int = Query(100, ge=1, le=500),
    offset:      int = Query(0, ge=0),
    employee_id: Optional[str] = None,
    action_type: Optional[str] = None
):
    """Get admin action log (Admin only)."""
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
        "total":   len(actions)
    }


@router.get("/debug/time")
async def debug_time():
    """Check server time."""
    utc = now_utc()
    return {
        "utc_time": utc.isoformat(),
        "ist_time": to_ist(utc).isoformat()
    }