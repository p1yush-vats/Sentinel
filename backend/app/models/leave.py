# backend/app/models/leave.py
import uuid
from sqlalchemy import Column, String, Integer, Text, Date, DateTime, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from ..core.database import Base


class Leave(Base):
    __tablename__ = "leaves"

    id             = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id    = Column(UUID(as_uuid=True), ForeignKey('employees.id', ondelete='CASCADE'), nullable=False, index=True)
    leave_type     = Column(String(10), nullable=False)   # EL, CL, SL, ML
    from_date      = Column(Date, nullable=False)
    to_date        = Column(Date, nullable=False)
    days_requested = Column(Integer, nullable=False, default=1)
    reason         = Column(Text, nullable=False)
    status         = Column(String(20), default='pending')  # pending, approved, rejected
    reviewed_by    = Column(UUID(as_uuid=True), ForeignKey('employees.id'), nullable=True)
    reviewed_at    = Column(DateTime(timezone=True), nullable=True)
    admin_response     = Column(Text, nullable=True)
    medical_certificate = Column(Text, nullable=True)
    comments           = Column(JSONB, nullable=True, default=list)
    created_at     = Column(DateTime(timezone=True), server_default=func.now())
    updated_at     = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def to_dict(self):
        return {
            "id":             str(self.id),
            "employee_id":    str(self.employee_id),
            "leave_type":     self.leave_type,
            "from_date":      str(self.from_date),
            "to_date":        str(self.to_date),
            "days_requested": self.days_requested,
            "reason":         self.reason,
            "status":         self.status,
            "reviewed_by":    str(self.reviewed_by) if self.reviewed_by else None,
            "reviewed_at":    self.reviewed_at.isoformat() if self.reviewed_at else None,
            "admin_response":      self.admin_response,
            "medical_certificate": self.medical_certificate,
            "comments":            self.comments or [],
            "created_at":     self.created_at.isoformat() if self.created_at else None,
        }
