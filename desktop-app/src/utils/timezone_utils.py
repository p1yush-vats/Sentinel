"""
Timezone Utilities - IST (Indian Standard Time)

Ensures consistent timezone handling across the application.
"""
from datetime import datetime, timezone, timedelta
from typing import Optional


# IST is UTC+5:30
IST = timezone(timedelta(hours=5, minutes=30))


def now_ist() -> datetime:
    """
    Get current time in IST
    
    Returns:
        datetime: Current datetime in IST timezone
    """
    return datetime.now(IST)


def utc_to_ist(dt: datetime) -> datetime:
    """
    Convert UTC datetime to IST
    
    Args:
        dt: UTC datetime
    
    Returns:
        datetime: Datetime in IST
    """
    if dt.tzinfo is None:
        # Assume UTC if no timezone
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(IST)


def ist_to_utc(dt: datetime) -> datetime:
    """
    Convert IST datetime to UTC
    
    Args:
        dt: IST datetime
    
    Returns:
        datetime: Datetime in UTC
    """
    if dt.tzinfo is None:
        # Assume IST if no timezone
        dt = dt.replace(tzinfo=IST)
    return dt.astimezone(timezone.utc)


def parse_datetime_ist(dt_string: str) -> datetime:
    """
    Parse datetime string and ensure it's in IST
    
    Args:
        dt_string: ISO format datetime string
    
    Returns:
        datetime: Parsed datetime in IST
    """
    dt = datetime.fromisoformat(dt_string.replace('Z', '+00:00'))
    return utc_to_ist(dt)


def format_datetime_ist(dt: datetime) -> str:
    """
    Format datetime in IST for display
    
    Args:
        dt: Datetime object
    
    Returns:
        str: Formatted string in IST
    """
    ist_dt = utc_to_ist(dt) if dt.tzinfo else dt.replace(tzinfo=IST)
    return ist_dt.strftime('%I:%M %p on %B %d, %Y')


def format_time_ist(dt: datetime) -> str:
    """
    Format just the time in IST
    
    Args:
        dt: Datetime object
    
    Returns:
        str: Formatted time string (e.g., "02:30 PM")
    """
    ist_dt = utc_to_ist(dt) if dt.tzinfo else dt.replace(tzinfo=IST)
    return ist_dt.strftime('%I:%M %p')


def to_iso_string(dt: datetime) -> str:
    """
    Convert datetime to ISO string for API
    
    Args:
        dt: Datetime object
    
    Returns:
        str: ISO format string
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=IST)
    return dt.isoformat()


def datetime_ist(year: int, month: int, day: int, hour: int = 0, minute: int = 0, second: int = 0) -> datetime:
    """
    Create datetime in IST timezone
    
    Args:
        year, month, day, hour, minute, second: Date/time components
    
    Returns:
        datetime: Datetime in IST
    """
    return datetime(year, month, day, hour, minute, second, tzinfo=IST)


# Example usage
if __name__ == "__main__":
    # Current time
    current = now_ist()
    print(f"Current IST: {format_datetime_ist(current)}")
    
    # UTC to IST
    utc_time = datetime.now(timezone.utc)
    ist_time = utc_to_ist(utc_time)
    print(f"\nUTC: {utc_time}")
    print(f"IST: {ist_time}")
    
    # Parse datetime string
    dt_str = "2026-01-18T14:30:00Z"  # UTC
    parsed = parse_datetime_ist(dt_str)
    print(f"\nParsed '{dt_str}':")
    print(f"IST: {format_datetime_ist(parsed)}")