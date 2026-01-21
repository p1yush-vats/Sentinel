"""
Employees API Endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from pydantic import BaseModel, EmailStr
from typing import Optional

from ..core.database import get_db
from ..core.security import get_current_user_id, RoleChecker, get_password_hash
from ..models.employee import Employee

router = APIRouter()


# Schemas
class EmployeeCreate(BaseModel):
    """Create employee"""
    email: EmailStr
    password: str
    full_name: str
    department: Optional[str] = None
    role: str = "employee"


class EmployeeUpdate(BaseModel):
    """Update employee"""
    full_name: Optional[str] = None
    department: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None


@router.get("/", dependencies=[Depends(RoleChecker(["admin"]))])
async def get_employees(
    db: AsyncSession = Depends(get_db),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    department: Optional[str] = None,
    is_active: Optional[bool] = None
):
    """Get all employees (Admin only)"""
    query = select(Employee)
    
    if department:
        query = query.where(Employee.department == department)
    if is_active is not None:
        query = query.where(Employee.is_active == is_active)
    
    query = query.order_by(desc(Employee.created_at)).limit(limit).offset(offset)
    
    result = await db.execute(query)
    employees = result.scalars().all()
    
    return {
        "employees": [e.to_dict() for e in employees],
        "total": len(employees)
    }


@router.get("/{employee_id}")
async def get_employee(
    employee_id: str,
    db: AsyncSession = Depends(get_db),
    current_user_id: str = Depends(get_current_user_id)
):
    """Get employee details"""
    result = await db.execute(
        select(Employee).where(Employee.id == employee_id)
    )
    employee = result.scalar_one_or_none()
    
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    return employee.to_dict()


@router.post("/", dependencies=[Depends(RoleChecker(["admin"]))])
async def create_employee(
    employee_data: EmployeeCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create new employee (Admin only)"""
    # Check if email exists
    result = await db.execute(
        select(Employee).where(Employee.email == employee_data.email)
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create employee
    new_employee = Employee(
        email=employee_data.email,
        password_hash=get_password_hash(employee_data.password),
        full_name=employee_data.full_name,
        department=employee_data.department,
        role=employee_data.role,
        is_active=True
    )
    
    db.add(new_employee)
    await db.commit()
    await db.refresh(new_employee)
    
    return {
        "message": "Employee created successfully",
        "employee": new_employee.to_dict()
    }


@router.patch("/{employee_id}", dependencies=[Depends(RoleChecker(["admin"]))])
async def update_employee(
    employee_id: str,
    employee_data: EmployeeUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Update employee (Admin only)"""
    result = await db.execute(
        select(Employee).where(Employee.id == employee_id)
    )
    employee = result.scalar_one_or_none()
    
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Update fields
    if employee_data.full_name is not None:
        employee.full_name = employee_data.full_name
    if employee_data.department is not None:
        employee.department = employee_data.department
    if employee_data.role is not None:
        employee.role = employee_data.role
    if employee_data.is_active is not None:
        employee.is_active = employee_data.is_active
    
    await db.commit()
    await db.refresh(employee)
    
    return {
        "message": "Employee updated successfully",
        "employee": employee.to_dict()
    }


@router.delete("/{employee_id}", dependencies=[Depends(RoleChecker(["admin"]))])
async def delete_employee(
    employee_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete employee (Admin only)"""
    result = await db.execute(
        select(Employee).where(Employee.id == employee_id)
    )
    employee = result.scalar_one_or_none()
    
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    await db.delete(employee)
    await db.commit()
    
    return {"message": "Employee deleted successfully"}