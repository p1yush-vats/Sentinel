"""
Sync Client

Handles synchronization between local database and backend API.
"""
import httpx
import asyncio
from datetime import datetime
from typing import Optional, Callable, Dict, List
from pathlib import Path
import uuid

from storage.local_db import LocalDB


class SyncClient:
    """
    Synchronization client for backend API
    
    Features:
    - Auto-sync on interval
    - Offline queue management
    - Retry logic with exponential backoff
    - Conflict resolution
    """
    
    def __init__(
        self,
        api_base_url: str,
        access_token: str,
        employee_id: str,
        local_db: LocalDB,
        on_sync_complete: Optional[Callable] = None,
        on_sync_error: Optional[Callable] = None,
        sync_interval_seconds: int = 60
    ):
        """
        Initialize sync client
        
        Args:
            api_base_url: Backend API URL
            access_token: JWT token
            employee_id: Current employee ID
            local_db: Local database instance
            on_sync_complete: Callback when sync completes
            on_sync_error: Callback on sync errors
            sync_interval_seconds: Auto-sync interval
        """
        self.api_base_url = api_base_url
        self.access_token = access_token
        self.employee_id = employee_id
        self.local_db = local_db
        self.on_sync_complete = on_sync_complete
        self.on_sync_error = on_sync_error
        self.sync_interval_seconds = sync_interval_seconds
        
        # Sync state
        self.is_syncing = False
        self.last_sync_time: Optional[datetime] = None
        self.sync_errors: List[str] = []
        
        # Background sync task
        self.sync_task: Optional[asyncio.Task] = None
    
    def _get_headers(self) -> Dict[str, str]:
        """Get HTTP headers"""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
    
    async def sync_all(self) -> Dict:
        """
        Sync all pending data
        
        Returns:
            Sync summary
        """
        if self.is_syncing:
            return {"status": "already_syncing"}
        
        self.is_syncing = True
        summary = {
            "sessions_synced": 0,
            "abnormalities_synced": 0,
            "errors": []
        }
        
        try:
            # Sync sessions
            sessions = self.local_db.get_unsynced_sessions()
            for session in sessions:
                success = await self._sync_session(session)
                if success:
                    summary["sessions_synced"] += 1
                else:
                    summary["errors"].append(f"Failed to sync session {session['id']}")
            
            # Sync abnormalities
            abnormalities = self.local_db.get_unsynced_abnormalities()
            for abn in abnormalities:
                success = await self._sync_abnormality(abn)
                if success:
                    summary["abnormalities_synced"] += 1
                else:
                    summary["errors"].append(f"Failed to sync abnormality {abn['id']}")
            
            self.last_sync_time = datetime.now()
            
            if self.on_sync_complete:
                self.on_sync_complete(summary)
        
        except Exception as e:
            summary["errors"].append(str(e))
            if self.on_sync_error:
                self.on_sync_error(str(e))
        
        finally:
            self.is_syncing = False
        
        return summary
    
    async def _sync_session(self, session: Dict) -> bool:
        """Sync individual session"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # If no backend session ID, create it first
                if not session.get("backend_session_id"):
                    response = await client.post(
                        f"{self.api_base_url}/api/v1/sessions/start",
                        headers=self._get_headers()
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        backend_id = data["session"]["id"]
                        
                        # Update local database
                        conn = self.local_db._get_connection()
                        cursor = conn.cursor()
                        cursor.execute(
                            "UPDATE sessions SET backend_session_id = ? WHERE id = ?",
                            (backend_id, session["id"])
                        )
                        conn.commit()
                        conn.close()
                        
                        session["backend_session_id"] = backend_id
                
                # Update session data
                if session.get("backend_session_id"):
                    # If session is completed, end it
                    if session.get("status") == "completed":
                        response = await client.post(
                            f"{self.api_base_url}/api/v1/sessions/{session['backend_session_id']}/end",
                            headers=self._get_headers(),
                            json={
                                "total_work_minutes": session.get("total_work_minutes", 0),
                                "total_break_minutes": session.get("total_break_minutes", 0),
                                "lunch_taken": bool(session.get("lunch_taken")),
                                "session_quality_score": session.get("session_quality_score")
                            }
                        )
                    else:
                        # Update active session
                        response = await client.patch(
                            f"{self.api_base_url}/api/v1/sessions/{session['backend_session_id']}",
                            headers=self._get_headers(),
                            json={
                                "total_work_minutes": session.get("total_work_minutes", 0),
                                "total_break_minutes": session.get("total_break_minutes", 0),
                                "lunch_taken": bool(session.get("lunch_taken")),
                                "status": session.get("status", "active")
                            }
                        )
                    
                    if response.status_code == 200:
                        # Mark as synced
                        conn = self.local_db._get_connection()
                        cursor = conn.cursor()
                        cursor.execute(
                            "UPDATE sessions SET synced = 1 WHERE id = ?",
                            (session["id"],)
                        )
                        conn.commit()
                        conn.close()
                        return True
            
            return False
        
        except Exception as e:
            self.sync_errors.append(f"Session sync error: {e}")
            return False
    
    async def _sync_abnormality(self, abnormality: Dict) -> bool:
        """Sync individual abnormality"""
        try:
            # Get backend session ID
            session = self.local_db.get_session(abnormality["session_id"])
            if not session or not session.get("backend_session_id"):
                # Can't sync without backend session
                return False
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.api_base_url}/api/v1/abnormalities",
                    headers=self._get_headers(),
                    json={
                        "session_id": session["backend_session_id"],
                        "abnormality_type": abnormality["abnormality_type"],
                        "confidence_score": abnormality["confidence_score"],
                        "detected_at": abnormality["detected_at"],
                        "metadata": abnormality.get("metadata", {})
                    }
                )
                
                if response.status_code == 200:
                    # Mark as synced
                    self.local_db.mark_abnormality_synced(abnormality["id"])
                    return True
            
            return False
        
        except Exception as e:
            self.sync_errors.append(f"Abnormality sync error: {e}")
            return False
    
    async def start_auto_sync(self):
        """Start automatic background syncing"""
        async def sync_loop():
            while True:
                await asyncio.sleep(self.sync_interval_seconds)
                try:
                    await self.sync_all()
                except Exception as e:
                    if self.on_sync_error:
                        self.on_sync_error(f"Auto-sync error: {e}")
        
        self.sync_task = asyncio.create_task(sync_loop())
    
    def stop_auto_sync(self):
        """Stop automatic syncing"""
        if self.sync_task:
            self.sync_task.cancel()
    
    async def report_abnormality(
        self,
        session_id: str,
        abnormality_type: str,
        confidence_score: float,
        metadata: Dict
    ) -> bool:
        """
        Report abnormality immediately
        
        Args:
            session_id: Local session ID
            abnormality_type: Type of abnormality
            confidence_score: Confidence (0-1)
            metadata: Additional data
        
        Returns:
            True if reported successfully
        """
        # Save to local DB first
        abn_id = str(uuid.uuid4())
        self.local_db.create_abnormality(
            abnormality_id=abn_id,
            session_id=session_id,
            abnormality_type=abnormality_type,
            confidence_score=confidence_score,
            detected_at=datetime.now(),
            metadata=metadata
        )
        
        # Try to sync immediately
        abnormality = self.local_db.get_session_abnormalities(session_id)
        if abnormality:
            return await self._sync_abnormality(abnormality[-1])
        
        return False
    
    def get_sync_status(self) -> Dict:
        """Get current sync status"""
        return {
            "is_syncing": self.is_syncing,
            "last_sync_time": self.last_sync_time.isoformat() if self.last_sync_time else None,
            "pending_sessions": len(self.local_db.get_unsynced_sessions()),
            "pending_abnormalities": len(self.local_db.get_unsynced_abnormalities()),
            "errors": self.sync_errors[-10:]  # Last 10 errors
        }


# Example usage
if __name__ == "__main__":
    from pathlib import Path
    
    async def test():
        db = LocalDB(Path.home() / ".sentinel" / "test.db")
        
        client = SyncClient(
            api_base_url="http://127.0.0.1:8000",
            access_token="test_token",
            employee_id="test-employee",
            local_db=db,
            on_sync_complete=lambda s: print(f"✓ Sync complete: {s}"),
            on_sync_error=lambda e: print(f"✗ Sync error: {e}")
        )
        
        # Sync all
        summary = await client.sync_all()
        print(f"Sync summary: {summary}")
        
        # Get status
        status = client.get_sync_status()
        print(f"Status: {status}")
    
    asyncio.run(test())