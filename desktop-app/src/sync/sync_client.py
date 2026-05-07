import logging
import httpx
import asyncio
import threading
import time
from datetime import datetime
from typing import Optional, Callable, Dict, List

from storage.local_db import LocalDB

logger = logging.getLogger(__name__)


class SyncClient:
    """
    Dual-layer sync client.

    Layer 1 = SQLite (AbnormalityAggregator, instant, offline-safe)
    Layer 2 = Supabase backend (this class, on interval, with retry)
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
        self.api_base_url          = api_base_url
        self.access_token          = access_token
        self.employee_id           = employee_id
        self.local_db              = local_db
        self.on_sync_complete      = on_sync_complete
        self.on_sync_error         = on_sync_error
        self.sync_interval_seconds = sync_interval_seconds

        self.is_syncing: bool                   = False
        self.last_sync_time: Optional[datetime] = None
        self.sync_errors: List[str]             = []
        self.backend_online: bool               = True

        self._flush_thread: Optional[threading.Thread] = None
        self._flush_running: bool               = False

        # Legacy compat
        self.sync_task = None

    # ─────────────────────────────────────────────────────────
    # HELPERS
    # ─────────────────────────────────────────────────────────

    def _get_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type":  "application/json"
        }

    def _mark_backend_online(self):
        if not self.backend_online:
            logger.info("Backend back online — resuming sync")
        self.backend_online = True

    def _mark_backend_offline(self, reason: str = ""):
        if self.backend_online:
            logger.warning(f"Backend offline — working locally ({reason})")
        self.backend_online = False

    # ─────────────────────────────────────────────────────────
    # BACKGROUND FLUSH (Layer 2)
    # ─────────────────────────────────────────────────────────

    def start_background_flush(self):
        """Start the background sync thread. Safe to call multiple times."""
        if self._flush_running:
            return
        self._flush_running = True
        self._flush_thread = threading.Thread(
            target=self._flush_loop,
            daemon=True,
            name="sentinel-sync-flush"
        )
        self._flush_thread.start()
        logger.info(f"Background flush started (every {self.sync_interval_seconds}s)")

    def stop_background_flush(self):
        """Signal the background thread to stop after its current sleep."""
        self._flush_running = False

    def _flush_loop(self):
        """Background thread: sleep → flush → repeat."""
        while self._flush_running:
            time.sleep(self.sync_interval_seconds)
            if not self._flush_running:
                break
            try:
                self._run_flush_cycle()
            except Exception as e:
                logger.error(f"Flush cycle error: {e}")
                self.sync_errors.append(f"Flush cycle: {e}")

    def _run_flush_cycle(self):
        """
        One complete flush cycle.
        Sessions are pushed first (abnormalities need backend_session_id).
        Each unsynced abnormality record (one per session) gets one HTTP UPSERT.
        """
        unsynced_sessions      = self.local_db.get_unsynced_sessions()
        unsynced_abnormalities = self.local_db.get_unsynced_abnormalities()

        if not unsynced_sessions and not unsynced_abnormalities:
            return

        total = len(unsynced_sessions) + len(unsynced_abnormalities)
        logger.info(f"Flush cycle: {total} record(s) to sync "
              f"({len(unsynced_sessions)} sessions, "
              f"{len(unsynced_abnormalities)} abnormality records)")

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        synced_count = 0
        failed_count = 0

        try:
            # 1. Push sessions first
            for session in unsynced_sessions:
                try:
                    success = loop.run_until_complete(
                        self._push_session_to_backend(session)
                    )
                    if success:
                        synced_count += 1
                    else:
                        failed_count += 1
                except Exception as e:
                    failed_count += 1
                    logger.error(f"Session flush error: {e}")

            # 2. Push abnormality records (one per session)
            for abn in unsynced_abnormalities:
                try:
                    local_session = self.local_db.get_session(abn["session_id"])
                    if not local_session or not local_session.get("backend_session_id"):
                        logger.warning(f"Orphaned abnormality for session {abn['session_id'][:8]}... — no backend session ID. Marking as skipped.")
                        self.local_db.mark_abnormality_synced(abn["session_id"])
                        failed_count += 1
                        continue

                    backend_session_id = local_session["backend_session_id"]

                    success = loop.run_until_complete(
                        self._push_abnormality_to_backend(
                            backend_session_id=backend_session_id,
                            detections=abn["detections"],
                            overall_severity=abn["overall_severity"],
                            confidence_score=abn["confidence_score"],
                            first_detected_at=abn["first_detected_at"],
                            last_updated_at=abn["last_updated_at"],
                        )
                    )

                    if success:
                        synced_count += 1
                        self.local_db.mark_abnormality_synced(abn["session_id"])
                        logger.info(f"Synced abnormality record for session {abn['session_id'][:8]}... [{abn['overall_severity']}]")
                    else:
                        failed_count += 1

                except Exception as e:
                    failed_count += 1
                    logger.error(f"Abnormality flush error: {e}")

            self.last_sync_time = datetime.now()
            logger.info(f"Flush complete: {synced_count} synced, {failed_count} pending")

            if self.on_sync_complete and synced_count > 0:
                self.on_sync_complete({
                    "sessions_synced":      len(unsynced_sessions),
                    "abnormalities_synced": synced_count,
                    "errors": []
                })

        finally:
            loop.close()

    # ─────────────────────────────────────────────────────────
    # HTTP CALLS
    # ─────────────────────────────────────────────────────────

    async def _push_abnormality_to_backend(
        self,
        backend_session_id: str,
        detections: dict,
        overall_severity: str,
        confidence_score: float,
        first_detected_at: str,
        last_updated_at: str,
    ) -> bool:
        """
        Push ONE abnormality record to the backend.
        The backend route is a UPSERT — finds existing row for session_id,
        merges, or creates fresh. We send FULL current state.
        """
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                all_ok = True

                for abn_type, details in detections.items():
                    payload = {
                        "session_id":       backend_session_id,
                        "abnormality_type": abn_type,
                        "confidence_score": float(details.get("confidence", confidence_score)),
                        "metadata": {
                            "occurrences": details.get("occurrences", 1),
                            "severity":    details.get("severity", overall_severity),
                            "confidence":  details.get("confidence", confidence_score),
                            "timestamps":  details.get("timestamps", []),
                            "last_seen":   details.get("last_seen", last_updated_at),
                        }
                    }

                    response = await client.post(
                        f"{self.api_base_url}/api/v1/abnormalities/",
                        headers=self._get_headers(),
                        json=payload
                    )

                    logger.debug(f"HTTP {response.status_code} [{abn_type}]")

                    if response.status_code in (200, 201):
                        self._mark_backend_online()
                    else:
                        self.sync_errors.append(
                            f"HTTP {response.status_code} for {abn_type}: "
                            f"{response.text[:100]}"
                        )
                        all_ok = False

                return all_ok

        except httpx.ConnectError:
            self._mark_backend_offline("connection refused")
            return False
        except httpx.TimeoutException:
            self._mark_backend_offline("timeout")
            return False
        except Exception as e:
            self._mark_backend_offline(str(e))
            self.sync_errors.append(f"Push error: {e}")
            return False

    async def _push_session_to_backend(self, session: Dict) -> bool:
        """Push an unsynced session to backend."""
        try:
            if session.get("backend_session_id"):
                return True  # Already has backend ID

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.api_base_url}/api/v1/sessions/start",
                    headers=self._get_headers()
                )

                if response.status_code in (200, 201):
                    data = response.json()
                    backend_id = data["session"]["id"]
                    self.local_db.update_session(
                        session_id=session["id"],
                        backend_session_id=backend_id,
                        synced=True
                    )
                    self._mark_backend_online()
                    return True

            return False

        except Exception as e:
            self._mark_backend_offline(str(e))
            return False

    async def _delete_session_from_backend(self, backend_session_id: str) -> bool:
        """
        DELETE a session from Supabase via the backend API.
        Supabase CASCADE wipes abnormalities + work_logs automatically.
        Used when user chooses 'End & Start New' on conflict.
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.delete(
                    f"{self.api_base_url}/api/v1/sessions/{backend_session_id}",
                    headers=self._get_headers()
                )
                if response.status_code in (200, 404):
                    # 404 is fine — already gone
                    logger.info(f"Deleted backend session {backend_session_id[:8]}...")
                    self._mark_backend_online()
                    return True
                else:
                    logger.error(f"Failed to delete backend session: HTTP {response.status_code}")
                    return False

        except httpx.ConnectError:
            self._mark_backend_offline("connection refused")
            return False
        except httpx.TimeoutException:
            self._mark_backend_offline("timeout")
            return False
        except Exception as e:
            logger.error(f"Error deleting backend session: {e}")
            return False

    def delete_session_now(self, backend_session_id: str) -> bool:
        """
        Synchronous wrapper for _delete_session_from_backend.
        Call from main thread (e.g. end_and_start_new in main.py).
        """
        try:
            loop = asyncio.new_event_loop()
            result = loop.run_until_complete(
                self._delete_session_from_backend(backend_session_id)
            )
            loop.close()
            return result
        except Exception as e:
            logger.error(f"delete_session_now error: {e}")
            return False

    # ─────────────────────────────────────────────────────────
    # FORCED SYNC (called at session end by main.py)
    # ─────────────────────────────────────────────────────────

    def sync_now(self):
        """
        Synchronously run one flush cycle on the calling thread.
        Called by main.py just before ending a session to guarantee
        all data is pushed before the app closes.
        """
        logger.info("Final sync before closing session...")
        try:
            self._run_flush_cycle()
        except Exception as e:
            logger.error(f"Final sync error: {e}")

    async def sync_all(self):
        """Async version of sync_now (legacy compat)."""
        unsynced_sessions      = self.local_db.get_unsynced_sessions()
        unsynced_abnormalities = self.local_db.get_unsynced_abnormalities()

        for session in unsynced_sessions:
            await self._push_session_to_backend(session)

        for abn in unsynced_abnormalities:
            local_session = self.local_db.get_session(abn["session_id"])
            if not local_session or not local_session.get("backend_session_id"):
                continue

            success = await self._push_abnormality_to_backend(
                backend_session_id=local_session["backend_session_id"],
                detections=abn["detections"],
                overall_severity=abn["overall_severity"],
                confidence_score=abn["confidence_score"],
                first_detected_at=abn["first_detected_at"],
                last_updated_at=abn["last_updated_at"],
            )
            if success:
                self.local_db.mark_abnormality_synced(abn["session_id"])

        self.last_sync_time = datetime.now()

    # ─────────────────────────────────────────────────────────
    # COMPATIBILITY SHIM
    # ─────────────────────────────────────────────────────────

    async def report_abnormality(self, *args, **kwargs) -> bool:
        """
        NO-OP — kept for interface compatibility only.
        Abnormalities are written to SQLite by AbnormalityAggregator.
        Background flush pushes them to Supabase on its interval.
        """
        return True

    # ─────────────────────────────────────────────────────────
    # STATUS
    # ─────────────────────────────────────────────────────────

    def get_sync_status(self) -> Dict:
        pending_abn  = len(self.local_db.get_unsynced_abnormalities())
        pending_sess = len(self.local_db.get_unsynced_sessions())
        return {
            "backend_online":        self.backend_online,
            "is_syncing":            self.is_syncing,
            "last_sync_time":        self.last_sync_time.isoformat() if self.last_sync_time else None,
            "pending_sessions":      pending_sess,
            "pending_abnormalities": pending_abn,
            "total_pending":         pending_abn + pending_sess,
            "flush_running":         self._flush_running,
            "errors":                self.sync_errors[-10:]
        }

    # Legacy compat
    def stop_auto_sync(self):
        self.stop_background_flush()