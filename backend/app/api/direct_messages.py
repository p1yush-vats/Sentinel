from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, or_, and_, update
from sqlalchemy.orm import selectinload
from pydantic import BaseModel
import uuid

from ..core.database import get_db
from ..core.security import get_current_user_id
from ..models.employee import Employee
from ..models.chat import DirectMessage

router = APIRouter()


class DMCreate(BaseModel):
    content: str


@router.get("/unread/count")
async def get_unread_count(
    db: AsyncSession = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id)
):
    """Count unread DMs per sender for the current user."""
    try:
        me_uuid = uuid.UUID(current_user_id)
    except ValueError:
        return {"unread": {}}

    from sqlalchemy import func
    q = (
        select(DirectMessage.sender_id, func.count().label("count"))
        .where(
            DirectMessage.receiver_id == me_uuid,
            DirectMessage.is_read == False
        )
        .group_by(DirectMessage.sender_id)
    )
    result = await db.execute(q)
    rows = result.fetchall()
    return {"unread": {str(r[0]): r[1] for r in rows}}


@router.get("/{partner_id}")
async def get_dm_history(
    partner_id: str,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id),
    limit: int = Query(50, ge=1, le=200)
):
    """Fetch DM history between the current user and a partner."""
    try:
        me_uuid = uuid.UUID(current_user_id)
        partner_uuid = uuid.UUID(partner_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID")

    q = (
        select(DirectMessage)
        .options(selectinload(DirectMessage.sender), selectinload(DirectMessage.receiver))
        .where(
            or_(
                and_(DirectMessage.sender_id == me_uuid, DirectMessage.receiver_id == partner_uuid),
                and_(DirectMessage.sender_id == partner_uuid, DirectMessage.receiver_id == me_uuid),
            )
        )
        .order_by(desc(DirectMessage.created_at))
        .limit(limit)
    )
    result = await db.execute(q)
    messages = result.scalars().all()

    # Mark unread messages from partner as read
    await db.execute(
        update(DirectMessage)
        .where(
            DirectMessage.sender_id == partner_uuid,
            DirectMessage.receiver_id == me_uuid,
            DirectMessage.is_read == False
        )
        .values(is_read=True)
    )
    await db.commit()

    return {"messages": [m.to_dict() for m in reversed(messages)]}


@router.post("/{partner_id}")
async def send_dm(
    partner_id: str,
    data: DMCreate,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id)
):
    """Send a direct message to a partner."""
    from ..core.websocket import manager

    try:
        me_uuid = uuid.UUID(current_user_id)
        partner_uuid = uuid.UUID(partner_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID")

    # Fetch both users
    result = await db.execute(select(Employee).where(Employee.id == me_uuid))
    me = result.scalar_one_or_none()
    if not me:
        raise HTTPException(status_code=404, detail="Sender not found")

    result = await db.execute(select(Employee).where(Employee.id == partner_uuid))
    partner = result.scalar_one_or_none()
    if not partner:
        raise HTTPException(status_code=404, detail="Recipient not found")

    msg = DirectMessage(
        sender_id=me_uuid,
        receiver_id=partner_uuid,
        content=data.content
    )
    db.add(msg)
    await db.commit()
    await db.refresh(msg)

    msg.sender = me
    msg.receiver = partner
    msg_data = msg.to_dict()

    # Push to receiver and sender via WebSocket
    payload = {"type": "direct_message", "message": msg_data}
    await manager.send_personal_message(payload, partner_id)
    await manager.send_personal_message(payload, current_user_id)

    return {"message": "Sent", "data": msg_data}

