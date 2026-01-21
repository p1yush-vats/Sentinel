"""
Base Pydantic Schemas

Common base schemas and mixins used across the application.
"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class TimestampMixin(BaseModel):
    """Mixin for models with timestamps"""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ResponseBase(BaseModel):
    """Base response schema"""
    message: str
    success: bool = True


class PaginationParams(BaseModel):
    """Pagination parameters"""
    limit: int = 50
    offset: int = 0
    
    class Config:
        json_schema_extra = {
            "example": {
                "limit": 50,
                "offset": 0
            }
        }


class PaginatedResponse(BaseModel):
    """Paginated response wrapper"""
    total: int
    limit: int
    offset: int
    has_more: bool
    
    @classmethod
    def create(cls, items: list, total: int, limit: int, offset: int):
        """Create paginated response"""
        return cls(
            total=total,
            limit=limit,
            offset=offset,
            has_more=(offset + limit) < total
        )


# Example: How to use these base schemas
# 
# class EmployeeResponse(TimestampMixin):
#     id: str
#     email: str
#     full_name: str
#     role: str
#     department: Optional[str]
#     is_active: bool
# 
# class EmployeeListResponse(PaginatedResponse):
#     employees: list[EmployeeResponse]