"""
Self-Report Schemas
陵水县人民医院慢病管理系统 - 患者自主上报相关模型
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from uuid import UUID
from decimal import Decimal


class SelfReportBase(BaseModel):
    """Base self-report schema"""
    model_config = ConfigDict(from_attributes=True)
    
    patient_id: str
    report_type: str = Field(..., max_length=20, description="上报类型：BP/BG/WEIGHT/EXERCISE等")
    report_date: date
    report_content: str
    report_value: Optional[Decimal] = Field(None, max_digits=8, decimal_places=2)
    report_unit: Optional[str] = Field(None, max_length=20)
    data_source: str = Field(default='WECHAT', max_length=20, description="数据来源：WECHAT/MANUAL/DEVICE")


class SelfReportCreate(SelfReportBase):
    """Self-report creation schema"""
    pass


class SelfReportUpdate(BaseModel):
    """Self-report update schema"""
    model_config = ConfigDict(from_attributes=True)
    
    report_content: Optional[str] = None
    report_value: Optional[Decimal] = Field(None, max_digits=8, decimal_places=2)
    report_unit: Optional[str] = Field(None, max_length=20)
    note: Optional[str] = None


class SelfReportResponse(SelfReportBase):
    """Self-report response schema"""
    report_id: str
    verified: bool = False
    verified_by: Optional[str] = None
    verified_at: Optional[datetime] = None
    note: Optional[str] = None
    created_at: datetime


class SelfReportSearchParams(BaseModel):
    """Self-report search parameters"""
    model_config = ConfigDict(from_attributes=True)
    
    patient_id: Optional[str] = None
    report_type: Optional[str] = None
    data_source: Optional[str] = None
    is_verified: Optional[bool] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    min_value: Optional[Decimal] = Field(None, max_digits=8, decimal_places=2)
    max_value: Optional[Decimal] = Field(None, max_digits=8, decimal_places=2)
    skip: int = Field(0, ge=0)
    limit: int = Field(100, ge=1, le=1000)


class SelfReportStats(BaseModel):
    """Self-report statistics"""
    model_config = ConfigDict(from_attributes=True)
    
    total_reports: int
    by_type: Dict[str, int]
    by_source: Dict[str, int]
    by_month: Dict[str, int]
    verified_count: int
    unverified_count: int
    avg_reports_per_patient: float


class PaginatedSelfReportResponse(BaseModel):
    """Paginated self-report response"""
    model_config = ConfigDict(from_attributes=True)
    
    items: List[SelfReportResponse]
    total: int
    page: int
    page_size: int
