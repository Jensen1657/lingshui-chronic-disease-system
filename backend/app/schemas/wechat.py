"""
Wechat Schemas
陵水县人民医院慢病管理系统 - 微信绑定相关模型
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from uuid import UUID


class WechatBase(BaseModel):
    """Base wechat schema"""
    model_config = ConfigDict(from_attributes=True)
    
    patient_id: str
    openid: str = Field(..., max_length=100, description="微信OpenID")
    nickname: Optional[str] = Field(None, max_length=100)
    avatar_url: Optional[str] = None
    bind_date: date
    is_active: bool = True


class WechatCreate(WechatBase):
    """Wechat creation schema"""
    pass


class WechatUpdate(BaseModel):
    """Wechat update schema"""
    model_config = ConfigDict(from_attributes=True)
    
    nickname: Optional[str] = Field(None, max_length=100)
    avatar_url: Optional[str] = None
    is_active: Optional[bool] = None
    unbind_date: Optional[date] = None


class WechatResponse(WechatBase):
    """Wechat response schema"""
    wechat_id: str
    unbind_date: Optional[date] = None
    created_at: datetime


class WechatSearchParams(BaseModel):
    """Wechat search parameters"""
    model_config = ConfigDict(from_attributes=True)
    
    patient_id: Optional[str] = None
    openid: Optional[str] = None
    nickname: Optional[str] = None
    is_active: Optional[bool] = None
    bind_date_start: Optional[date] = None
    bind_date_end: Optional[date] = None
    skip: int = Field(0, ge=0)
    limit: int = Field(100, ge=1, le=1000)


class WechatStats(BaseModel):
    """Wechat statistics"""
    model_config = ConfigDict(from_attributes=True)
    
    total_bindings: int
    active_bindings: int
    inactive_bindings: int
    by_month: Dict[str, int]
    avg_bindings_per_month: float


class PaginatedWechatResponse(BaseModel):
    """Paginated wechat response"""
    model_config = ConfigDict(from_attributes=True)
    
    items: List[WechatResponse]
    total: int
    page: int
    page_size: int
