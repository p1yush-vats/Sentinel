"""
Application Constants

Centralized constants used across the application.
"""

# User Roles
class UserRole:
    EMPLOYEE = "employee"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"
    
    ALL = [EMPLOYEE, ADMIN, SUPER_ADMIN]
    ADMIN_ROLES = [ADMIN, SUPER_ADMIN]


# Session Status
class SessionStatus:
    ACTIVE = "active"
    COMPLETED = "completed"
    FLAGGED = "flagged"
    CONTESTED = "contested"
    
    ALL = [ACTIVE, COMPLETED, FLAGGED, CONTESTED]


# Work Log Types
class LogType:
    WORK = "work"
    BREAK = "break"
    LUNCH = "lunch"
    
    ALL = [WORK, BREAK, LUNCH]


# Abnormality Types
class AbnormalityType:
    MECHANICAL_TYPING = "mechanical_typing"
    AUTOMATION_DETECTED = "automation"
    SUSPICIOUS_PASTE = "suspicious_paste"
    EXCESSIVE_SPEED = "excessive_speed"
    LONG_IDLE = "long_idle"
    MOUSE_PATTERN_IRREGULAR = "mouse_pattern_irregular"
    
    ALL = [
        MECHANICAL_TYPING,
        AUTOMATION_DETECTED,
        SUSPICIOUS_PASTE,
        EXCESSIVE_SPEED,
        LONG_IDLE,
        MOUSE_PATTERN_IRREGULAR
    ]


# Admin Action Types
class AdminActionType:
    WARNING_ISSUED = "warning_issued"
    SESSION_FLAGGED = "session_flagged"
    APPEAL_APPROVED = "appeal_approved"
    APPEAL_REJECTED = "appeal_rejected"
    ACCOUNT_SUSPENDED = "account_suspended"
    ACCOUNT_ACTIVATED = "account_activated"
    
    ALL = [
        WARNING_ISSUED,
        SESSION_FLAGGED,
        APPEAL_APPROVED,
        APPEAL_REJECTED,
        ACCOUNT_SUSPENDED,
        ACCOUNT_ACTIVATED
    ]


# Report Types
class ReportType:
    DAILY_ATTENDANCE = "daily_attendance"
    WEEKLY_PRODUCTIVITY = "weekly_productivity"
    MONTHLY_SUMMARY = "monthly_summary"
    EMPLOYEE_DETAIL = "employee_detail"
    DEPARTMENT_COMPARISON = "department_comparison"
    ABNORMALITY_SUMMARY = "abnormality_summary"
    
    ALL = [
        DAILY_ATTENDANCE,
        WEEKLY_PRODUCTIVITY,
        MONTHLY_SUMMARY,
        EMPLOYEE_DETAIL,
        DEPARTMENT_COMPARISON,
        ABNORMALITY_SUMMARY
    ]


# Work Time Constants
class WorkTime:
    WORK_MINUTES_PER_HOUR = 50
    BREAK_MINUTES_PER_HOUR = 10
    LUNCH_DURATION_MINUTES = 30
    DAILY_WORK_TARGET_MINUTES = 400  # 8 hours * 50 min/hour
    HOURS_PER_SHIFT = 8


# Confidence Score Thresholds
class ConfidenceThreshold:
    LOW = 30.0
    MEDIUM = 50.0
    HIGH = 70.0
    CRITICAL = 90.0


# Risk Score Levels
class RiskLevel:
    LOW = "low"  # 0-25
    MEDIUM = "medium"  # 25-50
    HIGH = "high"  # 50-75
    CRITICAL = "critical"  # 75-100


# API Response Messages
class Messages:
    # Success
    LOGIN_SUCCESS = "Login successful"
    REGISTER_SUCCESS = "User registered successfully"
    SESSION_STARTED = "Session started successfully"
    SESSION_ENDED = "Session ended successfully"
    PASSWORD_CHANGED = "Password changed successfully"
    
    # Errors
    INVALID_CREDENTIALS = "Invalid email or password"
    EMAIL_EXISTS = "Email already registered"
    USER_NOT_FOUND = "User not found"
    SESSION_NOT_FOUND = "Session not found"
    UNAUTHORIZED = "Unauthorized access"
    FORBIDDEN = "Insufficient permissions"
    ACTIVE_SESSION_EXISTS = "You already have an active session"
    
    # Warnings
    HIGH_ABNORMALITY_DETECTED = "High confidence abnormality detected"
    BREAK_OVERDUE = "Break time is overdue"
    WORK_TARGET_NOT_MET = "Daily work target not met"


# File Extensions
class FileExtension:
    PDF = ".pdf"
    EXCEL = ".xlsx"
    CSV = ".csv"
    JSON = ".json"


# Pagination Defaults
class Pagination:
    DEFAULT_LIMIT = 50
    MAX_LIMIT = 500
    DEFAULT_OFFSET = 0


# TODO: Add more constants as features are implemented