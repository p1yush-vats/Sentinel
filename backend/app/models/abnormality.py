"""
Abnormality Model — ONE ROW PER SESSION

Design contract:
  - session_id has a UNIQUE constraint → enforced at DB level
  - All detection types for a session live in `detections` JSONB
  - `overall_severity` and `confidence_score` are rolling max values
    updated every time a new detection type is merged in
  - Backend route does an UPSERT (insert or merge), never a plain insert

detections JSONB shape:
{
  "rapid_paste": {
    "occurrences": 5,
    "confidence":  0.80,
    "severity":    "HIGH",
    "timestamps":  ["2026-03-06T12:24:29", "..."],
    "last_seen":   "2026-03-06T12:24:36"
  },
  "long_idle": {
    "occurrences": 1,
    "confidence":  0.98,
    "severity":    "CRITICAL",
    "timestamps":  ["2026-03-06T12:24:23"],
    "last_seen":   "2026-03-06T12:24:23"
  }
}
"""
from sqlalchemy import Column, String, Boolean, DateTime, Numeric, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
import uuid

from ..core.database import Base

SEVERITY_RANK = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}


class Abnormality(Base):
    __tablename__ = "abnormalities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # ONE ROW PER SESSION — unique constraint mirrors the DB schema
    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey('sessions.id', ondelete='CASCADE'),
        nullable=False,
        unique=True,
        index=True
    )
    employee_id = Column(
        UUID(as_uuid=True),
        ForeignKey('employees.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    # Rolling worst-case values across all detected types
    overall_severity = Column(String(20), nullable=False, default='LOW', index=True)
    confidence_score = Column(Numeric(5, 2), nullable=False, default=0)

    # All detections for this session — merged incrementally
    detections = Column(JSONB, nullable=False, default=dict)

    # Timing
    first_detected_at = Column(DateTime(timezone=True), nullable=False)
    last_updated_at   = Column(DateTime(timezone=True), nullable=False)

    # Admin review
    reviewed        = Column(Boolean, default=False, index=True)
    reviewed_by     = Column(UUID(as_uuid=True), ForeignKey('employees.id'), nullable=True)
    reviewed_at     = Column(DateTime(timezone=True), nullable=True)
    review_decision = Column(String(50), nullable=True)  # dismissed | warning_issued | escalated

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # ─────────────────────────────────────────────────────────
    # Helpers
    # ─────────────────────────────────────────────────────────

    @staticmethod
    def recalculate_overall(detections: dict) -> tuple[str, float]:
        """
        Given the full detections dict, return (overall_severity, max_confidence).
        Called after every merge so the top-level fields stay accurate.
        """
        if not detections:
            return "LOW", 0.0

        best_severity = "LOW"
        max_conf = 0.0

        for d in detections.values():
            sev = d.get("severity", "LOW")
            conf = float(d.get("confidence", 0))

            if SEVERITY_RANK.get(sev, 0) > SEVERITY_RANK.get(best_severity, 0):
                best_severity = sev
            if conf > max_conf:
                max_conf = conf

        return best_severity, round(max_conf, 2)

    def merge_detection(self, abnormality_type: str, detection_payload: dict):
        """
        Merge a new detection type into this record's detections JSONB.
        Updates overall_severity and confidence_score in place.
        """
        current = dict(self.detections or {})
        current[abnormality_type] = detection_payload
        self.detections = current

        severity, confidence = self.recalculate_overall(current)
        self.overall_severity = severity
        self.confidence_score = confidence

    def to_dict(self) -> dict:
        return {
            "id":               str(self.id),
            "session_id":       str(self.session_id),
            "employee_id":      str(self.employee_id),
            "overall_severity": self.overall_severity,
            "confidence_score": float(self.confidence_score),
            "detections":       self.detections or {},
            "first_detected_at": self.first_detected_at.isoformat() if self.first_detected_at else None,
            "last_updated_at":  self.last_updated_at.isoformat()   if self.last_updated_at   else None,
            "reviewed":         self.reviewed,
            "reviewed_by":      str(self.reviewed_by) if self.reviewed_by else None,
            "reviewed_at":      self.reviewed_at.isoformat() if self.reviewed_at else None,
            "review_decision":  self.review_decision,
            "created_at":       self.created_at.isoformat() if self.created_at else None,
        }


class AdminAction(Base):
    """Admin actions audit trail — unchanged"""
    __tablename__ = "admin_actions"

    id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    admin_id    = Column(UUID(as_uuid=True), ForeignKey('employees.id'), nullable=False)
    employee_id = Column(UUID(as_uuid=True), ForeignKey('employees.id'), nullable=False)
    session_id  = Column(UUID(as_uuid=True), ForeignKey('sessions.id'), nullable=True)
    action_type = Column(String(100), nullable=False)
    justification = Column(String(2000), nullable=False)
    action_metadata = Column('metadata', JSONB, nullable=True)
    created_at  = Column(DateTime(timezone=True), server_default=func.now())

    def to_dict(self) -> dict:
        return {
            "id":            str(self.id),
            "admin_id":      str(self.admin_id),
            "employee_id":   str(self.employee_id),
            "session_id":    str(self.session_id) if self.session_id else None,
            "action_type":   self.action_type,
            "justification": self.justification,
            "metadata":      self.action_metadata,
            "created_at":    self.created_at.isoformat() if self.created_at else None,
        }