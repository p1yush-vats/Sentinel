import logging
import platform
import threading
import time
from collections import deque
from datetime import datetime
from typing import Optional, Callable, Dict, List

from pynput import keyboard, mouse

# Import DEMO_MODE from the single source of truth.
try:
    from detection.abnormality_detector import DEMO_MODE
except ImportError:
    DEMO_MODE = False   # safe fallback when running standalone

logger = logging.getLogger(__name__)

# Windows clipboard (size only, never content)
HAS_CLIPBOARD = False
try:
    import win32clipboard
    HAS_CLIPBOARD = True
except ImportError:
    pass

# Windows API keyboard state
HAS_WIN32 = False
if platform.system() == 'Windows':
    try:
        import ctypes
        HAS_WIN32 = True
    except ImportError:
        pass


class InputMetadata:
    """Container for a single input event's metadata"""

    def __init__(self):
        self.timestamp    = datetime.now()
        self.event_type:  str = ""
        self.interval_ms: Optional[int] = None
        self.metadata:    Dict = {}


class InputCollector:
    """
    Privacy-safe input metadata collector.

    COLLECTS (metadata only):
      - Keystroke timing intervals (NOT which keys)
      - Mouse movement timing (NOT positions)
      - Paste event timing + clipboard SIZE (NOT clipboard content)
      - Idle periods

    NEVER COLLECTS:
      - Actual key characters
      - Text content of any kind
      - Clipboard text (only byte length)
      - Screen content
      - Mouse coordinates
    """

    def __init__(
        self,
        on_pattern_detected: Optional[Callable] = None,
        buffer_size: int = 1000
    ):
        self.on_pattern_detected = on_pattern_detected
        self.buffer_size         = buffer_size

        # Rolling event buffers
        self.keystroke_intervals = deque(maxlen=buffer_size)
        self.mouse_movements     = deque(maxlen=buffer_size)
        self.paste_events        = deque(maxlen=100)
        self.key_sequence        = deque(maxlen=50)   # anonymised key codes only

        # Timing cursors
        self.last_keystroke_time: Optional[datetime] = None
        self.last_mouse_time:     Optional[datetime] = None
        self.last_activity_time:  Optional[datetime] = None
        self.is_collecting = False

        # Session statistics
        self.stats = {
            "total_keystrokes":      0,
            "total_mouse_movements": 0,
            "total_pastes":          0,
            "total_large_pastes":    0,
            "session_start":         None,
            "last_activity":         None,
            "idle_periods":          []
        }

        # pynput listener handles
        self.keyboard_listener: Optional[keyboard.Listener] = None
        self.mouse_listener:    Optional[mouse.Listener]    = None

        # Paste detection
        self.last_paste_time:   Optional[datetime] = None
        self.paste_debounce_ms  = 150
        self.paste_poll_thread: Optional[threading.Thread] = None

        # ── Large paste thresholds (DEMO_MODE aware) ──────────
        # Production: 1000+ chars = essay-sized paste (genuinely suspicious)
        #             3000+ chars = document-sized (very suspicious)
        # Demo mode:  50+ chars = triggers immediately for demo purposes
        if DEMO_MODE:
            self.LARGE_PASTE_THRESHOLD      = 50
            self.VERY_LARGE_PASTE_THRESHOLD = 200
        else:
            self.LARGE_PASTE_THRESHOLD      = 1000
            self.VERY_LARGE_PASTE_THRESHOLD = 3000

        # ── Idle detection ────────────────────────────────────
        # How long without activity before we consider the user idle.
        # Production: 60s (1 minute). Demo: 15s so it fires in the demo.
        self.idle_start_time:      Optional[datetime] = None
        self.idle_threshold_seconds = 15 if DEMO_MODE else 60
        self.is_currently_idle      = False
        self.idle_checker_thread:  Optional[threading.Thread] = None

        # Windows API virtual key codes
        # ── Per-pattern callback cooldown ────────────────────
        # Prevents the same pattern from spamming the callback on every
        # keypress / mouse event. Keyed by pattern type → last fire time.
        self._last_pattern_fire: Dict[str, datetime] = {}
        # How long to wait before re-firing the same pattern (seconds)
        self._pattern_cooldown_seconds = 5 if DEMO_MODE else 10

        self.use_win32 = HAS_WIN32
        if self.use_win32:
            self.GetAsyncKeyState = ctypes.windll.user32.GetAsyncKeyState
            self.VK_CONTROL = 0x11
            self.VK_SHIFT   = 0x10
            self.VK_V       = 0x56
            self.VK_INSERT  = 0x2D
            self.VK_LWIN    = 0x5B
            self.VK_RWIN    = 0x5C
        else:
            self.keys_pressed = set()

    # Lifecycle

    def start_collecting(self):
        """Start all collection hooks. Idempotent."""
        if self.is_collecting:
            return

        self.is_collecting              = True
        self.stats["session_start"]     = datetime.now()
        self.last_activity_time         = datetime.now()

        # Keyboard — timing intervals only
        self.keyboard_listener = keyboard.Listener(
            on_press=self._on_key_press,
            on_release=self._on_key_release
        )
        self.keyboard_listener.start()

        # Mouse — movement timing only, no positions
        self.mouse_listener = mouse.Listener(
            on_move=self._on_mouse_move,
            on_click=self._on_mouse_click
        )
        self.mouse_listener.start()

        # Paste detection polling thread
        self.paste_poll_thread = threading.Thread(
            target=self._poll_for_paste,
            daemon=True
        )
        self.paste_poll_thread.start()

        # Idle checker thread
        self.idle_checker_thread = threading.Thread(
            target=self._idle_checker_loop,
            daemon=True
        )
        self.idle_checker_thread.start()

        method = "Windows API" if self.use_win32 else "pynput fallback"
        logger.info(f"Input collector started (privacy-safe mode)")
        logger.info(f"Paste detection active ({method})")
        if HAS_CLIPBOARD:
            logger.info(f"Clipboard size detection active")
        logger.info(f"Idle detection active")

    def stop_collecting(self):
        """Stop all hooks cleanly."""
        if not self.is_collecting:
            return

        self.is_collecting = False

        if self.keyboard_listener:
            try:
                self.keyboard_listener.stop()
            except Exception:
                pass

        if self.mouse_listener:
            try:
                self.mouse_listener.stop()
            except Exception:
                pass

        logger.info("Input collector stopped")

    # ─────────────────────────────────────────────────────────
    # PUBLIC SUMMARY METHODS (called by detection loop)
    # ─────────────────────────────────────────────────────────

    def get_activity_summary(self) -> Dict:
        """
        Return aggregated stats for the current session.
        Called by _detection_loop in main.py every 30 seconds.

        FIX: idle_seconds now counts from session_start when
        last_activity_time is None (i.e. no events yet).
        Previously it returned 0 forever until the first event.
        """
        if not self.stats["session_start"]:
            return {"status": "not_started"}

        session_duration = (datetime.now() - self.stats["session_start"]).total_seconds()
        keystroke_rate   = self.stats["total_keystrokes"] / session_duration \
                           if session_duration > 0 else 0

        # ── Idle seconds (FIXED) ──────────────────────────────
        if self.last_activity_time:
            idle_seconds = (datetime.now() - self.last_activity_time).total_seconds()
        else:
            # No activity at all since session opened — idle since start
            idle_seconds = session_duration

        # Total cumulative idle time this session
        total_idle_time = sum(p["duration_seconds"] for p in self.stats["idle_periods"])
        if self.is_currently_idle and self.idle_start_time:
            total_idle_time += (datetime.now() - self.idle_start_time).total_seconds()

        return {
            "session_duration_seconds":  round(session_duration, 1),
            "total_keystrokes":          self.stats["total_keystrokes"],
            "total_mouse_movements":     self.stats["total_mouse_movements"],
            "total_pastes":              self.stats["total_pastes"],
            "total_large_pastes":        self.stats["total_large_pastes"],
            "keystroke_rate_per_minute": round(keystroke_rate * 60, 1),
            "idle_seconds":              round(idle_seconds, 1),
            "total_idle_time":           round(total_idle_time, 1),
            "idle_periods_count":        len(self.stats["idle_periods"]),
            "is_active":                 idle_seconds < 60,
            "is_currently_idle":         self.is_currently_idle
        }

    def get_keystroke_pattern(self) -> Dict:
        """
        Analyse keystroke timing for mechanical/bot behaviour.
        Returns 'insufficient_data' if < 10 intervals recorded.
        """
        if len(self.keystroke_intervals) < 10:
            return {"status": "insufficient_data"}

        intervals    = list(self.keystroke_intervals)
        avg_interval = sum(intervals) / len(intervals)
        min_interval = min(intervals)
        max_interval = max(intervals)

        variance = sum((x - avg_interval) ** 2 for x in intervals) / len(intervals)
        std_dev  = variance ** 0.5

        # Low consistency_score = very consistent timing = suspicious
        consistency = std_dev / avg_interval if avg_interval > 0 else 0

        return {
            "status":               "ok",
            "avg_interval_ms":      round(avg_interval, 2),
            "min_interval_ms":      min_interval,
            "max_interval_ms":      max_interval,
            "std_deviation":        round(std_dev, 2),
            "consistency_score":    round(consistency, 3),
            "sample_size":          len(intervals),
            "mechanical_suspected": consistency < 0.2
        }

    def get_idle_periods(self) -> List[Dict]:
        """Return all recorded idle periods including any current one."""
        periods = self.stats["idle_periods"].copy()
        if self.is_currently_idle and self.idle_start_time:
            periods.append({
                "start":            self.idle_start_time,
                "end":              datetime.now(),
                "duration_seconds": (datetime.now() - self.idle_start_time).total_seconds(),
                "ongoing":          True
            })
        return periods

    def clear_buffers(self):
        """Reset all rolling buffers (called at session end)."""
        self.keystroke_intervals.clear()
        self.mouse_movements.clear()
        self.paste_events.clear()
        self.key_sequence.clear()
        self.stats["idle_periods"].clear()

    # ─────────────────────────────────────────────────────────
    # INTERNAL — activity marking
    # ─────────────────────────────────────────────────────────

    def _mark_activity(self):
        """Called on every keyboard/mouse event. Resets idle state."""
        now = datetime.now()

        if self.is_currently_idle and self.idle_start_time:
            idle_duration = (now - self.idle_start_time).total_seconds()
            self.stats["idle_periods"].append({
                "start":            self.idle_start_time,
                "end":              now,
                "duration_seconds": idle_duration
            })
            if self.on_pattern_detected and idle_duration > self.idle_threshold_seconds:
                self.on_pattern_detected({
                    "type":       "idle_period",
                    "confidence": min(idle_duration / (self.idle_threshold_seconds * 2), 1.0),
                    "details":    f"Idle for {idle_duration/60:.1f} minutes"
                })

        self.is_currently_idle       = False
        self.idle_start_time         = None
        self.last_activity_time      = now
        self.stats["last_activity"]  = now

    # ─────────────────────────────────────────────────────────
    # INTERNAL — idle checker background thread
    # ─────────────────────────────────────────────────────────

    def _idle_checker_loop(self):
        """Checks every 5 seconds whether the user has gone idle."""
        while self.is_collecting:
            time.sleep(5)

            if not self.last_activity_time:
                continue

            now = datetime.now()
            time_since = (now - self.last_activity_time).total_seconds()

            if time_since > self.idle_threshold_seconds and not self.is_currently_idle:
                self.is_currently_idle = True
                self.idle_start_time   = self.last_activity_time

    # ─────────────────────────────────────────────────────────
    # INTERNAL — keyboard handlers
    # ─────────────────────────────────────────────────────────

    def _on_key_press(self, key):
        """Record keystroke timing interval. No key content stored."""
        try:
            now = datetime.now()
            self._mark_activity()

            if not self.use_win32:
                self.keys_pressed.add(key)
                if hasattr(key, 'char') and key.char:
                    self.keys_pressed.add(key.char.lower())

            if self.last_keystroke_time:
                interval_ms = int((now - self.last_keystroke_time).total_seconds() * 1000)
                self.keystroke_intervals.append(interval_ms)

            # Store anonymised key code for repetition detection only
            key_code = None
            try:
                if hasattr(key, 'vk'):
                    key_code = key.vk
                elif hasattr(key, 'char') and key.char:
                    key_code = ord(key.char)
            except Exception:
                pass

            if key_code:
                self.key_sequence.append(key_code)
                self._check_repetitive_pattern()

            self.last_keystroke_time = now
            self.stats["total_keystrokes"] += 1

        except Exception as e:
            logger.error(f"Error in key handler: {e}")

    def _on_key_release(self, key):
        try:
            if not self.use_win32:
                self.keys_pressed.discard(key)
                if hasattr(key, 'char') and key.char:
                    self.keys_pressed.discard(key.char.lower())
        except Exception:
            pass

    def _check_repetitive_pattern(self):
        """
        Detect keyboard sitting — same key pressed repeatedly.
        Some employees put a heavy object on the keyboard to look active.

        Fires at most once per _pattern_cooldown_seconds to avoid spamming
        the callback on every key-repeat event when a key is held down.
        """
        if len(self.key_sequence) < 20:
            return

        recent_keys = list(self.key_sequence)[-20:]
        from collections import Counter
        most_common_key, count = Counter(recent_keys).most_common(1)[0]

        if count > 14:   # > 70% of last 20 keys are the same
            now = datetime.now()
            last = self._last_pattern_fire.get("keyboard_sitting")
            if last and (now - last).total_seconds() < self._pattern_cooldown_seconds:
                return  # still within cooldown — skip
            self._last_pattern_fire["keyboard_sitting"] = now
            if self.on_pattern_detected:
                self.on_pattern_detected({
                    "type":       "keyboard_sitting",
                    "confidence": count / 20,
                    "details":    f"Same key repeated {count}/20 times — possible keyboard sitting"
                })

    # ─────────────────────────────────────────────────────────
    # INTERNAL — mouse handlers
    # ─────────────────────────────────────────────────────────

    def _on_mouse_move(self, x, y):
        """Record mouse movement TIMING only. Position x, y never stored."""
        try:
            now = datetime.now()
            self._mark_activity()

            if self.last_mouse_time:
                interval_ms = int((now - self.last_mouse_time).total_seconds() * 1000)

                if interval_ms > 100:   # 100ms debounce
                    self.mouse_movements.append({
                        "timestamp":   now,
                        "interval_ms": interval_ms
                    })
                    self.stats["total_mouse_movements"] += 1
                    self._check_mouse_jiggler()

            self.last_mouse_time = now

        except Exception as e:
            logger.error(f"Error in mouse handler: {e}")

    def _on_mouse_click(self, x, y, button, pressed):
        try:
            if pressed:
                self._mark_activity()
        except Exception:
            pass

    def _check_mouse_jiggler(self):
        """
        Real-time mouse jiggler detection layer.
        Runs on every mouse move event (complements the 30s detector loop).

        Looks at the last 10 movement timing intervals. If their std deviation
        is very low and average is 1–10 seconds, it's a jiggler.
        """
        if len(self.mouse_movements) < 10:
            return

        recent_moves = list(self.mouse_movements)[-10:]
        intervals    = [m["interval_ms"] for m in recent_moves]

        if len(intervals) > 5:
            avg_interval = sum(intervals) / len(intervals)
            variance     = sum((x - avg_interval) ** 2 for x in intervals) / len(intervals)
            std_dev      = variance ** 0.5

            # Regular 1–10 second movements with < 50ms std deviation = jiggler
            if std_dev < 50 and 1000 < avg_interval < 10000:
                now = datetime.now()
                last = self._last_pattern_fire.get("mouse_jiggler")
                if last and (now - last).total_seconds() < self._pattern_cooldown_seconds:
                    return  # still within cooldown — skip
                self._last_pattern_fire["mouse_jiggler"] = now
                if self.on_pattern_detected:
                    self.on_pattern_detected({
                        "type":       "mouse_jiggler",
                        "confidence": max(0.7, 1.0 - (std_dev / 100)),
                        "details":    f"Regular mouse movement: every {avg_interval/1000:.1f}s "
                                      f"(±{std_dev:.1f}ms variance)"
                    })

    # ─────────────────────────────────────────────────────────
    # INTERNAL — paste detection
    # ─────────────────────────────────────────────────────────

    def _is_key_pressed_win32(self, vk_code: int) -> bool:
        try:
            return bool(self.GetAsyncKeyState(vk_code) & 0x8000)
        except Exception:
            return False

    def _check_paste_windows(self) -> Optional[str]:
        ctrl   = self._is_key_pressed_win32(self.VK_CONTROL)
        shift  = self._is_key_pressed_win32(self.VK_SHIFT)
        v      = self._is_key_pressed_win32(self.VK_V)
        insert = self._is_key_pressed_win32(self.VK_INSERT)
        lwin   = self._is_key_pressed_win32(self.VK_LWIN)
        rwin   = self._is_key_pressed_win32(self.VK_RWIN)

        if ctrl and v:          return "Ctrl+V"
        if shift and insert:    return "Shift+Insert"
        if (lwin or rwin) and v: return "Win+V"
        return None

    def _check_paste_pynput(self) -> Optional[str]:
        if self.use_win32:
            return None
        ctrl = (keyboard.Key.ctrl_l in self.keys_pressed or
                keyboard.Key.ctrl_r in self.keys_pressed or
                keyboard.Key.ctrl   in self.keys_pressed)
        shift  = keyboard.Key.shift   in self.keys_pressed or \
                 keyboard.Key.shift_r in self.keys_pressed
        insert = keyboard.Key.insert in self.keys_pressed
        v      = 'v' in self.keys_pressed

        if ctrl and v:       return "Ctrl+V"
        if shift and insert: return "Shift+Insert"
        return None

    def _poll_for_paste(self):
        """Polling thread — checks for paste keystrokes every 10ms."""
        while self.is_collecting:
            try:
                method = self._check_paste_windows() if self.use_win32 \
                         else self._check_paste_pynput()
                if method:
                    self._on_paste_detected(method)
                time.sleep(0.01)
            except Exception as e:
                logger.error(f"Error in paste polling: {e}")

    def _get_clipboard_size(self) -> Optional[int]:
        """Return clipboard text byte length. Never returns actual content."""
        if not HAS_CLIPBOARD:
            return None
        try:
            win32clipboard.OpenClipboard()
            try:
                if win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_UNICODETEXT):
                    data = win32clipboard.GetClipboardData(win32clipboard.CF_UNICODETEXT)
                    return len(data) if data else 0
                elif win32clipboard.IsClipboardFormatAvailable(win32clipboard.CF_TEXT):
                    data = win32clipboard.GetClipboardData(win32clipboard.CF_TEXT)
                    return len(data) if data else 0
            finally:
                win32clipboard.CloseClipboard()
        except Exception:
            try:
                win32clipboard.CloseClipboard()
            except Exception:
                pass
        return None

    def _get_time_since_last_paste(self) -> Optional[float]:
        if self.paste_events:
            return (datetime.now() - self.paste_events[-1]["timestamp"]).total_seconds()
        return None

    def _on_paste_detected(self, method: str):
        """
        Handle a detected paste event.
        Gets clipboard SIZE (never content) and fires callbacks.
        """
        try:
            now = datetime.now()

            # Debounce
            if self.last_paste_time:
                delta_ms = (now - self.last_paste_time).total_seconds() * 1000
                if delta_ms < self.paste_debounce_ms:
                    return

            self.last_paste_time = now
            self.stats["total_pastes"] += 1

            clipboard_size = self._get_clipboard_size()
            is_large       = False
            paste_category = "normal"
            confidence     = 0.0

            if clipboard_size is not None:
                if clipboard_size >= self.VERY_LARGE_PASTE_THRESHOLD:
                    is_large, paste_category, confidence = True, "very_large", 0.99
                elif clipboard_size >= self.LARGE_PASTE_THRESHOLD:
                    is_large, paste_category, confidence = True, "large", 0.95
                elif clipboard_size >= 100:
                    paste_category, confidence = "medium", 0.80
                else:
                    paste_category, confidence = "small", 0.95

            self.paste_events.append({
                "timestamp":           now,
                "method":              method,
                "size":                clipboard_size,
                "category":            paste_category,
                "is_large":            is_large,
                "interval_since_last": self._get_time_since_last_paste()
            })

            if is_large:
                self.stats["total_large_pastes"] += 1
                if self.on_pattern_detected:
                    self.on_pattern_detected({
                        "type":       "large_paste",
                        "confidence": confidence,
                        "details":    f"Large paste: {clipboard_size} chars ({paste_category})",
                        "metadata":   {
                            "size":     clipboard_size,
                            "category": paste_category,
                            "method":   method
                        }
                    })

            # Rapid paste burst check — 3 pastes in under 10 seconds
            if len(self.paste_events) >= 3:
                recent    = list(self.paste_events)[-3:]
                time_span = (recent[-1]["timestamp"] - recent[0]["timestamp"]).total_seconds()
                if time_span < 10:
                    if self.on_pattern_detected:
                        self.on_pattern_detected({
                            "type":       "rapid_paste",
                            "confidence": 0.8,
                            "details":    f"{len(recent)} pastes in {time_span:.1f}s"
                        })

        except Exception as e:
            logger.error(f"Error in paste detection: {e}")


# ─── Standalone test ──────────────────────────────────────────
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    def on_pattern(pattern):
              f"({pattern.get('confidence', 0):.0%}) — {pattern.get('details', '')}")

    collector = InputCollector(on_pattern_detected=on_pattern)
    collector.start_collecting()

    print("\nCollecting for 30 seconds — type, move mouse, paste things...\n")
    try:
        for i in range(30):
            time.sleep(1)
            if i % 5 == 0 and i > 0:
                s = collector.get_activity_summary()
                print(f"[{i}s] keys={s['total_keystrokes']} "
                      f"pastes={s['total_pastes']} "
                      f"large={s['total_large_pastes']} "
                      f"idle={s['idle_seconds']:.0f}s")
    except KeyboardInterrupt:
        pass
    finally:
        collector.stop_collecting()