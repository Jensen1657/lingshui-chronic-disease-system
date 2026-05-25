"""
Reminder Schemas
陵水县人民医院慢病管理系统 - 随访提醒相关模型
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from uuid import UUID


class ReminderBase(BaseModel):
    """Base reminder schema"""
    model_config = ConfigDict(from_attributes=True)
    
    patient_id: str
    disease_code: Optional[str] = Field(None, max_length=20)
    plan_date: date
    plan_type: str = Field(..., max_length=20, description="计划类型：FOLLOWUP/ASSESSMENT/EXAM等")
    channel: Optional[str] = Field(None, max_length=20, description="提醒渠道：SMS/WECHAT/APP_PUSH")
    status: str = Field(default='PENDING', max_length=20, description="状态：PENDING/SENT/FAILED")


class ReminderCreate(ReminderBase):
    """Reminder creation schema"""
    pass


class ReminderUpdate(BaseModel):
    """Reminder update schema"""
    model_config = ConfigDict(from_attributes=True)
    
    plan_date: Optional[date] = None
    plan_type: Optional[str] = None
    channel: Optional[str] = None
    status: Optional[str] = None
    is_sent: Optional[bool] = None
    sent_at: Optional[datetime] = None


class ReminderResponse(ReminderBase):
    """Reminder response schema"""
    reminder_id: str
    is_sent: bool = False
    sent_at: Optional[datetime] = None
    created_at: datetime


class ReminderSearchParams(BaseModel):
    """Reminder search parameters"""
    model_config = ConfigDict(from_attributes=True)
    
    patient_id: Optional[str] = None
    disease_code: Optional[str] = None
    plan_type: Optional[str] = None
    channel: Optional[str] = None
    status: Optional[str] = None
    is_sent: Optional[bool] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    skip: int = Field(0, ge=0)
    limit: int = Field(100, ge=1, le=1000)


class ReminderStats(BaseModel):
    """Reminder statistics"""
    model_config = ConfigDict(from_attributes=True)
    
    total_reminders: int
    by_type: Dict[str, int]
    by_channel: Dict[str, int]
    by_status: Dict[str, int]
    sent_count: int
    pending_count: int
    failed_count: int
    sent_rate: float


class PaginatedReminderResponse(BaseModel):
    """Paginated reminder response"""
    model_config = ConfigDict(from_attributes=True)
    
    items: List[ReminderResponse]
    total: int
    page: int
    page_size: int
