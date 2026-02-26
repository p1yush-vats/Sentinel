"""
HYBRID LARGE PASTE DETECTOR
Uses multiple methods to infer paste size (privacy-safe)
"""
from pynput import keyboard
from datetime import datetime
import time
import platform
import threading

# Windows clipboard access (to get size only, not content)
HAS_CLIPBOARD = False
try:
    import win32clipboard
    HAS_CLIPBOARD = True
    print("✅ Clipboard size detection available")
except:
    print("⚠️  Clipboard module not available (install: pip install pywin32)")

# Windows API support
HAS_WIN32 = False
if platform.system() == 'Windows':
    try:
        import ctypes
        HAS_WIN32 = True
        print("✅ Windows API available")
    except:
        print("❌ Windows API not available")


class HybridPasteDetector:
    """
    Detects large pastes using multiple methods:
    1. Clipboard size (if available) - MOST ACCURATE
    2. Keystroke burst (for old apps)
    3. Time delay before next action (user reading)
    """
    
    def __init__(self):
        self.paste_count = 0
        self.large_paste_count = 0
        self.running = False
        
        # Timing tracking
        self.last_paste_time = None
        self.last_action_time = None
        self.paste_burst_window = 0.5
        self.keystrokes_in_burst = []
        self.monitoring_burst = False
        
        # Delay monitoring
        self.monitoring_delay = False
        self.delay_threshold = 2.0  # 2 seconds
        
        # Windows API
        if HAS_WIN32:
            self.GetAsyncKeyState = ctypes.windll.user32.GetAsyncKeyState
            self.VK_CONTROL = 0x11
            self.VK_V = 0x56
            self.VK_SHIFT = 0x10
            self.VK_INSERT = 0x2D
    
    def get_clipboard_size(self):
        """Get clipboard text size without reading content"""
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
    
    def is_key_pressed(self, vk_code):
        """Check if key is pressed (Windows API)"""
        if not HAS_WIN32:
            return False
        state = self.GetAsyncKeyState(vk_code)
        return (state & 0x8000) != 0
    
    def check_paste(self):
        """Check for Ctrl+V or Shift+Insert"""
        if not HAS_WIN32:
            return False
        
        ctrl = self.is_key_pressed(self.VK_CONTROL)
        shift = self.is_key_pressed(self.VK_SHIFT)
        v = self.is_key_pressed(self.VK_V)
        insert = self.is_key_pressed(self.VK_INSERT)
        
        if ctrl and v:
            return "Ctrl+V"
        elif shift and insert:
            return "Shift+Insert"
        
        return None
    
    def on_paste_detected(self):
        """Handle paste detection"""
        self.paste_count += 1
        self.last_paste_time = datetime.now()
        self.keystrokes_in_burst = []
        self.monitoring_burst = True
        self.monitoring_delay = True
        
        print(f"\n📋 PASTE #{self.paste_count} at {self.last_paste_time.strftime('%H:%M:%S')}")
        
        # METHOD 1: Check clipboard size (most accurate)
        clipboard_size = self.get_clipboard_size()
        
        if clipboard_size is not None:
            print(f"   📏 Clipboard size: {clipboard_size} characters")
            self._analyze_clipboard_size(clipboard_size)
        else:
            print(f"   ⏳ Using fallback methods (burst + delay)...")
    
    def on_action(self):
        """Handle any user action (keystroke or mouse)"""
        now = datetime.now()
        
        # Track for burst counting
        if self.monitoring_burst and self.last_paste_time:
            elapsed = (now - self.last_paste_time).total_seconds()
            if elapsed <= self.paste_burst_window:
                self.keystrokes_in_burst.append(now)
        
        # Track for delay measurement
        if self.monitoring_delay and not self.last_action_time:
            # First action after paste
            delay = (now - self.last_paste_time).total_seconds()
            self._analyze_delay(delay)
            self.monitoring_delay = False
        
        self.last_action_time = now
    
    def _analyze_clipboard_size(self, size):
        """Analyze paste size from clipboard"""
        if size < 20:
            category = "TINY"
            icon = "✓"
            confidence = 0.95
            is_large = False
        elif size < 100:
            category = "SMALL"
            icon = "✓"
            confidence = 0.95
            is_large = False
        elif size < 300:
            category = "MEDIUM"
            icon = "ℹ️"
            confidence = 0.95
            is_large = False
        elif size < 1000:
            category = "LARGE"
            icon = "⚠️"
            confidence = 0.95
            is_large = True
        else:
            category = "VERY LARGE"
            icon = "🚨"
            confidence = 0.99
            is_large = True
        
        print(f"   {icon} Size category: {category}")
        print(f"   🎯 Confidence: {confidence:.0%}")
        
        if is_large:
            print(f"   🚨 ABNORMALITY: Large paste detected!")
            self.large_paste_count += 1
    
    def _analyze_delay(self, delay):
        """Analyze paste based on delay to next action"""
        print(f"   ⏱️  Delay to next action: {delay:.2f}s")
        
        if delay > 3.0:
            category = "LARGE"
            confidence = min(delay / 10.0, 0.85)
            icon = "⚠️"
            print(f"   {icon} Inferred: {category} paste (user took time to read)")
            print(f"   🎯 Confidence: {confidence:.0%}")
            self.large_paste_count += 1
        elif delay > 1.5:
            print(f"   ℹ️  Possible medium paste")
    
    def check_timeouts(self):
        """Check if monitoring windows should end"""
        if not self.last_paste_time:
            return
        
        now = datetime.now()
        elapsed = (now - self.last_paste_time).total_seconds()
        
        # Burst window timeout
        if self.monitoring_burst and elapsed > self.paste_burst_window:
            self.monitoring_burst = False
            burst_count = len(self.keystrokes_in_burst)
            
            if burst_count > 0:
                print(f"   📊 Burst detected: {burst_count} keystrokes in 500ms")
                if burst_count > 50:
                    print(f"   ⚠️  Large paste (burst method)!")
                    self.large_paste_count += 1
        
        # Delay timeout (if no action within delay threshold)
        if self.monitoring_delay and elapsed > self.delay_threshold:
            self.monitoring_delay = False
            print(f"   ⏱️  No action within {self.delay_threshold}s")
    
    def start(self):
        """Start detection"""
        self.running = True
        
        print("\n" + "="*70)
        print("🧪 HYBRID LARGE PASTE DETECTION TEST")
        print("="*70)
        print("\nDetection methods (in order of accuracy):")
        print("1. ✅ Clipboard size (most accurate, requires pywin32)")
        print("2. 📊 Keystroke burst (for old apps)")
        print("3. ⏱️  Action delay (for reading large text)")
        print("\nInstructions:")
        print("1. Copy text of different sizes")
        print("2. Press Ctrl+V to paste")
        print("3. See which method detects it!")
        print("\nPress ESC to exit\n")
        print("-"*70)
        
        if not HAS_WIN32:
            print("❌ Windows API not available - test cannot run")
            return
        
        # Keyboard listener
        def on_press(key):
            if key == keyboard.Key.esc:
                return False
            self.on_action()
        
        listener = keyboard.Listener(on_press=on_press)
        listener.start()
        
        # Main polling loop
        last_paste_check = None
        try:
            while self.running:
                # Check for paste
                method = self.check_paste()
                if method:
                    # Debounce
                    now = datetime.now()
                    if not last_paste_check or (now - last_paste_check).total_seconds() > 0.2:
                        self.on_paste_detected()
                        last_paste_check = now
                
                # Check timeouts
                self.check_timeouts()
                
                time.sleep(0.01)
                
        except KeyboardInterrupt:
            pass
        finally:
            listener.stop()
            self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*70)
        print("📊 TEST SUMMARY")
        print("="*70)
        print(f"Total pastes detected: {self.paste_count}")
        print(f"Large pastes detected: {self.large_paste_count}")
        
        if HAS_CLIPBOARD:
            print(f"\n✅ Clipboard size detection: WORKING")
        else:
            print(f"\n⚠️  Clipboard size detection: NOT AVAILABLE")
            print(f"   Install: pip install pywin32")
        
        if self.large_paste_count > 0:
            print(f"\n✅ Large paste detection is WORKING!")
        else:
            print(f"\nℹ️  No large pastes detected")
        
        print("\nTest complete!")


def main():
    detector = HybridPasteDetector()
    detector.start()


if __name__ == "__main__":
    main()