import uuid
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from ..core.database import Base


class WorkRule(Base):
    __tablename__ = "work_rules"

    id                        = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    department                = Column(String(100), nullable=True)
    employee_id               = Column(UUID(as_uuid=True), ForeignKey('employees.id'), nullable=True)
    work_minutes_per_hour     = Column(Integer, default=50)
    break_minutes_per_hour    = Column(Integer, default=10)
    lunch_duration_minutes    = Column(Integer, default=30)
    daily_work_target_minutes = Column(Integer, default=400)
    detection_sensitivity     = Column(String(20), default='medium')
    created_at                = Column(DateTime, server_default=func.now())
    updated_at                = Column(DateTime, server_default=func.now(), onupdate=func.now())

    def to_dict(self):
        return {
            "id":                        str(self.id),
            "department":                self.department,
            "employee_id":               str(self.employee_id) if self.employee_id else None,
            "work_minutes_per_hour":     self.work_minutes_per_hour,
            "break_minutes_per_hour":    self.break_minutes_per_hour,
            "lunch_duration_minutes":    self.lunch_duration_minutes,
            "daily_work_target_minutes": self.daily_work_target_minutes,
            "detection_sensitivity":     self.detection_sensitivity,
            "created_at":                self.created_at.isoformat() if self.created_at else None,
            "updated_at":                self.updated_at.isoformat() if self.updated_at else None,
        }
