from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from pydantic import BaseModel, EmailStr
from typing import Optional

from ..core.database import get_db
from ..core.security import get_current_user_id, RoleChecker, get_password_hash, get_current_user_email
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
            Session.status != "active",
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
    emp_ids = [emp.id for emp in employees]

    # Bulk fetch sessions for all employees to solve N+1 connection latency
    emp_sessions = {}
    if emp_ids:
        q_sess = (
            select(Session.employee_id, Session.risk_score)
            .where(
                Session.employee_id.in_(emp_ids),
                Session.status != "active",
                Session.risk_score.isnot(None),
            )
            .order_by(desc(Session.start_time))
            # No limit here, we'll slice grouping in memory which is fast since it's just 1 query
        )
        s_result = await db.execute(q_sess)
        for row in s_result.fetchall():
            eid = str(row[0])
            score = float(row[1])
            if eid not in emp_sessions:
                emp_sessions[eid] = []
            if len(emp_sessions[eid]) < 10:
                emp_sessions[eid].append(score)

    employee_dicts = []
    for emp in employees:
        d = emp.to_dict()
        scores = emp_sessions.get(str(emp.id), [])
        if not scores:
            d["risk_score"] = 0.0
        else:
            total_w, total_s = 0.0, 0.0
            for i, score in enumerate(scores):
                weight = 2.0 if i < 5 else 1.0
                total_s += score * weight
                total_w += weight
            d["risk_score"] = round(total_s / total_w, 1)

        employee_dicts.append(d)

    return {"employees": employee_dicts, "total": len(employee_dicts)}


@router.get("/my-team")
async def get_my_team(
    db: AsyncSession = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id)
):
    # Get current user's department
    import uuid as _uuid
    try:
        me_uuid = _uuid.UUID(current_user_id)
    except ValueError:
        return {"team": []}
        
    result = await db.execute(select(Employee).where(Employee.id == me_uuid))
    me = result.scalar_one_or_none()
    if not me or not me.department:
        return {"team": []}
        
    # Get all active employees in same department except self
    q = select(Employee).where(
        Employee.department == me.department,
        Employee.is_active == True,
        Employee.id != me_uuid
    ).order_by(Employee.full_name)
    
    result = await db.execute(q)
    team_members = result.scalars().all()
    
    if not team_members:
        return {"team": []}
        
    team_ids = [emp.id for emp in team_members]
    
    # Check active session to check online status (Now using Websocket Manager!)
    from ..core.websocket import manager
    
    team_dicts = []
    for emp in team_members:
        team_dicts.append({
            "id": str(emp.id),
            "full_name": emp.full_name,
            "position": emp.position,
            "avatar_url": emp.avatar_url,
            "email": emp.email,
            "is_online": str(emp.id) in manager.active_connections
        })
        
    return {"team": team_dicts}


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
    db:   AsyncSession = Depends(get_db),
    admin_email: str = Depends(get_current_user_email)
):
    if admin_email == "demo-admin@sentinel.com":
        if not data.email.startswith("demo-temp-"):
            data.email = f"demo-temp-{data.email}"

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
    db:          AsyncSession = Depends(get_db),
    admin_email: str = Depends(get_current_user_email)
):
    result = await db.execute(select(Employee).where(Employee.id == employee_id))
    employee = result.scalar_one_or_none()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    if admin_email == "demo-admin@sentinel.com":
        if not employee.email.startswith("demo-"):
            raise HTTPException(status_code=403, detail="Demo accounts cannot modify real employees")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(employee, field, value)

    await db.commit()
    await db.refresh(employee)
    return {"message": "Employee updated successfully", "employee": employee.to_dict()}


@router.delete("/{employee_id}", dependencies=[Depends(RoleChecker(["admin"]))])
async def delete_employee(
    employee_id: str,
    db:          AsyncSession = Depends(get_db),
    admin_email: str = Depends(get_current_user_email)
):
    result = await db.execute(select(Employee).where(Employee.id == employee_id))
    employee = result.scalar_one_or_none()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
        
    if admin_email == "demo-admin@sentinel.com":
        if not employee.email.startswith("demo-"):
            raise HTTPException(status_code=403, detail="Demo accounts cannot delete real employees")
            
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


class ForcePasswordRequest(BaseModel):
    new_password: str

@router.post("/{employee_id}/force-password", dependencies=[Depends(RoleChecker(["admin"]))])
async def force_change_password(
    employee_id:  str,
    request_data: ForcePasswordRequest,
    admin_id:     str = Depends(get_current_user_id),
    db:           AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Employee).where(Employee.id == employee_id))
    employee = result.scalar_one_or_none()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    # Protect demo accounts from having their passwords changed
    if employee.email in ["demo-employee@sentinel.com", "demo-admin@sentinel.com"]:
        raise HTTPException(status_code=403, detail="Cannot force change password for demo accounts.")

    employee.password_hash = get_password_hash(request_data.new_password)
    await db.commit()

    from .audit_log import write_audit
    await write_audit(db, "password_force_reset", "admin_force_password_reset",
                      actor_id=admin_id, target_id=str(employee.id), target_type="employee",
                      metadata={"admin": admin_id})
    await db.commit()

    return {"message": "Password successfully forced"}