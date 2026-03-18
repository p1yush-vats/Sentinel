import uuid
from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from ..core.database import Base


class Appeal(Base):
    __tablename__ = "appeals"

    id             = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id    = Column(UUID(as_uuid=True), ForeignKey('employees.id', ondelete='CASCADE'), nullable=False)
    session_id     = Column(UUID(as_uuid=True), ForeignKey('sessions.id',  ondelete='CASCADE'), nullable=False)
    abnormality_id = Column(UUID(as_uuid=True), ForeignKey('abnormalities.id'), nullable=True)
    reason         = Column(Text, nullable=False)
    status         = Column(String(50), default='pending')
    reviewed_by    = Column(UUID(as_uuid=True), ForeignKey('employees.id'), nullable=True)
    reviewed_at    = Column(DateTime(timezone=True), nullable=True)
    admin_response = Column(Text, nullable=True)
    created_at     = Column(DateTime(timezone=True), server_default=func.now())

    def to_dict(self):
        return {
            "id":             str(self.id),
            "employee_id":    str(self.employee_id),
            "session_id":     str(self.session_id),
            "abnormality_id": str(self.abnormality_id) if self.abnormality_id else None,
            "reason":         self.reason,
            "status":         self.status,
            "reviewed_by":    str(self.reviewed_by) if self.reviewed_by else None,
            "reviewed_at":    self.reviewed_at.isoformat() if self.reviewed_at else None,
            "admin_response": self.admin_response,
            "created_at":     self.created_at.isoformat() if self.created_at else None,
        }
