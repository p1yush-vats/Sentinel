import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from ..core.database import get_db
from ..core.security import get_current_user_id, RoleChecker
from ..models.work_rule import WorkRule
from .audit_log import write_audit

router = APIRouter()


class WorkRuleCreate(BaseModel):
    department:                Optional[str] = None
    employee_id:               Optional[str] = None
    work_minutes_per_hour:     int = 50
    break_minutes_per_hour:    int = 10
    lunch_duration_minutes:    int = 30
    daily_work_target_minutes: int = 400
    detection_sensitivity:     str = 'medium'


class WorkRuleUpdate(BaseModel):
    work_minutes_per_hour:     Optional[int] = None
    break_minutes_per_hour:    Optional[int] = None
    lunch_duration_minutes:    Optional[int] = None
    daily_work_target_minutes: Optional[int] = None
    detection_sensitivity:     Optional[str] = None


@router.get("/")
async def get_work_rules(
    db:         AsyncSession = Depends(get_db),
    user_id:    str = Depends(get_current_user_id),
    department: Optional[str] = None,
):
    query = select(WorkRule)
    if department:
        query = query.where(WorkRule.department == department)
    result = await db.execute(query)
    rules = result.scalars().all()
    return {"rules": [r.to_dict() for r in rules], "total": len(rules)}


@router.post("/", dependencies=[Depends(RoleChecker(["admin"]))])
async def create_work_rule(
    data:     WorkRuleCreate,
    admin_id: str = Depends(get_current_user_id),
    db:       AsyncSession = Depends(get_db),
):
    if data.detection_sensitivity not in ('low', 'medium', 'high'):
        raise HTTPException(status_code=400, detail="sensitivity must be low | medium | high")

    rule = WorkRule(
        department                = data.department,
        employee_id               = uuid.UUID(data.employee_id) if data.employee_id else None,
        work_minutes_per_hour     = data.work_minutes_per_hour,
        break_minutes_per_hour    = data.break_minutes_per_hour,
        lunch_duration_minutes    = data.lunch_duration_minutes,
        daily_work_target_minutes = data.daily_work_target_minutes,
        detection_sensitivity     = data.detection_sensitivity,
    )
    db.add(rule)
    await db.commit()
    await db.refresh(rule)

    await write_audit(db, "work_rule_created", "create_work_rule",
        actor_id=admin_id, target_id=str(rule.id), target_type="work_rule",
        metadata={"department": data.department, "sensitivity": data.detection_sensitivity})
    await db.commit()

    return {"message": "Work rule created", "rule": rule.to_dict()}


@router.patch("/{rule_id}", dependencies=[Depends(RoleChecker(["admin"]))])
async def update_work_rule(
    rule_id:  str,
    data:     WorkRuleUpdate,
    admin_id: str = Depends(get_current_user_id),
    db:       AsyncSession = Depends(get_db),
):
    result = await db.execute(select(WorkRule).where(WorkRule.id == rule_id))
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    changes = {}
    if data.work_minutes_per_hour     is not None:
        changes['work_minutes_per_hour']     = data.work_minutes_per_hour
        rule.work_minutes_per_hour           = data.work_minutes_per_hour
    if data.break_minutes_per_hour    is not None:
        changes['break_minutes_per_hour']    = data.break_minutes_per_hour
        rule.break_minutes_per_hour          = data.break_minutes_per_hour
    if data.lunch_duration_minutes    is not None:
        changes['lunch_duration_minutes']    = data.lunch_duration_minutes
        rule.lunch_duration_minutes          = data.lunch_duration_minutes
    if data.daily_work_target_minutes is not None:
        changes['daily_work_target_minutes'] = data.daily_work_target_minutes
        rule.daily_work_target_minutes       = data.daily_work_target_minutes
    if data.detection_sensitivity     is not None:
        changes['detection_sensitivity']     = data.detection_sensitivity
        rule.detection_sensitivity           = data.detection_sensitivity

    await db.commit()
    await db.refresh(rule)

    await write_audit(db, "work_rule_updated", "update_work_rule",
        actor_id=admin_id, target_id=rule_id, target_type="work_rule",
        metadata={"changes": changes, "department": rule.department})
    await db.commit()

    return {"message": "Work rule updated", "rule": rule.to_dict()}


@router.delete("/{rule_id}", dependencies=[Depends(RoleChecker(["admin"]))])
async def delete_work_rule(
    rule_id:  str,
    admin_id: str = Depends(get_current_user_id),
    db:       AsyncSession = Depends(get_db),
):
    result = await db.execute(select(WorkRule).where(WorkRule.id == rule_id))
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    await db.delete(rule)
    await db.commit()

    await write_audit(db, "work_rule_deleted", "delete_work_rule",
        actor_id=admin_id, target_id=rule_id, target_type="work_rule",
        metadata={"department": rule.department})
    await db.commit()

    return {"message": "Work rule deleted"}
