"""
Desktop App Configuration
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from datetime import timezone, timedelta

# Load environment variables from the .env next to this package
_env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(dotenv_path=_env_path)

# IST Timezone
IST = timezone(timedelta(hours=5, minutes=30))


class Config:
    """Application configuration"""

    # App Info
    APP_NAME    = "SENTINEL Desktop"
    APP_VERSION = "1.0.0"

    # Timezone
    TIMEZONE      = IST
    TIMEZONE_NAME = "Asia/Kolkata"

    # Backend API — defaults to localhost for development
    API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")
    API_VERSION  = "/api/v1"

    # Work Rules (match backend defaults)
    WORK_MINUTES_PER_HOUR      = int(os.getenv("WORK_MINUTES_PER_HOUR", 50))
    BREAK_MINUTES_PER_HOUR     = int(os.getenv("BREAK_MINUTES_PER_HOUR", 10))
    LUNCH_DURATION_MINUTES     = int(os.getenv("LUNCH_DURATION_MINUTES", 30))
    DAILY_WORK_TARGET_MINUTES  = int(os.getenv("DAILY_WORK_TARGET_MINUTES", 400))
    HOURS_PER_SHIFT            = 8

    # Session Recovery
    SESSION_RECOVERY_WINDOW_HOURS = 4

    # Local Database
    DB_DIR           = Path.home() / ".sentinel"
    DB_PATH          = DB_DIR / "sentinel.db"
    DB_ENCRYPTION_KEY = os.getenv("DB_ENCRYPTION_KEY",
                                   "default-key-change-in-production")

    # Detection Settings
    ABNORMALITY_CONFIDENCE_THRESHOLD = float(
        os.getenv("ABNORMALITY_CONFIDENCE_THRESHOLD", 0.7))

    # Keystroke Detection
    MIN_KEY_INTERVAL_MS           = 20
    MAX_KEY_INTERVAL_MS           = 5000
    MECHANICAL_INTERVAL_THRESHOLD = 5

    # Mouse Detection
    MIN_MOUSE_MOVEMENT_DISTANCE = 5
    IDLE_THRESHOLD_SECONDS      = 300

    # Paste Detection
    MAX_PASTE_SIZE              = 1000
    SUSPICIOUS_PASTE_THRESHOLD  = 500

    # Sync Settings
    SYNC_INTERVAL_SECONDS  = int(os.getenv("SYNC_INTERVAL_SECONDS", 60))
    OFFLINE_QUEUE_MAX_SIZE = int(os.getenv("OFFLINE_QUEUE_MAX_SIZE", 1000))

    # UI Settings
    THEME         = os.getenv("THEME", "dark")
    WINDOW_WIDTH  = 1140
    WINDOW_HEIGHT = 720

    # Logging
    LOG_DIR   = DB_DIR / "logs"
    LOG_FILE  = DB_DIR / "logs" / "sentinel.log"
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    @classmethod
    def ensure_dirs(cls):
        """Create necessary directories."""
        cls.DB_DIR.mkdir(parents=True, exist_ok=True)
        cls.LOG_DIR.mkdir(parents=True, exist_ok=True)

    @classmethod
    def get_api_url(cls, endpoint: str) -> str:
        """Build a full API URL."""
        return f"{cls.API_BASE_URL}{cls.API_VERSION}{endpoint}"


# Create dirs on import
Config.ensure_dirs()