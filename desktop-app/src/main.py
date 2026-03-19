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

sys.path.insert(0, str(Path(__file__).parent))

from ui.login_window import LoginWindow
from ui.main_window import MainWindow
from core.config import Config
from core.time_engine import SessionState
from auth.jwt_handler import JWTHandler
from core.session_manager import SessionManager
from storage.local_db import LocalDB
from sync.sync_client import SyncClient
from detection.input_collector import InputCollector
from detection.abnormality_detector import AbnormalityDetector, Abnormality
from detection.abnormality_aggregator import AbnormalityAggregator
import customtkinter as ctk

IST = pytz.timezone('Asia/Kolkata')


def now_ist():
    return datetime.now(IST)


def parse_datetime_ist(dt_string: str) -> datetime:
    try:
        dt = datetime.fromisoformat(dt_string.replace('Z', '+00:00'))
        if dt.tzinfo is None:
            dt = IST.localize(dt)
        else:
            dt = dt.astimezone(IST)
        return dt
    except Exception as e:
        print(f"Warning parsing datetime '{dt_string}': {e}")
        try:
            clean_str = dt_string.split('+')[0].split('.')[0]
            dt = datetime.strptime(clean_str, '%Y-%m-%d %H:%M:%S')
            return IST.localize(dt)
        except Exception:
            return now_ist()


class SentinelApp:

    def __init__(self):
        self.jwt_handler = JWTHandler(Config.DB_DIR)
        self.local_db    = LocalDB(Config.DB_PATH)

        self.login_window  = None
        self.main_window   = None

        self.session_manager:        Optional[SessionManager]        = None
        self.sync_client:            Optional[SyncClient]            = None
        self.input_collector:        Optional[InputCollector]        = None
        self.abnormality_detector:   Optional[AbnormalityDetector]   = None
        self.abnormality_aggregator: Optional[AbnormalityAggregator] = None

        self.user          = None
        self.access_token  = None

        self.current_session_id: Optional[str] = None

        # Work log segment tracking (NEW)
        self._work_segment_start:  Optional[datetime] = None
        self._break_segment_start: Optional[datetime] = None
        self._lunch_segment_start: Optional[datetime] = None

        # Hourly productivity metrics accumulator (NEW)
        self._hourly_metrics: dict = {}

        self.detection_task    = None
        self.detection_running = False
        self.sync_task         = None

    def run(self):
        print("🛡️ SENTINEL Desktop App Starting...")
        print(f"   Version: 1.0.0")
        print(f"   API: {Config.API_BASE_URL}")
        print(f"   Database: {Config.DB_PATH}")
        print(f"   Sync interval: {Config.SYNC_INTERVAL_SECONDS}s")

        if self.jwt_handler.has_saved_tokens() and self.jwt_handler.is_token_valid():
            print("✅ Found valid saved session")
            self.user         = self.jwt_handler.get_user_data()
            self.access_token = self.jwt_handler.get_access_token()

            if self.user and self.access_token and 'id' in self.user:
                try:
                    print(f"User: {self.user['full_name']} ({self.user['email']})")
                    print(f"Role: {self.user['role']}")

                    self.initialize_session_components()
                    incomplete_session = self.check_for_incomplete_session()

                    if incomplete_session:
                        self.show_session_recovery_dialog(incomplete_session)
                    else:
                        self.show_main_window()

                    return
                except Exception as e:
                    print(f"❌ Error loading saved session: {e}")
                    import traceback
                    traceback.print_exc()
                    print("   Clearing saved tokens and showing login...")
                    self.jwt_handler.clear_tokens()
            else:
                print("⚠️ Saved session data incomplete, clearing tokens...")
                self.jwt_handler.clear_tokens()

        self.show_login()

    def check_for_incomplete_session(self) -> Optional[dict]:
        try:
            session = self.local_db.get_active_session(self.user['id'])

            if session:
                start_time_str = session['start_time']
                print(f"📅 Checking session start_time: {start_time_str}")

                start_time   = parse_datetime_ist(start_time_str)
                current_time = now_ist()

                print(f"   Parsed start time (IST): {start_time}")
                print(f"   Current time (IST): {current_time}")

                time_since_start = current_time - start_time
                minutes_ago      = time_since_start.total_seconds() / 60
                print(f"   Time since start: {minutes_ago:.1f} minutes ago")

                if time_since_start < timedelta(hours=Config.SESSION_RECOVERY_WINDOW_HOURS):
                    print(f"⚠️ Found incomplete session from {minutes_ago:.0f} minutes ago")
                    return session
                else:
                    print(f"⚠️ Found old incomplete session (>{Config.SESSION_RECOVERY_WINDOW_HOURS} hours), marking as abandoned")
                    self.local_db.update_session(
                        session_id=session['id'],
                        status='abandoned',
                        end_time=now_ist()
                    )

            return None

        except Exception as e:
            print(f"❌ Error checking for incomplete session: {e}")
            import traceback
            traceback.print_exc()
            return None

    def show_session_recovery_dialog(self, incomplete_session: dict):
        root = ctk.CTk()
        root.withdraw()

        dialog = ctk.CTkToplevel(root)
        dialog.title("Session Recovery")
        dialog.geometry("550x400")
        dialog.resizable(False, False)

        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - 275
        y = (dialog.winfo_screenheight() // 2) - 200
        dialog.geometry(f"550x400+{x}+{y}")

        dialog.attributes('-topmost', True)
        dialog.focus_force()

        container = ctk.CTkFrame(dialog, fg_color="#1E293B")
        container.pack(fill="both", expand=True, padx=30, pady=30)

        ctk.CTkLabel(
            container,
            text="🔄 Incomplete Session Detected",
            font=("Arial", 18, "bold"),
            text_color="#F59E0B"
        ).pack(pady=(0, 15))

        start_time_str = incomplete_session.get('start_time', '')
        try:
            start_dt      = parse_datetime_ist(start_time_str)
            display_time  = start_dt.strftime('%I:%M %p on %B %d')
        except Exception:
            display_time  = start_time_str

        ctk.CTkLabel(
            container,
            text=f"You have an incomplete session from:\n\n{display_time}\n\n"
                 f"Work time: {incomplete_session.get('total_work_minutes', 0)} minutes",
            font=("Arial", 12),
            text_color="#94A3B8",
            justify="center"
        ).pack(pady=(0, 25))

        button_frame = ctk.CTkFrame(container, fg_color="transparent")
        button_frame.pack(fill="x")

        def continue_session():
            print(f"📋 Continuing session: {incomplete_session['id']}")
            self.current_session_id  = incomplete_session['id']
            self._work_segment_start = now_ist()
            dialog.destroy()
            root.destroy()
            self.show_main_window()

        ctk.CTkButton(
            button_frame,
            text="▶️ Continue Session",
            command=continue_session,
            height=50,
            font=("Arial", 14, "bold"),
            fg_color="#10B981",
            hover_color="#059669",
            corner_radius=10
        ).pack(side="left", expand=True, fill="x", padx=(0, 10))

        def start_fresh():
            print(f"🆕 Starting fresh, abandoning session: {incomplete_session['id']}")
            self.local_db.update_session(
                session_id=incomplete_session['id'],
                status='abandoned',
                end_time=now_ist()
            )
            dialog.destroy()
            root.destroy()
            self.show_main_window()

        ctk.CTkButton(
            button_frame,
            text="🆕 Start Fresh",
            command=start_fresh,
            height=50,
            font=("Arial", 14, "bold"),
            fg_color="#6B7280",
            hover_color="#4B5563",
            corner_radius=10
        ).pack(side="right", expand=True, fill="x", padx=(10, 0))

        dialog.protocol("WM_DELETE_WINDOW", start_fresh)
        root.mainloop()

    def show_login(self):
        self.login_window = LoginWindow(
            on_login_success=self.on_login_success,
            api_base_url=Config.API_BASE_URL
        )
        self.login_window.mainloop()

    def on_login_success(self, user: dict, access_token: str):
        self.user         = user
        self.access_token = access_token

        self.jwt_handler.save_tokens(
            access_token=access_token,
            refresh_token="",
            user_data=user
        )

        print(f"\n✅ Login successful!")
        print(f"User: {user['full_name']} ({user['email']})")
        print(f"Role: {user['role']}")
        print(f"Employee ID: {user['id']}")

        self.initialize_session_components()
        self.show_main_window()

    def logout(self):
        print("\n🚪 Logging out...")

        self.stop_detection()

        if self.sync_client:
            self.sync_client.stop_background_flush()
            print("  ✓ Sync client stopped")

        self.jwt_handler.clear_tokens()
        print("  ✓ Tokens cleared")

        if self.main_window:
            self.main_window.destroy()

        self.user               = None
        self.access_token       = None
        self.current_session_id = None
        self.session_manager    = None
        self.sync_client        = None

        print("✓ Logged out successfully")

        self.show_login()

    def initialize_session_components(self):
        print("\n🔧 Initializing components...")

        self.session_manager = SessionManager(
            api_base_url=Config.API_BASE_URL,
            access_token=self.access_token,
            employee_id=self.user['id'],
            on_state_change=self.on_session_state_change,
            on_sync_error=self.on_sync_error
        )
        print("  ✓ Session manager initialized")

        self.sync_client = SyncClient(
            api_base_url=Config.API_BASE_URL,
            access_token=self.access_token,
            employee_id=self.user['id'],
            local_db=self.local_db,
            on_sync_complete=self.on_sync_complete,
            on_sync_error=self.on_sync_error,
            sync_interval_seconds=Config.SYNC_INTERVAL_SECONDS
        )

        self.sync_client.start_background_flush()
        print("  ✓ Sync client initialized + background flush started")

        self.input_collector = InputCollector(
            on_pattern_detected=self.on_pattern_detected,
            buffer_size=1000
        )
        print("  ✓ Input collector ready")

        self.abnormality_detector = AbnormalityDetector(
            on_abnormality_detected=self.on_abnormality_detected,
            confidence_threshold=Config.ABNORMALITY_CONFIDENCE_THRESHOLD
        )
        print("  ✓ Abnormality detector ready")

        print("✓ All components initialized")

    def show_main_window(self):
        self.main_window = MainWindow(
            user=self.user,
            access_token=self.access_token,
            time_engine=self.session_manager.time_engine
        )

        self.main_window.on_start_session = self.start_integrated_session
        self.main_window.on_end_session   = self.end_integrated_session
        self.main_window.on_take_break    = self.take_break
        self.main_window.on_end_break     = self.end_break
        self.main_window.on_take_lunch    = self.take_lunch
        self.main_window.on_end_lunch     = self.end_lunch
        self.main_window.on_logout        = self.logout

        print("  ✓ Main window ready — all callbacks wired")
        self.main_window.mainloop()

    # ============================================
    # WORK LOG + PRODUCTIVITY HELPERS (NEW)
    # ============================================

    def _post_work_log(self, log_type: str, start: datetime, end: datetime, break_token_used: bool = False):
        duration = int((end - start).total_seconds() / 60)
        if duration <= 0:
            return

        def _send():
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(
                    self.session_manager.create_work_log(
                        log_type=log_type,
                        start_time=start,
                        end_time=end,
                        duration_minutes=duration,
                        break_token_used=break_token_used,
                    )
                )
                loop.close()
                print(f"  📋 Work log saved: {log_type} ({duration} min)")
            except Exception as e:
                print(f"  ⚠️ Work log post failed: {e}")

        threading.Thread(target=_send, daemon=True).start()

    def _accumulate_hourly_metric(self, activity: dict):
        hour = datetime.now().hour
        if hour not in self._hourly_metrics:
            self._hourly_metrics[hour] = {'keystrokes': 0, 'mouse_moves': 0, 'pastes': 0}
        self._hourly_metrics[hour]['keystrokes']  = activity.get('total_keystrokes', 0)
        self._hourly_metrics[hour]['mouse_moves'] = activity.get('total_mouse_movements', 0)
        self._hourly_metrics[hour]['pastes']      = activity.get('total_pastes', 0)

    def _flush_productivity_metrics(self):
        if not self._hourly_metrics or not self.session_manager.backend_session_id:
            return

        metrics_payload = []
        for hour, data in self._hourly_metrics.items():
            ks = data.get('keystrokes', 0)
            mm = data.get('mouse_moves', 0)
            ps = data.get('pastes', 0)
            intensity = min(round((ks / max(mm + 1, 1)) * 50, 2), 100.0)
            metrics_payload.append({
                "session_id":           self.session_manager.backend_session_id,
                "hour_of_day":          hour,
                "activity_intensity":   intensity,
                "keystroke_count":      ks,
                "mouse_movement_count": mm,
                "paste_count":          ps,
            })

        def _send():
            try:
                headers = {
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type":  "application/json"
                }
                with httpx.Client(timeout=10.0) as client:
                    resp = client.post(
                        f"{Config.API_BASE_URL}/api/v1/productivity-metrics/bulk",
                        headers=headers,
                        json={"metrics": metrics_payload}
                    )
                    if resp.status_code == 200:
                        print(f"  📊 Productivity metrics synced: {len(metrics_payload)} hourly records")
                    else:
                        print(f"  ⚠️ Metrics sync failed: {resp.status_code}")
            except Exception as e:
                print(f"  ⚠️ Metrics sync error: {e}")

        threading.Thread(target=_send, daemon=True).start()
        self._hourly_metrics = {}

    # ============================================
    # BREAK & LUNCH
    # ============================================

    def take_break(self):
        try:
            if self._work_segment_start:
                self._post_work_log('work', self._work_segment_start, now_ist())
                self._work_segment_start = None

            self.session_manager.take_break()
            self._break_segment_start = now_ist()
            print("☕ Break started")
            self.stop_detection()
        except Exception as e:
            print(f"❌ Break failed: {e}")
            if self.main_window:
                self.main_window.status_label.configure(
                    text=f"Break failed: {str(e)}", text_color="#EF4444")

    def end_break(self):
        try:
            if self._break_segment_start:
                self._post_work_log('break', self._break_segment_start, now_ist(), break_token_used=True)
                self._break_segment_start = None

            self.session_manager.end_break()
            self._work_segment_start = now_ist()
            print("▶ Resumed work")
            self.start_detection()
        except Exception as e:
            print(f"❌ Resume failed: {e}")

    def take_lunch(self):
        try:
            if self._work_segment_start:
                self._post_work_log('work', self._work_segment_start, now_ist())
                self._work_segment_start = None

            self.session_manager.take_lunch()
            self._lunch_segment_start = now_ist()
            print("🍽 Lunch started")
            self.stop_detection()
        except Exception as e:
            print(f"❌ Lunch failed: {e}")
            if self.main_window:
                self.main_window.status_label.configure(
                    text=f"Lunch failed: {str(e)}", text_color="#EF4444")

    def end_lunch(self):
        try:
            if self._lunch_segment_start:
                self._post_work_log('lunch', self._lunch_segment_start, now_ist())
                self._lunch_segment_start = None

            self.session_manager.end_lunch()
            self._work_segment_start = now_ist()
            print("▶ Resumed work from lunch")
            self.start_detection()
        except Exception as e:
            print(f"❌ Resume failed: {e}")

    # ============================================
    # SESSION MANAGEMENT
    # ============================================

    def start_integrated_session(self):
        if self.session_manager.time_engine.state.value != 'idle':
            print("⚠️ Session already running locally")
            if self.main_window:
                self.main_window.status_label.configure(
                    text="Session already active", text_color="#F59E0B")
            return

        try:
            if not self.current_session_id:
                self.current_session_id = str(uuid.uuid4())

            print(f"\n🚀 Starting session: {self.current_session_id[:8]}...")
            print(f"   Employee: {self.user.get('full_name', 'Unknown')}")
            print(f"   Time: {now_ist().strftime('%H:%M:%S IST')}")

            if self.main_window:
                self.main_window.status_label.configure(
                    text="⏳ Starting session...",
                    text_color="#F59E0B"
                )

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self.session_manager.start_session())
            loop.close()

            if result.get("conflict"):
                existing = result.get("existing_session", {})
                print(f"\n⚠️ Conflict: active session exists on backend")
                print(f"   Session ID: {existing.get('id', 'unknown')[:8]}...")
                self.show_session_conflict_dialog(existing)
                return

            existing_session = self.local_db.get_session(self.current_session_id)

            if not existing_session:
                self.local_db.create_session(
                    session_id=self.current_session_id,
                    employee_id=self.user['id'],
                    start_time=now_ist(),
                    backend_session_id=result.get('backend_session_id')
                )
                print(f"\n✅ New session started: {self.current_session_id}")
                print(f"   Backend session ID: {result.get('backend_session_id', 'offline')}")
            else:
                print(f"\n▶️ Continuing session: {self.current_session_id}")
                if result.get('backend_session_id'):
                    self.local_db.update_session(
                        session_id=self.current_session_id,
                        status='active'
                    )

            print(f"   Backend synced: {result.get('synced', False)}")

            self._work_segment_start = now_ist()
            self._hourly_metrics     = {}

            self.abnormality_aggregator = AbnormalityAggregator(
                session_id=self.current_session_id,
                local_db=self.local_db,
                sync_client=self.sync_client
            )
            print("  ✓ Abnormality aggregator initialized")

            print("\n🔍 Starting abnormality detection...")
            self.start_detection()

            print(f"   Detection active: {self.detection_running}")

            if self.main_window:
                self.main_window.status_label.configure(
                    text="✅ Session started - Detection active",
                    text_color="#10B981"
                )

        except Exception as e:
            print(f"❌ Session start failed: {e}")
            import traceback
            traceback.print_exc()
            if self.main_window:
                self.main_window.status_label.configure(
                    text=f"Failed to start session: {str(e)}", text_color="#EF4444")

    def end_integrated_session(self):
        try:
            self.stop_detection()

            if self._work_segment_start:
                self._post_work_log('work', self._work_segment_start, now_ist())
                self._work_segment_start = None

            self._flush_productivity_metrics()

            if self.abnormality_aggregator:
                print("\n📊 Finalizing abnormality summary...")
                self.abnormality_aggregator.flush()
                abn_summary = self.abnormality_aggregator.get_summary()

                if abn_summary:
                    print(f"\n📈 Abnormality Summary:")
                    for abn_type, stats in abn_summary.items():
                        print(f"   • {abn_type}: {stats['occurrences']}x ({stats['severity']})")
                else:
                    print(f"  ✅ No abnormalities detected this session")

                self.abnormality_aggregator = None

            try:
                self.sync_client.sync_now()
            except Exception as e:
                print(f"  ⚠️ Final sync error (data still safe in local DB): {e}")

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            summary = loop.run_until_complete(self.session_manager.end_session())
            loop.close()

            risk_score = 0.0
            if self.current_session_id:
                risk_score = self.abnormality_detector.get_risk_score()

                self.local_db.update_session(
                    session_id=self.current_session_id,
                    end_time=now_ist(),
                    total_work_minutes=summary['work_minutes'],
                    total_break_minutes=summary['break_minutes'],
                    lunch_taken=summary['lunch_taken'],
                    status='completed',
                    risk_score=risk_score
                )

            if self.main_window:
                self.main_window.show_session_summary(summary)

            print(f"\n✅ Session ended")
            print(f"   Work: {summary['work_minutes']} min")
            print(f"   Break: {summary['break_minutes']} min")
            print(f"   Lunch: {summary['lunch_taken']}")
            print(f"   Risk Score: {risk_score:.1f}/100")

            self.abnormality_detector.clear_session()
            self.input_collector.clear_buffers()
            self.current_session_id = None
            self._hourly_metrics    = {}

            self.sync_client.stop_background_flush()

            if self.main_window:
                self.main_window.session_button.configure(
                    text="Logout",
                    command=self.logout,
                    fg_color="#6B7280",
                    hover_color="#4B5563"
                )

        except Exception as e:
            print(f"❌ Session end failed: {e}")
            import traceback
            traceback.print_exc()

    # ============================================
    # DETECTION PIPELINE
    # ============================================

    def start_detection(self):
        if self.detection_running:
            print("⚠️ Detection already running")
            return

        print("🚀 Starting detection pipeline...")
        self.input_collector.start_collecting()
        print("  ✓ Input collector started (privacy-safe mode)")
        print("  ✓ Paste detection active (Windows API)")
        print("  ✓ Clipboard size detection active")
        print("  ✓ Idle detection active")
        print("  ✓ Input collector started (hooks active)")

        self.detection_running = True
        self.detection_task = threading.Thread(
            target=self._detection_loop,
            daemon=True
        )
        self.detection_task.start()
        print("  ✓ Detection loop started (analyzing every 30s)")

    def stop_detection(self):
        if not self.detection_running:
            return
        print("⏸️ Stopping detection...")
        self.detection_running = False
        self.input_collector.stop_collecting()
        print("  ✓ Input collector stopped")
        print("  ✓ Detection stopped")

    def _detection_loop(self):
        print("🔄 Detection loop running...")

        detection_interval = 30

        while self.detection_running:
            try:
                state      = self.session_manager.get_current_state()
                is_working = state['state'] == 'working'

                pattern  = self.input_collector.get_keystroke_pattern()
                activity = self.input_collector.get_activity_summary()

                print(f"\n📊 Detection Check [{datetime.now().strftime('%H:%M:%S')}]:")
                if not self.detection_running:
                    break

                print(f"   State: {state['state']}")
                print(f"   Keystrokes: {activity.get('total_keystrokes', 0)}")
                print(f"   Pastes: {activity.get('total_pastes', 0)}")
                print(f"   Large pastes: {activity.get('total_large_pastes', 0)}")
                print(f"   Idle: {activity.get('idle_seconds', 0):.0f}s")
                print(f"   Mouse moves: {activity.get('total_mouse_movements', 0)}")
                print(f"   Pattern: {pattern.get('status', 'unknown')}")

                self._accumulate_hourly_metric(activity)

                abnormalities = self.abnormality_detector.run_comprehensive_analysis(
                    keystroke_pattern=pattern,
                    activity_summary=activity,
                    is_work_time=is_working
                )

                if abnormalities:
                    print(f"  🚨 Detected {len(abnormalities)} abnormality(ies)!")
                    for abn in abnormalities:
                        self._save_abnormality_to_aggregator(abn)
                else:
                    print("  ✅ No abnormalities detected")

                # ── Sync session state to backend every cycle ──────────
                # Runs in a background thread so it never blocks the UI
                # or the detection loop. Pushes accurate work_minutes,
                # break_minutes, lunch_taken so the dashboard stays live.
                if self.session_manager.backend_session_id:
                    def _do_sync():
                        try:
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                            success = loop.run_until_complete(
                                self.session_manager.sync_session_state()
                            )
                            loop.close()
                            if success:
                                print(f"  📡 Session state synced to backend")
                            else:
                                print(f"  ⚠️ Session sync skipped (offline or no session)")
                        except Exception as e:
                            print(f"  ⚠️ Session sync error: {e}")

                    threading.Thread(target=_do_sync, daemon=True).start()

                if self.sync_client:
                    sync_status = self.sync_client.get_sync_status()
                    if sync_status.get('total_pending', 0) > 0:
                        print(f"  📡 Pending sync: {sync_status['total_pending']} record(s)")

            except Exception as e:
                print(f"❌ Detection error: {e}")
                import traceback
                traceback.print_exc()

            time.sleep(detection_interval)

        print("⏹️ Detection loop stopped")
    # ============================================
    # CALLBACKS & EVENT HANDLERS
    # ============================================

    def on_session_state_change(self, state, data):
        print(f"📊 Session state changed: {state.value}")
        if self.main_window:
            self.main_window.update_state_ui(state, data)

    def on_sync_complete(self, summary):
        print(f"✓ Sync complete: {summary.get('sessions_synced', 0)} sessions, "
              f"{summary.get('abnormalities_synced', 0)} abnormalities")

    def on_sync_error(self, error):
        print(f"⚠️ Sync error: {error}")

    def on_pattern_detected(self, pattern):
        pattern_type = pattern.get('type')
        confidence   = pattern.get('confidence', 0)
        details      = pattern.get('details', 'N/A')

        print(f"🔍 Pattern detected: {pattern_type}")
        print(f"   Confidence: {confidence:.0%}")
        print(f"   Details: {details}")

        pattern_to_abnormality = {
            'large_paste':      'suspicious_paste',
            'rapid_paste':      'rapid_paste',
            'keyboard_sitting': 'keyboard_sitting',
            'mouse_jiggler':    'mouse_jiggler',
            'idle_period':      'long_idle',
            'burst_then_idle':  'burst_then_idle',
            'activity_burst':   'activity_burst',
            'clock_in_out':     'clock_in_clock_out',
        }

        abnormality_type = pattern_to_abnormality.get(pattern_type)

        if abnormality_type and confidence >= self.abnormality_detector.confidence_threshold:
            if self.abnormality_aggregator:
                self.abnormality_aggregator.add_detection(
                    abnormality_type=abnormality_type,
                    confidence=confidence,
                    timestamp=datetime.now(),
                    description=details
                )
            else:
                print(f"  ⚠️ Aggregator not initialized, skipping")

        if self.main_window:
            self.main_window.after(0, lambda: self.main_window.status_label.configure(
                text=f"🔍 {pattern_type.replace('_', ' ').title()} detected",
                text_color="#60A5FA"
            ))

    def on_abnormality_detected(self, abnormality: Abnormality):
        abn_label = (
            abnormality.abnormality_type.value
            if hasattr(abnormality.abnormality_type, 'value')
            else str(abnormality.abnormality_type)
        )
        print(f"\n🚨 ABNORMALITY DETECTED!")
        print(f"   Type: {abn_label}")
        print(f"   Confidence: {abnormality.confidence_score:.2%}")
        print(f"   Description: {abnormality.metadata.get('description', 'N/A')}")

        if self.main_window:
            def update_ui():
                if self.main_window:
                    self.main_window.status_label.configure(
                        text=f"⚠️ {abn_label.replace('_', ' ').title()} "
                             f"({abnormality.confidence_score:.0%})",
                        text_color="#F59E0B"
                    )
            self.main_window.after(0, update_ui)

    def _save_abnormality_to_aggregator(self, abnormality: Abnormality):
        if not self.abnormality_aggregator:
            print(f"  ⚠️ Aggregator not initialized, skipping save")
            return

        abn_type = (
            abnormality.abnormality_type.value
            if hasattr(abnormality.abnormality_type, 'value')
            else str(abnormality.abnormality_type)
        )
        self.abnormality_aggregator.add_detection(
            abnormality_type=abn_type,
            confidence=abnormality.confidence_score,
            timestamp=datetime.now(),
            description=abnormality.metadata.get('description', '')
        )

    # ============================================
    # UTILITY / DIALOGS
    # ============================================

    def show_session_conflict_dialog(self, existing_session: dict):
        dialog = ctk.CTkToplevel(self.main_window)
        dialog.title("Active Session Found")
        dialog.geometry("500x300")
        dialog.resizable(False, False)

        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - 250
        y = (dialog.winfo_screenheight() // 2) - 150
        dialog.geometry(f"500x300+{x}+{y}")

        dialog.transient(self.main_window)
        dialog.grab_set()

        container = ctk.CTkFrame(dialog, fg_color="#1E293B")
        container.pack(fill="both", expand=True, padx=30, pady=30)

        ctk.CTkLabel(
            container,
            text="⚠️ Active Session Found",
            font=("Arial", 20, "bold"),
            text_color="#F59E0B"
        ).pack(pady=(0, 20))

        start_time = existing_session.get('start_time', '')
        if start_time:
            try:
                start_dt       = parse_datetime_ist(start_time)
                start_time_str = start_dt.strftime('%I:%M %p on %B %d')
            except Exception:
                start_time_str = start_time
        else:
            start_time_str = "Unknown time"

        ctk.CTkLabel(
            container,
            text=f"You have an active session that started at:\n\n{start_time_str}\n\n"
                 f"Work time: {existing_session.get('total_work_minutes', 0)} minutes\n"
                 f"Break time: {existing_session.get('total_break_minutes', 0)} minutes",
            font=("Arial", 12),
            text_color="#94A3B8",
            justify="center"
        ).pack(pady=(0, 30))

        button_frame = ctk.CTkFrame(container, fg_color="transparent")
        button_frame.pack(fill="x")

        def continue_session():
            dialog.destroy()
            try:
                existing_backend_id = existing_session.get('id')
                existing_local_id   = self.current_session_id

                if existing_local_id and existing_backend_id:
                    self.local_db.update_session(
                        session_id=existing_local_id,
                        backend_session_id=existing_backend_id,
                        status='active'
                    )
                    self.session_manager.backend_session_id = existing_backend_id

                self.abnormality_aggregator = AbnormalityAggregator(
                    session_id=existing_local_id or str(uuid.uuid4()),
                    local_db=self.local_db,
                    sync_client=self.sync_client
                )
                self._work_segment_start = now_ist()
                self.start_detection()

                print(f"▶️ Continuing existing session: {existing_backend_id}")
                if self.main_window:
                    self.main_window.status_label.configure(
                        text="✅ Continuing existing session",
                        text_color="#10B981"
                    )
            except Exception as e:
                print(f"❌ Failed to continue session: {e}")
                if self.main_window:
                    self.main_window.status_label.configure(
                        text=f"Failed to continue session: {str(e)}",
                        text_color="#EF4444"
                    )

        ctk.CTkButton(
            button_frame,
            text="Continue Session",
            command=continue_session,
            height=45,
            font=("Arial", 13, "bold"),
            fg_color="#10B981",
            hover_color="#059669"
        ).pack(side="left", expand=True, fill="x", padx=(0, 10))

        def end_and_start_new():
            dialog.destroy()
            try:
                old_local = self.local_db.get_session(self.current_session_id) \
                    if self.current_session_id else None
                old_backend_id = old_local.get('backend_session_id') if old_local else None

                if old_backend_id:
                    print(f"🗑️ Deleting backend session {old_backend_id[:8]}...")
                    self.sync_client.delete_session_now(old_backend_id)

                if self.current_session_id:
                    self.local_db.delete_session(self.current_session_id)
                    print(f"🗑️ Cleared local session {self.current_session_id[:8]}...")

                self.session_manager.time_engine.state              = SessionState.IDLE
                self.session_manager.time_engine.session_start_time = None
                self.session_manager.time_engine.work_start_time    = None
                self.session_manager.backend_session_id             = None

                self.current_session_id = str(uuid.uuid4())

                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(
                    self.session_manager.start_session(force_end_existing=True)
                )
                loop.close()

                if not result.get("conflict"):
                    self.local_db.create_session(
                        session_id=self.current_session_id,
                        employee_id=self.user['id'],
                        start_time=now_ist(),
                        backend_session_id=result.get('backend_session_id')
                    )
                    self.abnormality_aggregator = AbnormalityAggregator(
                        session_id=self.current_session_id,
                        local_db=self.local_db,
                        sync_client=self.sync_client
                    )
                    self._work_segment_start = now_ist()
                    self._hourly_metrics     = {}
                    self.start_detection()
                    print(f"\n✅ New session started: {self.current_session_id}")
                    if self.main_window:
                        self.main_window.status_label.configure(
                            text="New session started successfully",
                            text_color="#10B981"
                        )
                else:
                    print("❌ Still got conflict after force_end")
                    if self.main_window:
                        self.main_window.status_label.configure(
                            text="Could not start session — please try again",
                            text_color="#EF4444"
                        )

            except Exception as e:
                print(f"❌ Failed to start new session: {e}")
                import traceback
                traceback.print_exc()
                if self.main_window:
                    self.main_window.status_label.configure(
                        text=f"Failed: {str(e)}", text_color="#EF4444")

        ctk.CTkButton(
            button_frame,
            text="End & Start New",
            command=end_and_start_new,
            height=45,
            font=("Arial", 13, "bold"),
            fg_color="#EF4444",
            hover_color="#DC2626"
        ).pack(side="right", expand=True, fill="x", padx=(10, 0))


def main():
    try:
        Config.ensure_dirs()

        if len(sys.argv) > 1 and sys.argv[1] == '--reset':
            print("🔄 Resetting saved session...")
            jwt_handler = JWTHandler(Config.DB_DIR)
            jwt_handler.clear_tokens()
            print("✓ Saved tokens cleared")

        app = SentinelApp()
        app.run()

    except KeyboardInterrupt:
        print("\n\n👋 Application closed by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()