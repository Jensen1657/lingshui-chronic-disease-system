"""
Referral Schemas
陵水县人民医院慢病管理系统 - 双向转诊相关模型
"""
from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from uuid import UUID


class ReferralBase(BaseModel):
    """Base referral schema"""
    model_config = ConfigDict(from_attributes=True)
    
    patient_id: str
    disease_code: Optional[str] = Field(None, max_length=20)
    referral_type: str = Field(..., max_length=10, description="转诊类型：UP(上转)/DOWN(下转)")
    apply_org_code: str = Field(..., max_length=50)
    referral_reason: Optional[str] = None
    match_criteria: Optional[Dict[str, Any]] = None
    down_plan: Optional[Dict[str, Any]] = None
    receive_org_code: Optional[str] = Field(None, max_length=50)
    status: str = Field(default='PENDING', max_length=20, description="状态：PENDING/ACCEPTED/REJECTED/COMPLETED")


class ReferralCreate(ReferralBase):
    """Referral creation schema"""
    apply_doctor: Optional[str] = None


class ReferralUpdate(BaseModel):
    """Referral update schema"""
    model_config = ConfigDict(from_attributes=True)
    
    is_eligible: Optional[bool] = None
    reject_reason: Optional[str] = None
    receive_org_code: Optional[str] = Field(None, max_length=50)
    receive_doctor: Optional[str] = None
    receive_at: Optional[datetime] = None
    status: Optional[str] = Field(None, max_length=20)
    completed_at: Optional[datetime] = None
    post_referral_fu_id: Optional[str] = None


class ReferralResponse(ReferralBase):
    """Referral response schema"""
    model_config = ConfigDict(from_attributes=True)
    
    referral_id: str
    apply_doctor: Optional[str] = None
    apply_at: datetime
    is_eligible: Optional[bool] = None
    reject_reason: Optional[str] = None
    receive_org_code: Optional[str] = None
    receive_doctor: Optional[str] = None
    receive_at: Optional[datetime] = None
    status: str = 'PENDING'
    timeout_alert_sent: bool = False
    completed_at: Optional[datetime] = None
    post_referral_fu_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    # 列表展示用扩展字段（非数据库字段）
    patient_name: Optional[str] = None
    apply_org_name: Optional[str] = None
    receive_org_name: Optional[str] = None
    
    @field_validator('match_criteria', 'down_plan', mode='before')
    @classmethod
    def parse_json_fields(cls, v):
        """解析 JSON 字符串或返回 Dict"""
        if v is None:
            return None
        if isinstance(v, str):
            try:
                import json
                return json.loads(v)
            except json.JSONDecodeError:
                return None
        return v


class PaginatedReferralResponse(BaseModel):
    """分页转诊记录响应模型"""
    items: List[ReferralResponse]
    total: int
    page: int
    page_size: int


class ReferralSearchParams(BaseModel):
    """Referral search parameters"""
    model_config = ConfigDict(from_attributes=True)
    
    patient_id: Optional[str] = None
    referral_type: Optional[str] = None
    apply_org_code: Optional[str] = None
    receive_org_code: Optional[str] = None
    status: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_eligible: Optional[bool] = None
    skip: int = Field(0, ge=0)
    limit: int = Field(100, ge=1, le=1000)


class ReferralStats(BaseModel):
    """Referral statistics"""
    model_config = ConfigDict(from_attributes=True)
    
    total_referrals: int
    by_type: Dict[str, int]
    by_status: Dict[str, int]
    by_org: Dict[str, int]
    by_month: Dict[str, int]
    avg_completion_days: Optional[float] = None
    pending_count: int
    accepted_count: int
    rejected_count: int
    completed_count: int


class ReferralEligibilityCheck(BaseModel):
    """Referral eligibility check request"""
    model_config = ConfigDict(from_attributes=True)
    
    patient_id: str
    disease_code: str
    referral_type: str
    referral_reason: str
