import uuid
from sqlalchemy import Column, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.types import Numeric
from sqlalchemy.sql import func
from ..core.database import Base


class ProductivityMetric(Base):
    __tablename__ = "productivity_metrics"

    id                        = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id                = Column(UUID(as_uuid=True), ForeignKey('sessions.id', ondelete='CASCADE'), nullable=False)
    employee_id               = Column(UUID(as_uuid=True), ForeignKey('employees.id', ondelete='CASCADE'), nullable=False)
    hour_of_day               = Column(Integer, nullable=True)
    activity_intensity        = Column(Numeric(5, 2), nullable=True)
    break_effectiveness_score = Column(Numeric(5, 2), nullable=True)
    keystroke_count           = Column(Integer, nullable=True)
    mouse_movement_count      = Column(Integer, nullable=True)
    paste_count               = Column(Integer, nullable=True)
    recorded_at               = Column(DateTime, nullable=False)
    created_at                = Column(DateTime, server_default=func.now())

    def to_dict(self):
        return {
            "id":                        str(self.id),
            "session_id":                str(self.session_id),
            "employee_id":               str(self.employee_id),
            "hour_of_day":               self.hour_of_day,
            "activity_intensity":        float(self.activity_intensity) if self.activity_intensity else None,
            "break_effectiveness_score": float(self.break_effectiveness_score) if self.break_effectiveness_score else None,
            "keystroke_count":           self.keystroke_count,
            "mouse_movement_count":      self.mouse_movement_count,
            "paste_count":               self.paste_count,
            "recorded_at":               self.recorded_at.isoformat() if self.recorded_at else None,
        }
