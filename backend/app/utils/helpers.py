"""
Helper Utilities

Common utility functions used across the application.
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import uuid


def generate_uuid() -> str:
    """Generate a new UUID string"""
    return str(uuid.uuid4())


def calculate_duration_minutes(start: datetime, end: Optional[datetime] = None) -> int:
    """
    Calculate duration in minutes between two timestamps
    
    Args:
        start: Start timestamp
        end: End timestamp (defaults to now)
        
    Returns:
        int: Duration in minutes
    """
    if end is None:
        end = datetime.utcnow()
    
    duration = end - start
    return int(duration.total_seconds() / 60)


def format_work_time(minutes: int) -> str:
    """
    Format work time in a human-readable way
    
    Args:
        minutes: Total minutes
        
    Returns:
        str: Formatted time (e.g., "2h 30m")
    """
    hours = minutes // 60
    mins = minutes % 60
    
    if hours > 0:
        return f"{hours}h {mins}m"
    return f"{mins}m"


def calculate_completion_percentage(
    actual_minutes: int,
    target_minutes: int = 400
) -> float:
    """
    Calculate work completion percentage
    
    Args:
        actual_minutes: Minutes worked
        target_minutes: Target minutes (default 400 = 8 hours)
        
    Returns:
        float: Percentage (0-100)
    """
    if target_minutes == 0:
        return 0.0
    
    percentage = (actual_minutes / target_minutes) * 100
    return min(percentage, 100.0)  # Cap at 100%


def is_within_working_hours(
    timestamp: datetime,
    start_hour: int = 9,
    end_hour: int = 18
) -> bool:
    """
    Check if timestamp is within working hours
    
    Args:
        timestamp: Time to check
        start_hour: Work start hour (default 9 AM)
        end_hour: Work end hour (default 6 PM)
        
    Returns:
        bool: True if within working hours
    """
    hour = timestamp.hour
    return start_hour <= hour < end_hour


def sanitize_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize metadata to remove sensitive information
    
    Args:
        metadata: Raw metadata dict
        
    Returns:
        Dict: Sanitized metadata
    """
    # Remove any keys that might contain sensitive data
    sensitive_keys = ['password', 'token', 'secret', 'key', 'credential']
    
    return {
        k: v for k, v in metadata.items()
        if not any(sensitive in k.lower() for sensitive in sensitive_keys)
    }


def get_time_of_day(timestamp: datetime) -> str:
    """
    Get time of day category
    
    Args:
        timestamp: Time to categorize
        
    Returns:
        str: "morning", "afternoon", "evening", or "night"
    """
    hour = timestamp.hour
    
    if 5 <= hour < 12:
        return "morning"
    elif 12 <= hour < 17:
        return "afternoon"
    elif 17 <= hour < 21:
        return "evening"
    else:
        return "night"


def calculate_risk_level(score: float) -> str:
    """
    Determine risk level from score
    
    Args:
        score: Risk score (0-100)
        
    Returns:
        str: "low", "medium", "high", or "critical"
    """
    if score < 25:
        return "low"
    elif score < 50:
        return "medium"
    elif score < 75:
        return "high"
    else:
        return "critical"


# TODO: Add more utilities as needed
# - Date/time formatting
# - Data validation helpers
# - File handling utilities
# - Encryption/decryption helpers
# - API response builders