"""
Alert Schemas
陵水县人民医院慢病管理系统 - 预警相关模型
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID


class AlertBase(BaseModel):
    """Base alert schema"""
    model_config = ConfigDict(from_attributes=True)
    
    patient_id: Optional[str] = None
    org_code: Optional[str] = Field(None, max_length=50)
    alert_type: str = Field(..., max_length=50, description="预警类型：BP_HIGH/BP_LOW/BG_HIGH/MISS_FU等")
    alert_level: str = Field(..., max_length=20, description="预警级别：LOW/MEDIUM/HIGH/CRITICAL")
    alert_title: str = Field(..., max_length=200)
    alert_content: str


class AlertCreate(AlertBase):
    """Alert creation schema"""
    pass


class AlertUpdate(BaseModel):
    """Alert update schema"""
    model_config = ConfigDict(from_attributes=True)
    
    is_handled: Optional[bool] = None
    handle_note: Optional[str] = None


class AlertResponse(AlertBase):
    """Alert response schema"""
    alert_id: str
    is_handled: bool = False
    handled_by: Optional[str] = None
    handled_at: Optional[datetime] = None
    handle_note: Optional[str] = None
    created_at: datetime


class PaginatedAlertResponse(BaseModel):
    """分页预警记录响应模型"""
    items: List[AlertResponse]
    total: int
    page: int
    page_size: int


class AlertSearchParams(BaseModel):
    """Alert search parameters"""
    model_config = ConfigDict(from_attributes=True)
    
    patient_id: Optional[str] = None
    org_code: Optional[str] = None
    alert_type: Optional[str] = None
    alert_level: Optional[str] = None
    is_handled: Optional[bool] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    skip: int = Field(0, ge=0)
    limit: int = Field(100, ge=1, le=1000)


class AlertStats(BaseModel):
    """Alert statistics"""
    model_config = ConfigDict(from_attributes=True)
    
    total_alerts: int
    by_type: Dict[str, int]
    by_level: Dict[str, int]
    by_org: Dict[str, int]
    by_month: Dict[str, int]
    handled_count: int
    unhandled_count: int
    avg_handle_minutes: Optional[float] = None


class AlertBatchHandle(BaseModel):
    """Alert batch handle request"""
    model_config = ConfigDict(from_attributes=True)
    
    alert_ids: List[UUID]
    handle_note: Optional[str] = None
