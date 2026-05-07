import logging
import sqlite3
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict
import uuid

logger = logging.getLogger(__name__)


class LocalDB:
    """
    Local SQLite database for offline storage.

    Tables:
      sessions         — work sessions
      work_logs        — work/break/lunch log entries
      abnormalities    — ONE ROW PER SESSION (upserted, not appended)
      sync_queue       — legacy compatibility (kept but unused by abnormalities)
    """

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    # Connection

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    # Schema

    def _init_db(self):
        conn = self._get_connection()
        cursor = conn.cursor()

        # Sessions
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id                   TEXT PRIMARY KEY,
                employee_id          TEXT NOT NULL,
                start_time           TEXT NOT NULL,
                end_time             TEXT,
                total_work_minutes   INTEGER DEFAULT 0,
                total_break_minutes  INTEGER DEFAULT 0,
                lunch_taken          BOOLEAN DEFAULT 0,
                status               TEXT DEFAULT 'active',
                session_quality_score REAL,
                risk_score           REAL DEFAULT 0,
                backend_session_id   TEXT,
                synced               BOOLEAN DEFAULT 0,
                created_at           TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Work logs
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS work_logs (
                id                TEXT PRIMARY KEY,
                session_id        TEXT NOT NULL,
                log_type          TEXT NOT NULL,
                start_time        TEXT NOT NULL,
                end_time          TEXT,
                duration_minutes  INTEGER,
                break_token_used  BOOLEAN DEFAULT 0,
                synced            BOOLEAN DEFAULT 0,
                created_at        TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions(id)
            )
        """)

        # Abnormalities — one row per session
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS abnormalities (
                id                TEXT PRIMARY KEY,
                session_id        TEXT NOT NULL UNIQUE,
                overall_severity  TEXT NOT NULL DEFAULT 'LOW',
                confidence_score  REAL NOT NULL DEFAULT 0,
                detections        TEXT NOT NULL DEFAULT '{}',
                first_detected_at TEXT NOT NULL,
                last_updated_at   TEXT NOT NULL,
                synced            INTEGER DEFAULT 0
            )
        """)

        # Sync queue (for sessions / work_logs)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sync_queue (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                operation_type TEXT NOT NULL,
                table_name     TEXT NOT NULL,
                record_id      TEXT NOT NULL,
                payload        TEXT NOT NULL,
                created_at     TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()
        conn.close()

    # Sessions

    def create_session(
        self,
        session_id: str,
        employee_id: str,
        start_time: datetime,
        backend_session_id: Optional[str] = None
    ) -> str:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR IGNORE INTO sessions (
                id, employee_id, start_time, backend_session_id
            ) VALUES (?, ?, ?, ?)
        """, (session_id, employee_id, start_time.isoformat(), backend_session_id))
        conn.commit()
        conn.close()
        return session_id

    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get session by local UUID."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def get_active_session(self, employee_id: str) -> Optional[Dict]:
        """Get the active session for an employee (or None)."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM sessions
            WHERE employee_id = ? AND status = 'active'
            ORDER BY start_time DESC
            LIMIT 1
        """, (employee_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def get_session_by_backend_id(self, backend_session_id: str) -> Optional[Dict]:
        """Get a local session record by its backend UUID."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM sessions WHERE backend_session_id = ?",
            (backend_session_id,)
        )
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def delete_session(self, session_id: str):
        """Delete a session and its associated abnormality record from local DB."""
        conn = self._get_connection()
        cursor = conn.cursor()
        # Abnormalities have a FK on session_id but no CASCADE in SQLite DDL,
        # so delete child records first.
        cursor.execute("DELETE FROM abnormalities WHERE session_id = ?", (session_id,))
        cursor.execute("DELETE FROM work_logs WHERE session_id = ?", (session_id,))
        cursor.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
        conn.commit()
        conn.close()
        logger.info(f"Deleted local session {session_id[:8]}... and related records")
    def update_session(
        self,
        session_id: str,
        end_time: Optional[datetime] = None,
        total_work_minutes: Optional[int] = None,
        total_break_minutes: Optional[int] = None,
        lunch_taken: Optional[bool] = None,
        status: Optional[str] = None,
        session_quality_score: Optional[float] = None,
        risk_score: Optional[float] = None,
        backend_session_id: Optional[str] = None,
        synced: Optional[bool] = None
    ):
        conn = self._get_connection()
        cursor = conn.cursor()

        updates, values = [], []

        if end_time              is not None: updates.append("end_time = ?");               values.append(end_time.isoformat())
        if total_work_minutes    is not None: updates.append("total_work_minutes = ?");     values.append(total_work_minutes)
        if total_break_minutes   is not None: updates.append("total_break_minutes = ?");    values.append(total_break_minutes)
        if lunch_taken           is not None: updates.append("lunch_taken = ?");            values.append(1 if lunch_taken else 0)
        if status                is not None: updates.append("status = ?");                 values.append(status)
        if session_quality_score is not None: updates.append("session_quality_score = ?");  values.append(session_quality_score)
        if risk_score            is not None: updates.append("risk_score = ?");             values.append(risk_score)
        if backend_session_id    is not None: updates.append("backend_session_id = ?");     values.append(backend_session_id)
        if synced                is not None: updates.append("synced = ?");                 values.append(1 if synced else 0)

        if updates:
            values.append(session_id)
            cursor.execute(f"UPDATE sessions SET {', '.join(updates)} WHERE id = ?", values)
            conn.commit()

        conn.close()

    def get_unsynced_sessions(self) -> List[Dict]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sessions WHERE synced = 0 AND backend_session_id IS NULL")
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    # Work logs

    def create_work_log(
        self,
        session_id: str,
        log_type: str,
        start_time: datetime,
        end_time: Optional[datetime] = None,
        duration_minutes: Optional[int] = None,
        break_token_used: bool = False
    ) -> str:
        log_id = str(uuid.uuid4())
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO work_logs (
                id, session_id, log_type, start_time, end_time,
                duration_minutes, break_token_used
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            log_id, session_id, log_type,
            start_time.isoformat(),
            end_time.isoformat() if end_time else None,
            duration_minutes,
            1 if break_token_used else 0
        ))
        conn.commit()
        conn.close()
        return log_id

    def get_session_logs(self, session_id: str) -> List[Dict]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM work_logs WHERE session_id = ? ORDER BY start_time",
            (session_id,)
        )
        rows = cursor.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    # Abnormalities — one row per session, upserted

    def upsert_session_abnormality(
        self,
        session_id: str,
        overall_severity: str,
        confidence_score: float,
        detections: dict,
        first_detected_at: datetime,
        last_updated_at: datetime
    ) -> str:
        """
        INSERT or REPLACE the abnormality record for this session.

        Called by AbnormalityAggregator every time add_detection() runs.
        The full in-memory state is written — no partial updates.

        Returns the record id (stable UUID for this session).
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # Derive a stable id from session_id so it never changes across upserts
        record_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"abnormality:{session_id}"))

        cursor.execute("""
            INSERT INTO abnormalities (
                id, session_id, overall_severity, confidence_score,
                detections, first_detected_at, last_updated_at, synced
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 0)
            ON CONFLICT(session_id) DO UPDATE SET
                overall_severity  = excluded.overall_severity,
                confidence_score  = excluded.confidence_score,
                detections        = excluded.detections,
                last_updated_at   = excluded.last_updated_at,
                synced            = 0
        """, (
            record_id,
            session_id,
            overall_severity,
            confidence_score,
            json.dumps(detections),
            first_detected_at.isoformat(),
            last_updated_at.isoformat()
        ))

        conn.commit()
        conn.close()
        return record_id

    def get_session_abnormality(self, session_id: str) -> Optional[Dict]:
        """Get the single abnormality record for a session (or None)."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM abnormalities WHERE session_id = ?", (session_id,)
        )
        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        data = dict(row)
        data["detections"] = json.loads(data["detections"] or "{}")
        return data

    def get_unsynced_abnormalities(self) -> List[Dict]:
        """Return all abnormality records not yet pushed to backend."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM abnormalities WHERE synced = 0")
        rows = cursor.fetchall()
        conn.close()

        result = []
        for row in rows:
            data = dict(row)
            data["detections"] = json.loads(data["detections"] or "{}")
            result.append(data)
        return result

    def mark_abnormality_synced(self, session_id: str):
        """Mark the abnormality record for this session as synced=1."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE abnormalities SET synced = 1 WHERE session_id = ?",
            (session_id,)
        )
        conn.commit()
        conn.close()

    # Legacy compatibility shims
    # Kept so nothing breaks if old call sites exist.

    def get_session_abnormalities(self, session_id: str) -> List[Dict]:
        """Legacy: returns list with 0 or 1 item."""
        record = self.get_session_abnormality(session_id)
        return [record] if record else []

    def mark_abnormality_synced_by_id(self, record_id: str):
        """Legacy: mark synced by record id."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE abnormalities SET synced = 1 WHERE id = ?", (record_id,))
        conn.commit()
        conn.close()

    # Sync Queue (for sessions / work_logs — not abnormalities)

    def add_to_sync_queue(self, operation_type: str, table_name: str,
                          record_id: str, payload: Dict):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO sync_queue (operation_type, table_name, record_id, payload)
            VALUES (?, ?, ?, ?)
        """, (operation_type, table_name, record_id, json.dumps(payload)))
        conn.commit()
        conn.close()

    def get_sync_queue(self, limit: int = 100) -> List[Dict]:
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sync_queue ORDER BY created_at LIMIT ?", (limit,))
        rows = cursor.fetchall()
        conn.close()
        result = []
        for row in rows:
            data = dict(row)
            data["payload"] = json.loads(data["payload"])
            result.append(data)
        return result

    def remove_from_sync_queue(self, queue_id: int):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM sync_queue WHERE id = ?", (queue_id,))
        conn.commit()
        conn.close()

    def clear_sync_queue(self):
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM sync_queue")
        conn.commit()
        conn.close()