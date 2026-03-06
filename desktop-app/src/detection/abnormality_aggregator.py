"""
Abnormality Aggregator

Responsibilities:
  - Track detections per type across the session (1 DB row per type)
  - Calculate severity and build metadata
  - Delegate ALL sync to SyncClient (no own queue, no own thread)

How it works:
  - add_detection() is called every time a pattern is detected
  - It updates the in-memory dict (aggregating occurrences)
  - Saves to local SQLite via local_db (always, instant)
  - Tells sync_client to push to backend (sync_client owns retry logic)
  - get_summary() and flush() are called at session end by main.py
"""
from datetime import datetime
from typing import Dict, Optional
import uuid
import asyncio


class AbnormalityAggregator:
    """
    Session-level abnormality aggregator.

    One instance per session. Tracks all detections in memory,
    persists to SQLite, and delegates backend sync to SyncClient.
    """

    def __init__(self, session_id: str, local_db, sync_client):
        """
        Args:
            session_id:   Local session UUID
            local_db:     LocalDB instance
            sync_client:  SyncClient instance (owns all backend sync + retry)
        """
        self.session_id = session_id
        self.local_db = local_db
        self.sync_client = sync_client

        # In-memory store: { abnormality_type -> { id, detections[], confidences[], first_detected } }
        self.session_abnormalities: Dict[str, Dict] = {}

        # Resolve backend session ID once at init
        self.backend_session_id = self._get_backend_session_id()

        # Load any existing abnormalities from DB (session recovery)
        self._load_existing()

    # =========================================================
    # INIT HELPERS
    # =========================================================

    def _get_backend_session_id(self) -> Optional[str]:
        """Resolve backend session UUID from local DB."""
        try:
            session = self.local_db.get_session(self.session_id)
            if session:
                backend_id = session.get('backend_session_id')
                if backend_id:
                    print(f"  ✓ Backend session ID: {backend_id}")
                    return backend_id
                else:
                    print(f"  ⚠️ No backend session ID (offline mode)")
                    return None
            return None
        except Exception as e:
            print(f"  ⚠️ Could not resolve backend session ID: {e}")
            return None

    def _load_existing(self):
        """
        Load existing abnormalities from SQLite into memory.
        Used when recovering a session that was interrupted.
        """
        try:
            existing = self.local_db.get_session_abnormalities(self.session_id)
            for abn in existing:
                abn_type = abn['abnormality_type']
                metadata = abn.get('metadata', {})

                self.session_abnormalities[abn_type] = {
                    'id': abn['id'],
                    'detections': metadata.get('timestamps', []),
                    'confidences': metadata.get('confidences', []),
                    'first_detected': (
                        datetime.fromisoformat(abn['detected_at'])
                        if isinstance(abn['detected_at'], str)
                        else abn['detected_at']
                    )
                }

            if existing:
                print(f"  📂 Loaded {len(existing)} existing abnormality type(s) from DB")

        except Exception as e:
            print(f"  ⚠️ Error loading existing abnormalities: {e}")

    # =========================================================
    # SEVERITY CALCULATOR
    # =========================================================

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

    # =========================================================
    # CORE METHOD — called every time a pattern is detected
    # =========================================================

    def add_detection(
        self,
        abnormality_type: str,
        confidence: float,
        timestamp: datetime,
        description: str = ""
    ):
        """
        Record a new detection of the given abnormality type.

        Aggregates into the session-level entry (one row per type).
        Saves to SQLite immediately.
        Delegates backend push to SyncClient.

        Args:
            abnormality_type: e.g. "suspicious_paste", "rapid_paste"
            confidence:       0.0–1.0
            timestamp:        When it was detected
            description:      Human-readable detail string
        """
        # ── Initialize if first occurrence ───────────────────────────
        if abnormality_type not in self.session_abnormalities:
            self.session_abnormalities[abnormality_type] = {
                'id': str(uuid.uuid4()),
                'detections': [],
                'confidences': [],
                'first_detected': timestamp
            }

        # ── Update in-memory aggregation ─────────────────────────────
        abn = self.session_abnormalities[abnormality_type]
        abn['detections'].append(timestamp.isoformat())
        abn['confidences'].append(confidence)

        occurrences = len(abn['detections'])
        avg_conf = sum(abn['confidences']) / occurrences
        max_conf = max(abn['confidences'])
        severity = self._calculate_severity(occurrences, max_conf)

        print(f"  📊 {abnormality_type}: {occurrences}x, {severity}")

        # ── Build metadata payload ────────────────────────────────────
        metadata = {
            'description': description or f"{abnormality_type.replace('_', ' ').title()} detected {occurrences} time(s)",
            'occurrences': occurrences,
            'avg_confidence': round(float(avg_conf), 4),
            'max_confidence': round(float(max_conf), 4),
            'severity': severity,
            'first_detected_at': abn['first_detected'].isoformat(),
            'last_detected_at': timestamp.isoformat(),
            'timestamps': abn['detections'],
            'confidences': abn['confidences']
        }

        # ── LAYER 1: Save to SQLite (always) ─────────────────────────
        try:
            existing = self.local_db.get_session_abnormalities(self.session_id)
            already_exists = any(e['abnormality_type'] == abnormality_type for e in existing)

            if already_exists:
                self.local_db.update_abnormality(
                    abnormality_id=abn['id'],
                    confidence_score=max_conf,
                    metadata=metadata
                )
            else:
                self.local_db.create_abnormality(
                    abnormality_id=abn['id'],
                    session_id=self.session_id,
                    abnormality_type=abnormality_type,
                    confidence_score=max_conf,
                    detected_at=abn['first_detected'],
                    metadata=metadata
                )
            print(f"     💾 Saved locally")

        except Exception as e:
            print(f"     ❌ Local save failed: {e}")
            return  # If local save fails, don't attempt backend

        # ── LAYER 2: Delegate backend sync to SyncClient ─────────────
        # SyncClient handles immediate push + retry via background flush
        if self.sync_client and self.backend_session_id:
            try:
                # SyncClient.report_abnormality is async — run in new event loop
                # (we're in a background thread, not an async context)
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(
                        self.sync_client.report_abnormality(
                            session_id=self.backend_session_id,
                            abnormality_type=abnormality_type,
                            confidence_score=max_conf,
                            metadata=metadata
                        )
                    )
                finally:
                    loop.close()

            except Exception as e:
                # Non-fatal — data is in SQLite, background flush will retry
                print(f"     ⚠️ Backend push error (will retry): {e}")
        else:
            print(f"     ⚡ Offline — queued for background flush")

    # =========================================================
    # SESSION END METHODS (called by main.py)
    # =========================================================

    def get_summary(self) -> Dict:
        """
        Get a summary of all abnormalities detected this session.
        Returns empty dict if none detected.
        Called by main.py before showing session end screen.
        """
        summary = {}

        for abn_type, abn in self.session_abnormalities.items():
            if not abn['detections']:
                continue

            occurrences = len(abn['detections'])
            avg_conf = sum(abn['confidences']) / occurrences
            max_conf = max(abn['confidences'])
            severity = self._calculate_severity(occurrences, max_conf)

            summary[abn_type] = {
                'occurrences': occurrences,
                'avg_confidence': round(avg_conf, 4),
                'max_confidence': round(max_conf, 4),
                'severity': severity,
                'first_detected_at': abn['first_detected'].isoformat()
            }

        return summary

    def flush(self):
        """
        Called at session end to finalize.

        Since sync is delegated to SyncClient (which has its own background
        flush thread), this just logs the final state and prints a summary.
        SyncClient.sync_all() is called separately by main.py to force-flush
        any remaining unsynced records before the session closes.
        """
        total_types = len(self.session_abnormalities)
        total_detections = sum(
            len(a['detections']) for a in self.session_abnormalities.values()
        )

        print(f"\n📊 Aggregator finalizing: {total_types} type(s), {total_detections} total detection(s)")

        if total_types == 0:
            print(f"  ✅ Clean session — no abnormalities recorded")
        else:
            for abn_type, abn in self.session_abnormalities.items():
                occurrences = len(abn['detections'])
                max_conf = max(abn['confidences']) if abn['confidences'] else 0
                severity = self._calculate_severity(occurrences, max_conf)
                print(f"  • {abn_type}: {occurrences}x [{severity}] max={max_conf:.0%}")

        print(f"  ✅ All data in SQLite — SyncClient will flush remaining to backend")