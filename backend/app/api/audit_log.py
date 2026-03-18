import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..core.security import RoleChecker
from ..models.audit_log_model import AuditLog

router = APIRouter()


async def write_audit(
    db,
    event_type:  str,
    action:      str,
    actor_id:    Optional[str] = None,
    target_id:   Optional[str] = None,
    target_type: Optional[str] = None,
    metadata:    Optional[dict] = None,
    ip_address:  Optional[str] = None,
    user_agent:  Optional[str] = None,
):
    entry = AuditLog(
        event_type     = event_type,
        action         = action,
        actor_id       = uuid.UUID(actor_id)  if actor_id  else None,
        target_id      = uuid.UUID(target_id) if target_id else None,
        target_type    = target_type,
        event_metadata = metadata or {},
        ip_address     = ip_address,
        user_agent     = user_agent,
    )
    db.add(entry)
    # caller must await db.commit()


@router.get("/", dependencies=[Depends(RoleChecker(["admin"]))])
async def get_audit_logs(
    db:          AsyncSession = Depends(get_db),
    event_type:  Optional[str] = None,
    actor_id:    Optional[str] = None,
    target_type: Optional[str] = None,
    limit:       int = Query(100, ge=1, le=500),
    offset:      int = Query(0, ge=0),
):
    query = select(AuditLog)
    if event_type:
        query = query.where(AuditLog.event_type == event_type)
    if actor_id:
        query = query.where(AuditLog.actor_id == actor_id)
    if target_type:
        query = query.where(AuditLog.target_type == target_type)

    query = query.order_by(desc(AuditLog.created_at)).limit(limit).offset(offset)
    result = await db.execute(query)
    logs = result.scalars().all()
    return {"logs": [l.to_dict() for l in logs], "total": len(logs)}