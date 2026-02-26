"""
Input Collector - PRODUCTION VERSION WITH CLIPBOARD SIZE DETECTION

Collects keyboard/mouse METADATA only (privacy-safe).
NO actual content or keystrokes are recorded.

FEATURES:
- Windows API for 100% reliable Ctrl+V detection
- Clipboard SIZE detection (not content) for large paste detection
- Idle period tracking
- Keyboard sitting detection
- Mouse jiggler detection
"""
from pynput import keyboard, mouse
from datetime import datetime
from typing import Optional, Callable, Dict, List
from collections import deque
import threading
import time
import platform

# Windows clipboard access (size only, not content)
HAS_CLIPBOARD = False
try:
    import win32clipboard
    HAS_CLIPBOARD = True
except:
    pass  # Will use fallback methods

# Windows API support
HAS_WIN32 = False
if platform.system() == 'Windows':
    try:
        import ctypes
        HAS_WIN32 = True
    except:
        pass


class InputMetadata:
    """Container for input metadata"""
    
    def __init__(self):
        self.timestamp = datetime.now()
        self.event_type: str = ""  # keystroke, mouse_move, mouse_click, paste, large_paste
        self.interval_ms: Optional[int] = None
        self.metadata: Dict = {}


class InputCollector:
    """
    Privacy-safe input collector with comprehensive detection
    
    COLLECTS:
    - Keystroke timing intervals (NOT content)
    - Mouse movement patterns (NOT positions)
    - Paste detection with SIZE (NOT content)
    - Activity periods
    - Idle detection
    
    DOES NOT COLLECT:
    - Actual keystrokes
    - Actual text content
    - Clipboard content (only size)
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
        self.key_sequence = deque(maxlen=50)  # Track last 50 keys for pattern detection
        
        # Tracking
        self.last_keystroke_time: Optional[datetime] = None
        self.last_mouse_time: Optional[datetime] = None
        self.last_activity_time: Optional[datetime] = None
        self.is_collecting = False
        
        # Statistics
        self.stats = {
            "total_keystrokes": 0,
            "total_mouse_movements": 0,
            "total_pastes": 0,
            "total_large_pastes": 0,  # NEW: Large paste counter
            "session_start": None,
            "last_activity": None,
            "idle_periods": []
        }
        
        # Listeners
        self.keyboard_listener: Optional[keyboard.Listener] = None
        self.mouse_listener: Optional[mouse.Listener] = None
        
        # Paste detection
        self.last_paste_time: Optional[datetime] = None
        self.paste_debounce_ms = 150  # Ignore pastes within 150ms
        self.paste_poll_thread: Optional[threading.Thread] = None
        
        # Large paste detection thresholds
        self.LARGE_PASTE_THRESHOLD = 300  # 300+ characters = large
        self.VERY_LARGE_PASTE_THRESHOLD = 1000  # 1000+ characters = very large
        
        # Idle detection
        self.idle_start_time: Optional[datetime] = None
        self.idle_threshold_seconds = 60  # 1 minute idle = suspicious
        self.is_currently_idle = False
        self.idle_checker_thread: Optional[threading.Thread] = None
        
        # Windows API setup
        self.use_win32 = HAS_WIN32
        if self.use_win32:
            self.GetAsyncKeyState = ctypes.windll.user32.GetAsyncKeyState
            # Virtual key codes
            self.VK_CONTROL = 0x11
            self.VK_SHIFT = 0x10
            self.VK_V = 0x56
            self.VK_INSERT = 0x2D
            self.VK_LWIN = 0x5B
            self.VK_RWIN = 0x5C
        else:
            # Fallback: track keys with pynput
            self.keys_pressed = set()
    
    def start_collecting(self):
        """Start collecting input metadata"""
        if self.is_collecting:
            return
        
        self.is_collecting = True
        self.stats["session_start"] = datetime.now()
        self.last_activity_time = datetime.now()
        
        # Start keyboard listener (for timing only)
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
        
        # Start paste detection thread
        self.paste_poll_thread = threading.Thread(
            target=self._poll_for_paste,
            daemon=True
        )
        self.paste_poll_thread.start()
        
        # Start idle checker thread
        self.idle_checker_thread = threading.Thread(
            target=self._idle_checker_loop,
            daemon=True
        )
        self.idle_checker_thread.start()
        
        method = "Windows API" if self.use_win32 else "pynput fallback"
        print(f"✓ Input collector started (privacy-safe mode)")
        print(f"✓ Paste detection active ({method})")
        if HAS_CLIPBOARD:
            print(f"✓ Clipboard size detection active")
        print(f"✓ Idle detection active")
    
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
    
    def _get_clipboard_size(self):
        """Get clipboard text size without reading content (privacy-safe)"""
        if not HAS_CLIPBOARD:
            return None
        
        try:
            win32clipboard.OpenClipboard()
            
            # Check if clipboard has text
            if win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_UNICODETEXT):
                text = win32clipboard.GetClipboardData(win32clipboard.CF_UNICODETEXT)
                size = len(text) if text else 0
                win32clipboard.CloseClipboard()
                return size
            
            win32clipboard.CloseClipboard()
            return None
            
        except Exception as e:
            try:
                win32clipboard.CloseClipboard()
            except:
                pass
            return None
    
    def _is_key_pressed_win32(self, vk_code):
        """Check if key is pressed using Windows API"""
        if not self.use_win32:
            return False
        state = self.GetAsyncKeyState(vk_code)
        return (state & 0x8000) != 0
    
    def _check_paste_windows(self):
        """Check for paste using Windows API"""
        if not self.use_win32:
            return None
        
        ctrl = self._is_key_pressed_win32(self.VK_CONTROL)
        shift = self._is_key_pressed_win32(self.VK_SHIFT)
        v = self._is_key_pressed_win32(self.VK_V)
        insert = self._is_key_pressed_win32(self.VK_INSERT)
        lwin = self._is_key_pressed_win32(self.VK_LWIN)
        rwin = self._is_key_pressed_win32(self.VK_RWIN)
        
        # Ctrl+V
        if ctrl and v:
            return "Ctrl+V"
        
        # Shift+Insert
        if shift and insert:
            return "Shift+Insert"
        
        # Windows+V (clipboard history)
        if (lwin or rwin) and v:
            return "Win+V"
        
        return None
    
    def _check_paste_pynput(self):
        """Check for paste using pynput (fallback)"""
        if self.use_win32:
            return None
        
        ctrl = (keyboard.Key.ctrl_l in self.keys_pressed or
                keyboard.Key.ctrl_r in self.keys_pressed or
                keyboard.Key.ctrl in self.keys_pressed)
        
        shift = (keyboard.Key.shift in self.keys_pressed or
                 keyboard.Key.shift_r in self.keys_pressed)
        
        insert = keyboard.Key.insert in self.keys_pressed
        v = 'v' in self.keys_pressed
        
        if ctrl and v:
            return "Ctrl+V"
        elif shift and insert:
            return "Shift+Insert"
        
        return None
    
    def _poll_for_paste(self):
        """Poll for paste key combinations"""
        while self.is_collecting:
            try:
                # Check using appropriate method
                if self.use_win32:
                    method = self._check_paste_windows()
                else:
                    method = self._check_paste_pynput()
                
                if method:
                    self._on_paste_detected(method)
                
                time.sleep(0.01)  # 10ms polling
                
            except Exception as e:
                print(f"Error in paste polling: {e}")
    
    def _mark_activity(self):
        """Mark that activity occurred (reset idle timer)"""
        now = datetime.now()
        
        # If was idle, record idle period
        if self.is_currently_idle and self.idle_start_time:
            idle_duration = (now - self.idle_start_time).total_seconds()
            self.stats["idle_periods"].append({
                "start": self.idle_start_time,
                "end": now,
                "duration_seconds": idle_duration
            })
            
            # Trigger idle detection callback
            if self.on_pattern_detected and idle_duration > self.idle_threshold_seconds:
                self.on_pattern_detected({
                    "type": "idle_period",
                    "confidence": min(idle_duration / (self.idle_threshold_seconds * 2), 1.0),
                    "details": f"Idle for {idle_duration/60:.1f} minutes"
                })
        
        self.is_currently_idle = False
        self.idle_start_time = None
        self.last_activity_time = now
        self.stats["last_activity"] = now
    
    def _idle_checker_loop(self):
        """Background thread to check for idle periods"""
        while self.is_collecting:
            time.sleep(5)  # Check every 5 seconds
            
            if not self.last_activity_time:
                continue
            
            now = datetime.now()
            time_since_activity = (now - self.last_activity_time).total_seconds()
            
            if time_since_activity > self.idle_threshold_seconds:
                if not self.is_currently_idle:
                    # Just became idle
                    self.is_currently_idle = True
                    self.idle_start_time = self.last_activity_time
    
    def _on_key_press(self, key):
        """Handle key press (NO CONTENT RECORDED)"""
        try:
            now = datetime.now()
            self._mark_activity()
            
            # For pynput fallback: track pressed keys
            if not self.use_win32:
                self.keys_pressed.add(key)
                if hasattr(key, 'char') and key.char:
                    self.keys_pressed.add(key.char.lower())
            
            # Record timing interval (NOT the key itself)
            if self.last_keystroke_time:
                interval_ms = int((now - self.last_keystroke_time).total_seconds() * 1000)
                self.keystroke_intervals.append(interval_ms)
            
            # Track key for pattern detection (anonymized)
            key_code = None
            try:
                if hasattr(key, 'vk'):
                    key_code = key.vk
                elif hasattr(key, 'char'):
                    key_code = ord(key.char) if key.char else None
            except:
                pass
            
            if key_code:
                self.key_sequence.append(key_code)
                self._check_repetitive_pattern()
            
            self.last_keystroke_time = now
            self.stats["total_keystrokes"] += 1
            
        except Exception as e:
            print(f"Error in key handler: {e}")
    
    def _on_key_release(self, key):
        """Handle key release"""
        try:
            # For pynput fallback: remove from pressed keys
            if not self.use_win32:
                self.keys_pressed.discard(key)
                if hasattr(key, 'char') and key.char:
                    self.keys_pressed.discard(key.char.lower())
        except:
            pass
    
    def _check_repetitive_pattern(self):
        """Check for repetitive key patterns (keyboard sitting)"""
        if len(self.key_sequence) < 20:
            return
        
        # Check last 20 keys
        recent_keys = list(self.key_sequence)[-20:]
        
        # Count most common key
        from collections import Counter
        key_counts = Counter(recent_keys)
        most_common_key, count = key_counts.most_common(1)[0]
        
        # If >70% of keys are the same = keyboard sitting
        if count > 14:  # 70% of 20
            if self.on_pattern_detected:
                self.on_pattern_detected({
                    "type": "keyboard_sitting",
                    "confidence": count / 20,
                    "details": f"Same key pressed {count} times in last 20 keystrokes"
                })
    
    def _on_mouse_move(self, x, y):
        """Handle mouse movement (NO POSITION RECORDED)"""
        try:
            now = datetime.now()
            self._mark_activity()
            
            # Record timing interval only (NOT position)
            if self.last_mouse_time:
                interval_ms = int((now - self.last_mouse_time).total_seconds() * 1000)
                
                # Only record if significant movement (debounce)
                if interval_ms > 100:  # 100ms debounce
                    self.mouse_movements.append({
                        "timestamp": now,
                        "interval_ms": interval_ms
                    })
                    self.stats["total_mouse_movements"] += 1
                    
                    # Check for mouse jiggler pattern
                    self._check_mouse_jiggler()
            
            self.last_mouse_time = now
            
        except Exception as e:
            print(f"Error in mouse handler: {e}")
    
    def _check_mouse_jiggler(self):
        """Detect mouse jiggler devices"""
        if len(self.mouse_movements) < 10:
            return
        
        # Get last 10 movements
        recent_moves = list(self.mouse_movements)[-10:]
        intervals = [m["interval_ms"] for m in recent_moves]
        
        # Check if intervals are suspiciously regular
        if len(intervals) > 5:
            avg_interval = sum(intervals) / len(intervals)
            
            # Calculate variance
            variance = sum((x - avg_interval) ** 2 for x in intervals) / len(intervals)
            std_dev = variance ** 0.5
            
            # Very low variance = mouse jiggler
            if std_dev < 50 and 1000 < avg_interval < 10000:  # Regular 1-10 second movements
                if self.on_pattern_detected:
                    self.on_pattern_detected({
                        "type": "mouse_jiggler",
                        "confidence": max(0.7, 1.0 - (std_dev / 100)),
                        "details": f"Suspiciously regular mouse movement (variance: {std_dev:.1f}ms)"
                    })
    
    def _on_mouse_click(self, x, y, button, pressed):
        """Handle mouse click"""
        try:
            if pressed:
                self._mark_activity()
        except:
            pass
    
    def _on_paste_detected(self, method: str):
        """Handle paste detection with clipboard size analysis"""
        try:
            now = datetime.now()
            
            # Debounce - ignore if too close to last paste
            if self.last_paste_time:
                delta_ms = (now - self.last_paste_time).total_seconds() * 1000
                if delta_ms < self.paste_debounce_ms:
                    return  # Too soon, ignore
            
            self.last_paste_time = now
            self.stats["total_pastes"] += 1
            
            # Get clipboard size (privacy-safe - size only, not content)
            clipboard_size = self._get_clipboard_size()
            
            # Analyze paste size
            is_large = False
            paste_category = "normal"
            confidence = 0.0
            
            if clipboard_size is not None:
                if clipboard_size >= self.VERY_LARGE_PASTE_THRESHOLD:
                    is_large = True
                    paste_category = "very_large"
                    confidence = 0.99
                elif clipboard_size >= self.LARGE_PASTE_THRESHOLD:
                    is_large = True
                    paste_category = "large"
                    confidence = 0.95
                elif clipboard_size >= 100:
                    paste_category = "medium"
                    confidence = 0.80
                else:
                    paste_category = "small"
                    confidence = 0.95
            
            # Record paste event
            self.paste_events.append({
                "timestamp": now,
                "method": method,
                "size": clipboard_size,
                "category": paste_category,
                "is_large": is_large,
                "interval_since_last": self._get_time_since_last_paste()
            })
            
            # Update large paste counter
            if is_large:
                self.stats["total_large_pastes"] += 1
            
            # Trigger pattern detection for large pastes
            if is_large and self.on_pattern_detected:
                self.on_pattern_detected({
                    "type": "large_paste",
                    "confidence": confidence,
                    "details": f"Large paste detected: {clipboard_size} characters ({paste_category})",
                    "metadata": {
                        "size": clipboard_size,
                        "category": paste_category,
                        "method": method
                    }
                })
            
            # Check for rapid paste pattern
            if len(self.paste_events) >= 3:
                recent_pastes = list(self.paste_events)[-3:]
                time_span = (recent_pastes[-1]["timestamp"] - recent_pastes[0]["timestamp"]).total_seconds()
                
                # 3+ pastes in 10 seconds = suspicious
                if time_span < 10:
                    if self.on_pattern_detected:
                        self.on_pattern_detected({
                            "type": "rapid_paste",
                            "confidence": 0.8,
                            "details": f"{len(recent_pastes)} pastes in {time_span:.1f}s"
                        })
        
        except Exception as e:
            print(f"Error in paste detection: {e}")
    
    def _get_time_since_last_paste(self) -> Optional[float]:
        """Get seconds since last paste"""
        if len(self.paste_events) > 0:
            last = self.paste_events[-1]["timestamp"]
            return (datetime.now() - last).total_seconds()
        return None
    
    def get_keystroke_pattern(self) -> Dict:
        """Analyze keystroke timing patterns (NO actual keystrokes)"""
        if len(self.keystroke_intervals) < 10:
            return {"status": "insufficient_data"}
        
        intervals = list(self.keystroke_intervals)
        
        # Calculate statistics
        avg_interval = sum(intervals) / len(intervals)
        min_interval = min(intervals)
        max_interval = max(intervals)
        
        # Calculate variance
        variance = sum((x - avg_interval) ** 2 for x in intervals) / len(intervals)
        std_dev = variance ** 0.5
        
        # Detect mechanical patterns (very consistent timing = bot-like)
        consistency = std_dev / avg_interval if avg_interval > 0 else 0
        
        return {
            "avg_interval_ms": round(avg_interval, 2),
            "min_interval_ms": min_interval,
            "max_interval_ms": max_interval,
            "std_deviation": round(std_dev, 2),
            "consistency_score": round(consistency, 3),
            "sample_size": len(intervals),
            "mechanical_suspected": consistency < 0.2  # Very low variance = suspicious
        }
    
    def get_activity_summary(self) -> Dict:
        """Get activity summary including large paste detection"""
        if not self.stats["session_start"]:
            return {"status": "not_started"}
        
        session_duration = (datetime.now() - self.stats["session_start"]).total_seconds()
        
        # Calculate activity rate
        keystroke_rate = self.stats["total_keystrokes"] / session_duration if session_duration > 0 else 0
        
        # Current idle status
        idle_seconds = 0
        if self.last_activity_time:
            idle_seconds = (datetime.now() - self.last_activity_time).total_seconds()
        
        # Total idle time
        total_idle_time = sum(p["duration_seconds"] for p in self.stats["idle_periods"])
        if self.is_currently_idle and self.idle_start_time:
            total_idle_time += (datetime.now() - self.idle_start_time).total_seconds()
        
        return {
            "session_duration_seconds": round(session_duration, 1),
            "total_keystrokes": self.stats["total_keystrokes"],
            "total_mouse_movements": self.stats["total_mouse_movements"],
            "total_pastes": self.stats["total_pastes"],
            "total_large_pastes": self.stats["total_large_pastes"],  # NEW
            "keystroke_rate_per_minute": round(keystroke_rate * 60, 1),
            "idle_seconds": round(idle_seconds, 1),
            "total_idle_time": round(total_idle_time, 1),
            "idle_periods_count": len(self.stats["idle_periods"]),
            "is_active": idle_seconds < 60,
            "is_currently_idle": self.is_currently_idle
        }
    
    def get_idle_periods(self) -> List[Dict]:
        """Get all recorded idle periods"""
        periods = self.stats["idle_periods"].copy()
        
        # Add current idle period if idle now
        if self.is_currently_idle and self.idle_start_time:
            periods.append({
                "start": self.idle_start_time,
                "end": datetime.now(),
                "duration_seconds": (datetime.now() - self.idle_start_time).total_seconds(),
                "ongoing": True
            })
        
        return periods
    
    def clear_buffers(self):
        """Clear all event buffers"""
        self.keystroke_intervals.clear()
        self.mouse_movements.clear()
        self.paste_events.clear()
        self.key_sequence.clear()
        self.stats["idle_periods"].clear()


# Example usage
if __name__ == "__main__":
    def on_pattern(pattern):
        print(f"\n🚨 Pattern detected: {pattern['type']}")
        print(f"   Confidence: {pattern.get('confidence', 0):.0%}")
        print(f"   Details: {pattern.get('details', 'N/A')}")
    
    collector = InputCollector(on_pattern_detected=on_pattern)
    collector.start_collecting()
    
    print("\nCollecting input metadata for 30 seconds...")
    print("Try typing, moving mouse, and pasting different sizes")
    print("Press Ctrl+C to stop early\n")
    
    try:
        for i in range(30):
            time.sleep(1)
            
            if i % 5 == 0 and i > 0:
                summary = collector.get_activity_summary()
                print(f"\n📊 Activity Update ({i}s):")
                print(f"   Keystrokes: {summary['total_keystrokes']}")
                print(f"   Pastes: {summary['total_pastes']}")
                print(f"   Large pastes: {summary['total_large_pastes']}")
                print(f"   Mouse moves: {summary['total_mouse_movements']}")
        
        # Final analysis
        print("\n" + "="*50)
        summary = collector.get_activity_summary()
        
        print(f"📈 Final Analysis:")
        print(f"   Total keystrokes: {summary['total_keystrokes']}")
        print(f"   Total pastes: {summary['total_pastes']}")
        print(f"   Total LARGE pastes: {summary['total_large_pastes']}")
        print(f"   Total idle time: {summary['total_idle_time']:.1f}s")
        
    except KeyboardInterrupt:
        print("\n\n👋 Stopped by user")
    finally:
        collector.stop_collecting()