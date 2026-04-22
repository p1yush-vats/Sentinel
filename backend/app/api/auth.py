from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr
from datetime import timedelta

from ..core.database import get_db
from ..core.security import (
    verify_password, get_password_hash,
    create_access_token, create_refresh_token,
    decode_token, get_current_user_id
)
from ..core.config import settings
from ..models.employee import Employee
from .audit_log import write_audit

router = APIRouter()


class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: dict

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    department: str | None = None

class TokenRefreshRequest(BaseModel):
    refresh_token: str

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


@router.post("/login", response_model=LoginResponse)
async def login(credentials: LoginRequest, request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Employee).where(Employee.email == credentials.email))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")

    if not verify_password(credentials.password, user.password_hash):
        await write_audit(db, "login_failed", "login_attempt_failed",
            target_id=str(user.id), target_type="employee",
            metadata={"email": credentials.email},
            ip_address=request.client.host if request.client else None)
        await db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account is inactive")

    token_data = {"sub": str(user.id), "email": user.email, "role": user.role}
    access_token  = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    await write_audit(db, "user_login", "login",
        actor_id=str(user.id), target_id=str(user.id), target_type="employee",
        metadata={"role": user.role},
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"))
    await db.commit()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": user.to_dict()
    }


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(user_data: RegisterRequest, request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Employee).where(Employee.email == user_data.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    new_employee = Employee(
        email=user_data.email,
        password_hash=get_password_hash(user_data.password),
        full_name=user_data.full_name,
        role='employee',
        department=user_data.department,
        is_active=True
    )
    db.add(new_employee)
    await db.commit()
    await db.refresh(new_employee)

    await write_audit(db, "employee_registered", "register",
        target_id=str(new_employee.id), target_type="employee",
        metadata={"email": new_employee.email, "department": new_employee.department},
        ip_address=request.client.host if request.client else None)
    await db.commit()

    return {"message": "User registered successfully", "user": new_employee.to_dict()}


@router.post("/refresh")
async def refresh_token(request_data: TokenRefreshRequest):
    try:
        payload = decode_token(request_data.refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")
        token_data = {"sub": payload.get("sub"), "email": payload.get("email"), "role": payload.get("role")}
        new_access_token = create_access_token(token_data)
        return {"access_token": new_access_token, "token_type": "bearer"}
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")


@router.get("/me")
async def get_current_user(user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Employee).where(Employee.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user.to_dict()


@router.post("/change-password")
async def change_password(
    request_data: ChangePasswordRequest,
    request: Request,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Employee).where(Employee.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        
    # Protect demo accounts from being locked out by public users
    if user.email in ["demo-employee@sentinel.com", "demo-admin@sentinel.com"]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Demo accounts cannot change their passwords.")
        
    if not verify_password(request_data.current_password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect")

    user.password_hash = get_password_hash(request_data.new_password)
    await db.commit()

    await write_audit(db, "password_changed", "change_password",
        actor_id=str(user.id), target_id=str(user.id), target_type="employee",
        ip_address=request.client.host if request.client else None)
    await db.commit()

    return {"message": "Password changed successfully"}


@router.post("/logout")
async def logout(request: Request, user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    await write_audit(db, "user_logout", "logout",
        actor_id=user_id, target_id=user_id, target_type="employee",
        ip_address=request.client.host if request.client else None)
    await db.commit()
    return {"message": "Logged out successfully"}


@router.get("/validate-token")
async def validate_token(user_id: str = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Employee).where(Employee.id == user_id))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or inactive user")
    return {"valid": True, "user_id": str(user.id), "email": user.email, "role": user.role}