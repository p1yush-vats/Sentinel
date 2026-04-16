import uuid
from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET
from sqlalchemy.sql import func
from ..core.database import Base


class AuditLog(Base):
    __tablename__ = "audit_log"

    id             = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_type     = Column(String(100), nullable=False)
    actor_id       = Column(UUID(as_uuid=True), ForeignKey('employees.id'), nullable=True)
    target_id      = Column(UUID(as_uuid=True), nullable=True)
    target_type    = Column(String(50), nullable=True)
    action         = Column(String(100), nullable=False)
    event_metadata = Column("metadata", JSONB, nullable=True)   # column stays "metadata" in DB
    ip_address     = Column(INET, nullable=True)
    user_agent     = Column(Text, nullable=True)
    created_at     = Column(DateTime, server_default=func.now())

    def to_dict(self):
        return {
            "id":          str(self.id),
            "event_type":  self.event_type,
            "actor_id":    str(self.actor_id) if self.actor_id else None,
            "target_id":   str(self.target_id) if self.target_id else None,
            "target_type": self.target_type,
            "action":      self.action,
            "metadata":    self.event_metadata,
            "ip_address":  str(self.ip_address) if self.ip_address else None,
            "user_agent":  self.user_agent,
            "created_at":  self.created_at.isoformat() if self.created_at else None,
        }