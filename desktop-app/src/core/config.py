"""
Desktop App Configuration
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from datetime import timezone, timedelta

# Load environment variables
load_dotenv()

# IST Timezone
IST = timezone(timedelta(hours=5, minutes=30))

class Config:
    """Application configuration"""
    
    # App Info
    APP_NAME = "SENTINEL Desktop"
    APP_VERSION = "1.0.0"
    
    # Timezone
    TIMEZONE = IST
    TIMEZONE_NAME = "Asia/Kolkata"
    
    # Backend API
    API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")
    API_VERSION = "/api/v1"
    
    # Work Rules (match backend defaults)
    WORK_MINUTES_PER_HOUR = 50
    BREAK_MINUTES_PER_HOUR = 10
    LUNCH_DURATION_MINUTES = 30
    DAILY_WORK_TARGET_MINUTES = 400  # 8 hours * 50 min
    HOURS_PER_SHIFT = 8
    
    # Session Recovery
    SESSION_RECOVERY_WINDOW_HOURS = 4  # How far back to look for incomplete sessions
    
    # Local Database
    DB_DIR = Path.home() / ".sentinel"
    DB_PATH = DB_DIR / "sentinel.db"
    DB_ENCRYPTION_KEY = os.getenv("DB_ENCRYPTION_KEY", "default-key-change-in-production")
    
    # Detection Settings
    ABNORMALITY_CONFIDENCE_THRESHOLD = 0.7
    
    # Keystroke Detection
    MIN_KEY_INTERVAL_MS = 20   # Minimum time between keystrokes
    MAX_KEY_INTERVAL_MS = 5000 # Maximum time (idle threshold)
    MECHANICAL_INTERVAL_THRESHOLD = 5  # Variance threshold for mechanical typing
    
    # Mouse Detection
    MIN_MOUSE_MOVEMENT_DISTANCE = 5  # Minimum pixels to count as movement
    IDLE_THRESHOLD_SECONDS = 300     # 5 minutes idle = suspicious
    
    # Paste Detection
    MAX_PASTE_SIZE = 1000  # Characters
    SUSPICIOUS_PASTE_THRESHOLD = 500  # Large pastes are suspicious
    
    # Sync Settings
    SYNC_INTERVAL_SECONDS = 300  # Sync every 5 minutes
    OFFLINE_QUEUE_MAX_SIZE = 1000
    
    # UI Settings
    THEME = "dark"  # "dark" or "light"
    WINDOW_WIDTH = 800
    WINDOW_HEIGHT = 600
    
    # Logging
    LOG_DIR = DB_DIR / "logs"
    LOG_FILE = LOG_DIR / "sentinel.log"
    LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR
    
    @classmethod
    def ensure_dirs(cls):
        """Create necessary directories"""
        cls.DB_DIR.mkdir(parents=True, exist_ok=True)
        cls.LOG_DIR.mkdir(parents=True, exist_ok=True)
    
    @classmethod
    def get_api_url(cls, endpoint: str) -> str:
        """Get full API URL for endpoint"""
        return f"{cls.API_BASE_URL}{cls.API_VERSION}{endpoint}"


# Initialize directories on import
Config.ensure_dirs()