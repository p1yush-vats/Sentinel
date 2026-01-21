"""
SENTINEL Desktop Application - Complete Integration
Main entry point with all components integrated
FIXED: Timezone handling and session recovery
"""
import sys
import asyncio
from pathlib import Path
from datetime import datetime, timezone, timedelta
import uuid
from typing import Optional
import pytz

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
import customtkinter as ctk

# IST Timezone using pytz
IST = pytz.timezone('Asia/Kolkata')

def now_ist():
    """Get current time in IST"""
    return datetime.now(IST)

def parse_datetime_ist(dt_string: str) -> datetime:
    """
    Parse datetime string to IST (handles both naive and aware datetimes)
    
    FIXED: Properly handles timezone-naive strings from database
    """
    try:
        # Try parsing as ISO format
        dt = datetime.fromisoformat(dt_string.replace('Z', '+00:00'))
        
        # If datetime is timezone-naive, assume it's IST
        if dt.tzinfo is None:
            dt = IST.localize(dt)
        else:
            # Convert to IST if it has a different timezone
            dt = dt.astimezone(IST)
        
        return dt
    except Exception as e:
        print(f"⚠️ Error parsing datetime '{dt_string}': {e}")
        # Fallback: try to parse as naive datetime and localize to IST
        try:
            # Remove timezone info if present
            clean_str = dt_string.split('+')[0].split('.')[0]
            dt = datetime.strptime(clean_str, '%Y-%m-%d %H:%M:%S')
            return IST.localize(dt)
        except:
            # Last resort: return current time
            print(f"❌ Failed to parse datetime, using current time")
            return now_ist()


class SentinelApp:
    """
    Complete SENTINEL Application
    
    Integrates:
    - Authentication
    - Session tracking
    - Input detection
    - Abnormality detection
    - Local storage
    - Backend synchronization
    """
    
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
            
            # Validate that we have complete user data
            if self.user and self.access_token and 'id' in self.user:
                try:
                    # Initialize components first
                    self.initialize_session_components()
                    
                    # Check for incomplete local session
                    incomplete_session = self.check_for_incomplete_session()
                    
                    if incomplete_session:
                        # Show recovery dialog before main window
                        self.show_session_recovery_dialog(incomplete_session)
                    else:
                        # No incomplete session, show main window normally
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
        
        # Show login if no valid saved session
        self.show_login()
    
    def check_for_incomplete_session(self) -> Optional[dict]:
        """
        Check for incomplete sessions in local database
        
        FIXED: Properly handles timezone comparisons
        
        Returns session if found within last 4 hours and not completed
        """
        try:
            # Get active session for this employee
            session = self.local_db.get_active_session(self.user['id'])
            
            if session:
                # CRITICAL FIX: Parse start_time with timezone handling
                start_time_str = session['start_time']
                print(f"🔍 Checking session start_time: {start_time_str}")
                
                start_time = parse_datetime_ist(start_time_str)
                current_time = now_ist()
                
                print(f"   Parsed start time (IST): {start_time}")
                print(f"   Current time (IST): {current_time}")
                
                # Check if session was started within last 4 hours
                time_since_start = current_time - start_time
                minutes_ago = time_since_start.total_seconds() / 60
                
                print(f"   Time since start: {minutes_ago:.1f} minutes ago")
                
                if time_since_start < timedelta(hours=Config.SESSION_RECOVERY_WINDOW_HOURS):
                    print(f"⚠️ Found incomplete session from {minutes_ago:.0f} minutes ago")
                    return session
                else:
                    print(f"⚠️ Found old incomplete session (>{Config.SESSION_RECOVERY_WINDOW_HOURS} hours), marking as abandoned")
                    # Mark old session as abandoned
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
        from datetime import datetime
        
        # Create a temporary window for the dialog
        root = ctk.CTk()
        root.withdraw()  # Hide the root window
        
        dialog = ctk.CTkToplevel(root)
        dialog.title("Session Recovery")
        dialog.geometry("550x400")
        dialog.resizable(False, False)
        
        # Center dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - 275
        y = (dialog.winfo_screenheight() // 2) - 200
        dialog.geometry(f"550x400+{x}+{y}")
        
        # Make it stay on top
        dialog.attributes('-topmost', True)
        dialog.focus_force()
        
        # Content
        container = ctk.CTkFrame(dialog, fg_color="#1E293B")
        container.pack(fill="both", expand=True, padx=30, pady=30)
        
        # Icon and title
        title = ctk.CTkLabel(
            container,
            text="🔄 Incomplete Session Detected",
            font=("Arial", 22, "bold"),
            text_color="#F59E0B"
        )
        title.pack(pady=(0, 20))
        
        # Session info
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
        
        # Session stats
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
        
        # Message
        message = ctk.CTkLabel(
            container,
            text="The app was closed before the session ended.\nWould you like to continue or start fresh?",
            font=("Arial", 13),
            text_color="#94A3B8",
            justify="center"
        )
        message.pack(pady=(0, 25))
        
        # Button frame
        button_frame = ctk.CTkFrame(container, fg_color="transparent")
        button_frame.pack(fill="x")
        
        # Continue button
        def continue_session():
            print(f"📋 Continuing session: {incomplete_session['id']}")
            self.current_session_id = incomplete_session['id']
            
            # TODO: Restore session state in TimeEngine
            # For now, we'll mark it as continued and start fresh tracking
            
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
        
        # Start fresh button
        def start_fresh():
            print(f"🆕 Starting fresh, abandoning session: {incomplete_session['id']}")
            
            # Mark old session as abandoned
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
        
        # Handle window close
        def on_closing():
            # Default to start fresh if closed
            start_fresh()
        
        dialog.protocol("WM_DELETE_WINDOW", on_closing)
        
        # Run dialog loop
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
        
        # Save tokens
        self.jwt_handler.save_tokens(
            access_token=access_token,
            refresh_token="",  # TODO: Get from login response
            user_data=user
        )
        
        print(f"\n✅ Login successful!")
        print(f"User: {user['full_name']} ({user['email']})")
        print(f"Role: {user['role']}")
        
        # Initialize components
        self.initialize_session_components()
        
        # Show main window
        self.show_main_window()
    
    def initialize_session_components(self):
        """Initialize all session-related components"""
        print("\n🔧 Initializing components...")
        
        # Session manager (handles time tracking + backend sync)
        self.session_manager = SessionManager(
            api_base_url=Config.API_BASE_URL,
            access_token=self.access_token,
            employee_id=self.user['id'],
            on_state_change=self.on_session_state_change,
            on_sync_error=self.on_sync_error
        )
        
        # Sync client (handles background syncing)
        self.sync_client = SyncClient(
            api_base_url=Config.API_BASE_URL,
            access_token=self.access_token,
            employee_id=self.user['id'],
            local_db=self.local_db,
            on_sync_complete=self.on_sync_complete,
            on_sync_error=self.on_sync_error,
            sync_interval_seconds=Config.SYNC_INTERVAL_SECONDS
        )
        
        # Input collector (privacy-safe input monitoring)
        self.input_collector = InputCollector(
            on_pattern_detected=self.on_pattern_detected,
            buffer_size=1000
        )
        
        # Abnormality detector
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
        except Exception as e:
            print(f"❌ Resume failed: {e}")
    
    def take_lunch(self):
        """Take lunch break"""
        try:
            self.session_manager.take_lunch()
            print("🍽 Lunch started")
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
        except Exception as e:
            print(f"❌ Resume failed: {e}")
    
    def start_integrated_session(self):
        """Start session with full integration"""
        # Check if already have local active session
        if self.session_manager.time_engine.state.value != 'idle':
            print("⚠️ Session already running locally")
            if self.main_window:
                self.main_window.status_label.configure(
                    text="Session already active",
                    text_color="#F59E0B"
                )
            return
        
        try:
            # Create local session ID (or use existing if continuing)
            if not self.current_session_id:
                self.current_session_id = str(uuid.uuid4())
            
            # Try to start session in manager (checks backend FIRST)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self.session_manager.start_session())
            loop.close()
            
            # Check for conflict (existing active session in backend)
            if result.get("conflict"):
                existing = result.get("existing_session", {})
                self.show_session_conflict_dialog(existing)
                return
            
            # If no conflict, session is now started (TimeEngine is running)
            # Check if we're continuing an existing session
            existing_session = self.local_db.get_session(self.current_session_id)
            
            if not existing_session:
                # New session - create in local DB
                self.local_db.create_session(
                    session_id=self.current_session_id,
                    employee_id=self.user['id'],
                    start_time=now_ist(),
                    backend_session_id=result.get('backend_session_id')
                )
                print(f"\n✅ New session started: {self.current_session_id}")
            else:
                # Continuing existing session
                print(f"\n▶️ Continuing session: {self.current_session_id}")
                # Update backend session ID if we got one
                if result.get('backend_session_id'):
                    self.local_db.update_session(
                        session_id=self.current_session_id,
                        status='active'
                    )
            
            # Start input collection
            self.input_collector.start_collecting()
            
            print(f"   Backend synced: {result.get('synced', False)}")
            
            if self.main_window:
                self.main_window.status_label.configure(
                    text="Session started successfully",
                    text_color="#10B981"
                )
            
        except Exception as e:
            print(f"❌ Session start failed: {e}")
            if self.main_window:
                self.main_window.status_label.configure(
                    text=f"Failed to start session: {str(e)}",
                    text_color="#EF4444"
                )
    
    def show_session_conflict_dialog(self, existing_session: dict):
        """Show dialog when active session exists"""
        dialog = ctk.CTkToplevel(self.main_window)
        dialog.title("Active Session Found")
        dialog.geometry("500x300")
        dialog.resizable(False, False)
        
        # Center dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - 250
        y = (dialog.winfo_screenheight() // 2) - 150
        dialog.geometry(f"500x300+{x}+{y}")
        
        # Make modal
        dialog.transient(self.main_window)
        dialog.grab_set()
        
        # Content
        container = ctk.CTkFrame(dialog, fg_color="#1E293B")
        container.pack(fill="both", expand=True, padx=30, pady=30)
        
        # Warning icon and title
        title = ctk.CTkLabel(
            container,
            text="⚠️ Active Session Found",
            font=("Arial", 20, "bold"),
            text_color="#F59E0B"
        )
        title.pack(pady=(0, 20))
        
        # Message
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
        
        # Button frame
        button_frame = ctk.CTkFrame(container, fg_color="transparent")
        button_frame.pack(fill="x", pady=(0, 0))
        
        # Continue button
        def continue_session():
            dialog.destroy()
            # TODO: Load existing session into UI
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
        
        # End and start new button
        def end_and_start_new():
            dialog.destroy()
            
            # Retry with force flag
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(
                    self.session_manager.start_session(force_end_existing=True)
                )
                loop.close()
                
                if not result.get("conflict"):
                    # Success! Save and start
                    self.local_db.create_session(
                        session_id=self.current_session_id,
                        employee_id=self.user['id'],
                        start_time=now_ist(),
                        backend_session_id=result.get('backend_session_id')
                    )
                    
                    self.input_collector.start_collecting()
                    
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
            # Stop input collection
            self.input_collector.stop_collecting()
            
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
    
    def logout(self):
        """Logout user and return to login screen"""
        print("\n🚪 Logging out...")
        
        # Clear saved tokens
        self.jwt_handler.clear_tokens()
        
        # Close main window
        if self.main_window:
            self.main_window.destroy()
        
        # Reset user data
        self.user = None
        self.access_token = None
        self.current_session_id = None
        
        # Stop any active collection
        if self.input_collector:
            self.input_collector.stop_collecting()
        
        print("✓ Logged out successfully")
        
        # Show login window again
        self.show_login()
    
    def start_background_tasks(self):
        """Start background detection and sync tasks"""
        # Detection task (runs every 30 seconds)
        def detection_loop():
            while True:
                try:
                    # Get input patterns
                    pattern = self.input_collector.get_keystroke_pattern()
                    activity = self.input_collector.get_activity_summary()
                    
                    # Get current work state
                    state = self.session_manager.get_current_state()
                    is_working = state['state'] == 'working'
                    
                    # Run detection
                    abnormalities = self.abnormality_detector.run_comprehensive_analysis(
                        keystroke_pattern=pattern,
                        activity_summary=activity,
                        is_work_time=is_working
                    )
                    
                    # Report to backend
                    if abnormalities and self.current_session_id:
                        for abn in abnormalities:
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                            loop.run_until_complete(
                                self.sync_client.report_abnormality(
                                    session_id=self.current_session_id,
                                    abnormality_type=abn.abnormality_type,
                                    confidence_score=abn.confidence_score,
                                    metadata=abn.metadata
                                )
                            )
                            loop.close()
                
                except Exception as e:
                    print(f"Detection error: {e}")
                
                # Wait 30 seconds
                import time
                time.sleep(30)
        
        # Start detection in thread
        import threading
        self.detection_task = threading.Thread(target=detection_loop, daemon=True)
        self.detection_task.start()
        
        # Start auto-sync
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.sync_client.start_auto_sync())
    
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
        """Handle detected input patterns"""
        print(f"🔍 Pattern: {pattern['type']} (confidence: {pattern['details']})")
        
    def on_abnormality_detected(self, abnormality: Abnormality):
        """Handle detected abnormalities"""
        print(f"🚨 ABNORMALITY: {abnormality.abnormality_type}")
        print(f"   Confidence: {abnormality.confidence_score:.2%}")
        print(f"   Details: {abnormality.metadata.get('description')}")
        
        # Show notification in UI
        if self.main_window:
            self.main_window.after(0, lambda: self.main_window.status_label.configure(
                text=f"⚠️ Detected: {abnormality.abnormality_type}",
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