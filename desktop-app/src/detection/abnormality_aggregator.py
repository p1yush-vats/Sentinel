"""
Abnormality Aggregator — CLEAN REWRITE

Contract:
  - ONE row per session in SQLite (mirrors Supabase)
  - add_detection() updates in-memory state → writes full state to SQLite
  - NO HTTP calls, NO asyncio event loops, NO blocking
  - SyncClient background flush thread is the ONLY thing that touches HTTP
  - get_summary() / flush() called by main.py at session end

In-memory structure:
  self.detections = {
    "rapid_paste": {
      "occurrences": 5,
      "confidence":  0.80,
      "severity":    "HIGH",
      "timestamps":  ["2026-03-06T12:24:29", ...],
      "last_seen":   "2026-03-06T12:24:36"
    },
    "long_idle": { ... }
  }

  self.first_detected_at  → datetime of first ever detection this session
  self.overall_severity   → rolling max severity across all types
  self.confidence_score   → rolling max confidence across all types
"""
from datetime import datetime
from typing import Dict, Optional
import uuid


SEVERITY_RANK = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}


class AbnormalityAggregator:
    """
    Session-level abnormality aggregator.

    One instance per session. Lives in memory, writes to SQLite on every
    detection. SyncClient background thread handles Supabase push.
    """

    def __init__(self, session_id: str, local_db, sync_client):
        """
        Args:
            session_id:   Local session UUID (str)
            local_db:     LocalDB instance
            sync_client:  SyncClient instance (owns all HTTP sync)
        """
        self.session_id  = session_id
        self.local_db    = local_db
        self.sync_client = sync_client

        # Resolve backend session ID once — used by SyncClient flush
        self.backend_session_id: Optional[str] = self._get_backend_session_id()

        # In-memory aggregation state
        self.detections: Dict[str, Dict] = {}
        self.first_detected_at: Optional[datetime] = None
        self.overall_severity: str = "LOW"
        self.confidence_score: float = 0.0

        # Load any existing record from SQLite (session recovery after crash)
        self._load_existing()

        print(f"  ✓ AbnormalityAggregator ready (session: {session_id[:8]}...)")

    # ─────────────────────────────────────────────────────────
    # INIT HELPERS
    # ─────────────────────────────────────────────────────────

    def _get_backend_session_id(self) -> Optional[str]:
        """Resolve backend session UUID from local DB."""
        try:
            session = self.local_db.get_session(self.session_id)
            if session:
                return session.get('backend_session_id')
        except Exception as e:
            print(f"  ⚠️ Could not resolve backend session ID: {e}")
        return None

    def _load_existing(self):
        """
        Load existing SQLite record into memory.
        Handles crash recovery — if the app was killed mid-session, we
        resume from wherever we left off rather than starting fresh.
        """
        try:
            record = self.local_db.get_session_abnormality(self.session_id)
            if not record:
                return

            self.detections        = dict(record.get("detections", {}))
            self.overall_severity  = record.get("overall_severity", "LOW")
            self.confidence_score  = float(record.get("confidence_score", 0))

            first_str = record.get("first_detected_at")
            if first_str:
                try:
                    self.first_detected_at = datetime.fromisoformat(first_str)
                except Exception:
                    self.first_detected_at = None

            if self.detections:
                print(f"  📂 Recovered {len(self.detections)} detection type(s) from local DB")

        except Exception as e:
            print(f"  ⚠️ Error loading existing abnormalities: {e}")

    # ─────────────────────────────────────────────────────────
    # SEVERITY CALCULATOR
    # ─────────────────────────────────────────────────────────

    @staticmethod
    def _calculate_severity(occurrences: int, max_confidence: float) -> str:
        if occurrences >= 10 or max_confidence >= 0.95:
            return "CRITICAL"
        elif occurrences >= 5 or max_confidence >= 0.85:
            return "HIGH"
        elif occurrences >= 2 or max_confidence >= 0.75:
            return "MEDIUM"
        else:
            return "LOW"

    def _recalculate_overall(self):
        """Recalculate overall_severity and confidence_score from all detections."""
        if not self.detections:
            self.overall_severity = "LOW"
            self.confidence_score = 0.0
            return

        best_sev  = "LOW"
        max_conf  = 0.0

        for d in self.detections.values():
            sev  = d.get("severity", "LOW")
            conf = float(d.get("confidence", 0))
            if SEVERITY_RANK.get(sev, 0) > SEVERITY_RANK.get(best_sev, 0):
                best_sev = sev
            if conf > max_conf:
                max_conf = conf

        self.overall_severity = best_sev
        self.confidence_score = round(max_conf, 4)

    # ─────────────────────────────────────────────────────────
    # CORE — called every time a pattern fires
    # ─────────────────────────────────────────────────────────

    def add_detection(
        self,
        abnormality_type: str,
        confidence: float,
        timestamp: datetime,
        description: str = ""
    ):
        """
        Record a new detection of the given type.

        Steps:
          1. Update in-memory detections dict (merge, not replace)
          2. Recalculate overall severity + confidence
          3. Write full state to SQLite (upsert — one row per session)
          4. Done. SyncClient background flush handles Supabase.

        No HTTP calls here. No event loops. No blocking.
        """
        now = timestamp

        # ── Track first detection time ────────────────────────
        if self.first_detected_at is None:
            self.first_detected_at = now

        # ── Merge into in-memory dict ─────────────────────────
        if abnormality_type not in self.detections:
            self.detections[abnormality_type] = {
                "occurrences": 0,
                "confidence":  0.0,
                "severity":    "LOW",
                "timestamps":  [],
                "last_seen":   now.isoformat(),
            }

        entry = self.detections[abnormality_type]
        entry["occurrences"] += 1
        entry["timestamps"].append(now.isoformat())
        entry["last_seen"]   = now.isoformat()

        # Keep rolling max confidence per type
        if confidence > entry["confidence"]:
            entry["confidence"] = round(confidence, 4)

        # Recalculate severity for this type
        entry["severity"] = self._calculate_severity(
            entry["occurrences"], entry["confidence"]
        )

        print(f"  📊 [{abnormality_type}] "
              f"x{entry['occurrences']} | "
              f"conf={entry['confidence']:.0%} | "
              f"sev={entry['severity']}")

        # ── Recalculate overall ───────────────────────────────
        self._recalculate_overall()

        # ── Write to SQLite (guaranteed, no internet needed) ──
        self._save_to_sqlite(now)

    def _save_to_sqlite(self, last_updated_at: datetime):
        """
        Write the full current state to SQLite as a single upsert.
        This is the ONLY write path for abnormalities.
        """
        try:
            self.local_db.upsert_session_abnormality(
                session_id        = self.session_id,
                overall_severity  = self.overall_severity,
                confidence_score  = self.confidence_score,
                detections        = self.detections,
                first_detected_at = self.first_detected_at or last_updated_at,
                last_updated_at   = last_updated_at
            )
            print(f"     💾 Saved to SQLite "
                  f"[{self.overall_severity} | {self.confidence_score:.0%}]")
        except Exception as e:
            print(f"     ❌ SQLite save failed: {e}")

    # ─────────────────────────────────────────────────────────
    # SESSION END — called by main.py
    # ─────────────────────────────────────────────────────────

    def flush(self):
        """
        Final save before session ends.
        Ensures SQLite has the very latest state.
        SyncClient.sync_all() will then push it to Supabase.
        """
        if self.detections:
            self._save_to_sqlite(datetime.now())
            print(f"  ✅ Aggregator flushed: "
                  f"{len(self.detections)} type(s) | "
                  f"{self.overall_severity} | "
                  f"{self.confidence_score:.0%}")
        else:
            print(f"  ✅ Aggregator flush: no detections this session")

    def get_summary(self) -> Dict:
        """
        Return the current aggregated state.
        Called by main.py to display the end-of-session summary.

        Returns {} if nothing was detected.
        """
        if not self.detections:
            return {}

        return {
            abn_type: {
                "occurrences": d["occurrences"],
                "severity":    d["severity"],
                "confidence":  d["confidence"],
                "last_seen":   d["last_seen"],
            }
            for abn_type, d in self.detections.items()
        }

    def get_overall(self) -> Dict:
        """Return the top-level severity + confidence for this session."""
        return {
            "overall_severity": self.overall_severity,
            "confidence_score": self.confidence_score,
            "detection_types":  list(self.detections.keys()),
            "total_types":      len(self.detections),
        }