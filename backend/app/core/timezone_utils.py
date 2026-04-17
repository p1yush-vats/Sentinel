"""
Timezone Utilities
All datetimes are stored as UTC in the database and converted to IST only for display.
Uses pytz for reliable cross-platform timezone handling.
"""
from datetime import datetime
from typing import Optional
import pytz

# IST Timezone - use pytz for reliability
IST = pytz.timezone('Asia/Kolkata')
UTC = pytz.UTC


def now_ist() -> datetime:
    """
    Get current time in IST timezone
    
    Returns:
        datetime: Current time with IST timezone
    """
    return datetime.now(IST)


def now_utc() -> datetime:
    """
    Get current time in UTC (for database storage)
    
    Returns:
        datetime: Current time in UTC
    """
    return datetime.now(UTC)


def to_utc(dt: datetime) -> datetime:
    """
    Convert any datetime to UTC (for database storage)
    
    Args:
        dt: Datetime (can be any timezone or naive)
    
    Returns:
        datetime: Datetime in UTC timezone
    """
    if dt.tzinfo is None:
        # Naive datetimes are assumed to be IST
        dt = IST.localize(dt)
    
    return dt.astimezone(UTC)


def to_ist(dt: datetime) -> datetime:
    """
    Convert any datetime to IST (for display)
    
    Args:
        dt: Datetime (can be any timezone or naive)
    
    Returns:
        datetime: Datetime in IST timezone
    """
    if dt.tzinfo is None:
        # Naive datetimes coming from the DB are assumed to be UTC
        dt = UTC.localize(dt)
    
    return dt.astimezone(IST)


def parse_ist_string(dt_string: str) -> datetime:
    """
    Parse ISO datetime string and ensure it's in IST
    
    Args:
        dt_string: ISO format datetime string
    
    Returns:
        datetime: Parsed datetime in IST
    """
    if dt_string.endswith('Z'):
        dt_string = dt_string[:-1] + '+00:00'
    
    dt = datetime.fromisoformat(dt_string)
    return to_ist(dt)


def format_ist(dt: datetime, fmt: str = '%Y-%m-%d %I:%M:%S %p IST') -> str:
    """
    Format datetime in IST for display
    
    Args:
        dt: Datetime to format
        fmt: Format string
    
    Returns:
        str: Formatted datetime string
    """
    ist_dt = to_ist(dt)
    return ist_dt.strftime(fmt)


# Database helper - always store UTC
def prepare_for_db(dt: datetime) -> datetime:
    """
    Prepare datetime for database storage (convert to UTC)
    
    Args:
        dt: Datetime in any timezone
    
    Returns:
        datetime: UTC datetime ready for database
    """
    return to_utc(dt)


# Database helper - convert from DB to IST
def from_db_to_ist(dt: datetime) -> datetime:
    """
    Convert datetime from database (assumed UTC) to IST
    
    Args:
        dt: Datetime from database
    
    Returns:
        datetime: IST datetime
    """
    return to_ist(dt)


if __name__ == "__main__":
    # Test the utilities
    print("=== Timezone Utilities Test ===\n")
    
    # Current times
    ist_now = now_ist()
    utc_now = now_utc()
    
    print(f"Current IST: {ist_now}")
    print(f"Current UTC: {utc_now}")
    print(f"Formatted IST: {format_ist(ist_now)}")
    
    # Conversion test
    print("\n=== Conversion Test ===")
    test_dt = now_ist()
    print(f"Original (IST): {test_dt}")
    
    utc_version = to_utc(test_dt)
    print(f"Converted to UTC: {utc_version}")
    
    back_to_ist = to_ist(utc_version)
    print(f"Back to IST: {back_to_ist}")
    
    # Database simulation
    print("\n=== Database Simulation ===")
    ist_time = now_ist()
    print(f"1. IST time: {ist_time}")
    
    db_time = prepare_for_db(ist_time)
    print(f"2. Stored in DB (UTC): {db_time}")
    
    retrieved_time = from_db_to_ist(db_time)
    print(f"3. Retrieved from DB (IST): {retrieved_time}")
    
    print(f"\nMatch? {ist_time == retrieved_time}")