from sqlalchemy import Column, String, Boolean, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from ..core.database import Base


class Employee(Base):
    __tablename__ = "employees"

    id            = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email         = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name     = Column(String(255), nullable=False)
    role          = Column(String(50),  nullable=False, default='employee')
    department    = Column(String(100), nullable=True)
    position      = Column(String(100), nullable=True)
    phone         = Column(String(20),  nullable=True)
    employee_code = Column(String(20),  nullable=True)
    avatar_url    = Column(Text,        nullable=True)
    is_active     = Column(Boolean, default=True)
    created_at    = Column(DateTime(timezone=True), server_default=func.now())
    updated_at    = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def to_dict(self):
        return {
            "id":            str(self.id),
            "email":         self.email,
            "full_name":     self.full_name,
            "role":          self.role,
            "department":    self.department,
            "position":      self.position,
            "phone":         self.phone,
            "employee_code": self.employee_code,
            "avatar_url":    self.avatar_url,
            "is_active":     self.is_active,
            "created_at":    self.created_at.isoformat() if self.created_at else None,
            "updated_at":    self.updated_at.isoformat() if self.updated_at else None,
        }