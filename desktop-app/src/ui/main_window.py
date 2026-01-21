"""
Main Work Session Window for SENTINEL Desktop App
FIXED: Break button reappears when token available
FIXED: Better state management
"""
import customtkinter as ctk
from datetime import datetime
from typing import Optional, Callable
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.time_engine import SessionState


class MainWindow(ctk.CTk):
    """Main work session tracking window with modern UI"""
    
    def __init__(self, user: dict, access_token: str, time_engine=None):
        super().__init__()
        
        self.user = user
        self.access_token = access_token
        
        # Use external time engine (from SessionManager)
        self.time_engine = time_engine
        
        # Callbacks for session control (set by main app)
        self.on_start_session: Optional[Callable] = None
        self.on_end_session: Optional[Callable] = None
        self.on_take_break: Optional[Callable] = None
        self.on_end_break: Optional[Callable] = None
        self.on_take_lunch: Optional[Callable] = None
        self.on_end_lunch: Optional[Callable] = None
        self.on_logout: Optional[Callable] = None
        
        # Track previous state to detect changes
        self.previous_state = None
        self.previous_tokens = 0
        
        # Configure window
        self.title(f"SENTINEL - {user['full_name']}")
        self.geometry("1000x700")
        self.resizable(False, False)
        
        # Set theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Center window
        self.center_window()
        
        # Create UI
        self.create_widgets()
        
        # Start update loop
        self.update_ui()
        
    def center_window(self):
        """Center window on screen"""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')
    
    def create_widgets(self):
        """Create and layout all widgets"""
        
        # ============ HEADER ============
        header = ctk.CTkFrame(self, height=70, fg_color="#0F172A", corner_radius=0)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        # Logo and title
        title_frame = ctk.CTkFrame(header, fg_color="transparent")
        title_frame.pack(side="left", padx=30)
        
        title = ctk.CTkLabel(
            title_frame,
            text="🛡️ SENTINEL",
            font=("Arial", 22, "bold"),
            text_color="#60A5FA"
        )
        title.pack(side="left")
        
        # User info and logout section
        user_section = ctk.CTkFrame(header, fg_color="transparent")
        user_section.pack(side="right", padx=30)
        
        # Logout button
        self.logout_button = ctk.CTkButton(
            user_section,
            text="🚪 Logout",
            command=self.handle_logout,
            width=100,
            height=35,
            font=("Arial", 12, "bold"),
            fg_color="#6B7280",
            hover_color="#4B5563",
            corner_radius=8
        )
        self.logout_button.pack(side="right", padx=(15, 0))
        
        # User info
        user_frame = ctk.CTkFrame(user_section, fg_color="transparent")
        user_frame.pack(side="right")
        
        user_name = ctk.CTkLabel(
            user_frame,
            text=self.user['full_name'],
            font=("Arial", 13, "bold")
        )
        user_name.pack(anchor="e")
        
        user_role = ctk.CTkLabel(
            user_frame,
            text=self.user['role'].replace('_', ' ').title(),
            font=("Arial", 10),
            text_color="#94A3B8"
        )
        user_role.pack(anchor="e")
        
        # ============ MAIN CONTENT ============
        main = ctk.CTkFrame(self, fg_color="#1E293B")
        main.pack(fill="both", expand=True)
        
        # Content container with padding
        content = ctk.CTkFrame(main, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=40, pady=30)
        
        # ============ LEFT COLUMN - TIMER ============
        left_col = ctk.CTkFrame(content, fg_color="transparent")
        left_col.pack(side="left", fill="both", expand=True, padx=(0, 20))
        
        # Timer card
        timer_card = ctk.CTkFrame(left_col, fg_color="#0F172A", corner_radius=20)
        timer_card.pack(fill="both", expand=True)
        
        # State badge
        self.state_badge = ctk.CTkLabel(
            timer_card,
            text="● Not Started",
            font=("Arial", 12, "bold"),
            text_color="#64748B",
            fg_color="#1E293B",
            corner_radius=20,
            padx=20,
            pady=8
        )
        self.state_badge.pack(pady=(30, 20))
        
        # Main work timer
        timer_label_text = ctk.CTkLabel(
            timer_card,
            text="WORK TIME",
            font=("Arial", 11, "bold"),
            text_color="#64748B"
        )
        timer_label_text.pack()
        
        self.work_timer_label = ctk.CTkLabel(
            timer_card,
            text="00:00:00",
            font=("Arial", 72, "bold"),
            text_color="#10B981"
        )
        self.work_timer_label.pack(pady=(10, 30))
        
        # Break timer (hidden by default)
        self.break_timer_card = ctk.CTkFrame(
            timer_card,
            fg_color="#F59E0B",
            corner_radius=15,
            height=100
        )
        
        break_label = ctk.CTkLabel(
            self.break_timer_card,
            text="BREAK TIME",
            font=("Arial", 11, "bold"),
            text_color="white"
        )
        break_label.pack(pady=(15, 5))
        
        self.break_timer_label = ctk.CTkLabel(
            self.break_timer_card,
            text="00:00",
            font=("Arial", 40, "bold"),
            text_color="white"
        )
        self.break_timer_label.pack(pady=(0, 15))
        
        # Session control button
        self.session_button = ctk.CTkButton(
            timer_card,
            text="Start Session",
            command=self.toggle_session,
            height=55,
            font=("Arial", 16, "bold"),
            fg_color="#10B981",
            hover_color="#059669",
            corner_radius=12
        )
        self.session_button.pack(pady=(20, 30), padx=40, fill="x")
        
        # ============ RIGHT COLUMN - STATS & CONTROLS ============
        right_col = ctk.CTkFrame(content, fg_color="transparent", width=380)
        right_col.pack(side="right", fill="both")
        right_col.pack_propagate(False)
        
        # Progress card
        progress_card = ctk.CTkFrame(right_col, fg_color="#0F172A", corner_radius=20)
        progress_card.pack(fill="x", pady=(0, 20))
        
        progress_title = ctk.CTkLabel(
            progress_card,
            text="Daily Progress",
            font=("Arial", 16, "bold")
        )
        progress_title.pack(pady=(25, 15), padx=25, anchor="w")
        
        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(
            progress_card,
            height=12,
            corner_radius=6,
            progress_color="#10B981",
            fg_color="#1E293B"
        )
        self.progress_bar.set(0)
        self.progress_bar.pack(padx=25, pady=(0, 10), fill="x")
        
        self.progress_text = ctk.CTkLabel(
            progress_card,
            text="0 / 400 minutes · 0%",
            font=("Arial", 12),
            text_color="#94A3B8"
        )
        self.progress_text.pack(padx=25, anchor="w")
        
        # Stats grid
        stats_grid = ctk.CTkFrame(progress_card, fg_color="transparent")
        stats_grid.pack(pady=(15, 25), padx=25, fill="x")
        
        # Work stat
        work_stat = self.create_stat_box(stats_grid, "Work", "0m", "#10B981")
        work_stat.pack(side="left", expand=True, fill="x", padx=(0, 10))
        self.work_stat_value = work_stat.winfo_children()[1]
        
        # Break stat
        break_stat = self.create_stat_box(stats_grid, "Break", "0m", "#F59E0B")
        break_stat.pack(side="left", expand=True, fill="x")
        self.break_stat_value = break_stat.winfo_children()[1]
        
        # Break controls card
        break_card = ctk.CTkFrame(right_col, fg_color="#0F172A", corner_radius=20)
        break_card.pack(fill="x", pady=(0, 20))
        
        break_title = ctk.CTkLabel(
            break_card,
            text="Break Management",
            font=("Arial", 16, "bold")
        )
        break_title.pack(pady=(25, 10), padx=25, anchor="w")
        
        # Break tokens
        self.token_label = ctk.CTkLabel(
            break_card,
            text="Break Tokens Available: 0",
            font=("Arial", 12),
            text_color="#94A3B8"
        )
        self.token_label.pack(padx=25, anchor="w", pady=(0, 15))
        
        # Break buttons
        self.break_button = ctk.CTkButton(
            break_card,
            text="☕ Take Break (10 min)",
            command=self.take_break,
            height=45,
            font=("Arial", 13, "bold"),
            fg_color="#F59E0B",
            hover_color="#D97706",
            corner_radius=10,
            state="disabled"
        )
        self.break_button.pack(padx=25, pady=(0, 10), fill="x")
        
        self.end_break_button = ctk.CTkButton(
            break_card,
            text="▶ Resume Work",
            command=self.end_break,
            height=45,
            font=("Arial", 13, "bold"),
            fg_color="#10B981",
            hover_color="#059669",
            corner_radius=10
        )
        
        self.lunch_button = ctk.CTkButton(
            break_card,
            text="🍽 Take Lunch (30 min)",
            command=self.take_lunch,
            height=45,
            font=("Arial", 13, "bold"),
            fg_color="#8B5CF6",
            hover_color="#7C3AED",
            corner_radius=10,
            state="disabled"
        )
        self.lunch_button.pack(padx=25, pady=(0, 25), fill="x")
        
        self.end_lunch_button = ctk.CTkButton(
            break_card,
            text="▶ Resume Work",
            command=self.end_lunch,
            height=45,
            font=("Arial", 13, "bold"),
            fg_color="#10B981",
            hover_color="#059669",
            corner_radius=10
        )
        
        # Status card
        status_card = ctk.CTkFrame(right_col, fg_color="#0F172A", corner_radius=20, height=80)
        status_card.pack(fill="x")
        status_card.pack_propagate(False)
        
        self.status_label = ctk.CTkLabel(
            status_card,
            text="Ready to start your work session",
            font=("Arial", 12),
            text_color="#94A3B8",
            wraplength=320
        )
        self.status_label.pack(expand=True, padx=25)
    
    def create_stat_box(self, parent, label: str, value: str, color: str):
        """Create a stat box"""
        box = ctk.CTkFrame(parent, fg_color="#1E293B", corner_radius=12)
        
        label_widget = ctk.CTkLabel(
            box,
            text=label.upper(),
            font=("Arial", 10, "bold"),
            text_color="#64748B"
        )
        label_widget.pack(pady=(15, 5))
        
        value_widget = ctk.CTkLabel(
            box,
            text=value,
            font=("Arial", 24, "bold"),
            text_color=color
        )
        value_widget.pack(pady=(0, 15))
        
        return box
    
    def handle_logout(self):
        """Handle logout button click"""
        # Confirm if session is active
        if self.time_engine and self.time_engine.state != SessionState.IDLE:
            dialog = ctk.CTkToplevel(self)
            dialog.title("Confirm Logout")
            dialog.geometry("400x200")
            dialog.resizable(False, False)
            
            # Center dialog
            dialog.update_idletasks()
            x = (dialog.winfo_screenwidth() // 2) - 200
            y = (dialog.winfo_screenheight() // 2) - 100
            dialog.geometry(f"400x200+{x}+{y}")
            
            # Make modal
            dialog.transient(self)
            dialog.grab_set()
            
            # Content
            container = ctk.CTkFrame(dialog, fg_color="#1E293B")
            container.pack(fill="both", expand=True, padx=30, pady=30)
            
            title = ctk.CTkLabel(
                container,
                text="⚠️ Active Session",
                font=("Arial", 18, "bold"),
                text_color="#F59E0B"
            )
            title.pack(pady=(0, 15))
            
            message = ctk.CTkLabel(
                container,
                text="You have an active session.\nEnd it before logging out.",
                font=("Arial", 12),
                text_color="#94A3B8",
                justify="center"
            )
            message.pack(pady=(0, 20))
            
            ok_btn = ctk.CTkButton(
                container,
                text="OK",
                command=dialog.destroy,
                height=40,
                font=("Arial", 13, "bold"),
                fg_color="#3B82F6",
                hover_color="#2563EB"
            )
            ok_btn.pack(fill="x")
        else:
            # No active session, logout directly
            if self.on_logout:
                self.on_logout()
    
    def toggle_session(self):
        """Start or end session"""
        if not self.time_engine:
            self.status_label.configure(
                text="Error: No time engine connected",
                text_color="#EF4444"
            )
            return
        
        if self.time_engine.state == SessionState.IDLE:
            # Call external start handler
            if self.on_start_session:
                self.on_start_session()
        else:
            # Call external end handler
            if self.on_end_session:
                self.on_end_session()
    
    def take_break(self):
        """Take a break"""
        if self.on_take_break:
            self.on_take_break()
    
    def end_break(self):
        """End break and resume work"""
        if self.on_end_break:
            self.on_end_break()
    
    def take_lunch(self):
        """Take lunch break"""
        if self.on_take_lunch:
            self.on_take_lunch()
    
    def end_lunch(self):
        """End lunch and resume work"""
        if self.on_end_lunch:
            self.on_end_lunch()
    
    def update_state_ui(self, state: SessionState, data: dict):
        """Update UI based on state change"""
        
        # Get current token count
        tokens_available = data.get('break_tokens', 0)
        
        if state == SessionState.WORKING:
            # Working state
            self.state_badge.configure(
                text="● Working",
                text_color="#10B981",
                fg_color="#0F3B2F"
            )
            self.work_timer_label.configure(text_color="#10B981")
            self.session_button.configure(
                text="End Session",
                fg_color="#EF4444",
                hover_color="#DC2626"
            )
            
            # Enable/disable break button based on tokens
            if tokens_available > 0:
                self.break_button.configure(state="normal")
            else:
                self.break_button.configure(state="disabled")
            
            self.lunch_button.configure(state="normal" if not data.get('lunch_taken') else "disabled")
            self.status_label.configure(
                text="Work time is being tracked",
                text_color="#10B981"
            )
            
            # Hide break timer and resume buttons
            self.break_timer_card.pack_forget()
            self.end_break_button.pack_forget()
            self.end_lunch_button.pack_forget()
            
            # CRITICAL FIX: Make sure break button is visible again
            self.break_button.pack(padx=25, pady=(0, 10), fill="x")
            
        elif state == SessionState.ON_BREAK:
            # Break state
            self.state_badge.configure(
                text="● On Break",
                text_color="#F59E0B",
                fg_color="#3B2817"
            )
            self.work_timer_label.configure(text_color="#475569")
            self.break_button.configure(state="disabled")
            self.lunch_button.configure(state="disabled")
            self.status_label.configure(
                text="Taking a break - work timer paused",
                text_color="#F59E0B"
            )
            
            # Show break timer
            self.break_timer_card.configure(fg_color="#F59E0B")
            self.break_timer_card.pack(pady=(0, 20), padx=40, fill="x")
            
            # Show resume button, hide break button
            self.break_button.pack_forget()
            self.end_break_button.pack(padx=25, pady=(0, 10), fill="x")
            
        elif state == SessionState.ON_LUNCH:
            # Lunch state
            self.state_badge.configure(
                text="● Lunch Break",
                text_color="#8B5CF6",
                fg_color="#2E1A47"
            )
            self.work_timer_label.configure(text_color="#475569")
            self.break_button.configure(state="disabled")
            self.lunch_button.configure(state="disabled")
            self.status_label.configure(
                text="Lunch break - work timer paused",
                text_color="#8B5CF6"
            )
            
            # Show lunch timer
            self.break_timer_card.configure(fg_color="#8B5CF6")
            self.break_timer_card.pack(pady=(0, 20), padx=40, fill="x")
            
            # Show resume button, hide lunch button
            self.lunch_button.pack_forget()
            self.end_lunch_button.pack(padx=25, pady=(0, 25), fill="x")
        
        elif state == SessionState.IDLE:
            # Reset to idle state
            self.state_badge.configure(
                text="● Not Started",
                text_color="#64748B",
                fg_color="#1E293B"
            )
            self.work_timer_label.configure(text_color="#10B981")
            self.session_button.configure(
                text="Start Session",
                fg_color="#10B981",
                hover_color="#059669"
            )
            self.break_button.configure(state="disabled")
            self.lunch_button.configure(state="disabled")
            self.status_label.configure(
                text="Ready to start your work session",
                text_color="#94A3B8"
            )
            
            # Hide break timers
            self.break_timer_card.pack_forget()
            self.end_break_button.pack_forget()
            self.end_lunch_button.pack_forget()
    
    def update_ui(self):
        """Update UI with current state"""
        if not self.time_engine:
            self.after(1000, self.update_ui)
            return
        
        state = self.time_engine.update()
        current_state = self.time_engine.state
        current_tokens = state['break_tokens']
        
        # CRITICAL FIX: Detect when break token becomes available
        if current_state == SessionState.WORKING:
            if current_tokens > self.previous_tokens:
                print(f"🔄 Token regenerated! Previous: {self.previous_tokens}, Current: {current_tokens}")
                # Re-enable break button
                self.break_button.configure(state="normal")
                self.status_label.configure(
                    text="✨ Break token regenerated!",
                    text_color="#10B981"
                )
        
        # Update previous values
        self.previous_tokens = current_tokens
        self.previous_state = current_state
        
        # Update work timer
        h = state['work_seconds'] // 3600
        m = (state['work_seconds'] % 3600) // 60
        s = state['work_seconds'] % 60
        self.work_timer_label.configure(text=f"{h:02d}:{m:02d}:{s:02d}")
        
        # Update break timer with COUNTDOWN if on break
        if self.time_engine.state in [SessionState.ON_BREAK, SessionState.ON_LUNCH]:
            remaining = state['current_break_remaining']
            bm = remaining // 60
            bs = remaining % 60
            self.break_timer_label.configure(text=f"{bm:02d}:{bs:02d}")
        
        # Update stats
        self.work_stat_value.configure(text=f"{state['work_minutes']}m")
        self.break_stat_value.configure(text=f"{state['break_minutes']}m")
        
        # Update progress
        self.progress_bar.set(state['progress'])
        pct = int(state['progress'] * 100)
        self.progress_text.configure(
            text=f"{state['work_minutes']} / {state['target_minutes']} minutes · {pct}%"
        )
        
        # Update tokens
        self.token_label.configure(
            text=f"Break Tokens Available: {state['break_tokens']}"
        )
        
        # Schedule next update
        self.after(1000, self.update_ui)
    
    def show_session_summary(self, summary: dict):
        """Show session summary dialog"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Session Complete")
        dialog.geometry("500x400")
        dialog.resizable(False, False)
        
        # Center dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - 250
        y = (dialog.winfo_screenheight() // 2) - 200
        dialog.geometry(f"500x400+{x}+{y}")
        
        # Make modal
        dialog.transient(self)
        dialog.grab_set()
        
        # Content
        container = ctk.CTkFrame(dialog, fg_color="#1E293B")
        container.pack(fill="both", expand=True, padx=30, pady=30)
        
        # Title
        title = ctk.CTkLabel(
            container,
            text="🎉 Session Completed!",
            font=("Arial", 24, "bold"),
            text_color="#10B981"
        )
        title.pack(pady=(0, 30))
        
        # Summary stats
        stats_frame = ctk.CTkFrame(container, fg_color="#0F172A", corner_radius=15)
        stats_frame.pack(fill="x", pady=(0, 20))
        
        # Work time
        work_stat = ctk.CTkFrame(stats_frame, fg_color="transparent")
        work_stat.pack(fill="x", padx=30, pady=15)
        
        ctk.CTkLabel(
            work_stat,
            text="⏱️ Total Work Time",
            font=("Arial", 13),
            text_color="#94A3B8"
        ).pack(side="left")
        
        ctk.CTkLabel(
            work_stat,
            text=f"{summary['work_minutes']} minutes",
            font=("Arial", 16, "bold"),
            text_color="#10B981"
        ).pack(side="right")
        
        # Break time
        break_stat = ctk.CTkFrame(stats_frame, fg_color="transparent")
        break_stat.pack(fill="x", padx=30, pady=15)
        
        ctk.CTkLabel(
            break_stat,
            text="☕ Total Break Time",
            font=("Arial", 13),
            text_color="#94A3B8"
        ).pack(side="left")
        
        ctk.CTkLabel(
            break_stat,
            text=f"{summary['break_minutes']} minutes",
            font=("Arial", 16, "bold"),
            text_color="#F59E0B"
        ).pack(side="right")
        
        # Session duration
        duration_stat = ctk.CTkFrame(stats_frame, fg_color="transparent")
        duration_stat.pack(fill="x", padx=30, pady=15)
        
        ctk.CTkLabel(
            duration_stat,
            text="🕐 Session Duration",
            font=("Arial", 13),
            text_color="#94A3B8"
        ).pack(side="left")
        
        session_mins = summary['session_seconds'] // 60
        ctk.CTkLabel(
            duration_stat,
            text=f"{session_mins} minutes",
            font=("Arial", 16, "bold"),
            text_color="#60A5FA"
        ).pack(side="right")
        
        # Target completion
        completion_frame = ctk.CTkFrame(container, fg_color="#0F172A", corner_radius=15)
        completion_frame.pack(fill="x", pady=(0, 20))
        
        percentage = int(summary['progress'] * 100)
        if summary['completed']:
            status_text = "✅ Daily target completed!"
            status_color = "#10B981"
        else:
            status_text = f"Target: {percentage}% complete"
            status_color = "#F59E0B"
        
        ctk.CTkLabel(
            completion_frame,
            text=status_text,
            font=("Arial", 14, "bold"),
            text_color=status_color
        ).pack(pady=20)
        
        # Close button
        close_btn = ctk.CTkButton(
            container,
            text="Close",
            command=dialog.destroy,
            height=45,
            font=("Arial", 14, "bold"),
            fg_color="#3B82F6",
            hover_color="#2563EB"
        )
        close_btn.pack(fill="x")