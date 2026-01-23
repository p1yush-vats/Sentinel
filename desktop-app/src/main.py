"""
SENTINEL Desktop Application - FIXED DETECTION
Main entry point with working abnormality detection
"""
import sys
import asyncio
from pathlib import Path
from datetime import datetime, timezone, timedelta
import uuid
from typing import Optional
import pytz
import threading
import time

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from ui.login_window import LoginWindow
from ui.main_window import MainWindow
from core.config import Config
from auth.jwt_handler import JWTHandler
from core.session_manager import SessionManager
from storage.local_db import LocalDB
from sync.sync_client import SyncClient
from detection.input_collector import InputCollector
from detection.abnormality_detector import AbnormalityDetector, Abnormality
from detection.abnormality_detector import EnhancedAbnormalityDetector
import customtkinter as ctk

# IST Timezone using pytz
IST = pytz.timezone('Asia/Kolkata')

def now_ist():
    """Get current time in IST"""
    return datetime.now(IST)

def parse_datetime_ist(dt_string: str) -> datetime:
    """Parse datetime string to IST (handles both naive and aware datetimes)"""
    try:
        dt = datetime.fromisoformat(dt_string.replace('Z', '+00:00'))
        
        if dt.tzinfo is None:
            dt = IST.localize(dt)
        else:
            dt = dt.astimezone(IST)
        
        return dt
    except Exception as e:
        print(f"⚠️ Error parsing datetime '{dt_string}': {e}")
        try:
            clean_str = dt_string.split('+')[0].split('.')[0]
            dt = datetime.strptime(clean_str, '%Y-%m-%d %H:%M:%S')
            return IST.localize(dt)
        except:
            print(f"❌ Failed to parse datetime, using current time")
            return now_ist()


class SentinelApp:
    """Complete SENTINEL Application with WORKING Detection"""
    
    def __init__(self):
        # Core components
        self.jwt_handler = JWTHandler(Config.DB_DIR)
        self.local_db = LocalDB(Config.DB_PATH)
        
        # UI components
        self.login_window = None
        self.main_window = None
        
        # Session components
        self.session_manager: Optional[SessionManager] = None
        self.sync_client: Optional[SyncClient] = None
        self.input_collector: Optional[InputCollector] = None
        self.abnormality_detector: Optional[AbnormalityDetector] = None
        
        # User data
        self.user = None
        self.access_token = None
        
        # Current session
        self.current_session_id: Optional[str] = None
        
        # Background tasks
        self.detection_task = None
        self.detection_running = False
        self.sync_task = None
    
    def run(self):
        """Start the application"""
        print("🛡️ SENTINEL Desktop App Starting...")
        print(f"API: {Config.API_BASE_URL}")
        print(f"Database: {Config.DB_PATH}")
        
        # Check for saved tokens
        if self.jwt_handler.has_saved_tokens() and self.jwt_handler.is_token_valid():
            print("✅ Found valid saved session")
            self.user = self.jwt_handler.get_user_data()
            self.access_token = self.jwt_handler.get_access_token()
            
            if self.user and self.access_token and 'id' in self.user:
                try:
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
        """Check for incomplete sessions in local database"""
        try:
            session = self.local_db.get_active_session(self.user['id'])
            
            if session:
                start_time_str = session['start_time']
                print(f"📅 Checking session start_time: {start_time_str}")
                
                start_time = parse_datetime_ist(start_time_str)
                current_time = now_ist()
                
                print(f"   Parsed start time (IST): {start_time}")
                print(f"   Current time (IST): {current_time}")
                
                time_since_start = current_time - start_time
                minutes_ago = time_since_start.total_seconds() / 60
                
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
        """Show dialog to recover incomplete session"""
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
        
        title = ctk.CTkLabel(
            container,
            text="🔄 Incomplete Session Detected",
            font=("Arial", 22, "bold"),
            text_color="#F59E0B"
        )
        title.pack(pady=(0, 20))
        
        start_time = parse_datetime_ist(incomplete_session['start_time'])
        time_ago = (now_ist() - start_time).total_seconds() / 60
        
        if time_ago < 60:
            time_str = f"{int(time_ago)} minutes ago"
        else:
            time_str = f"{int(time_ago / 60)} hours {int(time_ago % 60)} minutes ago"
        
        info_frame = ctk.CTkFrame(container, fg_color="#0F172A", corner_radius=15)
        info_frame.pack(fill="x", pady=(0, 20))
        
        ctk.CTkLabel(
            info_frame,
            text=f"You started a session {time_str}",
            font=("Arial", 14),
            text_color="#94A3B8"
        ).pack(pady=(20, 10))
        
        ctk.CTkLabel(
            info_frame,
            text=f"Started at: {start_time.strftime('%I:%M %p on %B %d')}",
            font=("Arial", 12),
            text_color="#64748B"
        ).pack(pady=(0, 10))
        
        stats_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
        stats_frame.pack(pady=(10, 20), padx=30)
        
        ctk.CTkLabel(
            stats_frame,
            text=f"⏱️ Work: {incomplete_session['total_work_minutes']} min",
            font=("Arial", 12),
            text_color="#10B981"
        ).pack(pady=3)
        
        ctk.CTkLabel(
            stats_frame,
            text=f"☕ Break: {incomplete_session['total_break_minutes']} min",
            font=("Arial", 12),
            text_color="#F59E0B"
        ).pack(pady=3)
        
        message = ctk.CTkLabel(
            container,
            text="The app was closed before the session ended.\nWould you like to continue or start fresh?",
            font=("Arial", 13),
            text_color="#94A3B8",
            justify="center"
        )
        message.pack(pady=(0, 25))
        
        button_frame = ctk.CTkFrame(container, fg_color="transparent")
        button_frame.pack(fill="x")
        
        def continue_session():
            print(f"📋 Continuing session: {incomplete_session['id']}")
            self.current_session_id = incomplete_session['id']
            dialog.destroy()
            root.destroy()
            self.show_main_window()
        
        continue_btn = ctk.CTkButton(
            button_frame,
            text="▶️ Continue Session",
            command=continue_session,
            height=50,
            font=("Arial", 14, "bold"),
            fg_color="#10B981",
            hover_color="#059669",
            corner_radius=10
        )
        continue_btn.pack(side="left", expand=True, fill="x", padx=(0, 10))
        
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
        
        fresh_btn = ctk.CTkButton(
            button_frame,
            text="🆕 Start Fresh",
            command=start_fresh,
            height=50,
            font=("Arial", 14, "bold"),
            fg_color="#6B7280",
            hover_color="#4B5563",
            corner_radius=10
        )
        fresh_btn.pack(side="right", expand=True, fill="x", padx=(10, 0))
        
        def on_closing():
            start_fresh()
        
        dialog.protocol("WM_DELETE_WINDOW", on_closing)
        root.mainloop()
    
    def show_login(self):
        """Show login window"""
        self.login_window = LoginWindow(
            on_login_success=self.on_login_success,
            api_base_url=Config.API_BASE_URL
        )
        self.login_window.mainloop()
    
    def on_login_success(self, user: dict, access_token: str):
        """Handle successful login"""
        self.user = user
        self.access_token = access_token
        
        self.jwt_handler.save_tokens(
            access_token=access_token,
            refresh_token="",
            user_data=user
        )
        
        print(f"\n✅ Login successful!")
        print(f"User: {user['full_name']} ({user['email']})")
        print(f"Role: {user['role']}")
        
        self.initialize_session_components()
        self.show_main_window()
    
    def initialize_session_components(self):
        """Initialize all session-related components"""
        print("\n🔧 Initializing components...")
        
        # Session manager
        self.session_manager = SessionManager(
            api_base_url=Config.API_BASE_URL,
            access_token=self.access_token,
            employee_id=self.user['id'],
            on_state_change=self.on_session_state_change,
            on_sync_error=self.on_sync_error
        )
        
        # Sync client
        self.sync_client = SyncClient(
            api_base_url=Config.API_BASE_URL,
            access_token=self.access_token,
            employee_id=self.user['id'],
            local_db=self.local_db,
            on_sync_complete=self.on_sync_complete,
            on_sync_error=self.on_sync_error,
            sync_interval_seconds=Config.SYNC_INTERVAL_SECONDS
        )
        
        # Input collector (FIXED: Now with proper callback)
        self.input_collector = InputCollector(
            on_pattern_detected=self.on_pattern_detected,
            buffer_size=1000
        )
        
        # Abnormality detector (FIXED: Now with proper callback)
        self.abnormality_detector = AbnormalityDetector(
            on_abnormality_detected=self.on_abnormality_detected,
            confidence_threshold=Config.ABNORMALITY_CONFIDENCE_THRESHOLD
        )
        
        print("✓ All components initialized")
    
    def show_main_window(self):
        """Show main work session window"""
        self.main_window = MainWindow(
            user=self.user,
            access_token=self.access_token,
            time_engine=self.session_manager.time_engine
        )
        
        # Wire up callbacks
        self.main_window.on_start_session = self.start_integrated_session
        self.main_window.on_end_session = self.end_integrated_session
        self.main_window.on_take_break = self.take_break
        self.main_window.on_end_break = self.end_break
        self.main_window.on_take_lunch = self.take_lunch
        self.main_window.on_end_lunch = self.end_lunch
        self.main_window.on_logout = self.logout
        
        # Start main loop
        self.main_window.mainloop()
    
    def take_break(self):
        """Take a break"""
        try:
            self.session_manager.take_break()
            print("☕ Break started")
            
            # Stop detection during break
            self.stop_detection()
            
        except Exception as e:
            print(f"❌ Break failed: {e}")
            if self.main_window:
                self.main_window.status_label.configure(
                    text=f"Break failed: {str(e)}",
                    text_color="#EF4444"
                )
    
    def end_break(self):
        """End break and resume work"""
        try:
            self.session_manager.end_break()
            print("▶ Resumed work")
            
            # Resume detection
            self.start_detection()
            
        except Exception as e:
            print(f"❌ Resume failed: {e}")
    
    def take_lunch(self):
        """Take lunch break"""
        try:
            self.session_manager.take_lunch()
            print("🍽 Lunch started")
            
            # Stop detection during lunch
            self.stop_detection()
            
        except Exception as e:
            print(f"❌ Lunch failed: {e}")
            if self.main_window:
                self.main_window.status_label.configure(
                    text=f"Lunch failed: {str(e)}",
                    text_color="#EF4444"
                )
    
    def end_lunch(self):
        """End lunch and resume work"""
        try:
            self.session_manager.end_lunch()
            print("▶ Resumed work from lunch")
            
            # Resume detection
            self.start_detection()
            
        except Exception as e:
            print(f"❌ Resume failed: {e}")
    
    def start_integrated_session(self):
        """Start session with full integration - FIXED"""
        if self.session_manager.time_engine.state.value != 'idle':
            print("⚠️ Session already running locally")
            if self.main_window:
                self.main_window.status_label.configure(
                    text="Session already active",
                    text_color="#F59E0B"
                )
            return
        
        try:
            if not self.current_session_id:
                self.current_session_id = str(uuid.uuid4())
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self.session_manager.start_session())
            loop.close()
            
            if result.get("conflict"):
                existing = result.get("existing_session", {})
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
            else:
                print(f"\n▶️ Continuing session: {self.current_session_id}")
                if result.get('backend_session_id'):
                    self.local_db.update_session(
                        session_id=self.current_session_id,
                        status='active'
                    )
            
            # 🔥 CRITICAL FIX: Start detection AFTER session starts
            print("\n🔍 Starting abnormality detection...")
            self.start_detection()
            
            print(f"   Backend synced: {result.get('synced', False)}")
            
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
                    text=f"Failed to start session: {str(e)}",
                    text_color="#EF4444"
                )
    
    def start_detection(self):
        """🔥 NEW: Start input collection and detection"""
        if self.detection_running:
            print("⚠️ Detection already running")
            return
        
        print("🚀 Starting enhanced detection pipeline...")
        
        # Start input collector with tracking callbacks
        self.input_collector.start_collecting()
        print("  ✓ Input collector started")
        
        # Start detection session
        self.abnormality_detector.start_session()
        print("  ✓ Detection session initialized")
        
        # Start detection loop in background thread
        self.detection_running = True
        self.detection_task = threading.Thread(
            target=self._detection_loop,
            daemon=True
        )
        self.detection_task.start()
        print("  ✓ Detection loop started")
        
        # Start auto-sync
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.sync_client.start_auto_sync())
        print("  ✓ Auto-sync started")
        
        print("✅ Enhanced detection pipeline fully active!")
        print(f"   - Continuous monitoring")
        print(f"   - Analysis every 5 minutes")
        print(f"   - Risk calculation every 30 minutes")    
    def stop_detection(self):
        """🔥 NEW: Stop detection"""
        if not self.detection_running:
            return
        
        print("⏸️ Stopping detection...")
        
        self.detection_running = False
        self.input_collector.stop_collecting()
        
        print("  ✓ Detection stopped")
    
def _detection_loop(self):
    """🔥 ENHANCED: Background detection with 30-min risk calculation"""
    print("🔄 Enhanced detection loop running...")
    
    analysis_interval = 300  # Run comprehensive analysis every 5 minutes
    last_analysis = datetime.now()
    
    while self.detection_running:
        try:
            current_time = datetime.now()
            
            # Get current state
            state = self.session_manager.get_current_state()
            is_working = state['state'] == 'working'
            
            # Track idle if working
            if is_working:
                idle_seconds = self.input_collector.get_activity_summary().get('idle_seconds', 0)
                self.abnormality_detector.track_idle(idle_seconds, True)
            
            # Run comprehensive analysis every 5 minutes
            if (current_time - last_analysis).total_seconds() >= analysis_interval:
                print(f"\n📊 Running scheduled analysis...")
                self.abnormality_detector.run_periodic_analysis()
                last_analysis = current_time
            
            # Check if 30-minute risk calculation is due
            if self.abnormality_detector.should_calculate_risk():
                risk = self.abnormality_detector.calculate_current_risk()
                print(f"⚠️ 30-min risk score: {risk:.1f}/100")
                
                # Update session risk in local DB
                if self.current_session_id:
                    self.local_db.update_session(
                        session_id=self.current_session_id,
                        risk_score=self.abnormality_detector.get_average_risk()
                    )
                
                # Report to backend
                if self.current_session_id:
                    try:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        # Update session risk on backend
                        loop.run_until_complete(
                            self.session_manager.sync_session_state()
                        )
                        loop.close()
                    except Exception as e:
                        print(f"  ❌ Failed to sync risk score: {e}")
            
        except Exception as e:
            print(f"❌ Detection error: {e}")
            import traceback
            traceback.print_exc()
        
        # Wait before next check (check every 30 seconds)
        time.sleep(30)
    
    print("⏹️ Detection loop stopped")    
    def show_session_conflict_dialog(self, existing_session: dict):
        """Show dialog when active session exists"""
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
        
        title = ctk.CTkLabel(
            container,
            text="⚠️ Active Session Found",
            font=("Arial", 20, "bold"),
            text_color="#F59E0B"
        )
        title.pack(pady=(0, 20))
        
        start_time = existing_session.get('start_time', '')
        if start_time:
            try:
                start_dt = parse_datetime_ist(start_time)
                start_time_str = start_dt.strftime('%I:%M %p on %B %d')
            except:
                start_time_str = start_time
        else:
            start_time_str = "Unknown time"
        
        message = ctk.CTkLabel(
            container,
            text=f"You have an active session that started at:\n\n{start_time_str}\n\n"
                 f"Work time: {existing_session.get('total_work_minutes', 0)} minutes\n"
                 f"Break time: {existing_session.get('total_break_minutes', 0)} minutes",
            font=("Arial", 12),
            text_color="#94A3B8",
            justify="center"
        )
        message.pack(pady=(0, 30))
        
        button_frame = ctk.CTkFrame(container, fg_color="transparent")
        button_frame.pack(fill="x", pady=(0, 0))
        
        def continue_session():
            dialog.destroy()
            if self.main_window:
                self.main_window.status_label.configure(
                    text="Continuing existing session (not yet implemented)",
                    text_color="#F59E0B"
                )
        
        continue_btn = ctk.CTkButton(
            button_frame,
            text="Continue Session",
            command=continue_session,
            height=45,
            font=("Arial", 13, "bold"),
            fg_color="#10B981",
            hover_color="#059669"
        )
        continue_btn.pack(side="left", expand=True, fill="x", padx=(0, 10))
        
        def end_and_start_new():
            dialog.destroy()
            
            try:
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
                    
                    # Start detection
                    self.start_detection()
                    
                    print(f"\n✅ New session started: {self.current_session_id}")
                    
                    if self.main_window:
                        self.main_window.status_label.configure(
                            text="New session started successfully",
                            text_color="#10B981"
                        )
            except Exception as e:
                print(f"❌ Failed to start new session: {e}")
                if self.main_window:
                    self.main_window.status_label.configure(
                        text=f"Failed: {str(e)}",
                        text_color="#EF4444"
                    )
        
        end_btn = ctk.CTkButton(
            button_frame,
            text="End & Start New",
            command=end_and_start_new,
            height=45,
            font=("Arial", 13, "bold"),
            fg_color="#EF4444",
            hover_color="#DC2626"
        )
        end_btn.pack(side="right", expand=True, fill="x", padx=(10, 0))
    
    def end_integrated_session(self):
        """End session with full integration"""
        try:
            # Stop detection FIRST
            self.stop_detection()
            
            # End session in manager
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            summary = loop.run_until_complete(self.session_manager.end_session())
            loop.close()
            
            # Update local DB
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
            
            # Show summary in main window
            if self.main_window:
                self.main_window.show_session_summary(summary)
            
            print(f"\n✅ Session ended")
            print(f"   Work: {summary['work_minutes']} min")
            print(f"   Break: {summary['break_minutes']} min")
            print(f"   Risk Score: {risk_score:.1f}/100")
            
            # Get final abnormality summary
            abnormalities = self.abnormality_detector.get_session_abnormalities()
            print(f"   Total Abnormalities: {len(abnormalities)}")
            
            # Clear detection data
            self.abnormality_detector.clear_session()
            self.input_collector.clear_buffers()
            self.current_session_id = None
            
            # Change button to Logout after session ends
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
    
    def logout(self):
        """Logout user and return to login screen"""
        print("\n🚪 Logging out...")
        
        # Stop detection if running
        self.stop_detection()
        
        # Clear saved tokens
        self.jwt_handler.clear_tokens()
        
        # Close main window
        if self.main_window:
            self.main_window.destroy()
        
        # Reset user data
        self.user = None
        self.access_token = None
        self.current_session_id = None
        
        print("✓ Logged out successfully")
        
        # Show login window again
        self.show_login()
    
    def on_session_state_change(self, state, data):
        """Handle session state changes"""
        print(f"📊 Session state: {state.value}")
        
        # Update UI if main window exists
        if self.main_window:
            self.main_window.update_state_ui(state, data)
    
    def on_sync_complete(self, summary):
        """Handle sync completion"""
        print(f"✓ Sync complete: {summary['sessions_synced']} sessions, "
              f"{summary['abnormalities_synced']} abnormalities")
    
    def on_sync_error(self, error):
        """Handle sync errors"""
        print(f"⚠️ Sync error: {error}")
    
    def on_pattern_detected(self, pattern):
        """🔥 NEW: Handle detected input patterns"""
        print(f"🔍 Pattern detected: {pattern['type']}")
        print(f"   Confidence: {pattern.get('confidence', 0)}")
        print(f"   Details: {pattern.get('details', 'N/A')}")
        
        # Update UI to show pattern detection
        if self.main_window:
            self.main_window.after(0, lambda: self.main_window.status_label.configure(
                text=f"🔍 Pattern: {pattern['type']}",
                text_color="#60A5FA"
            ))
    
    def on_abnormality_detected(self, abnormality: Abnormality):
        """🔥 FIXED: Handle detected abnormalities with better feedback"""
        print(f"\n🚨 ABNORMALITY DETECTED!")
        print(f"   Type: {abnormality.abnormality_type}")
        print(f"   Confidence: {abnormality.confidence_score:.2%}")
        print(f"   Description: {abnormality.metadata.get('description', 'N/A')}")
        print(f"   Metadata: {abnormality.metadata}")
        
        # Show notification in UI
        if self.main_window:
            self.main_window.after(0, lambda: self.main_window.status_label.configure(
                text=f"⚠️ {abnormality.abnormality_type} detected ({abnormality.confidence_score:.0%})",
                text_color="#F59E0B"
            ))


def main():
    """Application entry point"""
    try:
        # Ensure directories exist
        Config.ensure_dirs()
        
        # Check for --reset flag to clear saved tokens
        if len(sys.argv) > 1 and sys.argv[1] == '--reset':
            print("🔄 Resetting saved session...")
            jwt_handler = JWTHandler(Config.DB_DIR)
            jwt_handler.clear_tokens()
            print("✓ Saved tokens cleared")
        
        # Create and run app
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