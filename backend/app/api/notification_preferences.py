import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from ..core.database import get_db
from ..core.security import get_current_user_id, RoleChecker
from ..models.notification_preference import NotificationPreference
from .audit_log import write_audit

router = APIRouter()


class PrefsUpdate(BaseModel):
    email_notifications: Optional[bool] = None
    break_reminders:     Optional[bool] = None
    weekly_reports:      Optional[bool] = None
    abnormality_alerts:  Optional[bool] = None


async def _get_or_create(db, employee_id: str) -> NotificationPreference:
    result = await db.execute(
        select(NotificationPreference).where(
            NotificationPreference.employee_id == uuid.UUID(employee_id)
        )
    )
    pref = result.scalar_one_or_none()
    if not pref:
        pref = NotificationPreference(employee_id=uuid.UUID(employee_id))
        db.add(pref)
        await db.commit()
        await db.refresh(pref)
    return pref


@router.get("/me")
async def get_my_prefs(
    user_id: str = Depends(get_current_user_id),
    db:      AsyncSession = Depends(get_db),
):
    pref = await _get_or_create(db, user_id)
    return pref.to_dict()


@router.patch("/me")
async def update_my_prefs(
    data:    PrefsUpdate,
    user_id: str = Depends(get_current_user_id),
    db:      AsyncSession = Depends(get_db),
):
    pref = await _get_or_create(db, user_id)

    changes = {}
    if data.email_notifications is not None:
        changes['email_notifications'] = data.email_notifications
        pref.email_notifications       = data.email_notifications
    if data.break_reminders     is not None:
        changes['break_reminders']     = data.break_reminders
        pref.break_reminders           = data.break_reminders
    if data.weekly_reports      is not None:
        changes['weekly_reports']      = data.weekly_reports
        pref.weekly_reports            = data.weekly_reports
    if data.abnormality_alerts  is not None:
        changes['abnormality_alerts']  = data.abnormality_alerts
        pref.abnormality_alerts        = data.abnormality_alerts

    await db.commit()
    await db.refresh(pref)

    await write_audit(db, "prefs_updated", "update_notification_prefs",
        actor_id=user_id, target_id=user_id, target_type="employee",
        metadata={"changes": changes})
    await db.commit()

    return {"message": "Preferences updated", "preferences": pref.to_dict()}


@router.get("/all", dependencies=[Depends(RoleChecker(["admin"]))])
async def get_all_prefs(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(NotificationPreference))
    prefs = result.scalars().all()
    return {"preferences": [p.to_dict() for p in prefs], "total": len(prefs)}


@router.get("/{employee_id}", dependencies=[Depends(RoleChecker(["admin"]))])
async def get_employee_prefs(
    employee_id: str,
    db:          AsyncSession = Depends(get_db),
):
    pref = await _get_or_create(db, employee_id)
    return pref.to_dict()
