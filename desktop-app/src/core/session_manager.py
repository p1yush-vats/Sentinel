"""
Session Manager
Bridges TimeEngine with Backend API.
"""
import httpx
from datetime import datetime
from typing import Optional, Dict, Callable
from core.time_engine import TimeEngine, SessionState

_STATE_TO_BACKEND_STATUS = {
    "working":  "active",
    "on_break": "active",
    "on_lunch": "active",
    "idle":     "active",
    "ended":    "completed",
}


class SessionManager:

    def __init__(
        self,
        api_base_url: str,
        access_token: str,
        employee_id: str,
        on_state_change: Optional[Callable] = None,
        on_sync_error: Optional[Callable] = None
    ):
        self.api_base_url  = api_base_url
        self.access_token  = access_token
        self.employee_id   = employee_id
        self.on_sync_error = on_sync_error
        self.time_engine   = TimeEngine(on_state_change=on_state_change)
        self.backend_session_id: Optional[str] = None
        self.last_sync_time: Optional[datetime] = None
        self.offline_queue = []

    def _get_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type":  "application/json"
        }

    async def start_session(self, force_end_existing: bool = False) -> Dict:
        local_session = self.time_engine.start_session()
        url    = f"{self.api_base_url}/api/v1/sessions/start"
        params = {"force_end_existing": force_end_existing} if force_end_existing else {}
        print(f"POST {url}")
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, headers=self._get_headers(), params=params)
            print(f"Response: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                # Handle conflict embedded in 200
                if data.get("conflict"):
                    existing = data.get("existing_session") or data.get("session") or {}
                    print(f"Conflict: active session on server")
                    return {**local_session, "conflict": True,
                            "existing_session": existing, "synced": False}
                # Normal success
                session_data = data.get("session")
                if not session_data or "id" not in session_data:
                    print(f"Unexpected response keys: {list(data.keys())}")
                    if self.on_sync_error:
                        self.on_sync_error(f"Unexpected server response: {list(data.keys())}")
                    return {**local_session, "synced": False}
                self.backend_session_id = session_data["id"]
                print(f"Backend session: {self.backend_session_id}")
                return {**local_session, "backend_session_id": self.backend_session_id, "synced": True}

            elif response.status_code == 409:
                data         = response.json()
                error_detail = data.get("detail", {})
                existing = {}
                if isinstance(error_detail, dict):
                    existing = error_detail.get("active_session") or error_detail.get("existing_session") or {}
                print(f"409 Conflict")
                return {**local_session, "conflict": True, "existing_session": existing, "synced": False}

            else:
                print(f"Backend error {response.status_code}: {response.text[:200]}")
                self.offline_queue.append({"action": "start_session", "timestamp": datetime.now()})
                if self.on_sync_error:
                    self.on_sync_error(f"Session start failed: HTTP {response.status_code}")
                return {**local_session, "synced": False}

        except httpx.ConnectError as e:
            print(f"Connection error: {e}")
            self.offline_queue.append({"action": "start_session", "timestamp": datetime.now()})
            if self.on_sync_error:
                self.on_sync_error(f"Cannot connect to backend: {e}")
            return {**local_session, "synced": False}
        except Exception as e:
            print(f"Unexpected error in start_session: {e}")
            import traceback; traceback.print_exc()
            self.offline_queue.append({"action": "start_session", "timestamp": datetime.now()})
            if self.on_sync_error:
                self.on_sync_error(f"Offline: {e}")
            return {**local_session, "synced": False}

    async def end_session(self) -> Dict:
        local_summary = self.time_engine.end_session()
        if self.backend_session_id:
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.post(
                        f"{self.api_base_url}/api/v1/sessions/{self.backend_session_id}/end",
                        headers=self._get_headers(),
                        json={
                            "total_work_minutes":    local_summary["work_minutes"],
                            "total_break_minutes":   local_summary["break_minutes"],
                            "lunch_taken":           local_summary["lunch_taken"],
                            "session_quality_score": 100.0
                        }
                    )
                    if response.status_code == 200:
                        return {**local_summary, "synced": True}
            except Exception as e:
                if self.on_sync_error:
                    self.on_sync_error(f"Failed to sync session end: {e}")
        return {**local_summary, "synced": False}

    async def sync_session_state(self) -> bool:
        if not self.backend_session_id:
            return False
        state          = self.time_engine.get_current_state()
        backend_status = _STATE_TO_BACKEND_STATUS.get(state["state"], "active")
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.patch(
                    f"{self.api_base_url}/api/v1/sessions/{self.backend_session_id}",
                    headers=self._get_headers(),
                    json={
                        "total_work_minutes":  state["work_minutes"],
                        "total_break_minutes": state["break_minutes"],
                        "lunch_taken":         state["lunch_taken"],
                        "status":              backend_status,
                    }
                )
                if response.status_code == 200:
                    self.last_sync_time = datetime.now()
                    return True
                return False
        except Exception as e:
            if self.on_sync_error:
                self.on_sync_error(f"Sync failed: {e}")
            return False

    async def create_work_log(
        self,
        log_type: str,
        start_time: datetime,
        end_time: Optional[datetime] = None,
        duration_minutes: Optional[int] = None,
        break_token_used: bool = False
    ) -> bool:
        if not self.backend_session_id:
            return False
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.api_base_url}/api/v1/sessions/{self.backend_session_id}/logs",
                    headers=self._get_headers(),
                    json={
                        "log_type":         log_type,
                        "start_time":       start_time.isoformat(),
                        "end_time":         end_time.isoformat() if end_time else None,
                        "duration_minutes": duration_minutes,
                        "break_token_used": break_token_used
                    }
                )
                return response.status_code == 200
        except Exception as e:
            if self.on_sync_error:
                self.on_sync_error(f"Work log failed: {e}")
            return False

    def take_break(self):  return self.time_engine.take_break()
    def end_break(self):   return self.time_engine.end_break()
    def take_lunch(self):  return self.time_engine.take_lunch()
    def end_lunch(self):   return self.time_engine.end_lunch()
    def update(self) -> Dict: return self.time_engine.update()
    def get_current_state(self) -> Dict: return self.time_engine.get_current_state()