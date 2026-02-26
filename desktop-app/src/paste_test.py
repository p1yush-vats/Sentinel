"""
STANDALONE PASTE DETECTOR TEST
Tests ONLY paste detection - nothing else

Run this to verify paste hooks are working.
"""
from pynput import keyboard
from datetime import datetime
import time

class SimplePasteDetector:
    """Minimal paste detector for testing"""
    
    def __init__(self):
        self.ctrl_pressed = False
        self.cmd_pressed = False
        self.paste_count = 0
        self.paste_times = []
        
    def start(self):
        """Start listening"""
        print("🎯 PASTE DETECTOR ACTIVE")
        print("   Press Ctrl+V (or Cmd+V) to paste")
        print("   Press ESC to stop\n")
        
        listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release
        )
        listener.start()
        listener.join()
    
    def _on_press(self, key):
        """Handle key press"""
        try:
            # Track modifiers
            if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
                self.ctrl_pressed = True
            if key == keyboard.Key.cmd:
                self.cmd_pressed = True
            
            # Detect Ctrl+V or Cmd+V
            if (self.ctrl_pressed or self.cmd_pressed):
                if hasattr(key, 'char') and key.char == 'v':
                    self._on_paste()
            
            # ESC to quit
            if key == keyboard.Key.esc:
                print("\n👋 Stopping detector")
                return False
                
        except Exception as e:
            print(f"Error: {e}")
    
    def _on_release(self, key):
        """Handle key release"""
        try:
            if key == keyboard.Key.ctrl_l or key == keyboard.Key.ctrl_r:
                self.ctrl_pressed = False
            if key == keyboard.Key.cmd:
                self.cmd_pressed = False
        except:
            pass
    
    def _on_paste(self):
        """Handle paste event"""
        now = datetime.now()
        self.paste_count += 1
        self.paste_times.append(now)
        
        # Print immediately
        print(f"📋 PASTE #{self.paste_count} detected at {now.strftime('%H:%M:%S')}")
        
        # Check for rapid paste
        if len(self.paste_times) >= 3:
            recent = self.paste_times[-3:]
            time_span = (recent[-1] - recent[0]).total_seconds()
            
            if time_span < 10:
                print(f"   🚨 RAPID PASTE: {len(recent)} pastes in {time_span:.1f}s!")
        
        # Show stats
        if self.paste_count % 5 == 0:
            print(f"\n📊 Stats: {self.paste_count} total pastes")
            if len(self.paste_times) >= 2:
                total_time = (self.paste_times[-1] - self.paste_times[0]).total_seconds()
                rate = self.paste_count / total_time if total_time > 0 else 0
                print(f"   Rate: {rate:.2f} pastes/second\n")


if __name__ == "__main__":
    print("=" * 60)
    print("STANDALONE PASTE DETECTOR")
    print("=" * 60)
    print()
    
    detector = SimplePasteDetector()
    detector.start()