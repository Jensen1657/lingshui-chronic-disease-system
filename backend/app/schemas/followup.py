"""
Followup Schemas
陵水县人民医院慢病管理系统 - 随访相关模型
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from uuid import UUID
from decimal import Decimal


class FollowupBase(BaseModel):
    """Base followup schema"""
    model_config = ConfigDict(from_attributes=True)
    
    patient_id: str
    disease_code: str = Field(..., max_length=20)
    followup_type: str = Field(..., max_length=20, description="随访类型：常规/上门/电话/微信")
    followup_date: date
    bp_systolic: Optional[int] = Field(None, ge=0, le=300)
    bp_diastolic: Optional[int] = Field(None, ge=0, le=200)
    fbg: Optional[Decimal] = Field(None, max_digits=4, decimal_places=1)
    pbg: Optional[Decimal] = Field(None, max_digits=4, decimal_places=1)
    hba1c: Optional[Decimal] = Field(None, max_digits=4, decimal_places=1)
    ldl_c: Optional[Decimal] = Field(None, max_digits=4, decimal_places=2)
    hdl_c: Optional[Decimal] = Field(None, max_digits=4, decimal_places=2)
    tc: Optional[Decimal] = Field(None, max_digits=4, decimal_places=2)
    tg: Optional[Decimal] = Field(None, max_digits=4, decimal_places=2)
    weight: Optional[Decimal] = Field(None, max_digits=5, decimal_places=1)
    bmi: Optional[Decimal] = Field(None, max_digits=4, decimal_places=1)
    heart_rate: Optional[int] = Field(None, ge=0, le=300)
    medication_adherence: Optional[str] = Field(None, max_length=20)
    is_controlled: Optional[bool] = None
    next_followup_date: Optional[date] = None
    symptoms: Optional[str] = None
    signs: Optional[str] = None
    medication_changed: Optional[bool] = None
    medication_note: Optional[str] = None


class FollowupCreate(FollowupBase):
    """Followup creation schema"""
    org_code: str = Field(..., max_length=50)
    location_lat: Optional[Decimal] = Field(None, max_digits=10, decimal_places=6)
    location_lng: Optional[Decimal] = Field(None, max_digits=10, decimal_places=6)
    audio_record_url: Optional[str] = None
    device_data: Optional[Dict[str, Any]] = None


class FollowupUpdate(BaseModel):
    """Followup update schema"""
    model_config = ConfigDict(from_attributes=True)
    
    bp_systolic: Optional[int] = None
    bp_diastolic: Optional[int] = None
    fbg: Optional[Decimal] = None
    pbg: Optional[Decimal] = None
    hba1c: Optional[Decimal] = None
    ldl_c: Optional[Decimal] = None
    hdl_c: Optional[Decimal] = None
    tc: Optional[Decimal] = None
    tg: Optional[Decimal] = None
    weight: Optional[Decimal] = None
    bmi: Optional[Decimal] = None
    heart_rate: Optional[int] = None
    medication_adherence: Optional[str] = None
    is_controlled: Optional[bool] = None
    next_followup_date: Optional[date] = None
    symptoms: Optional[str] = None
    signs: Optional[str] = None
    medication_changed: Optional[bool] = None
    medication_note: Optional[str] = None
    is_audited: Optional[bool] = None
    audit_note: Optional[str] = None


class FollowupResponse(FollowupBase):
    """Followup response schema"""
    followup_id: str
    followup_no: int
    performed_by: str
    org_code: str
    is_audited: bool = False
    audited_by: Optional[str] = None
    audited_at: Optional[datetime] = None
    audit_note: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    patient_name: Optional[str] = None  # JOIN 患者姓名
    org_name: Optional[str] = None  # 所属机构名称


class PaginatedFollowupResponse(BaseModel):
    """分页随访记录响应模型"""
    items: List[FollowupResponse]
    total: int
    page: int
    page_size: int


class FollowupSearchParams(BaseModel):
    """Followup search parameters"""
    model_config = ConfigDict(from_attributes=True)
    
    patient_id: Optional[str] = None
    disease_code: Optional[str] = None
    followup_type: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    performed_by: Optional[str] = None
    org_code: Optional[str] = None
    is_controlled: Optional[bool] = None
    is_audited: Optional[bool] = None
    skip: int = Field(0, ge=0)
    limit: int = Field(100, ge=1, le=1000)


class FollowupStats(BaseModel):
    """Followup statistics"""
    model_config = ConfigDict(from_attributes=True)
    
    total_followups: int
    by_disease: Dict[str, int]
    by_org: Dict[str, int]
    by_month: Dict[str, int]
    controlled_rate: Decimal
    avg_bp_systolic: Optional[Decimal] = None
    avg_bp_diastolic: Optional[Decimal] = None
    avg_fbg: Optional[Decimal] = None
    pending_audit: int


class FollowupHypertensionCreate(BaseModel):
    """Hypertension-specific followup extension"""
    model_config = ConfigDict(from_attributes=True)
    
    followup_id: str
    bp_grade: Optional[str] = Field(None, max_length=20)
    cv_risk_updated: Optional[str] = Field(None, max_length=20)
    drug_adjust_reason: Optional[str] = None
    is_urgent_alert: bool = False


class FollowupDiabetesCreate(BaseModel):
    """Diabetes-specific followup extension"""
    model_config = ConfigDict(from_attributes=True)
    
    followup_id: str
    hypoglycemia_event: bool = False
    hypoglycemia_count: int = 0
    adverse_reaction: Optional[str] = None
    new_complication: Optional[str] = None
