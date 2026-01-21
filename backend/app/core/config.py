"""
SENTINEL Backend Configuration
"""
from pydantic_settings import BaseSettings
from typing import Optional, List


class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    APP_NAME: str = "SENTINEL Work Integrity System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # API
    API_V1_PREFIX: str = "/api/v1"
    
    # Database - FIXED: Added type annotation
    DATABASE_URL: str
    
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    
    # CORS - FIXED: Changed to List type
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8000"
    ]
    
    # Redis (for Celery)
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Email (SMTP)
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM_EMAIL: Optional[str] = None
    
    # Work Rules Defaults
    DEFAULT_WORK_MINUTES_PER_HOUR: int = 50
    DEFAULT_BREAK_MINUTES_PER_HOUR: int = 10
    DEFAULT_LUNCH_DURATION_MINUTES: int = 30
    DEFAULT_DAILY_WORK_TARGET: int = 400
    
    # Detection Settings
    ABNORMALITY_CONFIDENCE_THRESHOLD: float = 0.7
    HIGH_RISK_SCORE_THRESHOLD: float = 70.0
    
    # File Storage
    REPORTS_DIR: str = "./reports"
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()