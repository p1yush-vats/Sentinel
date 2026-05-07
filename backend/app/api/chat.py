from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload
from typing import Optional
from pydantic import BaseModel
import uuid

from ..core.database import get_db
from ..core.security import get_current_user_id
from ..models.employee import Employee
from ..models.chat import TeamMessage

router = APIRouter()


class ChatMessageCreate(BaseModel):
    content: str


@router.get("/team/pinned")
async def get_pinned_message(
    db: AsyncSession = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
):
    """Return the single currently pinned message for this department."""
    result = await db.execute(select(Employee).where(Employee.id == current_user_id))
    me = result.scalar_one_or_none()
    if not me or not me.department:
        return {"pinned": None}

    q = (
        select(TeamMessage)
        .options(selectinload(TeamMessage.sender), selectinload(TeamMessage.pinner))
        .where(TeamMessage.department == me.department, TeamMessage.is_pinned == True)
        .order_by(desc(TeamMessage.created_at))
        .limit(1)
    )
    result = await db.execute(q)
    msg = result.scalar_one_or_none()
    return {"pinned": msg.to_dict() if msg else None}


@router.get("/team")
async def get_team_chat_history(
    db: AsyncSession = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
    limit: int = Query(50, ge=1, le=100)
):
    # Get user's department
    result = await db.execute(select(Employee).where(Employee.id == current_user_id))
    me = result.scalar_one_or_none()
    if not me or not me.department:
        return {"messages": []}

    # Fetch recent messages for this department
    q = (
        select(TeamMessage)
        .options(selectinload(TeamMessage.sender), selectinload(TeamMessage.pinner))
        .where(TeamMessage.department == me.department)
        .order_by(desc(TeamMessage.created_at))
        .limit(limit)
    )
    result = await db.execute(q)
    messages = result.scalars().all()

    # Return in chronological order
    return {"messages": [m.to_dict() for m in reversed(messages)]}


@router.post("/team")
async def post_team_message(
    data: ChatMessageCreate,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id)
):
    from ..core.websocket import manager

    # Get user's department
    result = await db.execute(select(Employee).where(Employee.id == current_user_id))
    me = result.scalar_one_or_none()
    if not me or not me.department:
        raise HTTPException(status_code=400, detail="User does not have a department")

    # Create message
    msg = TeamMessage(
        sender_id=me.id,
        department=me.department,
        content=data.content
    )
    db.add(msg)
    await db.commit()
    await db.refresh(msg)

    msg.sender = me
    msg.pinner = None
    msg_data = msg.to_dict()

    # Broadcast to department via websocket
    q_dept = select(Employee.id).where(Employee.department == me.department)
    res_dept = await db.execute(q_dept)
    dept_ids = [str(r[0]) for r in res_dept.fetchall()]

    payload = {"type": "team_chat", "message": msg_data}
    for uid in dept_ids:
        await manager.send_personal_message(payload, uid)

    return {"message": "Sent", "data": msg_data}


@router.post("/team/pin/{message_id}")
async def pin_team_message(
    message_id: str,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id)
):
    """Pin or unpin a message in the department chat. Any department member can pin."""
    from ..core.websocket import manager

    try:
        msg_uuid = uuid.UUID(message_id)
        me_uuid = uuid.UUID(current_user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID")

    result = await db.execute(
        select(TeamMessage)
        .options(selectinload(TeamMessage.sender), selectinload(TeamMessage.pinner))
        .where(TeamMessage.id == msg_uuid)
    )
    msg = result.scalar_one_or_none()
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")

    # Verify user is in the same department
    res_me = await db.execute(select(Employee).where(Employee.id == me_uuid))
    me = res_me.scalar_one_or_none()
    if not me or me.department != msg.department:
        raise HTTPException(status_code=403, detail="Not in this department")

    # Unpin any currently pinned messages in the department first
    from sqlalchemy import update
    await db.execute(
        update(TeamMessage)
        .where(TeamMessage.department == msg.department, TeamMessage.is_pinned == True)
        .values(is_pinned=False, pinned_by=None)
    )

    # Toggle: if it was already pinned by us, just unpin it
    toggle_on = not msg.is_pinned
    if toggle_on:
        msg.is_pinned = True
        msg.pinned_by = me_uuid
    # else: leave it unpinned (already done above)

    await db.commit()
    await db.refresh(msg)
    msg_data = msg.to_dict()

    # Broadcast pin update to department
    q_dept = select(Employee.id).where(Employee.department == me.department)
    res_dept = await db.execute(q_dept)
    dept_ids = [str(r[0]) for r in res_dept.fetchall()]

    payload = {"type": "pin_update", "pinned": msg_data if toggle_on else None}
    for uid in dept_ids:
        await manager.send_personal_message(payload, uid)

    return {"pinned": msg_data if toggle_on else None}

