import uuid
from datetime import datetime, timezone, date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from ..core.database import get_db
from ..core.security import get_current_user_id, RoleChecker, get_current_user_email
from ..models.leave import Leave
from ..models.employee import Employee
from .audit_log import write_audit
from ..tasks.email_tasks import send_leave_decision

router = APIRouter()


def now_utc():
    return datetime.now(timezone.utc)


class LeaveCreate(BaseModel):
    leave_type:          str
    from_date:           date
    to_date:             date
    days_requested:      int
    reason:              str
    medical_certificate: Optional[str] = None


class LeaveReview(BaseModel):
    status:         str   # approved | rejected | needs_info
    admin_response: str

class LeaveComment(BaseModel):
    message: str


@router.post("/")
async def apply_leave(
    data:    LeaveCreate,
    user_id: str = Depends(get_current_user_id),
    db:      AsyncSession = Depends(get_db)
):
    valid_types = ['EL', 'CL', 'SL', 'ML']
    if data.leave_type not in valid_types:
        raise HTTPException(status_code=400, detail=f"Invalid leave type. Must be one of {valid_types}")
    if data.from_date > data.to_date:
        raise HTTPException(status_code=400, detail="From date must be before to date")
    if data.days_requested < 1:
        raise HTTPException(status_code=400, detail="Days requested must be at least 1")

    leave = Leave(
        employee_id    = uuid.UUID(user_id),
        leave_type     = data.leave_type,
        from_date      = data.from_date,
        to_date        = data.to_date,
        days_requested      = data.days_requested,
        reason              = data.reason,
        medical_certificate = data.medical_certificate,
        status              = 'pending',
    )
    db.add(leave)
    await db.commit()
    await db.refresh(leave)

    await write_audit(db, "leave_applied", "apply_leave",
        actor_id=user_id, target_id=str(leave.id), target_type="leave",
        metadata={"leave_type": data.leave_type, "days": data.days_requested, "from": str(data.from_date)})
    await db.commit()

    return {"message": "Leave application submitted", "leave": leave.to_dict()}


@router.get("/")
async def get_my_leaves(
    user_id: str = Depends(get_current_user_id),
    db:      AsyncSession = Depends(get_db),
    status:  Optional[str] = None,
    limit:   int = Query(50, ge=1, le=200),
):
    query = select(Leave).where(Leave.employee_id == uuid.UUID(user_id))
    if status:
        query = query.where(Leave.status == status)
    query = query.order_by(desc(Leave.created_at)).limit(limit)
    result = await db.execute(query)
    leaves = result.scalars().all()
    return {"leaves": [l.to_dict() for l in leaves], "total": len(leaves)}


@router.get("/team/")
async def get_team_leaves(
    user_id: str = Depends(get_current_user_id),
    db:      AsyncSession = Depends(get_db),
):
    """Get approved leaves for all employees (for team calendar)"""
    query = select(Leave, Employee).join(
        Employee, Leave.employee_id == Employee.id
    ).where(
        Leave.status == 'approved'
    ).order_by(desc(Leave.from_date)).limit(100)

    result = await db.execute(query)
    rows = result.all()

    leaves = []
    for leave, emp in rows:
        d = leave.to_dict()
        d['employee_name'] = emp.full_name
        d['department'] = emp.department
        leaves.append(d)

    return {"leaves": leaves, "total": len(leaves)}


@router.get("/all", dependencies=[Depends(RoleChecker(["admin"]))])
async def get_all_leaves(
    db:     AsyncSession = Depends(get_db),
    status: Optional[str] = None,
    limit:  int = Query(200, ge=1, le=500),
):
    query = select(Leave)
    if status:
        query = query.where(Leave.status == status)
    query = query.order_by(desc(Leave.created_at)).limit(limit)
    result = await db.execute(query)
    leaves = result.scalars().all()
    return {"leaves": [l.to_dict() for l in leaves], "total": len(leaves)}


@router.post("/{leave_id}/review", dependencies=[Depends(RoleChecker(["admin"]))])
async def review_leave(
    leave_id: str,
    review:   LeaveReview,
    background_tasks: BackgroundTasks,
    admin_id: str = Depends(get_current_user_id),
    admin_email: str = Depends(get_current_user_email),
    db:       AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Leave).where(Leave.id == leave_id))
    leave = result.scalar_one_or_none()
    if not leave:
        raise HTTPException(status_code=404, detail="Leave not found")
    if leave.status not in ('pending', 'needs_info'):
        raise HTTPException(status_code=400, detail="Leave already reviewed or not pending")
    if review.status not in ('approved', 'rejected', 'needs_info'):
        raise HTTPException(status_code=400, detail="Status must be approved, rejected, or needs_info")

    employee = await db.scalar(select(Employee).where(Employee.id == leave.employee_id))
    if admin_email == "demo-admin@sentinel.com":
        if employee and not employee.email.startswith("demo-"):
            raise HTTPException(status_code=403, detail="Demo accounts cannot process real leaves")

    leave.status         = review.status
    leave.admin_response = review.admin_response
    leave.reviewed_by    = uuid.UUID(admin_id)
    leave.reviewed_at    = now_utc()
    
    if review.status == 'needs_info' and review.admin_response:
        comments = list(leave.comments or [])
        comments.append({
            "sender": "admin",
            "message": review.admin_response,
            "timestamp": now_utc().isoformat()
        })
        leave.comments = comments

    await db.commit()
    await db.refresh(leave)

    await write_audit(db, "leave_reviewed", f"leave_{review.status}",
        actor_id=admin_id, target_id=str(leave.employee_id), target_type="leave",
        metadata={"leave_id": leave_id, "decision": review.status, "leave_type": leave.leave_type})
    await db.commit()

    if employee:
        background_tasks.add_task(send_leave_decision, employee.email, employee.full_name, review.status, review.admin_response)

    return {"message": "Leave reviewed", "leave": leave.to_dict()}


@router.delete("/{leave_id}")
async def cancel_leave(
    leave_id: str,
    user_id:  str = Depends(get_current_user_id),
    db:       AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Leave).where(Leave.id == leave_id))
    leave = result.scalar_one_or_none()
    if not leave:
        raise HTTPException(status_code=404, detail="Leave not found")
    if str(leave.employee_id) != user_id:
        raise HTTPException(status_code=403, detail="Not your leave")
    if leave.status != 'pending':
        raise HTTPException(status_code=400, detail="Can only cancel pending leaves")

    await db.delete(leave)
    await db.commit()
    return {"message": "Leave cancelled"}

@router.post("/{leave_id}/comment")
async def add_comment(
    leave_id: str,
    comment:  LeaveComment,
    user_id:  str = Depends(get_current_user_id),
    db:       AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Leave).where(Leave.id == leave_id))
    leave = result.scalar_one_or_none()
    if not leave:
        raise HTTPException(status_code=404, detail="Leave not found")
        
    is_owner = str(leave.employee_id) == user_id
    result = await db.execute(select(Employee).where(Employee.id == user_id))
    emp = result.scalar_one_or_none()
    if not emp or (not is_owner and emp.role not in ['admin', 'super_admin']):
        raise HTTPException(status_code=403, detail="Forbidden")

    sender = "employee" if is_owner else "admin"
    
    comments = list(leave.comments or [])
    comments.append({
        "sender": sender,
        "message": comment.message,
        "timestamp": now_utc().isoformat()
    })
    leave.comments = comments
    
    if is_owner and leave.status == 'needs_info':
        leave.status = 'pending'

    await db.commit()
    await db.refresh(leave)
    return {"message": "Comment added", "leave": leave.to_dict()}
