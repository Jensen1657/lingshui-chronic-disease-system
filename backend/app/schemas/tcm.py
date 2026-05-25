"""
TCM Schemas
陵水县人民医院慢病管理系统 - 中医管理相关模型
扩展支持完整中医临床路径：辨证→四诊→治法→方药→调护→随访
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from uuid import UUID


class TcmBase(BaseModel):
    """Base TCM schema - 扩展完整临床路径字段"""
    model_config = ConfigDict(from_attributes=True)

    patient_id: str
    disease_code: Optional[str] = Field(None, max_length=20)
    record_date: Optional[date] = None

    # 辨证信息
    syndrome_type: Optional[str] = Field(None, max_length=100, description="证型：气虚质/阳虚质/阴虚质等")
    syndrome_name: Optional[str] = Field(None, max_length=200, description="证名")
    syndrome_differentiation: Optional[str] = Field(None, description="辨证分析")
    tcm_disease: Optional[str] = Field(None, max_length=100, description="中医病名")

    # 四诊信息（望闻问切）
    inspection: Optional[str] = Field(None, description="望诊")
    auscultation: Optional[str] = Field(None, description="闻诊")
    interrogation: Optional[str] = Field(None, description="问诊")
    palpation: Optional[str] = Field(None, description="切诊")
    tongue_body: Optional[str] = Field(None, max_length=100, description="舌质")
    tongue_coating: Optional[str] = Field(None, max_length=100, description="舌苔（兼容 tongue_coat）")
    tongue_coat: Optional[str] = Field(None, max_length=100, description="舌苔")
    pulse: Optional[str] = Field(None, max_length=100, description="脉象（兼容 pulse_status）")
    pulse_status: Optional[str] = Field(None, max_length=100, description="脉象")

    # 中医治疗
    treatment_method: Optional[str] = Field(None, description="治法")
    prescription: Optional[str] = Field(None, description="方药（兼容 tcm_prescription）")
    tcm_prescription: Optional[str] = Field(None, description="方药")
    herbs: Optional[str] = Field(None, description="中药饮片（兼容 tcm_herbs JSON）")
    tcm_herbs: Optional[List[Dict[str, Any]]] = Field(None, description="中药饮片JSON")
    patent_medicine: Optional[str] = Field(None, description="中成药")

    # 其他疗法
    acupuncture: Optional[str] = Field(None, description="针灸")
    moxibustion: Optional[str] = Field(None, description="艾灸")
    tuina: Optional[str] = Field(None, description="推拿")
    other_therapy: Optional[str] = Field(None, description="其他疗法")
    therapy_type: Optional[List[str]] = Field(None, description="疗法类型列表")
    therapy_note: Optional[str] = Field(None, description="疗法备注")

    # 养生调护
    diet_therapy: Optional[str] = Field(None, description="饮食调理")
    exercise_therapy: Optional[str] = Field(None, description="运动调理")
    emotion_therapy: Optional[str] = Field(None, description="情志调理")
    lifestyle_guidance: Optional[str] = Field(None, description="起居指导")

    # 疗效与随访
    efficacy_evaluation: Optional[str] = Field(None, description="疗效评价")
    next_visit_date: Optional[date] = Field(None, description="下次就诊日期")

    # 就诊信息
    visit_date: Optional[date] = Field(None, description="就诊日期（兼容 record_date）")
    visit_doctor: Optional[str] = Field(None, max_length=100, description="就诊医生（兼容 recorded_by）")
    recorded_by: Optional[str] = Field(None, max_length=100, description="记录人")


class TcmCreate(TcmBase):
    """TCM creation schema"""
    pass


class TcmUpdate(BaseModel):
    """TCM update schema"""
    model_config = ConfigDict(from_attributes=True)

    disease_code: Optional[str] = None
    record_date: Optional[date] = None
    syndrome_type: Optional[str] = None
    syndrome_name: Optional[str] = None
    syndrome_differentiation: Optional[str] = None
    tcm_disease: Optional[str] = None
    inspection: Optional[str] = None
    auscultation: Optional[str] = None
    interrogation: Optional[str] = None
    palpation: Optional[str] = None
    tongue_body: Optional[str] = None
    tongue_coating: Optional[str] = None
    tongue_coat: Optional[str] = None
    pulse: Optional[str] = None
    pulse_status: Optional[str] = None
    treatment_method: Optional[str] = None
    prescription: Optional[str] = None
    tcm_prescription: Optional[str] = None
    herbs: Optional[str] = None
    tcm_herbs: Optional[List[Dict[str, Any]]] = None
    patent_medicine: Optional[str] = None
    acupuncture: Optional[str] = None
    moxibustion: Optional[str] = None
    tuina: Optional[str] = None
    other_therapy: Optional[str] = None
    therapy_type: Optional[List[str]] = None
    therapy_note: Optional[str] = None
    diet_therapy: Optional[str] = None
    exercise_therapy: Optional[str] = None
    emotion_therapy: Optional[str] = None
    lifestyle_guidance: Optional[str] = None
    efficacy_evaluation: Optional[str] = None
    next_visit_date: Optional[date] = None
    visit_date: Optional[date] = None
    visit_doctor: Optional[str] = None
    recorded_by: Optional[str] = None


class TcmResponse(TcmBase):
    """TCM response schema"""
    tcm_id: str
    patient_name: Optional[str] = None
    manage_org_name: Optional[str] = None
    created_at: datetime


class TcmSearchParams(BaseModel):
    """TCM search parameters"""
    model_config = ConfigDict(from_attributes=True)

    patient_id: Optional[str] = None
    disease_code: Optional[str] = None
    syndrome_type: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    recorded_by: Optional[str] = None
    skip: int = Field(0, ge=0)
    limit: int = Field(100, ge=1, le=1000)


class TcmStats(BaseModel):
    """TCM statistics"""
    model_config = ConfigDict(from_attributes=True)

    total_records: int
    by_syndrome_type: Dict[str, int]
    by_disease: Dict[str, int]
    by_therapy_type: Dict[str, int]
    avg_records_per_patient: float


class PaginatedTcmResponse(BaseModel):
    """Paginated TCM response"""
    model_config = ConfigDict(from_attributes=True)

    items: List[TcmResponse]
    total: int
    page: int
    page_size: int
