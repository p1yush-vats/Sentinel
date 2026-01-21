"""
Session Model - Work session tracking
"""
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from ..core.database import Base


class Session(Base):
    """Work session table model"""
    __tablename__ = "sessions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id = Column(UUID(as_uuid=True), ForeignKey('employees.id', ondelete='CASCADE'), nullable=False, index=True)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=True)
    total_work_minutes = Column(Integer, default=0)
    total_break_minutes = Column(Integer, default=0)
    lunch_taken = Column(Boolean, default=False)
    status = Column(String(50), default='active')  # active, completed, flagged, contested
    session_quality_score = Column(Numeric(5, 2), nullable=True)
    risk_score = Column(Numeric(5, 2), default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": str(self.id),
            "employee_id": str(self.employee_id),
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "total_work_minutes": self.total_work_minutes,
            "total_break_minutes": self.total_break_minutes,
            "lunch_taken": self.lunch_taken,
            "status": self.status,
            "session_quality_score": float(self.session_quality_score) if self.session_quality_score else None,
            "risk_score": float(self.risk_score) if self.risk_score else 0,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class WorkTimeLog(Base):
    """Work time logs - granular tracking"""
    __tablename__ = "work_time_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey('sessions.id', ondelete='CASCADE'), nullable=False, index=True)
    log_type = Column(String(50), nullable=False)  # work, break, lunch
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=True)
    duration_minutes = Column(Integer, nullable=True)
    break_token_used = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "session_id": str(self.session_id),
            "log_type": self.log_type,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_minutes": self.duration_minutes,
            "break_token_used": self.break_token_used
        }