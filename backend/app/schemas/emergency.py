"""
Emergency Alert Schemas
陵水县人民医院慢病管理系统 - 急救联动相关模型
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID


class EmergencyAlertBase(BaseModel):
    """Base emergency alert schema"""
    model_config = ConfigDict(from_attributes=True)
    
    patient_id: str
    alert_type: str = Field(..., max_length=20, description="预警类型：CHEST_PAIN/STROKE/HYPERTENSIVE_CRISIS等")
    patient_history: Optional[str] = None
    medications: Optional[str] = None
    allergies: Optional[str] = None
    vital_signs: Optional[Dict[str, Any]] = None
    target_org: Optional[str] = Field(None, max_length=50)
    target_dept: Optional[str] = Field(None, max_length=50)
    estimated_arrival: Optional[datetime] = None


class EmergencyAlertCreate(EmergencyAlertBase):
    """Emergency alert creation schema"""
    trigger_by: Optional[str] = None


class EmergencyAlertUpdate(BaseModel):
    """Emergency alert update schema"""
    model_config = ConfigDict(from_attributes=True)
    
    patient_history: Optional[str] = None
    medications: Optional[str] = None
    allergies: Optional[str] = None
    vital_signs: Optional[Dict[str, Any]] = None
    target_org: Optional[str] = Field(None, max_length=50)
    target_dept: Optional[str] = Field(None, max_length=50)
    estimated_arrival: Optional[datetime] = None
    status: Optional[str] = Field(None, max_length=20)


class EmergencyAlertResponse(EmergencyAlertBase):
    """Emergency alert response schema"""
    alert_id: str
    trigger_by: Optional[str] = None
    trigger_at: datetime
    status: str = "ACTIVATED"
    patient_name: Optional[str] = None
    manage_org_name: Optional[str] = None
    doctor_name: Optional[str] = None
    created_at: datetime


class EmergencyAlertSearchParams(BaseModel):
    """Emergency alert search parameters"""
    model_config = ConfigDict(from_attributes=True)
    
    patient_id: Optional[str] = None
    alert_type: Optional[str] = None
    trigger_by: Optional[str] = None
    status: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    skip: int = Field(0, ge=0)
    limit: int = Field(100, ge=1, le=1000)


class EmergencyAlertStats(BaseModel):
    """Emergency alert statistics"""
    model_config = ConfigDict(from_attributes=True)
    
    total_alerts: int
    by_type: Dict[str, int]
    by_status: Dict[str, int]
    by_org: Dict[str, int]
    by_month: Dict[str, int]
    avg_response_minutes: Optional[float] = None
    activated_count: int
    completed_count: int
    cancelled_count: int


class PaginatedEmergencyAlertResponse(BaseModel):
    """Paginated emergency alert response"""
    model_config = ConfigDict(from_attributes=True)
    
    items: List[EmergencyAlertResponse]
    total: int
    page: int
    page_size: int
