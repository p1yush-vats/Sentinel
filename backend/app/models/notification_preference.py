import uuid
from sqlalchemy import Column, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from ..core.database import Base


class NotificationPreference(Base):
    __tablename__ = "notification_preferences"

    id                  = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    employee_id         = Column(UUID(as_uuid=True), ForeignKey('employees.id', ondelete='CASCADE'), nullable=False, unique=True)
    email_notifications = Column(Boolean, default=True)
    break_reminders     = Column(Boolean, default=True)
    weekly_reports      = Column(Boolean, default=False)
    abnormality_alerts  = Column(Boolean, default=True)
    created_at          = Column(DateTime, server_default=func.now())
    updated_at          = Column(DateTime, server_default=func.now(), onupdate=func.now())

    def to_dict(self):
        return {
            "id":                  str(self.id),
            "employee_id":         str(self.employee_id),
            "email_notifications": self.email_notifications,
            "break_reminders":     self.break_reminders,
            "weekly_reports":      self.weekly_reports,
            "abnormality_alerts":  self.abnormality_alerts,
            "updated_at":          self.updated_at.isoformat() if self.updated_at else None,
        }
