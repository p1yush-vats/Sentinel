"""
ULTIMATE PASTE DETECTOR - Windows Ctrl+V Fix
Uses win32api for direct keyboard state checking on Windows
"""
import sys
import platform
from datetime import datetime
import time
import threading

# Try to import pynput
try:
    from pynput import keyboard
    HAS_PYNPUT = True
except:
    HAS_PYNPUT = False
    print("⚠️ pynput not available")

# Try to import Windows-specific keyboard library
HAS_WIN32 = False
if platform.system() == 'Windows':
    try:
        import ctypes
        from ctypes import wintypes
        HAS_WIN32 = True
    except:
        print("⚠️ ctypes not available")


class UltimatePasteDetector:
    """
    Windows-optimized paste detector
    Uses direct Windows API when available
    """
    
    def __init__(self):
        self.paste_count = 0
        self.running = False
        self.last_paste_time = None
        self.debounce_ms = 150
        
        # Virtual key codes for Windows
        self.VK_CONTROL = 0x11
        self.VK_SHIFT = 0x10
        self.VK_V = 0x56
        self.VK_INSERT = 0x2D
        self.VK_LWIN = 0x5B  # Left Windows key
        self.VK_RWIN = 0x5C  # Right Windows key
        
        if HAS_WIN32:
            # Windows API function
            self.GetAsyncKeyState = ctypes.windll.user32.GetAsyncKeyState
    
    def is_key_pressed_win32(self, vk_code):
        """Check if key is pressed using Windows API"""
        if not HAS_WIN32:
            return False
        # GetAsyncKeyState returns a short
        # High-order bit is 1 if key is currently down
        state = self.GetAsyncKeyState(vk_code)
        return (state & 0x8000) != 0
    
    def check_paste_windows(self):
        """Check for paste using Windows API"""
        if not HAS_WIN32:
            return None
        
        ctrl_pressed = self.is_key_pressed_win32(self.VK_CONTROL)
        shift_pressed = self.is_key_pressed_win32(self.VK_SHIFT)
        v_pressed = self.is_key_pressed_win32(self.VK_V)
        insert_pressed = self.is_key_pressed_win32(self.VK_INSERT)
        lwin_pressed = self.is_key_pressed_win32(self.VK_LWIN)
        rwin_pressed = self.is_key_pressed_win32(self.VK_RWIN)
        
        # Ctrl+V detection
        if ctrl_pressed and v_pressed:
            return "Ctrl+V"
        
        # Shift+Insert detection
        if shift_pressed and insert_pressed:
            return "Shift+Insert"
        
        # Windows+V detection (clipboard history)
        if (lwin_pressed or rwin_pressed) and v_pressed:
            return "Win+V"
        
        return None
    
    def start(self):
        """Start paste detection"""
        self.running = True
        
        print("🎯 ULTIMATE PASTE DETECTOR")
        print(f"   Platform: {platform.system()}")
        print(f"   Method: {'Windows API (Direct)' if HAS_WIN32 else 'pynput (Fallback)'}")
        print("   Detects: Ctrl+V, Shift+Insert, Win+V")
        print("   Press Ctrl+C to stop\n")
        
        if HAS_WIN32:
            # Use Windows API polling (most reliable)
            self._polling_loop()
        elif HAS_PYNPUT:
            # Fallback to pynput
            self._pynput_loop()
        else:
            print("❌ No input detection method available!")
    
    def _polling_loop(self):
        """Main polling loop using Windows API"""
        print("✅ Using Windows API for direct keyboard state checking\n")
        
        try:
            while self.running:
                method = self.check_paste_windows()
                
                if method:
                    self._trigger_paste(method)
                
                time.sleep(0.01)  # 10ms polling
                
        except KeyboardInterrupt:
            print("\n\n👋 Stopped by user")
            self.running = False
    
    def _pynput_loop(self):
        """Fallback polling loop using pynput"""
        print("⚠️ Using pynput fallback (may not detect Ctrl+V reliably)\n")
        
        keys_pressed = set()
        
        def on_press(key):
            keys_pressed.add(key)
            if hasattr(key, 'char') and key.char:
                keys_pressed.add(key.char.lower())
        
        def on_release(key):
            keys_pressed.discard(key)
            if hasattr(key, 'char') and key.char:
                keys_pressed.discard(key.char.lower())
        
        listener = keyboard.Listener(on_press=on_press, on_release=on_release)
        listener.start()
        
        try:
            while self.running:
                ctrl = (keyboard.Key.ctrl_l in keys_pressed or 
                       keyboard.Key.ctrl_r in keys_pressed or
                       keyboard.Key.ctrl in keys_pressed)
                shift = (keyboard.Key.shift in keys_pressed or 
                        keyboard.Key.shift_r in keys_pressed)
                insert = keyboard.Key.insert in keys_pressed
                v = 'v' in keys_pressed
                
                if ctrl and v:
                    self._trigger_paste("Ctrl+V")
                elif shift and insert:
                    self._trigger_paste("Shift+Insert")
                
                time.sleep(0.01)
                
        except KeyboardInterrupt:
            print("\n\n👋 Stopped by user")
            self.running = False
        finally:
            listener.stop()
    
    def _trigger_paste(self, method: str):
        """Trigger paste detection with debouncing"""
        now = datetime.now()
        
        # Debounce
        if self.last_paste_time:
            delta_ms = (now - self.last_paste_time).total_seconds() * 1000
            if delta_ms < self.debounce_ms:
                return
        
        self.last_paste_time = now
        self.paste_count += 1
        
        timestamp = now.strftime('%H:%M:%S.%f')[:-3]
        print(f"📋 PASTE #{self.paste_count} at {timestamp} via {method}")


def main():
    """Test the detector"""
    detector = UltimatePasteDetector()
    
    try:
        detector.start()
    except KeyboardInterrupt:
        print("\n\n👋 Stopped")


if __name__ == "__main__":
    main()