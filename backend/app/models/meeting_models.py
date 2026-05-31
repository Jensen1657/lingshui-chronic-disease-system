"""
用药记录模型 + 健康宣教模板模型 + 处方审核模型
会议纪要核心需求实现
"""
from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, Date, Text, Numeric,
    ForeignKey, Index, JSON, text
)
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

from app.db.session import Base


class PatientMedication(Base):
    """患者用药记录表 — 内科陈丹要求查看患者用药记录"""
    __tablename__ = "patient_medication"

    medication_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String(36), ForeignKey("patient.patient_id"), nullable=False)
    disease_code = Column(String(20), ForeignKey("dim_disease_type.disease_code"), nullable=False)
    drug_name = Column(String(200), nullable=False)
    drug_code = Column(String(50))
    drug_class = Column(String(100))
    specification = Column(String(100))
    dosage = Column(String(100))
    frequency = Column(String(50))
    route = Column(String(50), default="口服")
    start_date = Column(Date, nullable=False)
    end_date = Column(Date)
    is_long_term = Column(Boolean, default=True)
    is_active = Column(Boolean, default=True)
    prescribed_by = Column(String(36), ForeignKey("sys_user.user_id"))
    prescribed_org = Column(String(50))
    adjust_reason = Column(Text)
    adjust_date = Column(Date)
    is_ai_recommended = Column(Boolean, default=False)  # 是否AI推荐
    ai_confidence = Column(Numeric(4, 2))  # AI推荐置信度
    adherence_status = Column(String(20))  # 依从性状态: GOOD/PARTIAL/POOR
    side_effects = Column(Text)
    notes = Column(Text)
    created_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))

    __table_args__ = (
        Index("idx_med_patient", patient_id, is_active),
        Index("idx_med_drug", drug_name),
        Index("idx_med_date", start_date, end_date),
        Index("idx_med_ai", is_ai_recommended),
    )


class HealthEducationTemplate(Base):
    """健康宣教模板表 — 内科陈丹要求生成模板并一键发送"""
    __tablename__ = "health_education_template"

    template_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(200), nullable=False)
    category = Column(String(50), nullable=False)  # DIET/EXERCISE/MEDICATION/MONITORING/LIFESTYLE/GENERAL
    disease_code = Column(String(20), ForeignKey("dim_disease_type.disease_code"))
    risk_level = Column(String(20))  # 适用风险等级
    content_text = Column(Text, nullable=False)  # 纯文本版本
    content_rich = Column(Text)  # 富文本/HTML版本
    media_urls = Column(JSON)  # 配图/视频链接
    tags = Column(JSON)  # 标签
    usage_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_by = Column(String(36), ForeignKey("sys_user.user_id"))
    created_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))

    __table_args__ = (
        Index("idx_edu_template_cat", category, is_active),
        Index("idx_edu_template_disease", disease_code),
    )


class HealthEducationRecord(Base):
    """宣教推送记录表"""
    __tablename__ = "health_education_record"

    record_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String(36), ForeignKey("patient.patient_id"), nullable=False)
    template_id = Column(String(36), ForeignKey("health_education_template.template_id"))
    sent_channel = Column(String(20), nullable=False)  # WECHAT/SMS/APP/PRINT
    sent_by = Column(String(36), ForeignKey("sys_user.user_id"))
    sent_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))
    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime)
    patient_feedback = Column(Text)
    created_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))

    __table_args__ = (
        Index("idx_edu_send_patient", patient_id, sent_at),
        Index("idx_edu_send_template", template_id),
    )


class PrescriptionReview(Base):
    """处方审核指导表 — 叶胜业要求总院医生线上指导基层处方"""
    __tablename__ = "prescription_review"

    review_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    medication_id = Column(String(36), ForeignKey("patient_medication.medication_id"), nullable=False)
    patient_id = Column(String(36), ForeignKey("patient.patient_id"), nullable=False)
    review_type = Column(String(20), nullable=False)  # AUTO/MANUAL/APPEAL
    original_dosage = Column(String(100))
    original_frequency = Column(String(50))
    original_drug = Column(String(200))
    suggested_dosage = Column(String(100))
    suggested_frequency = Column(String(50))
    suggested_drug = Column(String(200))
    review_reason = Column(Text)
    review_result = Column(String(20), nullable=False)  # APPROVED/ADJUSTED/REJECTED
    reviewed_by = Column(String(36), ForeignKey("sys_user.user_id"), nullable=False)  # 总院医生
    reviewed_org = Column(String(50))
    prescribed_by = Column(String(36), ForeignKey("sys_user.user_id"))  # 基层医生
    reviewed_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))
    is_applied = Column(Boolean, default=False)  # 基层是否已采用
    applied_at = Column(DateTime)
    notes = Column(Text)
    created_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))

    __table_args__ = (
        Index("idx_rx_review_patient", patient_id, reviewed_at),
        Index("idx_rx_review_prescriber", prescribed_by),
        Index("idx_rx_review_status", is_applied, reviewed_at),
    )


class PatientRiskAssessment(Base):
    """患者风险评估/分层标记表 — 全量纳管+分级诊疗需求"""
    __tablename__ = "patient_risk_assessment"

    assessment_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String(36), ForeignKey("patient.patient_id"), nullable=False)

    # 风险评分
    risk_score = Column(Integer, nullable=False)
    risk_level = Column(String(20), nullable=False)  # LOW/MEDIUM/HIGH/CRITICAL
    risk_factors = Column(JSON)  # 风险因素列表

    # 分级诊疗标记
    manage_level = Column(String(20), nullable=False)  # VILLAGE/TOWNSHIP/COUNTY/REFERRAL
    recommended_org = Column(String(50))  # 推荐管理机构
    assigned_org = Column(String(50))  # 实际分配机构
    assigned_doctor = Column(String(36), ForeignKey("sys_user.user_id"))

    # 评估详情
    bp_assessment = Column(String(20))  # 血压评估: CONTROLLED/BORDERLINE/UNCONTROLLED
    bg_assessment = Column(String(20))  # 血糖评估
    lipid_assessment = Column(String(20))  # 血脂评估
    kidney_assessment = Column(String(20))  # 肾功能评估
    compliance_assessment = Column(String(20))  # 依从性评估: GOOD/FAIR/POOR

    # 管理建议
    followup_frequency = Column(String(50))  # 建议随访频率: WEEKLY/MONTHLY/QUARTERLY
    need_up_referral = Column(Boolean, default=False)
    referral_note = Column(Text)
    assessment_note = Column(Text)

    assessed_by = Column(String(36), ForeignKey("sys_user.user_id"))
    assessed_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))
    valid_until = Column(Date)
    next_assessment_date = Column(Date)
    created_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))

    __table_args__ = (
        Index("idx_risk_patient", patient_id, assessed_at.desc()),
        Index("idx_risk_level", risk_level, manage_level),
        Index("idx_risk_org", assigned_org),
        Index("idx_risk_valid", valid_until),
    )