from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from pydantic import BaseModel, EmailStr
from typing import Optional

from ..core.database import get_db
from ..core.security import get_current_user_id, RoleChecker, get_password_hash
from ..models.employee import Employee
from ..models.session import Session
from ..models.abnormality import Abnormality

router = APIRouter()


# ── Risk helpers ──────────────────────────────────────────────────────────────

async def _compute_employee_risk(db: AsyncSession, employee_id: str) -> float:
    """
    Compute a recency-weighted risk score (0–100) from the employee's last 10
    completed sessions.

    Weighting:
      - The 5 most recent sessions count at 2× weight
      - The 5 older sessions count at 1× weight

    This makes the score responsive to recent behaviour: one bad session
    spikes the score quickly; a run of clean sessions brings it back down.
    Returns 0.0 if the employee has no sessions yet.
    """
    q = (
        select(Session.risk_score)
        .where(
            Session.employee_id == employee_id,
            Session.status == "completed",
            Session.risk_score.isnot(None),
        )
        .order_by(desc(Session.start_time))
        .limit(10)
    )
    result = await db.execute(q)
    scores = [float(row[0]) for row in result.fetchall()]

    if not scores:
        return 0.0

    # Recency weighting: index 0 = newest
    total_w, total_s = 0.0, 0.0
    for i, score in enumerate(scores):
        weight = 2.0 if i < 5 else 1.0
        total_s += score * weight
        total_w += weight

    return round(total_s / total_w, 1) if total_w > 0 else 0.0


async def _count_unreviewed_flags(db: AsyncSession, employee_id: str) -> int:
    """Return the count of unreviewed abnormality records for this employee."""
    q = select(func.count()).where(
        Abnormality.employee_id == employee_id,
        Abnormality.reviewed == False,  # noqa: E712
    )
    result = await db.execute(q)
    return result.scalar() or 0


class EmployeeCreate(BaseModel):
    email:         EmailStr
    password:      str
    full_name:     str
    department:    Optional[str] = None
    gender:        Optional[str] = None
    position:      Optional[str] = None
    phone:         Optional[str] = None
    employee_code: Optional[str] = None
    avatar_url:    Optional[str] = None
    role:          str = "employee"


class EmployeeUpdate(BaseModel):
    full_name:     Optional[str]  = None
    department:    Optional[str]  = None
    position:      Optional[str]  = None
    phone:         Optional[str]  = None
    employee_code: Optional[str]  = None
    gender:        Optional[str]  = None
    avatar_url:    Optional[str]  = None
    role:          Optional[str]  = None
    is_active:     Optional[bool] = None


@router.get("/", dependencies=[Depends(RoleChecker(["admin"]))])
async def get_employees(
    db:          AsyncSession = Depends(get_db),
    limit:       int          = Query(100, ge=1, le=500),
    offset:      int          = Query(0,   ge=0),
    department:  Optional[str]  = None,
    is_active:   Optional[bool] = None
):
    query = select(Employee)
    if department: query = query.where(Employee.department == department)
    if is_active is not None: query = query.where(Employee.is_active == is_active)
    query = query.order_by(desc(Employee.created_at)).limit(limit).offset(offset)
    result = await db.execute(query)
    employees = result.scalars().all()

    # Compute risk_score per employee from last 10 sessions
    employee_dicts = []
    for emp in employees:
        d = emp.to_dict()
        d["risk_score"] = await _compute_employee_risk(db, str(emp.id))
        employee_dicts.append(d)

    return {"employees": employee_dicts, "total": len(employee_dicts)}


@router.get("/{employee_id}")
async def get_employee(
    employee_id:     str,
    db:              AsyncSession = Depends(get_db),
    current_user_id: str         = Depends(get_current_user_id)
):
    result = await db.execute(select(Employee).where(Employee.id == employee_id))
    employee = result.scalar_one_or_none()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    d = employee.to_dict()
    d["risk_score"]       = await _compute_employee_risk(db, employee_id)
    d["unreviewed_flags"] = await _count_unreviewed_flags(db, employee_id)
    return d


@router.post("/", dependencies=[Depends(RoleChecker(["admin"]))])
async def create_employee(
    data: EmployeeCreate,
    db:   AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Employee).where(Employee.email == data.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    employee = Employee(
        email         = data.email,
        password_hash = get_password_hash(data.password),
        full_name     = data.full_name,
        department    = data.department,
        gender        = data.gender,
        position      = data.position,
        phone         = data.phone,
        employee_code = data.employee_code,
        avatar_url    = data.avatar_url,
        role          = data.role,
        is_active     = True,
    )
    db.add(employee)
    await db.commit()
    await db.refresh(employee)
    return {"message": "Employee created successfully", "employee": employee.to_dict()}


@router.patch("/{employee_id}", dependencies=[Depends(RoleChecker(["admin"]))])
async def update_employee(
    employee_id: str,
    data:        EmployeeUpdate,
    db:          AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Employee).where(Employee.id == employee_id))
    employee = result.scalar_one_or_none()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(employee, field, value)

    await db.commit()
    await db.refresh(employee)
    return {"message": "Employee updated successfully", "employee": employee.to_dict()}


@router.delete("/{employee_id}", dependencies=[Depends(RoleChecker(["admin"]))])
async def delete_employee(
    employee_id: str,
    db:          AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Employee).where(Employee.id == employee_id))
    employee = result.scalar_one_or_none()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    await db.delete(employee)
    await db.commit()
    return {"message": "Employee deleted successfully"}


class AdminAlert(BaseModel):
    title: str = "Admin Message"
    message: str
    severity: str = "crit"

@router.post("/{employee_id}/alert", dependencies=[Depends(RoleChecker(["admin"]))])
async def alert_employee(
    employee_id: str,
    data:        AdminAlert,
    db:          AsyncSession = Depends(get_db)
):
    from ..core.websocket import manager
    
    # Check if employee exists
    result = await db.execute(select(Employee).where(Employee.id == employee_id))
    employee = result.scalar_one_or_none()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    payload = {
        "type": "admin_alert",
        "title": data.title,
        "message": data.message,
        "severity": data.severity
    }
    
    # Push WS message
    await manager.send_personal_message(payload, employee_id)
    
    return {"message": "Alert sent"}