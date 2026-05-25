"""
Pydantic Schemas for Slow Disease Management System
陵水县人民医院慢病管理系统 - Pydantic v2 模型
"""
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID


class BaseSchema(BaseModel):
    """Base schema with common configuration"""
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        validate_assignment=True,
    )


class ResponseSchema(BaseSchema):
    """Standard API response schema"""
    code: int = 200
    message: str = "success"
    data: Optional[Any] = None


class PaginationParams(BaseSchema):
    """Pagination parameters"""
    page: int = 1
    page_size: int = 20
    
    def get_offset(self) -> int:
        return (self.page - 1) * self.page_size
    
    def get_limit(self) -> int:
        return self.page_size


class PaginatedResponse(BaseSchema):
    """Paginated response schema"""
    items: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int
