import uuid
from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from ..core.database import Base


class Task(Base):
    __tablename__ = "tasks"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title           = Column(String(255), nullable=False)
    description     = Column(Text, nullable=True)
    assigned_to     = Column(UUID(as_uuid=True), ForeignKey('employees.id', ondelete='CASCADE'), nullable=False)
    assigned_by     = Column(UUID(as_uuid=True), ForeignKey('employees.id'), nullable=False)
    due_date        = Column(DateTime(timezone=True), nullable=True)
    priority        = Column(String(20), default='medium', nullable=False)   # low | medium | high | urgent
    status          = Column(String(20), default='pending', nullable=False)  # pending | in_progress | completed
    completion_note = Column(Text, nullable=True)
    created_at      = Column(DateTime(timezone=True), server_default=func.now())
    updated_at      = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    completed_at    = Column(DateTime(timezone=True), nullable=True)

    def to_dict(self):
        return {
            "id":              str(self.id),
            "title":           self.title,
            "description":     self.description,
            "assigned_to":     str(self.assigned_to),
            "assigned_by":     str(self.assigned_by),
            "due_date":        self.due_date.isoformat() if self.due_date else None,
            "priority":        self.priority,
            "status":          self.status,
            "completion_note": self.completion_note,
            "created_at":      self.created_at.isoformat() if self.created_at else None,
            "updated_at":      self.updated_at.isoformat() if self.updated_at else None,
            "completed_at":    self.completed_at.isoformat() if self.completed_at else None,
        }
