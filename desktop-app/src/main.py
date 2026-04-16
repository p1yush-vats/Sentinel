"""
main.py — SENTINEL Desktop App
Entry point. Wires SentinelApp into UI.
"""
import sys
import asyncio
from pathlib import Path
from datetime import datetime, timedelta
import uuid
from typing import Optional
import pytz
import threading
import time
import httpx
import ctypes
import pystray
from PIL import Image

try:
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("sentinel.desktop.app.1.0")
except Exception:
    pass

sys.path.insert(0, str(Path(__file__).parent))

from ui.login_window  import LoginWindow
from ui.main_window   import MainWindow
from core.config      import Config
from core.time_engine import SessionState
from auth.jwt_handler import JWTHandler
from core.session_manager         import SessionManager
from storage.local_db             import LocalDB
from sync.sync_client             import SyncClient
from detection.input_collector    import InputCollector
from detection.abnormality_detector   import AbnormalityDetector, Abnormality
from detection.abnormality_aggregator import AbnormalityAggregator
from utils.assets import ICO_PATH, set_window_icon
import customtkinter as ctk

IST = pytz.timezone("Asia/Kolkata")

# Palette (shared with dialogs)
BG0   = "#0B1120"; BG1 = "#0D1526"; BG2 = "#111C2E"
BG3   = "#1A2640"; BORD = "#1E2D45"
GREEN = "#10B981"; AMBER = "#F59E0B"; RED = "#EF4444"; BLUE = "#60A5FA"
T1 = "#E2E8F0";    T2 = "#94A3B8";   T3 = "#475569"
G_BG = "#0B1F14";  G_BD = "#0D3320"
A_BG = "#1A1400";  A_BD = "#3B2C00"
R_BG = "#1A0D0D";  R_BD = "#3B1010"


# Use the standardized helper from utils.assets
# (helpers removed here to avoid duplication)


def now_ist():
    return datetime.now(IST)


def parse_datetime_ist(dt_string: str) -> datetime:
    try:
        dt = datetime.fromisoformat(dt_string.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = IST.localize(dt)
        else:
            dt = dt.astimezone(IST)
        return dt
    except Exception:
        try:
            clean = dt_string.split("+")[0].split(".")[0]
            dt = datetime.strptime(clean, "%Y-%m-%d %H:%M:%S")
            return IST.localize(dt)
        except Exception:
            return now_ist()


class SentinelApp:

    def __init__(self):
        self.jwt_handler = JWTHandler(Config.DB_DIR)
        self.local_db    = LocalDB(Config.DB_PATH)

        self.login_window: Optional[LoginWindow] = None
        self.main_window:  Optional[MainWindow]  = None

        self.session_manager:        Optional[SessionManager]        = None
        self.sync_client:            Optional[SyncClient]            = None
        self.input_collector:        Optional[InputCollector]        = None
        self.abnormality_detector:   Optional[AbnormalityDetector]   = None
        self.abnormality_aggregator: Optional[AbnormalityAggregator] = None

        self.user:         Optional[dict] = None
        self.access_token: Optional[str]  = None
        self.current_session_id: Optional[str] = None

        self._work_segment_start:  Optional[datetime] = None
        self._break_segment_start: Optional[datetime] = None
        self._lunch_segment_start: Optional[datetime] = None
        self._hourly_metrics: dict = {}

        self.detection_running = False
        self.detection_task:   Optional[threading.Thread] = None

        # Set to True by _logout() so _show_main() knows to re-show login
        # after mainloop() returns cleanly (avoids destroying Tk mid-callback).
        self._logout_pending: bool = False
        
        self.tray_icon = None
        self._setup_tray()

    def _setup_tray(self):
        if not ICO_PATH.exists():
            return
        try:
            image = Image.open(str(ICO_PATH))
            menu = pystray.Menu(
                pystray.MenuItem("Show Sentinel", self._on_tray_show, default=True),
                pystray.MenuItem("Exit Sentinel", self._on_tray_exit)
            )
            self.tray_icon = pystray.Icon("Sentinel", image, "Sentinel", menu)
            # Add a dedicated click handler for double-click/default action
            self.tray_icon.on_activate = self._on_tray_show
            threading.Thread(target=self.tray_icon.run, daemon=True).start()
        except Exception as e:
            print(f"Tray error: {e}")

    def _on_tray_show(self, icon=None, item=None):
        print("Tray: Showing Sentinel...")
        def _show():
            target = self.main_window or self.login_window
            if target:
                target.deiconify()
                target.focus_force()
                target.state('normal')
                target.lift()
        
        # Try both direct and after() for maximum responsiveness across threads
        if self.main_window:
            self.main_window.after(0, _show)
        elif self.login_window:
            self.login_window.after(0, _show)

    def _on_tray_exit(self, icon, item):
        import os
        print("Tray exit: terminating Sentinel...")
        if self.tray_icon:
            self.tray_icon.stop()
        os._exit(0)

    # ─────────────────────────────────────────────────────────
    def run(self):
        print("=" * 50)
        print("  SENTINEL Desktop App v1.0.0")
        print(f"  API: {Config.API_BASE_URL}")
        print(f"  DB : {Config.DB_PATH}")
        print("=" * 50)

        if self.jwt_handler.has_saved_tokens() and self.jwt_handler.is_token_valid():
            self.user         = self.jwt_handler.get_user_data()
            self.access_token = self.jwt_handler.get_access_token()
            if self.user and self.access_token and "id" in self.user:
                try:
                    print(f"Auto-login: {self.user.get('full_name')} ({self.user.get('role')})")
                    self._init_components()
                    incomplete = self._check_incomplete_session()
                    if incomplete:
                        self._session_recovery_dialog(incomplete)
                    else:
                        self._show_main()
                    return
                except Exception as e:
                    print(f"Auto-login error: {e}")
                    import traceback; traceback.print_exc()
                    self.jwt_handler.clear_tokens()
            else:
                self.jwt_handler.clear_tokens()

        self._show_login()

    # ─────────────────────────────────────────────────────────
    def _check_incomplete_session(self) -> Optional[dict]:
        try:
            session = self.local_db.get_active_session(self.user["id"])
            if not session:
                return None
            start = parse_datetime_ist(session["start_time"])
            age   = now_ist() - start
            if age < timedelta(hours=Config.SESSION_RECOVERY_WINDOW_HOURS):
                print(f"Found incomplete session from {int(age.total_seconds()//60)} min ago")
                return session
            self.local_db.update_session(session_id=session["id"],
                                          status="abandoned", end_time=now_ist())
            return None
        except Exception as e:
            print(f"Error checking incomplete session: {e}")
            return None

    def _session_recovery_dialog(self, session: dict):
        """Standalone CTk dialog — no parent, blocks until user chooses."""
        choice = {"value": "fresh"}

        dlg = ctk.CTk()
        dlg.title("Session Recovery")
        dlg.geometry("540x320")
        dlg.resizable(False, False)
        dlg.configure(fg_color=BG1)
        dlg.attributes("-topmost", True)
        set_window_icon(dlg)
        dlg.update_idletasks()
        sw, sh = dlg.winfo_screenwidth(), dlg.winfo_screenheight()
        dlg.geometry(f"540x320+{(sw-540)//2}+{(sh-320)//2}")

        container = ctk.CTkFrame(dlg, fg_color=BG2, corner_radius=12)
        container.pack(fill="both", expand=True, padx=28, pady=28)

        ctk.CTkLabel(container, text="Incomplete session found",
                     font=("Arial", 16, "bold"), text_color=AMBER).pack(pady=(0, 12))

        try:
            start_dt = parse_datetime_ist(session.get("start_time", ""))
            display  = start_dt.strftime("%I:%M %p on %B %d")
        except Exception:
            display = session.get("start_time", "Unknown time")

        ctk.CTkLabel(
            container,
            text=f"Found an active session from:\n{display}\n"
                 f"Work logged: {session.get('total_work_minutes', 0)} min",
            font=("Arial", 12), text_color=T2, justify="center"
        ).pack(pady=(0, 24))

        btn_f = ctk.CTkFrame(container, fg_color="transparent")
        btn_f.pack(fill="x")
        btn_f.grid_columnconfigure((0, 1), weight=1)

        def _continue():
            choice["value"] = "continue"
            dlg.quit()
            dlg.destroy()

        def _fresh():
            choice["value"] = "fresh"
            dlg.quit()
            dlg.destroy()

        ctk.CTkButton(btn_f, text="Continue session", command=_continue,
                      height=46, font=("Arial", 13, "bold"), corner_radius=10,
                      fg_color=G_BG, hover_color="#0F2A1A",
                      text_color=GREEN, border_color=G_BD, border_width=1
                      ).grid(row=0, column=0, sticky="ew", padx=(0, 8))

        ctk.CTkButton(btn_f, text="Start fresh", command=_fresh,
                      height=46, font=("Arial", 13, "bold"), corner_radius=10,
                      fg_color=BG3, hover_color="#243450",
                      text_color=T2, border_color=BORD, border_width=1
                      ).grid(row=0, column=1, sticky="ew", padx=(8, 0))

        dlg.protocol("WM_DELETE_WINDOW", _fresh)
        dlg.mainloop()

        if choice["value"] == "continue":
            self.current_session_id  = session["id"]
            self._work_segment_start = now_ist()
        else:
            self.local_db.update_session(session_id=session["id"],
                                          status="abandoned", end_time=now_ist())

        self._show_main()

    # ─────────────────────────────────────────────────────────
    def _show_login(self):
        self.login_window = LoginWindow(
            on_login_success=self._on_login_success,
            api_base_url=Config.API_BASE_URL
        )
        self.login_window.protocol("WM_DELETE_WINDOW", self.login_window.withdraw)
        self.login_window.mainloop()
        # After mainloop() returns (window closed/logged out), clean up
        try:
            self.login_window.destroy()
        except Exception:
            pass
        self.login_window = None

    def _on_login_success(self, user, access_token):
        self.user = user
        self.access_token = access_token
        self.jwt_handler.save_tokens(
            access_token=access_token,
            refresh_token=access_token, # backend uses same for now
            user_data=user
        )
        if self.login_window:
            self.login_window.destroy()
            self.login_window = None

        # Resolve pyimage conflict by clearing cache before creating MainWindow root
        from utils import assets
        assets.clear_cache()

        self._init_components()
        self._show_main()

    def _logout(self):
        print("Logging out…")
        self._stop_detection()
        if self.sync_client:
            self.sync_client.stop_background_flush()
        self.jwt_handler.clear_tokens()

        # Reset state
        self.user               = None
        self.access_token       = None
        self.current_session_id = None
        self.session_manager    = None
        self.sync_client        = None

        # Signal _show_main() to re-show login after mainloop() returns
        # cleanly. We must NOT call _show_login() here because we are still
        # inside a Tkinter button callback; destroying the window and creating
        # a new CTk root here causes the "pyimage doesn't exist" crash.
        self._logout_pending = True

        if self.main_window:
            try:
                self.main_window.withdraw()
            except Exception:
                pass
            try:
                self.main_window.quit()   # causes mainloop() to return
            except Exception:
                pass

    def _init_components(self):
        print("Initializing components…")
        self.session_manager = SessionManager(
            api_base_url=Config.API_BASE_URL,
            access_token=self.access_token,
            employee_id=self.user["id"],
            on_state_change=self._on_state_change,
            on_sync_error=self._on_sync_error
        )
        self.session_manager.on_alert_received = self._on_alert_received
        self.session_manager.on_task_received  = self._on_task_received
        self.sync_client = SyncClient(
            api_base_url=Config.API_BASE_URL,
            access_token=self.access_token,
            employee_id=self.user["id"],
            local_db=self.local_db,
            on_sync_complete=self._on_sync_complete,
            on_sync_error=self._on_sync_error,
            sync_interval_seconds=Config.SYNC_INTERVAL_SECONDS
        )
        self.sync_client.start_background_flush()
        self.input_collector = InputCollector(
            on_pattern_detected=self._on_pattern_detected, buffer_size=1000)
        self.abnormality_detector = AbnormalityDetector(
            on_abnormality_detected=self._on_abnormality_detected,
            confidence_threshold=Config.ABNORMALITY_CONFIDENCE_THRESHOLD
        )
        print("Components ready.")

    def _on_alert_received(self, data: dict):
        if self.main_window:
            title = data.get("title", "Admin Message")
            msg = data.get("message", "")
            severity = data.get("severity", "crit")
            # Thread-safe UI update
            self.main_window.after(0, lambda: self.main_window.show_banner(f"{title}: {msg}", severity=severity, duration_ms=10000, is_admin_alert=True))
            self.main_window.after(0, lambda: self.main_window.notifier.send(title, msg, severity=severity))

    def _on_task_received(self, data: dict):
        task = data.get("data", {})
        title = task.get("title", "New Task")
        priority = task.get("priority", "medium")
        if self.main_window:
            # OS toast
            self.main_window.after(0, lambda: self.main_window.notifier.send(
                "New Task Assigned", f"{title} [{priority}]", severity="info"))
            # In-app banner
            self.main_window.after(0, lambda: self.main_window.show_banner(
                f"✓ New task: {title}", severity="info", duration_ms=6000))
            # Refresh Tasks tab list
            self.main_window.after(0, lambda: self.main_window.refresh_tasks())

    def _show_main(self):
        self.main_window = MainWindow(
            user=self.user,
            access_token=self.access_token,
            time_engine=self.session_manager.time_engine
        )
        self.main_window.on_start_session = self._start_session
        self.main_window.on_end_session   = self._end_session
        self.main_window.on_take_break    = self._take_break
        self.main_window.on_end_break     = self._end_break
        self.main_window.on_take_lunch    = self._take_lunch
        self.main_window.on_end_lunch     = self._end_lunch
        self.main_window.on_logout        = self._logout
        
        # Start persistent WS connection
        if self.session_manager:
            self.session_manager.connect_realtime()
            
        self.main_window.protocol("WM_DELETE_WINDOW", self.main_window.withdraw)
        self.main_window.mainloop()

        # mainloop() returned — clean up the window now that we are back
        # on the main thread, outside any Tkinter callback.
        mw = self.main_window
        self.main_window = None
        if mw:
            try:
                mw.destroy()
            except Exception:
                pass

        if self._logout_pending:
            self._logout_pending = False
            print("Logged out — showing login")
            self._show_login()

    # ─────────────────────────────────────────────────────────
    # SESSION LIFECYCLE
    # ─────────────────────────────────────────────────────────
    def _start_session(self):
        if self.session_manager.time_engine.state.value != "idle":
            return
        if not self.current_session_id:
            self.current_session_id = str(uuid.uuid4())

        def _run():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(self.session_manager.start_session())
                loop.close()

                if result.get("conflict"):
                    existing = result.get("existing_session", {})
                    if self.main_window:
                        self.main_window.after(0, lambda e=existing: self._conflict_dialog(e))
                    return

                existing_local = self.local_db.get_session(self.current_session_id)
                if not existing_local:
                    self.local_db.create_session(
                        session_id=self.current_session_id,
                        employee_id=self.user["id"],
                        start_time=now_ist(),
                        backend_session_id=result.get("backend_session_id")
                    )
                elif result.get("backend_session_id"):
                    self.local_db.update_session(
                        session_id=self.current_session_id,
                        backend_session_id=result.get("backend_session_id"),
                        status="active")

                self._work_segment_start = now_ist()
                self._hourly_metrics     = {}

                self.abnormality_aggregator = AbnormalityAggregator(
                    session_id=self.current_session_id,
                    local_db=self.local_db,
                    sync_client=self.sync_client
                )

                ts = now_ist().strftime("%I:%M %p")
                synced = result.get("synced", False)
                if self.main_window:
                    self.main_window.after(0, lambda t=ts, s=synced: (
                        self.main_window.add_feed_item("info", "Session started",
                                                        f"Detection active · {t}", "info"),
                        self.main_window.set_sync_status(s, t)
                    ))

                self._start_detection()

            except Exception as e:
                print(f"Session start error: {e}")
                import traceback; traceback.print_exc()

        threading.Thread(target=_run, daemon=True).start()

    def _end_session(self):
        self._stop_detection()

        if self._work_segment_start:
            self._post_work_log("work", self._work_segment_start, now_ist())
            self._work_segment_start = None

        self._flush_productivity_metrics()

        if self.abnormality_aggregator:
            self.abnormality_aggregator.flush()
            summary = self.abnormality_aggregator.get_summary()
            if summary:
                print(f"Abnormality summary: {len(summary)} type(s)")
            self.abnormality_aggregator = None

        try:
            self.sync_client.sync_now()
        except Exception as e:
            print(f"Final sync error: {e}")

        def _run():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                summary = loop.run_until_complete(self.session_manager.end_session())
                loop.close()

                risk = self.abnormality_detector.get_risk_score()
                if self.current_session_id:
                    self.local_db.update_session(
                        session_id=self.current_session_id,
                        end_time=now_ist(),
                        total_work_minutes=summary.get("work_minutes", 0),
                        total_break_minutes=summary.get("break_minutes", 0),
                        lunch_taken=summary.get("lunch_taken", False),
                        status="completed",
                        risk_score=risk
                    )

                if self.main_window:
                    self.main_window.after(0, lambda s=summary: self.main_window.show_session_summary(s))
                    self.main_window.after(0, lambda r=risk: self.main_window.set_risk_score(r))

                self.abnormality_detector.clear_session()
                self.input_collector.clear_buffers()
                self.current_session_id = None
                self._hourly_metrics    = {}
                self.sync_client.stop_background_flush()

            except Exception as e:
                print(f"Session end error: {e}")
                import traceback; traceback.print_exc()

        threading.Thread(target=_run, daemon=True).start()

    # ─────────────────────────────────────────────────────────
    # BREAK / LUNCH
    # ─────────────────────────────────────────────────────────
    def _take_break(self):
        try:
            if self._work_segment_start:
                self._post_work_log("work", self._work_segment_start, now_ist())
                self._work_segment_start = None
            self.session_manager.take_break()
            self._break_segment_start = now_ist()
            self._stop_detection()
        except Exception as e:
            print(f"Break error: {e}")

    def _end_break(self):
        try:
            if self._break_segment_start:
                self._post_work_log("break", self._break_segment_start,
                                    now_ist(), break_token_used=True)
                self._break_segment_start = None
            self.session_manager.end_break()
            self._work_segment_start = now_ist()
            self._start_detection()
        except Exception as e:
            print(f"End break error: {e}")

    def _take_lunch(self):
        try:
            if self._work_segment_start:
                self._post_work_log("work", self._work_segment_start, now_ist())
                self._work_segment_start = None
            self.session_manager.take_lunch()
            self._lunch_segment_start = now_ist()
            self._stop_detection()
        except Exception as e:
            print(f"Lunch error: {e}")

    def _end_lunch(self):
        try:
            if self._lunch_segment_start:
                self._post_work_log("lunch", self._lunch_segment_start, now_ist())
                self._lunch_segment_start = None
            self.session_manager.end_lunch()
            self._work_segment_start = now_ist()
            self._start_detection()
        except Exception as e:
            print(f"End lunch error: {e}")

    # ─────────────────────────────────────────────────────────
    # DETECTION
    # ─────────────────────────────────────────────────────────
    def _start_detection(self):
        if self.detection_running:
            return
        self.input_collector.start_collecting()
        self.detection_running = True
        self.detection_task = threading.Thread(
            target=self._detection_loop, daemon=True)
        self.detection_task.start()
        print("Detection pipeline started")

    def _stop_detection(self):
        if not self.detection_running:
            return
        self.detection_running = False
        self.input_collector.stop_collecting()
        print("Detection pipeline stopped")

    def _detection_loop(self):
        interval = 30
        while self.detection_running:
            try:
                state      = self.session_manager.get_current_state()
                is_working = state["state"] == "working"
                pattern    = self.input_collector.get_keystroke_pattern()
                activity   = self.input_collector.get_activity_summary()

                self._accumulate_hourly(activity)

                abnormalities = self.abnormality_detector.run_comprehensive_analysis(
                    keystroke_pattern=pattern,
                    activity_summary=activity,
                    is_work_time=is_working
                )

                if abnormalities:
                    for abn in abnormalities:
                        self._save_to_aggregator(abn)
                    risk = self.abnormality_detector.get_risk_score()
                    if self.main_window:
                        self.main_window.after(0, lambda r=risk: self.main_window.set_risk_score(r))
                else:
                    # Only show "Analysis clean" if the aggregator also has NO
                    # detections. keyboard_sitting and other pattern-callback
                    # detections are added to the aggregator directly (not via
                    # run_comprehensive_analysis), so we must check it here.
                    agg_clean = (
                        not self.abnormality_aggregator
                        or not self.abnormality_aggregator.detections
                    )
                    if agg_clean:
                        ts = now_ist().strftime("%I:%M %p")
                        if self.main_window:
                            self.main_window.after(
                                0, lambda t=ts: self.main_window.add_feed_item(
                                    "ok", "Analysis clean",
                                    f"No abnormalities detected · {t}", "OK"))

                if self.session_manager.backend_session_id:
                    def _sync():
                        try:
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                            ok = loop.run_until_complete(self.session_manager.sync_session_state())
                            loop.close()
                            if ok and self.main_window:
                                t = now_ist().strftime("%I:%M %p")
                                self.main_window.after(0, lambda ts=t:
                                    self.main_window.set_sync_status(True, ts))
                        except Exception as e:
                            print(f"Session sync error: {e}")
                    threading.Thread(target=_sync, daemon=True).start()

            except Exception as e:
                print(f"Detection loop error: {e}")
                import traceback; traceback.print_exc()

            time.sleep(interval)

        print("Detection loop stopped")

    # ─────────────────────────────────────────────────────────
    # CALLBACKS
    # ─────────────────────────────────────────────────────────
    def _on_state_change(self, state, data):
        if self.main_window:
            self.main_window.after(0, lambda s=state, d=data:
                self.main_window.update_state_ui(s, d))

    def _on_sync_complete(self, summary: dict):
        n = summary.get("sessions_synced", 0) + summary.get("abnormalities_synced", 0)
        print(f"Sync complete — {n} record(s)")
        if self.main_window:
            ts = now_ist().strftime("%I:%M %p")
            self.main_window.after(0, lambda t=ts: self.main_window.set_sync_status(True, t))

    def _on_sync_error(self, error: str):
        print(f"Sync error: {error}")
        if self.main_window:
            ts = now_ist().strftime("%I:%M %p")
            self.main_window.after(0, lambda t=ts: self.main_window.set_sync_status(False, t))

    def _on_pattern_detected(self, pattern: dict):
        pt         = pattern.get("type", "")
        confidence = pattern.get("confidence", 0.0)
        details    = pattern.get("details", "")

        _MAP = {
            "large_paste":      "suspicious_paste",
            "rapid_paste":      "rapid_paste",
            "keyboard_sitting": "keyboard_sitting",
            "mouse_jiggler":    "mouse_jiggler",
            "idle_period":      "long_idle",
            "burst_then_idle":  "burst_then_idle",
            "activity_burst":   "activity_burst",
            "clock_in_out":     "clock_in_clock_out",
        }
        abn_type = _MAP.get(pt)
        if (abn_type
                and confidence >= self.abnormality_detector.confidence_threshold
                and self.abnormality_aggregator):
            self.abnormality_aggregator.add_detection(
                abnormality_type=abn_type, confidence=confidence,
                timestamp=datetime.now(), description=details)

        _KIND = {
            "large_paste": "warn", "rapid_paste": "warn",
            "keyboard_sitting": "warn", "mouse_jiggler": "warn",
            "idle_period": "warn", "burst_then_idle": "warn",
            "activity_burst": "warn", "clock_in_out": "crit",
        }
        kind  = _KIND.get(pt, "info")
        title = pt.replace("_", " ").title()
        ts    = now_ist().strftime("%I:%M %p")
        meta  = f"{details[:60]} · {ts}" if details else ts
        badge = f"{confidence:.0%}"
        if self.main_window:
            self.main_window.after(0, lambda k=kind, ti=title, m=meta, b=badge:
                self.main_window.add_feed_item(k, ti, m, b))

    def _on_abnormality_detected(self, abnormality: Abnormality):
        abn_label = (abnormality.abnormality_type.value
                     if hasattr(abnormality.abnormality_type, "value")
                     else str(abnormality.abnormality_type))
        conf = abnormality.confidence_score
        _HIGH = {"mechanical_typing", "mouse_jiggler", "clock_in_clock_out",
                 "superhuman_speed", "suspicious_paste"}
        kind  = "crit" if (abn_label in _HIGH and conf >= 0.9) else "warn"
        title = abn_label.replace("_", " ").title()
        desc  = abnormality.metadata.get("description", "")
        ts    = now_ist().strftime("%I:%M %p")
        meta  = f"{desc[:60]} · {ts}" if desc else ts
        badge = f"{conf:.0%}"
        if self.main_window:
            self.main_window.after(0, lambda k=kind, ti=title, m=meta, b=badge:
                self.main_window.add_feed_item(k, ti, m, b))
            risk = self.abnormality_detector.get_risk_score()
            self.main_window.after(0, lambda r=risk: self.main_window.set_risk_score(r))

    def _save_to_aggregator(self, abnormality: Abnormality):
        if not self.abnormality_aggregator:
            return
        abn_type = (abnormality.abnormality_type.value
                    if hasattr(abnormality.abnormality_type, "value")
                    else str(abnormality.abnormality_type))
        self.abnormality_aggregator.add_detection(
            abnormality_type=abn_type,
            confidence=abnormality.confidence_score,
            timestamp=datetime.now(),
            description=abnormality.metadata.get("description", "")
        )

    # ─────────────────────────────────────────────────────────
    # WORK LOGS + PRODUCTIVITY
    # ─────────────────────────────────────────────────────────
    def _post_work_log(self, log_type: str, start: datetime,
                       end: datetime, break_token_used: bool = False):
        duration = int((end - start).total_seconds() / 60)
        if duration <= 0:
            return
        def _send():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(self.session_manager.create_work_log(
                    log_type=log_type, start_time=start, end_time=end,
                    duration_minutes=duration, break_token_used=break_token_used))
                loop.close()
                print(f"Work log saved: {log_type} ({duration} min)")
            except Exception as e:
                print(f"Work log error: {e}")
        threading.Thread(target=_send, daemon=True).start()

    def _accumulate_hourly(self, activity: dict):
        hour = datetime.now().hour
        if hour not in self._hourly_metrics:
            self._hourly_metrics[hour] = {"keystrokes": 0, "mouse_moves": 0, "pastes": 0}
        self._hourly_metrics[hour]["keystrokes"]  = activity.get("total_keystrokes", 0)
        self._hourly_metrics[hour]["mouse_moves"] = activity.get("total_mouse_movements", 0)
        self._hourly_metrics[hour]["pastes"]      = activity.get("total_pastes", 0)

    def _flush_productivity_metrics(self):
        if not self._hourly_metrics:
            return
        if not (self.session_manager and self.session_manager.backend_session_id):
            return
        payload = []
        for hour, data in self._hourly_metrics.items():
            ks = data.get("keystrokes", 0)
            mm = data.get("mouse_moves", 0)
            payload.append({
                "session_id":           self.session_manager.backend_session_id,
                "hour_of_day":          hour,
                "activity_intensity":   min(round((ks / max(mm+1, 1)) * 50, 2), 100.0),
                "keystroke_count":      ks,
                "mouse_movement_count": mm,
                "paste_count":          data.get("pastes", 0),
            })
        def _send():
            try:
                headers = {"Authorization": f"Bearer {self.access_token}",
                           "Content-Type": "application/json"}
                with httpx.Client(timeout=10.0) as client:
                    client.post(f"{Config.API_BASE_URL}/api/v1/productivity-metrics/bulk",
                                headers=headers, json={"metrics": payload})
            except Exception as e:
                print(f"Productivity metrics error: {e}")
        threading.Thread(target=_send, daemon=True).start()
        self._hourly_metrics = {}

    # ─────────────────────────────────────────────────────────
    # CONFLICT DIALOG
    # ─────────────────────────────────────────────────────────
    def _conflict_dialog(self, existing_session: dict):
        if not self.main_window:
            return
        dlg = ctk.CTkToplevel(self.main_window)
        dlg.title("Active session found")
        dlg.geometry("500x290")
        dlg.resizable(False, False)
        dlg.configure(fg_color=BG1)
        dlg.transient(self.main_window)
        dlg.grab_set()
        set_window_icon(dlg)
        dlg.update_idletasks()
        dlg.geometry(f"500x290+{(dlg.winfo_screenwidth()-500)//2}+{(dlg.winfo_screenheight()-290)//2}")

        container = ctk.CTkFrame(dlg, fg_color=BG2)
        container.pack(fill="both", expand=True, padx=28, pady=28)

        ctk.CTkLabel(container, text="Active session on server",
                     font=("Arial", 16, "bold"), text_color=AMBER).pack(pady=(0, 10))

        try:
            start_dt  = parse_datetime_ist(existing_session.get("start_time", ""))
            start_str = start_dt.strftime("%I:%M %p on %B %d")
        except Exception:
            start_str = existing_session.get("start_time", "Unknown")

        ctk.CTkLabel(
            container,
            text=f"Started: {start_str}\n"
                 f"Work: {existing_session.get('total_work_minutes', 0)} min  "
                 f"Break: {existing_session.get('total_break_minutes', 0)} min",
            font=("Arial", 12), text_color=T2, justify="center"
        ).pack(pady=(0, 24))

        btn_f = ctk.CTkFrame(container, fg_color="transparent")
        btn_f.pack(fill="x")
        btn_f.grid_columnconfigure((0, 1), weight=1)

        def _continue():
            dlg.destroy()
            eid = existing_session.get("id")
            lid = self.current_session_id
            if lid and eid:
                # Ensure the local session record exists before updating it.
                # _start_session returns early on conflict so the row may not
                # have been created yet — without this, backend_session_id is
                # never persisted and the SQLite→Supabase flush always fails.
                existing_local = self.local_db.get_session(lid)
                if not existing_local:
                    self.local_db.create_session(
                        session_id=lid,
                        employee_id=self.user["id"],
                        start_time=now_ist(),
                        backend_session_id=eid
                    )
                else:
                    self.local_db.update_session(
                        session_id=lid, backend_session_id=eid, status="active")
                self.session_manager.backend_session_id = eid

            # ── Restore TimeEngine from server session data ───────────────
            # When continuing after a force-close the server already has the
            # elapsed work/break time. We inject it back so the UI timer
            # resumes from where the employee left off instead of 0.
            te = self.session_manager.time_engine
            try:
                start_dt = parse_datetime_ist(existing_session.get("start_time", ""))
                te.session_start_time = start_dt
            except Exception:
                pass  # keep whatever was already set

            work_secs  = (existing_session.get("total_work_minutes",  0) or 0) * 60
            break_secs = (existing_session.get("total_break_minutes", 0) or 0) * 60
            te.total_work_seconds  = float(work_secs)
            te.total_break_seconds = float(break_secs)
            # Resume work from this moment
            te.work_start_time     = now_ist()
            te.state               = SessionState.WORKING
            te.current_hour_start  = now_ist()
            # ──────────────────────────────────────────────────────────────

            self.abnormality_aggregator = AbnormalityAggregator(
                session_id=lid or str(uuid.uuid4()),
                local_db=self.local_db, sync_client=self.sync_client)
            self._work_segment_start = now_ist()
            self._start_detection()

        def _new():
            dlg.destroy()
            old_local = self.local_db.get_session(self.current_session_id) if self.current_session_id else None
            old_bid   = old_local.get("backend_session_id") if old_local else None
            if old_bid:
                self.sync_client.delete_session_now(old_bid)
            if self.current_session_id:
                self.local_db.delete_session(self.current_session_id)
            te = self.session_manager.time_engine
            te.state = SessionState.IDLE
            te.session_start_time = None
            te.work_start_time    = None
            self.session_manager.backend_session_id = None
            self.current_session_id = str(uuid.uuid4())
            def _run():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(
                    self.session_manager.start_session(force_end_existing=True))
                loop.close()
                if not result.get("conflict"):
                    self.local_db.create_session(
                        session_id=self.current_session_id, employee_id=self.user["id"],
                        start_time=now_ist(), backend_session_id=result.get("backend_session_id"))
                    self.abnormality_aggregator = AbnormalityAggregator(
                        session_id=self.current_session_id,
                        local_db=self.local_db, sync_client=self.sync_client)
                    self._work_segment_start = now_ist()
                    self._hourly_metrics     = {}
                    self._start_detection()
            threading.Thread(target=_run, daemon=True).start()

        ctk.CTkButton(btn_f, text="Continue session", command=_continue,
                      height=44, corner_radius=10, font=("Arial", 13, "bold"),
                      fg_color=G_BG, hover_color="#0F2A1A",
                      text_color=GREEN, border_color=G_BD, border_width=1
                      ).grid(row=0, column=0, sticky="ew", padx=(0, 8))

        ctk.CTkButton(btn_f, text="End & start new", command=_new,
                      height=44, corner_radius=10, font=("Arial", 13, "bold"),
                      fg_color=R_BG, hover_color="#2A0D0D",
                      text_color=RED, border_color=R_BD, border_width=1
                      ).grid(row=0, column=1, sticky="ew", padx=(8, 0))


def main():
    try:
        Config.ensure_dirs()
        if len(sys.argv) > 1 and sys.argv[1] == "--reset":
            JWTHandler(Config.DB_DIR).clear_tokens()
            print("Saved tokens cleared.")
        SentinelApp().run()
    except KeyboardInterrupt:
        print("\nApplication closed.")
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback; traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()