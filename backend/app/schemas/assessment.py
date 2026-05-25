"""
Assessment Schemas
陵水县人民医院慢病管理系统 - 年度评估相关模型
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from uuid import UUID
from decimal import Decimal


class AssessmentBase(BaseModel):
    """Base assessment schema"""
    model_config = ConfigDict(from_attributes=True)
    
    patient_id: str
    disease_code: str = Field(..., max_length=20)
    assessment_year: int = Field(..., ge=2020, le=2100)
    bp_controlled_rate: Optional[Decimal] = Field(None, max_digits=5, decimal_places=2)
    bg_controlled_rate: Optional[Decimal] = Field(None, max_digits=5, decimal_places=2)
    lipid_controlled_rate: Optional[Decimal] = Field(None, max_digits=5, decimal_places=2)
    followup_completion_rate: Optional[Decimal] = Field(None, max_digits=5, decimal_places=2)
    eye_exam_done: Optional[bool] = None
    foot_exam_done: Optional[bool] = None
    echo_done: Optional[bool] = None
    report_content: Optional[str] = None
    report_url: Optional[str] = None


class AssessmentCreate(AssessmentBase):
    """Assessment creation schema"""
    assessed_by: Optional[str] = None


class AssessmentUpdate(BaseModel):
    """Assessment update schema"""
    model_config = ConfigDict(from_attributes=True)
    
    bp_controlled_rate: Optional[Decimal] = None
    bg_controlled_rate: Optional[Decimal] = None
    lipid_controlled_rate: Optional[Decimal] = None
    followup_completion_rate: Optional[Decimal] = None
    eye_exam_done: Optional[bool] = None
    foot_exam_done: Optional[bool] = None
    echo_done: Optional[bool] = None
    report_content: Optional[str] = None
    report_url: Optional[str] = None
    assessed_at: Optional[datetime] = None


class AssessmentResponse(AssessmentBase):
    """Assessment response schema"""
    assessment_id: str
    assessed_by: Optional[str] = None
    assessed_at: Optional[datetime] = None
    created_at: datetime


class PaginatedAssessmentResponse(BaseModel):
    """分页评估记录响应模型"""
    items: List[AssessmentResponse]
    total: int
    page: int
    page_size: int


class AssessmentSearchParams(BaseModel):
    """Assessment search parameters"""
    model_config = ConfigDict(from_attributes=True)
    
    patient_id: Optional[str] = None
    disease_code: Optional[str] = None
    assessment_year: Optional[int] = None
    org_code: Optional[str] = None
    min_bp_controlled_rate: Optional[Decimal] = Field(None, max_digits=5, decimal_places=2)
    max_bp_controlled_rate: Optional[Decimal] = Field(None, max_digits=5, decimal_places=2)
    min_bg_controlled_rate: Optional[Decimal] = Field(None, max_digits=5, decimal_places=2)
    max_bg_controlled_rate: Optional[Decimal] = Field(None, max_digits=5, decimal_places=2)
    eye_exam_done: Optional[bool] = None
    foot_exam_done: Optional[bool] = None
    skip: int = Field(0, ge=0)
    limit: int = Field(100, ge=1, le=1000)


class AssessmentStats(BaseModel):
    """Assessment statistics"""
    model_config = ConfigDict(from_attributes=True)
    
    total_assessments: int
    by_year: Dict[int, int]
    by_disease: Dict[str, int]
    by_org: Dict[str, int]
    avg_bp_controlled_rate: Optional[Decimal] = None
    avg_bg_controlled_rate: Optional[Decimal] = None
    avg_lipid_controlled_rate: Optional[Decimal] = None
    avg_followup_completion_rate: Optional[Decimal] = None
    eye_exam_rate: Optional[Decimal] = None
    foot_exam_rate: Optional[Decimal] = None
    echo_done_rate: Optional[Decimal] = None


class AssessmentReport(BaseModel):
    """Assessment report"""
    model_config = ConfigDict(from_attributes=True)
    
    patient_id: str
    patient_name: str
    disease_code: str
    disease_name: str
    assessment_year: int
    bp_controlled: bool
    bg_controlled: bool
    lipid_controlled: bool
    followup_completion: bool
    comprehensive_score: Decimal
    recommendations: List[str]
    generated_at: datetime
