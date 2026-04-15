import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from ..core.database import get_db
from ..core.security import get_current_user_id, RoleChecker
from ..core.websocket import manager
from ..models.task import Task
from .audit_log import write_audit

router = APIRouter()


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


# ── Schemas ──────────────────────────────────────────────────────────────────

class TaskCreate(BaseModel):
    title:        str
    description:  Optional[str] = None
    assigned_to:  str
    due_date:     Optional[datetime] = None
    priority:     str = "medium"   # low | medium | high | urgent


class TaskStatusUpdate(BaseModel):
    status:          str            # pending | in_progress | completed
    completion_note: Optional[str] = None


# ── Admin: create ─────────────────────────────────────────────────────────────

@router.post("/", dependencies=[Depends(RoleChecker(["admin"]))])
async def create_task(
    data:     TaskCreate,
    admin_id: str = Depends(get_current_user_id),
    db:       AsyncSession = Depends(get_db),
):
    task = Task(
        title       = data.title,
        description = data.description,
        assigned_to = uuid.UUID(data.assigned_to),
        assigned_by = uuid.UUID(admin_id),
        due_date    = data.due_date,
        priority    = data.priority,
        status      = "pending",
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)

    await write_audit(
        db, "task_assigned", "create_task",
        actor_id=admin_id, target_id=str(task.assigned_to), target_type="task",
        metadata={"task_id": str(task.id), "title": task.title, "priority": task.priority},
    )
    await db.commit()

    payload = task.to_dict()
    # Push real-time notification to the assigned employee
    await manager.send_personal_message(
        {"type": "task_assigned", "data": payload},
        data.assigned_to,
    )
    # Broadcast to admin feed
    await manager.broadcast({"type": "task_assigned", "data": payload})

    return {"message": "Task created", "task": payload}


# ── Admin: list all ───────────────────────────────────────────────────────────

@router.get("/all", dependencies=[Depends(RoleChecker(["admin"]))])
async def get_all_tasks(
    db:          AsyncSession = Depends(get_db),
    limit:       int = Query(100, ge=1, le=500),
    offset:      int = Query(0, ge=0),
    assigned_to: Optional[str] = None,
    status:      Optional[str] = None,
    priority:    Optional[str] = None,
):
    query = select(Task)
    if assigned_to: query = query.where(Task.assigned_to == assigned_to)
    if status:      query = query.where(Task.status == status)
    if priority:    query = query.where(Task.priority == priority)
    query = query.order_by(desc(Task.created_at)).limit(limit).offset(offset)
    result = await db.execute(query)
    tasks = result.scalars().all()
    return {"tasks": [t.to_dict() for t in tasks], "total": len(tasks)}


# ── Admin: delete ─────────────────────────────────────────────────────────────

@router.delete("/{task_id}", dependencies=[Depends(RoleChecker(["admin"]))])
async def delete_task(
    task_id: str,
    db:      AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    await db.delete(task)
    await db.commit()
    return {"message": "Task deleted"}


# ── Employee: get own tasks ───────────────────────────────────────────────────

@router.get("/my")
async def get_my_tasks(
    user_id: str = Depends(get_current_user_id),
    db:      AsyncSession = Depends(get_db),
    status:  Optional[str] = None,
):
    query = select(Task).where(Task.assigned_to == user_id)
    if status:
        query = query.where(Task.status == status)
    query = query.order_by(desc(Task.created_at))
    result = await db.execute(query)
    tasks = result.scalars().all()
    return {"tasks": [t.to_dict() for t in tasks], "total": len(tasks)}


# ── Employee: update status ───────────────────────────────────────────────────

@router.patch("/{task_id}/status")
async def update_task_status(
    task_id: str,
    data:    TaskStatusUpdate,
    user_id: str = Depends(get_current_user_id),
    db:      AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Task).where(Task.id == task_id, Task.assigned_to == user_id)
    )
    task = result.scalar_one_or_none()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    task.status = data.status
    if data.completion_note:
        task.completion_note = data.completion_note
    if data.status == "completed":
        task.completed_at = now_utc()

    await db.commit()
    await db.refresh(task)

    payload = task.to_dict()

    if data.status == "completed":
        await write_audit(
            db, "task_completed", "complete_task",
            actor_id=user_id, target_id=task_id, target_type="task",
            metadata={"title": task.title, "note": data.completion_note or ""},
        )
        await db.commit()
        await manager.broadcast({"type": "task_completed", "data": payload})

    return {"message": "Task updated", "task": payload}
