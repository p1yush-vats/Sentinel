"""
Input Collector

Collects keyboard/mouse METADATA only (privacy-safe).
NO actual content or keystrokes are recorded.
"""
from pynput import keyboard, mouse
from datetime import datetime
from typing import Optional, Callable, Dict, List
from collections import deque
import threading
import time


class InputMetadata:
    """Container for input metadata"""
    
    def __init__(self):
        self.timestamp = datetime.now()
        self.event_type: str = ""  # keystroke, mouse_move, mouse_click, paste
        self.interval_ms: Optional[int] = None  # Time since last event
        self.metadata: Dict = {}  # Additional metadata


class InputCollector:
    """
    Privacy-safe input collector
    
    COLLECTS:
    - Keystroke timing intervals (NOT content)
    - Mouse movement patterns (NOT positions)
    - Paste detection (NOT content)
    - Activity periods
    
    DOES NOT COLLECT:
    - Actual keystrokes
    - Actual text content
    - Screen content
    - Specific positions
    """
    
    def __init__(
        self,
        on_pattern_detected: Optional[Callable] = None,
        buffer_size: int = 1000
    ):
        """
        Initialize input collector
        
        Args:
            on_pattern_detected: Callback for detected patterns
            buffer_size: Size of event buffer
        """
        self.on_pattern_detected = on_pattern_detected
        self.buffer_size = buffer_size
        
        # Event buffers (recent events only)
        self.keystroke_intervals = deque(maxlen=buffer_size)
        self.mouse_movements = deque(maxlen=buffer_size)
        self.paste_events = deque(maxlen=100)
        
        # Tracking
        self.last_keystroke_time: Optional[datetime] = None
        self.last_mouse_time: Optional[datetime] = None
        self.is_collecting = False
        
        # Statistics
        self.stats = {
            "total_keystrokes": 0,
            "total_mouse_movements": 0,
            "total_pastes": 0,
            "session_start": None,
            "last_activity": None
        }
        
        # Listeners
        self.keyboard_listener: Optional[keyboard.Listener] = None
        self.mouse_listener: Optional[mouse.Listener] = None
        
        # Detection flags
        self.ctrl_pressed = False
        self.cmd_pressed = False
    
    def start_collecting(self):
        """Start collecting input metadata"""
        if self.is_collecting:
            return
        
        self.is_collecting = True
        self.stats["session_start"] = datetime.now()
        
        # Start keyboard listener
        self.keyboard_listener = keyboard.Listener(
            on_press=self._on_key_press,
            on_release=self._on_key_release
        )
        self.keyboard_listener.start()
        
        # Start mouse listener
        self.mouse_listener = mouse.Listener(
            on_move=self._on_mouse_move,
            on_click=self._on_mouse_click
        )
        self.mouse_listener.start()
        
        print("✓ Input collector started (privacy-safe mode)")
    
    def stop_collecting(self):
        """Stop collecting input metadata"""
        if not self.is_collecting:
            return
        
        self.is_collecting = False
        
        if self.keyboard_listener:
            self.keyboard_listener.stop()
        if self.mouse_listener:
            self.mouse_listener.stop()
        
        print("✓ Input collector stopped")
    
    def _on_key_press(self, key):
        """Handle key press (NO CONTENT RECORDED)"""
        try:
            now = datetime.now()
            
            # Track modifier keys for paste detection
            if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
                self.ctrl_pressed = True
            if key == keyboard.Key.cmd:
                self.cmd_pressed = True
            
            # Detect paste (Ctrl+V or Cmd+V)
            if (self.ctrl_pressed or self.cmd_pressed) and \
               (hasattr(key, 'char') and key.char == 'v'):
                self._on_paste_detected()
            
            # Record timing interval (NOT the key itself)
            if self.last_keystroke_time:
                interval_ms = int((now - self.last_keystroke_time).total_seconds() * 1000)
                self.keystroke_intervals.append(interval_ms)
            
            self.last_keystroke_time = now
            self.stats["total_keystrokes"] += 1
            self.stats["last_activity"] = now
            
        except Exception as e:
            print(f"Error in key handler: {e}")
    
    def _on_key_release(self, key):
        """Handle key release"""
        try:
            # Clear modifier flags
            if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
                self.ctrl_pressed = False
            if key == keyboard.Key.cmd:
                self.cmd_pressed = False
        except:
            pass
    
    def _on_mouse_move(self, x, y):
        """Handle mouse movement (NO POSITION RECORDED)"""
        try:
            now = datetime.now()
            
            # Record timing interval only (NOT position)
            if self.last_mouse_time:
                interval_ms = int((now - self.last_mouse_time).total_seconds() * 1000)
                
                # Only record if significant movement (debounce)
                if interval_ms > 100:  # 100ms debounce
                    self.mouse_movements.append(interval_ms)
                    self.stats["total_mouse_movements"] += 1
            
            self.last_mouse_time = now
            self.stats["last_activity"] = now
            
        except Exception as e:
            print(f"Error in mouse handler: {e}")
    
    def _on_mouse_click(self, x, y, button, pressed):
        """Handle mouse click"""
        try:
            if pressed:
                self.stats["last_activity"] = datetime.now()
        except:
            pass
    
    def _on_paste_detected(self):
        """Handle paste detection (NO CONTENT)"""
        try:
            now = datetime.now()
            
            self.paste_events.append({
                "timestamp": now,
                "interval_since_last": self._get_time_since_last_paste()
            })
            
            self.stats["total_pastes"] += 1
            
            # Trigger pattern detection
            if self.on_pattern_detected:
                # Check if suspicious paste pattern
                if len(self.paste_events) >= 3:
                    recent_pastes = list(self.paste_events)[-3:]
                    time_span = (recent_pastes[-1]["timestamp"] - recent_pastes[0]["timestamp"]).total_seconds()
                    
                    # 3+ pastes in 10 seconds = suspicious
                    if time_span < 10:
                        self.on_pattern_detected({
                            "type": "rapid_paste",
                            "confidence": 0.8,
                            "details": f"{len(recent_pastes)} pastes in {time_span:.1f}s"
                        })
        
        except Exception as e:
            print(f"Error in paste detection: {e}")
    
def get_detailed_activity(self) -> Dict:
    """
    🔥 NEW: Get detailed activity data for feeding to detector
    
    Returns all collected data in a format the detector can consume
    """
    keystrokes = list(self.keystroke_intervals)
    pastes = list(self.paste_events)
    mouse = list(self.mouse_movements)
    
    return {
        'keystroke_intervals': keystrokes,
        'paste_events': pastes,
        'mouse_movements': mouse,
        'total_keystrokes': self.stats['total_keystrokes'],
        'total_pastes': self.stats['total_pastes'],
        'total_mouse_movements': self.stats['total_mouse_movements']
    }

# Example usage
if __name__ == "__main__":
    def on_pattern(pattern):
        print(f"\n🚨 Pattern detected: {pattern}")
    
    collector = InputCollector(on_pattern_detected=on_pattern)
    collector.start_collecting()
    
    print("Collecting input metadata for 30 seconds...")
    print("Try typing and moving your mouse")
    
    try:
        for i in range(30):
            time.sleep(1)
            
            if i % 5 == 0:
                summary = collector.get_activity_summary()
                print(f"\n📊 Activity: {summary['total_keystrokes']} keystrokes, "
                      f"{summary['total_pastes']} pastes")
        
        # Final analysis
        pattern = collector.get_keystroke_pattern()
        print(f"\n📈 Keystroke Pattern Analysis:")
        print(f"   Average interval: {pattern.get('avg_interval_ms', 0)}ms")
        print(f"   Consistency: {pattern.get('consistency_score', 0)}")
        print(f"   Mechanical suspected: {pattern.get('mechanical_suspected', False)}")
        
    finally:
        collector.stop_collecting()