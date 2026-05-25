"""
Patient Schemas
陵水县人民医院慢病管理系统 - 患者相关模型
"""
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from uuid import UUID
from enum import Enum


class PaginatedResponse(BaseModel):
    """分页响应模型"""
    items: List[Any] = Field(default_factory=list, description="数据列表")
    total: int = Field(default=0, description="总数")
    page: int = Field(default=1, description="当前页码")
    page_size: int = Field(default=20, description="每页数量")


class GenderEnum(str, Enum):
    """Gender enumeration"""
    MALE = "M"
    FEMALE = "F"
    OTHER = "O"


class RiskLevelEnum(str, Enum):
    """Risk level enumeration"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    VERY_HIGH = "VERY_HIGH"


class EmpiStatusEnum(str, Enum):
    """EMPI status enumeration"""
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    MERGED = "MERGED"


class PatientBase(BaseModel):
    """Base patient schema"""
    model_config = ConfigDict(from_attributes=True)
    
    name: Optional[str] = Field(None, description="患者姓名（明文）")
    gender: str = Field(..., description="Gender: M/F/O")
    birth_date: date = Field(..., description="Birth date")
    phone: Optional[str] = Field(None, description="手机号（明文）")
    address: Optional[str] = None
    village_code: Optional[str] = Field(None, max_length=12)
    manage_org_code: str = Field(..., max_length=50)
    disease_list: List[str] = Field(default_factory=list, description="List of disease codes")


class PatientCreate(PatientBase):
    """Patient creation schema (前端提交明文，后端加密)"""
    name: str = Field(..., description="患者姓名（明文）")
    id_card: str = Field(..., description="身份证号（明文）")
    phone: Optional[str] = Field(None, description="手机号（明文）")
    # 加密字段改为可选，由后端填充
    name_enc: Optional[str] = Field(None, description="加密姓名（后端填充）")
    id_card_enc: Optional[str] = Field(None, description="加密身份证（后端填充）")
    id_card_hash: Optional[str] = Field(None, description="身份证哈希（后端填充）")
    phone_enc: Optional[str] = Field(None, description="加密手机号（后端填充）")


class PatientUpdate(BaseModel):
    """Patient update schema"""
    model_config = ConfigDict(from_attributes=True)
    
    # 明文字段（前端提交）
    name: Optional[str] = Field(None, description="患者姓名（明文）")
    phone: Optional[str] = Field(None, description="手机号（明文）")
    # 非加密字段
    address: Optional[str] = None
    village_code: Optional[str] = None
    manage_org_code: Optional[str] = None
    disease_list: Optional[List[str]] = None
    risk_level: Optional[str] = None
    is_active: Optional[bool] = None
    # 加密字段（后端填充，前端不传）
    name_enc: Optional[str] = Field(None, exclude=True)
    phone_enc: Optional[str] = Field(None, exclude=True)


class PatientResponse(PatientBase):
    """Patient response schema - 包含解密后的明文字段"""
    patient_id: str  # TEXT 类型，非 UUID
    id_card_hash: str
    age: Optional[int] = None
    risk_level: Optional[str] = None
    is_active: bool = True
    empi_status: str = "ACTIVE"
    created_at: datetime
    updated_at: datetime
    manage_org_name: Optional[str] = None
    disease_names: Optional[List[str]] = None
    
    @field_validator('gender')
    @classmethod
    def validate_gender(cls, v):
        mapping = {'MALE': 'M', 'male': 'M', 'FEMALE': 'F', 'female': 'F', 'm': 'M', 'f': 'F'}
        if v in mapping:
            return mapping[v]
        if v not in ['M', 'F', 'O']:
            return 'O'
        return v


class PatientSearchParams(BaseModel):
    """Patient search parameters"""
    model_config = ConfigDict(from_attributes=True)
    
    patient_id: Optional[str] = None  # TEXT 类型
    name_keyword: Optional[str] = None
    id_card_hash: Optional[str] = None
    village_code: Optional[str] = None
    manage_org_code: Optional[str] = None
    disease_code: Optional[str] = None
    risk_level: Optional[str] = None
    is_active: Optional[bool] = None
    min_age: Optional[int] = None
    max_age: Optional[int] = None
    created_start: Optional[date] = None
    created_end: Optional[date] = None


class PatientDiseaseSummary(BaseModel):
    """Patient disease summary"""
    model_config = ConfigDict(from_attributes=True)
    
    patient_id: str  # TEXT 类型
    name_enc: str
    gender: str
    birth_date: date
    village_code: Optional[str] = None
    disease_list: List[str]
    risk_level: Optional[str] = None
    created_at: datetime


class PatientPaginatedResponse(PaginatedResponse):
    """患者分页响应"""
    items: List[PatientResponse] = Field(default_factory=list, description="患者列表")


class PatientStats(BaseModel):
    """Patient statistics"""
    total_patients: int
    active_patients: int
    by_disease: Dict[str, int]
    by_risk_level: Dict[str, int]
    by_village: Dict[str, int]
