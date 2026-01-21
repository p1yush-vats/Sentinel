"""
Abnormality Model - Detected suspicious patterns
"""
from sqlalchemy import Column, String, Boolean, DateTime, Numeric, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
import uuid

from ..core.database import Base


class Abnormality(Base):
    """Abnormality detection table"""
    __tablename__ = "abnormalities"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey('sessions.id', ondelete='CASCADE'), nullable=False, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey('employees.id', ondelete='CASCADE'), nullable=False, index=True)
    abnormality_type = Column(String(100), nullable=False, index=True)
    confidence_score = Column(Numeric(5, 2), nullable=False)
    detected_at = Column(DateTime(timezone=True), nullable=False)
    
    # FIXED: Renamed from 'metadata' to 'detection_metadata' to avoid SQLAlchemy reserved word
    detection_metadata = Column('metadata', JSONB, nullable=True)
    
    reviewed = Column(Boolean, default=False, index=True)
    reviewed_by = Column(UUID(as_uuid=True), ForeignKey('employees.id'), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    review_decision = Column(String(50), nullable=True)  # dismissed, warning_issued, escalated
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "session_id": str(self.session_id),
            "employee_id": str(self.employee_id),
            "abnormality_type": self.abnormality_type,
            "confidence_score": float(self.confidence_score),
            "detected_at": self.detected_at.isoformat() if self.detected_at else None,
            "metadata": self.detection_metadata,  # Return as 'metadata' for API
            "reviewed": self.reviewed,
            "reviewed_by": str(self.reviewed_by) if self.reviewed_by else None,
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
            "review_decision": self.review_decision,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class AdminAction(Base):
    """Admin actions audit trail"""
    __tablename__ = "admin_actions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    admin_id = Column(UUID(as_uuid=True), ForeignKey('employees.id'), nullable=False, index=True)
    employee_id = Column(UUID(as_uuid=True), ForeignKey('employees.id'), nullable=False, index=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey('sessions.id'), nullable=True)
    action_type = Column(String(100), nullable=False, index=True)
    justification = Column(Text, nullable=False)
    
    # FIXED: Renamed from 'metadata' to 'action_metadata'
    action_metadata = Column('metadata', JSONB, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def to_dict(self):
        return {
            "id": str(self.id),
            "admin_id": str(self.admin_id),
            "employee_id": str(self.employee_id),
            "session_id": str(self.session_id) if self.session_id else None,
            "action_type": self.action_type,
            "justification": self.justification,
            "metadata": self.action_metadata,  # Return as 'metadata' for API
            "created_at": self.created_at.isoformat() if self.created_at else None
        }