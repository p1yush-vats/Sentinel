"""
Local Database - SQLite Storage

Stores session data locally for offline capability.
"""
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict
import json


class LocalDB:
    """
    Local SQLite database for offline storage
    
    Tables:
    - sessions: Work sessions
    - work_logs: Detailed work/break logs
    - abnormalities: Detected abnormalities
    - sync_queue: Pending sync operations
    """
    
    def __init__(self, db_path: Path):
        """
        Initialize local database
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database
        self._init_db()
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection"""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row  # Return rows as dicts
        return conn
    
    def _init_db(self):
        """Create database tables"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                employee_id TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT,
                total_work_minutes INTEGER DEFAULT 0,
                total_break_minutes INTEGER DEFAULT 0,
                lunch_taken BOOLEAN DEFAULT 0,
                status TEXT DEFAULT 'active',
                session_quality_score REAL,
                risk_score REAL DEFAULT 0,
                backend_session_id TEXT,
                synced BOOLEAN DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Work logs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS work_logs (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                log_type TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT,
                duration_minutes INTEGER,
                break_token_used BOOLEAN DEFAULT 0,
                synced BOOLEAN DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions(id)
            )
        """)
        
        # Abnormalities table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS abnormalities (
                id TEXT PRIMARY KEY,
                session_id TEXT NOT NULL,
                abnormality_type TEXT NOT NULL,
                confidence_score REAL NOT NULL,
                detected_at TEXT NOT NULL,
                metadata TEXT,
                synced BOOLEAN DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES sessions(id)
            )
        """)
        
        # Sync queue table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sync_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                operation_type TEXT NOT NULL,
                table_name TEXT NOT NULL,
                record_id TEXT NOT NULL,
                payload TEXT NOT NULL,
                attempts INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
    
    # ============ SESSIONS ============
    
    def create_session(
        self,
        session_id: str,
        employee_id: str,
        start_time: datetime,
        backend_session_id: Optional[str] = None
    ) -> str:
        """Create new session"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO sessions (
                id, employee_id, start_time, backend_session_id, synced
            ) VALUES (?, ?, ?, ?, ?)
        """, (
            session_id,
            employee_id,
            start_time.isoformat(),
            backend_session_id,
            1 if backend_session_id else 0
        ))
        
        conn.commit()
        conn.close()
        
        return session_id
    
    def update_session(
        self,
        session_id: str,
        end_time: Optional[datetime] = None,
        total_work_minutes: Optional[int] = None,
        total_break_minutes: Optional[int] = None,
        lunch_taken: Optional[bool] = None,
        status: Optional[str] = None,
        risk_score: Optional[float] = None
    ):
        """Update session"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        updates = []
        values = []
        
        if end_time is not None:
            updates.append("end_time = ?")
            values.append(end_time.isoformat())
        if total_work_minutes is not None:
            updates.append("total_work_minutes = ?")
            values.append(total_work_minutes)
        if total_break_minutes is not None:
            updates.append("total_break_minutes = ?")
            values.append(total_break_minutes)
        if lunch_taken is not None:
            updates.append("lunch_taken = ?")
            values.append(1 if lunch_taken else 0)
        if status is not None:
            updates.append("status = ?")
            values.append(status)
        if risk_score is not None:
            updates.append("risk_score = ?")
            values.append(risk_score)
        
        if updates:
            values.append(session_id)
            cursor.execute(f"""
                UPDATE sessions 
                SET {', '.join(updates)}, synced = 0
                WHERE id = ?
            """, values)
            
            conn.commit()
        
        conn.close()
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get session by ID"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM sessions WHERE id = ?", (session_id,))
        row = cursor.fetchone()
        conn.close()
        
        return dict(row) if row else None
    
    def get_active_session(self, employee_id: str) -> Optional[Dict]:
        """Get active session for employee"""
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
    
    def get_unsynced_sessions(self) -> List[Dict]:
        """Get sessions that need syncing"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM sessions WHERE synced = 0")
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    # ============ WORK LOGS ============
    
    def create_work_log(
        self,
        log_id: str,
        session_id: str,
        log_type: str,
        start_time: datetime,
        end_time: Optional[datetime] = None,
        duration_minutes: Optional[int] = None,
        break_token_used: bool = False
    ) -> str:
        """Create work log entry"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO work_logs (
                id, session_id, log_type, start_time, end_time, 
                duration_minutes, break_token_used
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            log_id,
            session_id,
            log_type,
            start_time.isoformat(),
            end_time.isoformat() if end_time else None,
            duration_minutes,
            1 if break_token_used else 0
        ))
        
        conn.commit()
        conn.close()
        
        return log_id
    
    def get_session_logs(self, session_id: str) -> List[Dict]:
        """Get all logs for a session"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM work_logs 
            WHERE session_id = ?
            ORDER BY start_time
        """, (session_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    # ============ ABNORMALITIES ============
    
    def create_abnormality(
        self,
        abnormality_id: str,
        session_id: str,
        abnormality_type: str,
        confidence_score: float,
        detected_at: datetime,
        metadata: Dict
    ) -> str:
        """Create abnormality record"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO abnormalities (
                id, session_id, abnormality_type, confidence_score,
                detected_at, metadata
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            abnormality_id,
            session_id,
            abnormality_type,
            confidence_score,
            detected_at.isoformat(),
            json.dumps(metadata)
        ))
        
        conn.commit()
        conn.close()
        
        return abnormality_id
    
    def get_session_abnormalities(self, session_id: str) -> List[Dict]:
        """Get abnormalities for a session"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM abnormalities
            WHERE session_id = ?
            ORDER BY detected_at DESC
        """, (session_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        result = []
        for row in rows:
            data = dict(row)
            # Parse JSON metadata
            if data.get("metadata"):
                data["metadata"] = json.loads(data["metadata"])
            result.append(data)
        
        return result
    
    def get_unsynced_abnormalities(self) -> List[Dict]:
        """Get abnormalities that need syncing"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM abnormalities WHERE synced = 0")
        rows = cursor.fetchall()
        conn.close()
        
        result = []
        for row in rows:
            data = dict(row)
            if data.get("metadata"):
                data["metadata"] = json.loads(data["metadata"])
            result.append(data)
        
        return result
    
    def mark_abnormality_synced(self, abnormality_id: str):
        """Mark abnormality as synced"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE abnormalities SET synced = 1 WHERE id = ?
        """, (abnormality_id,))
        
        conn.commit()
        conn.close()
    
    # ============ SYNC QUEUE ============
    
    def add_to_sync_queue(
        self,
        operation_type: str,
        table_name: str,
        record_id: str,
        payload: Dict
    ):
        """Add operation to sync queue"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO sync_queue (
                operation_type, table_name, record_id, payload
            ) VALUES (?, ?, ?, ?)
        """, (
            operation_type,
            table_name,
            record_id,
            json.dumps(payload)
        ))
        
        conn.commit()
        conn.close()
    
    def get_sync_queue(self, limit: int = 100) -> List[Dict]:
        """Get pending sync operations"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM sync_queue
            ORDER BY created_at
            LIMIT ?
        """, (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        result = []
        for row in rows:
            data = dict(row)
            data["payload"] = json.loads(data["payload"])
            result.append(data)
        
        return result
    
    def remove_from_sync_queue(self, queue_id: int):
        """Remove operation from sync queue"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM sync_queue WHERE id = ?", (queue_id,))
        
        conn.commit()
        conn.close()
    
    def clear_sync_queue(self):
        """Clear entire sync queue"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM sync_queue")
        
        conn.commit()
        conn.close()


# Example usage
if __name__ == "__main__":
    from pathlib import Path
    import uuid
    
    db = LocalDB(Path.home() / ".sentinel" / "test.db")
    
    # Create session
    session_id = str(uuid.uuid4())
    db.create_session(
        session_id=session_id,
        employee_id="test-employee",
        start_time=datetime.now()
    )
    
    print(f"✓ Session created: {session_id}")
    
    # Create abnormality
    abn_id = str(uuid.uuid4())
    db.create_abnormality(
        abnormality_id=abn_id,
        session_id=session_id,
        abnormality_type="mechanical_typing",
        confidence_score=0.85,
        detected_at=datetime.now(),
        metadata={"description": "Test abnormality"}
    )
    
    print(f"✓ Abnormality created: {abn_id}")
    
    # Get session
    session = db.get_session(session_id)
    print(f"✓ Session retrieved: {session['id']}")
    
    # Get abnormalities
    abnormalities = db.get_session_abnormalities(session_id)
    print(f"✓ Abnormalities: {len(abnormalities)}")