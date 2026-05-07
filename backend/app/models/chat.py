import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from ..core.database import Base

class TeamMessage(Base):
    __tablename__ = "team_messages"

    id         = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sender_id  = Column(UUID(as_uuid=True), ForeignKey("employees.id", ondelete="CASCADE"), nullable=False)
    department = Column(String(100), nullable=False, index=True)
    content    = Column(Text, nullable=False)
    is_pinned  = Column(Boolean, default=False, nullable=False)
    pinned_by  = Column(UUID(as_uuid=True), ForeignKey("employees.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    sender    = relationship("Employee", foreign_keys=[sender_id])
    pinner    = relationship("Employee", foreign_keys=[pinned_by])

    def to_dict(self):
        return {
            "id":           str(self.id),
            "sender_id":    str(self.sender_id),
            "department":   self.department,
            "content":      self.content,
            "is_pinned":    self.is_pinned,
            "pinned_by":    str(self.pinned_by) if self.pinned_by else None,
            "created_at":   self.created_at.isoformat() if self.created_at else None,
            "sender_name":  self.sender.full_name if self.sender else "Unknown",
            "sender_avatar": self.sender.avatar_url if self.sender else None,
        }


class DirectMessage(Base):
    __tablename__ = "direct_messages"

    id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sender_id   = Column(UUID(as_uuid=True), ForeignKey("employees.id", ondelete="CASCADE"), nullable=False)
    receiver_id = Column(UUID(as_uuid=True), ForeignKey("employees.id", ondelete="CASCADE"), nullable=False)
    content     = Column(Text, nullable=False)
    is_read     = Column(Boolean, default=False, nullable=False)
    created_at  = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    sender   = relationship("Employee", foreign_keys=[sender_id])
    receiver = relationship("Employee", foreign_keys=[receiver_id])

    def to_dict(self):
        return {
            "id":             str(self.id),
            "sender_id":      str(self.sender_id),
            "receiver_id":    str(self.receiver_id),
            "content":        self.content,
            "is_read":        self.is_read,
            "created_at":     self.created_at.isoformat() if self.created_at else None,
            "sender_name":    self.sender.full_name if self.sender else "Unknown",
            "sender_avatar":  self.sender.avatar_url if self.sender else None,
            "receiver_name":  self.receiver.full_name if self.receiver else "Unknown",
        }
