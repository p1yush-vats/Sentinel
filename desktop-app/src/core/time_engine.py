"""
Time Tracking Engine

Manages work/break time accounting with proper state tracking.
Enforces 50 min work / 10 min break per hour rule.
"""
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, Callable


class SessionState(Enum):
    """Session states"""
    IDLE = "idle"
    WORKING = "working"
    ON_BREAK = "on_break"
    ON_LUNCH = "on_lunch"
    ENDED = "ended"


class TimeEngine:
    """
    Core time tracking engine
    
    Rules:
    - 50 minutes of work per hour
    - 10 minute break token per hour (non-stackable)
    - 30 minute mandatory lunch break
    - 400 minutes total work time per day (8 hours)
    """
    
    def __init__(self, on_state_change: Optional[Callable] = None):
        """
        Initialize time engine
        
        Args:
            on_state_change: Callback when state changes (state, data)
        """
        self.on_state_change = on_state_change
        
        # Session tracking
        self.state = SessionState.IDLE
        self.session_start_time: Optional[datetime] = None
        self.session_end_time: Optional[datetime] = None
        
        # Work time tracking
        self.work_start_time: Optional[datetime] = None
        self.total_work_seconds = 0
        
        # Break tracking
        self.break_start_time: Optional[datetime] = None
        self.current_break_duration = 0  # Duration of CURRENT break
        self.total_break_seconds = 0  # Total break time accumulated
        self.break_tokens_available = 0
        self.current_hour_start: Optional[datetime] = None
        
        # Lunch tracking
        self.lunch_start_time: Optional[datetime] = None
        self.lunch_taken = False
        
        # Constants
        self.WORK_MINUTES_PER_HOUR = 50
        self.BREAK_MINUTES_PER_HOUR = 10
        self.LUNCH_DURATION_MINUTES = 30
        self.DAILY_WORK_TARGET_MINUTES = 400
    
    def start_session(self) -> dict:
        """Start a new work session"""
        if self.state != SessionState.IDLE:
            raise ValueError("Session already active")
        
        now = datetime.now()
        self.session_start_time = now
        self.current_hour_start = now
        self.state = SessionState.WORKING
        self.work_start_time = now
        self.break_tokens_available = 1
        
        # Reset counters
        self.total_work_seconds = 0
        self.total_break_seconds = 0
        self.current_break_duration = 0
        self.lunch_taken = False
        
        result = {
            "state": self.state.value,
            "session_start_time": self.session_start_time,
            "break_tokens": self.break_tokens_available
        }
        
        if self.on_state_change:
            self.on_state_change(self.state, result)
        
        return result
    
    def end_session(self) -> dict:
        """End the current work session"""
        if self.state == SessionState.IDLE:
            raise ValueError("No active session")
        
        # Stop any active work/break
        if self.state == SessionState.WORKING:
            self._pause_work()
        elif self.state == SessionState.ON_BREAK:
            self._end_break()
        elif self.state == SessionState.ON_LUNCH:
            self._end_lunch()
        
        self.session_end_time = datetime.now()
        prev_state = self.state
        self.state = SessionState.ENDED
        
        result = self.get_session_summary()
        
        if self.on_state_change:
            self.on_state_change(self.state, result)
        
        return result
    
    def take_break(self) -> dict:
        """Take a 10-minute break"""
        if self.state != SessionState.WORKING:
            raise ValueError("Must be working to take a break")
        
        if self.break_tokens_available <= 0:
            raise ValueError("No break tokens available")
        
        # Pause work timer
        self._pause_work()
        
        # Start break timer (FRESH)
        self.break_start_time = datetime.now()
        self.current_break_duration = self.BREAK_MINUTES_PER_HOUR * 60  # 10 min in seconds
        self.state = SessionState.ON_BREAK
        self.break_tokens_available -= 1
        
        result = {
            "state": self.state.value,
            "break_start_time": self.break_start_time,
            "break_duration_minutes": self.BREAK_MINUTES_PER_HOUR,
            "break_tokens": self.break_tokens_available
        }
        
        if self.on_state_change:
            self.on_state_change(self.state, result)
        
        return result
    
    def end_break(self) -> dict:
        """End break and resume work"""
        if self.state != SessionState.ON_BREAK:
            raise ValueError("Not on break")
        
        self._end_break()
        
        # Resume work
        self.work_start_time = datetime.now()
        self.state = SessionState.WORKING
        
        result = {
            "state": self.state.value,
            "break_tokens": self.break_tokens_available
        }
        
        if self.on_state_change:
            self.on_state_change(self.state, result)
        
        return result
    
    def take_lunch(self) -> dict:
        """Take 30-minute lunch break"""
        if self.state != SessionState.WORKING:
            raise ValueError("Must be working to take lunch")
        
        if self.lunch_taken:
            raise ValueError("Lunch already taken")
        
        # Pause work timer
        self._pause_work()
        
        # Start lunch timer (FRESH)
        self.lunch_start_time = datetime.now()
        self.current_break_duration = self.LUNCH_DURATION_MINUTES * 60  # 30 min in seconds
        self.state = SessionState.ON_LUNCH
        
        result = {
            "state": self.state.value,
            "lunch_start_time": self.lunch_start_time,
            "lunch_duration_minutes": self.LUNCH_DURATION_MINUTES
        }
        
        if self.on_state_change:
            self.on_state_change(self.state, result)
        
        return result
    
    def end_lunch(self) -> dict:
        """End lunch and resume work"""
        if self.state != SessionState.ON_LUNCH:
            raise ValueError("Not on lunch")
        
        self._end_lunch()
        self.lunch_taken = True
        
        # Resume work
        self.work_start_time = datetime.now()
        self.state = SessionState.WORKING
        
        result = {
            "state": self.state.value,
            "lunch_taken": self.lunch_taken
        }
        
        if self.on_state_change:
            self.on_state_change(self.state, result)
        
        return result
    
    def update(self) -> dict:
        """
        Update timers and check for hour boundaries
        Call this regularly (e.g., every second)
        
        Returns:
            Current state data
        """
        now = datetime.now()
        
        # Check if new hour started (issue new break token)
        if self.current_hour_start and self.state == SessionState.WORKING:
            if now - self.current_hour_start >= timedelta(hours=1):
                self.current_hour_start = now
                self.break_tokens_available = 1  # Non-stackable, always 1
        
        # Auto-end break after duration
        if self.state == SessionState.ON_BREAK:
            elapsed = (now - self.break_start_time).total_seconds()
            if elapsed >= self.BREAK_MINUTES_PER_HOUR * 60:
                self.end_break()
        
        # Auto-end lunch after duration
        if self.state == SessionState.ON_LUNCH:
            elapsed = (now - self.lunch_start_time).total_seconds()
            if elapsed >= self.LUNCH_DURATION_MINUTES * 60:
                self.end_lunch()
        
        return self.get_current_state()
    
    def get_current_state(self) -> dict:
        """Get current state and all time data"""
        now = datetime.now()
        
        # Calculate current work time
        work_seconds = self.total_work_seconds
        if self.state == SessionState.WORKING and self.work_start_time:
            work_seconds += (now - self.work_start_time).total_seconds()
        
        # Calculate current break elapsed time
        current_break_elapsed = 0
        if self.state == SessionState.ON_BREAK and self.break_start_time:
            current_break_elapsed = (now - self.break_start_time).total_seconds()
        elif self.state == SessionState.ON_LUNCH and self.lunch_start_time:
            current_break_elapsed = (now - self.lunch_start_time).total_seconds()
        
        # Calculate break countdown (remaining time)
        break_remaining = max(0, self.current_break_duration - current_break_elapsed)
        
        # Calculate session duration
        session_seconds = 0
        if self.session_start_time:
            end_time = self.session_end_time or now
            session_seconds = (end_time - self.session_start_time).total_seconds()
        
        return {
            "state": self.state.value,
            "session_seconds": int(session_seconds),
            "work_seconds": int(work_seconds),
            "break_seconds": int(self.total_break_seconds),
            "current_break_elapsed": int(current_break_elapsed),
            "current_break_remaining": int(break_remaining),
            "work_minutes": int(work_seconds // 60),
            "break_minutes": int(self.total_break_seconds // 60),
            "break_tokens": self.break_tokens_available,
            "lunch_taken": self.lunch_taken,
            "target_minutes": self.DAILY_WORK_TARGET_MINUTES,
            "progress": min(work_seconds / (self.DAILY_WORK_TARGET_MINUTES * 60), 1.0)
        }
    
    def get_session_summary(self) -> dict:
        """Get final session summary"""
        state = self.get_current_state()
        
        return {
            **state,
            "session_start_time": self.session_start_time,
            "session_end_time": self.session_end_time,
            "completed": state["work_minutes"] >= self.DAILY_WORK_TARGET_MINUTES
        }
    
    def _pause_work(self):
        """Pause work timer (internal)"""
        if self.work_start_time:
            self.total_work_seconds += (datetime.now() - self.work_start_time).total_seconds()
            self.work_start_time = None
    
    def _end_break(self):
        """End break timer (internal)"""
        if self.break_start_time:
            elapsed = (datetime.now() - self.break_start_time).total_seconds()
            self.total_break_seconds += elapsed
            self.break_start_time = None
            self.current_break_duration = 0  # Reset
    
    def _end_lunch(self):
        """End lunch timer (internal)"""
        if self.lunch_start_time:
            elapsed = (datetime.now() - self.lunch_start_time).total_seconds()
            self.total_break_seconds += elapsed
            self.lunch_start_time = None
            self.current_break_duration = 0  # Reset


# Example usage
if __name__ == "__main__":
    import time
    
    engine = TimeEngine()
    engine.start_session()
    
    print("Working for 5 seconds...")
    for i in range(5):
        time.sleep(1)
        state = engine.update()
        print(f"Work: {state['work_seconds']}s")
    
    print("\nTaking break...")
    engine.take_break()
    
    print("Break countdown:")
    for i in range(5):
        time.sleep(1)
        state = engine.update()
        remaining = state['current_break_remaining']
        print(f"Remaining: {remaining}s (countdown from 600)")
    
    engine.end_break()
    print("\nBreak ended, back to work!")