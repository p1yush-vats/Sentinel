"""
Sync Client - DUAL SYNC ENGINE

Architecture:
  Layer 1 (ALWAYS): Every abnormality/session is written to local SQLite instantly.
                    This never fails. No internet needed.

  Layer 2 (INTERVAL): A background thread flushes unsynced local records to
                      Supabase backend every SYNC_INTERVAL_SECONDS (default 60s).
                      If backend is offline, records stay in local DB and retry
                      on the next interval. Nothing is lost.

Flow for report_abnormality():
  1. Save to SQLite immediately → marked synced=0
  2. Attempt immediate HTTP push to backend
     - Success → mark synced=1 in SQLite
     - Fail (offline / error) → stays synced=0, background loop picks it up later

Background flush loop (every 60s):
  - Queries all unsynced abnormalities from SQLite
  - Attempts to push each to backend
  - On success → marks synced=1
  - On failure → leaves synced=0 for next cycle
  - Never crashes the app

This means even if backend is down for hours, all data is preserved locally
and will sync the moment connectivity is restored.
"""
import httpx
import asyncio
import threading
import time
from datetime import datetime
from typing import Optional, Callable, Dict, List
from pathlib import Path
import uuid

from storage.local_db import LocalDB


class SyncClient:
    """
    Dual-layer sync client.

    Layer 1 = SQLite (always, instant, offline-safe)
    Layer 2 = Supabase backend (on interval, with retry queue)
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
        self.backend_online: bool = True  # Optimistic — flips on first failure

        # Background flush thread (Layer 2)
        self._flush_thread: Optional[threading.Thread] = None
        self._flush_running: bool = False

        # Legacy async task (kept for compatibility)
        self.sync_task: Optional[asyncio.Task] = None

    # =========================================================
    # INTERNAL HELPERS
    # =========================================================

    def _get_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

    def _mark_backend_online(self):
        if not self.backend_online:
            print("  🟢 Backend back online — resuming sync")
        self.backend_online = True

    def _mark_backend_offline(self, reason: str = ""):
        if self.backend_online:
            print(f"  🔴 Backend offline — working locally ({reason})")
        self.backend_online = False

    # =========================================================
    # LAYER 1 — LOCAL SQLITE (synchronous, always called first)
    # =========================================================

    def save_abnormality_locally(
        self,
        abnormality_id: str,
        local_session_id: str,
        abnormality_type: str,
        confidence_score: float,
        detected_at: datetime,
        metadata: Dict
    ) -> bool:
        """
        Write abnormality to SQLite immediately.
        ALWAYS called first, regardless of internet state.
        Returns True on success.
        """
        try:
            # Check if already exists (aggregation — update instead of insert)
            existing = self.local_db.get_session_abnormalities(local_session_id)
            exists = any(e['id'] == abnormality_id for e in existing)

            if exists:
                self.local_db.update_abnormality(
                    abnormality_id=abnormality_id,
                    confidence_score=confidence_score,
                    metadata=metadata
                )
            else:
                self.local_db.create_abnormality(
                    abnormality_id=abnormality_id,
                    session_id=local_session_id,
                    abnormality_type=abnormality_type,
                    confidence_score=confidence_score,
                    detected_at=detected_at,
                    metadata=metadata
                )
            return True

        except Exception as e:
            print(f"  ❌ LOCAL SAVE FAILED: {e}")
            self.sync_errors.append(f"Local save error: {e}")
            return False

    # =========================================================
    # LAYER 2 — BACKEND HTTP (async, best-effort)
    # =========================================================

    async def _push_abnormality_to_backend(
        self,
        backend_session_id: str,
        abnormality_id: str,
        abnormality_type: str,
        confidence_score: float,
        detected_at: str,
        metadata: Dict
    ) -> bool:
        """
        Push one abnormality to Supabase backend.
        Returns True on success, False on any failure.
        Does NOT raise — always safe to call.
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.api_base_url}/api/v1/abnormalities/",
                    headers=self._get_headers(),
                    json={
                        "session_id": backend_session_id,
                        "abnormality_type": abnormality_type,
                        "confidence_score": confidence_score,
                        "detected_at": detected_at,
                        "metadata": metadata or {}
                    }
                )

                print(f"        📡 HTTP {response.status_code}")

                if response.status_code in (200, 201):
                    self._mark_backend_online()
                    self.local_db.mark_abnormality_synced(abnormality_id)
                    return True
                else:
                    self.sync_errors.append(
                        f"HTTP {response.status_code} for {abnormality_type}: {response.text[:150]}"
                    )
                    return False

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
                    f"{self.api_base_url}/api/v1/sessions/start/",
                    headers=self._get_headers()
                )

                if response.status_code in (200, 201):
                    data = response.json()
                    backend_id = data["session"]["id"]

                    conn = self.local_db._get_connection()
                    cursor = conn.cursor()
                    cursor.execute(
                        "UPDATE sessions SET backend_session_id = ?, synced = 1 WHERE id = ?",
                        (backend_id, session["id"])
                    )
                    conn.commit()
                    conn.close()
                    self._mark_backend_online()
                    return True

            return False

        except Exception as e:
            self._mark_backend_offline(str(e))
            return False

    # =========================================================
    # BACKGROUND FLUSH LOOP (Thread — runs every N seconds)
    # =========================================================

    def start_background_flush(self):
        """
        Start the background thread that periodically flushes
        all unsynced local records to the backend.
        Safe to call multiple times — only starts once.
        """
        if self._flush_running:
            return

        self._flush_running = True
        self._flush_thread = threading.Thread(
            target=self._flush_loop,
            daemon=True,
            name="sentinel-sync-flush"
        )
        self._flush_thread.start()
        print(f"  ✓ Background flush started (every {self.sync_interval_seconds}s)")

    def stop_background_flush(self):
        """Stop the background flush thread gracefully."""
        self._flush_running = False

    def _flush_loop(self):
        """
        Background thread loop.
        Every sync_interval_seconds: push all unsynced SQLite records to backend.
        """
        while self._flush_running:
            time.sleep(self.sync_interval_seconds)

            if not self._flush_running:
                break

            try:
                self._run_flush_cycle()
            except Exception as e:
                print(f"  ⚠️ Flush cycle error: {e}")
                self.sync_errors.append(f"Flush cycle: {e}")

    def _run_flush_cycle(self):
        """
        One complete flush cycle — called from background thread.
        Creates its own event loop to run async HTTP calls.
        """
        unsynced_abnormalities = self.local_db.get_unsynced_abnormalities()
        unsynced_sessions = self.local_db.get_unsynced_sessions()

        if not unsynced_abnormalities and not unsynced_sessions:
            return  # Nothing to do

        total = len(unsynced_abnormalities) + len(unsynced_sessions)
        print(f"\n🔄 Flush cycle: {total} unsynced records "
              f"({len(unsynced_abnormalities)} abnormalities, {len(unsynced_sessions)} sessions)")

        # Create a fresh event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        synced_count = 0
        failed_count = 0

        try:
            # Flush sessions first (abnormalities need backend_session_id)
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
                    print(f"  ⚠️ Session flush error: {e}")

            # Flush abnormalities
            for abn in unsynced_abnormalities:
                try:
                    # Get backend session ID for this abnormality
                    local_session = self.local_db.get_session(abn["session_id"])
                    if not local_session or not local_session.get("backend_session_id"):
                        # Backend session not yet synced — skip this cycle
                        failed_count += 1
                        continue

                    backend_session_id = local_session["backend_session_id"]
                    detected_at = abn.get("detected_at", datetime.now().isoformat())

                    success = loop.run_until_complete(
                        self._push_abnormality_to_backend(
                            backend_session_id=backend_session_id,
                            abnormality_id=abn["id"],
                            abnormality_type=abn["abnormality_type"],
                            confidence_score=abn["confidence_score"],
                            detected_at=detected_at,
                            metadata=abn.get("metadata", {})
                        )
                    )

                    if success:
                        synced_count += 1
                        print(f"  ✅ Flushed: {abn['abnormality_type']} "
                              f"(confidence: {abn['confidence_score']:.0%})")
                    else:
                        failed_count += 1

                except Exception as e:
                    failed_count += 1
                    print(f"  ⚠️ Abnormality flush error: {e}")

            self.last_sync_time = datetime.now()
            print(f"  📊 Flush complete: {synced_count} synced, {failed_count} pending next cycle")

            if self.on_sync_complete and synced_count > 0:
                self.on_sync_complete({
                    "sessions_synced": len(unsynced_sessions),
                    "abnormalities_synced": synced_count,
                    "errors": []
                })

        finally:
            loop.close()

    # =========================================================
    # PUBLIC API — report_abnormality (called by aggregator)
    # =========================================================

    async def report_abnormality(
        self,
        session_id: str,
        abnormality_type: str,
        confidence_score: float,
        metadata: Dict
    ) -> bool:
        """
        Report a detected abnormality — DUAL SYNC.

        Step 1 (GUARANTEED): Save to SQLite immediately.
                             Works offline. Never skipped.

        Step 2 (BEST EFFORT): Push to Supabase backend now.
                              If this fails, background flush retries later.

        Args:
            session_id:       Backend session UUID (from AbnormalityAggregator)
            abnormality_type: e.g. "rapid_paste", "suspicious_paste"
            confidence_score: 0.0–1.0
            metadata:         Detection details dict

        Returns:
            True if saved locally (the guarantee).
            True even if backend push fails.
            False only if local SQLite save itself fails (critical error).
        """
        now = datetime.now()
        abn_id = str(uuid.uuid4())

        # ── LAYER 1: Save to SQLite immediately ──────────────────────
        local_session = self.local_db.get_session_by_backend_id(session_id)
        local_session_id = local_session["id"] if local_session else session_id

        local_saved = self.save_abnormality_locally(
            abnormality_id=abn_id,
            local_session_id=local_session_id,
            abnormality_type=abnormality_type,
            confidence_score=confidence_score,
            detected_at=now,
            metadata=metadata
        )

        if not local_saved:
            print(f"  ❌ CRITICAL: Could not save {abnormality_type} to local DB")
            return False

        print(f"  💾 Saved locally: {abnormality_type}")

        # ── LAYER 2: Attempt immediate backend push ──────────────────
        if not self.backend_online:
            print(f"  ⚡ Backend offline — will sync in next flush cycle")
            return True  # Local save is the guarantee

        push_success = await self._push_abnormality_to_backend(
            backend_session_id=session_id,
            abnormality_id=abn_id,
            abnormality_type=abnormality_type,
            confidence_score=confidence_score,
            detected_at=now.isoformat(),
            metadata=metadata
        )

        if push_success:
            print(f"  ✅ Synced to backend: {abnormality_type}")
        else:
            print(f"  ⚡ Backend sync pending — retry in {self.sync_interval_seconds}s")

        # Always return True — local save is the real guarantee
        return True

    # =========================================================
    # BULK SYNC (call at session end to force flush everything)
    # =========================================================

    async def sync_all(self) -> Dict:
        """
        Manually flush all unsynced local records to backend.
        Call this at session end to ensure nothing is left behind.
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
            for session in self.local_db.get_unsynced_sessions():
                success = await self._push_session_to_backend(session)
                if success:
                    summary["sessions_synced"] += 1
                else:
                    summary["errors"].append(f"Failed: session {session['id']}")

            for abn in self.local_db.get_unsynced_abnormalities():
                local_session = self.local_db.get_session(abn["session_id"])
                if not local_session or not local_session.get("backend_session_id"):
                    summary["errors"].append(f"No backend session for abn {abn['id']}")
                    continue

                success = await self._push_abnormality_to_backend(
                    backend_session_id=local_session["backend_session_id"],
                    abnormality_id=abn["id"],
                    abnormality_type=abn["abnormality_type"],
                    confidence_score=abn["confidence_score"],
                    detected_at=abn.get("detected_at", datetime.now().isoformat()),
                    metadata=abn.get("metadata", {})
                )
                if success:
                    summary["abnormalities_synced"] += 1
                else:
                    summary["errors"].append(f"Failed: abnormality {abn['id']}")

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

    # =========================================================
    # LEGACY ASYNC AUTO-SYNC (kept for backward compatibility)
    # =========================================================

    async def start_auto_sync(self):
        """Legacy async auto-sync. Prefer start_background_flush() instead."""
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
        """Stop legacy async sync task."""
        if self.sync_task:
            self.sync_task.cancel()

    # =========================================================
    # STATUS
    # =========================================================

    def get_sync_status(self) -> Dict:
        """Get current sync status — useful for UI display."""
        pending_abn = len(self.local_db.get_unsynced_abnormalities())
        pending_sess = len(self.local_db.get_unsynced_sessions())

        return {
            "backend_online": self.backend_online,
            "is_syncing": self.is_syncing,
            "last_sync_time": self.last_sync_time.isoformat() if self.last_sync_time else None,
            "pending_sessions": pending_sess,
            "pending_abnormalities": pending_abn,
            "total_pending": pending_abn + pending_sess,
            "flush_running": self._flush_running,
            "errors": self.sync_errors[-10:]
        }


# ─── Example usage ────────────────────────────────────────────
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

        client.start_background_flush()

        success = await client.report_abnormality(
            session_id="test-backend-session-id",
            abnormality_type="suspicious_paste",
            confidence_score=0.99,
            metadata={"size": 5000, "category": "very_large"}
        )
        print(f"Report result: {success}")
        print(f"Status: {client.get_sync_status()}")

    asyncio.run(test())