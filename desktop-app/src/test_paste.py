"""
PASTE DETECTOR VIA TEXT INSERTION SPEED
Detects paste by measuring typing speed bursts
"""
from pynput import keyboard
from datetime import datetime
import time

class InsertionSpeedDetector:
    """Detects paste by abnormal typing speed"""
    
    def __init__(self):
        self.char_times = []
        self.paste_count = 0
        
    def start(self):
        """Start listening"""
        print("🎯 INSERTION SPEED DETECTOR")
        print("   Detects paste by typing speed bursts")
        print("   Press ESC to stop\n")
        
        listener = keyboard.Listener(on_press=self._on_press)
        listener.start()
        listener.join()
    
    def _on_press(self, key):
        """Handle key press"""
        try:
            # ESC to quit
            if key == keyboard.Key.esc:
                print("\n👋 Stopping")
                return False
            
            # Only track character keys
            if hasattr(key, 'char') and key.char:
                now = datetime.now()
                self.char_times.append(now)
                
                # Keep only last 10 characters
                if len(self.char_times) > 10:
                    self.char_times.pop(0)
                
                # Check for burst (5+ chars in under 0.1 seconds)
                if len(self.char_times) >= 5:
                    recent = self.char_times[-5:]
                    time_span = (recent[-1] - recent[0]).total_seconds()
                    
                    # 5 chars in under 100ms = paste
                    if time_span < 0.1:
                        self.paste_count += 1
                        print(f"📋 PASTE #{self.paste_count} detected!")
                        print(f"   5 chars in {time_span*1000:.1f}ms (impossible to type)")
                        
                        # Clear to avoid double-counting
                        self.char_times.clear()
                
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    detector = InsertionSpeedDetector()
    detector.start()