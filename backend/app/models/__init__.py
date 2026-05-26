"""
SQLAlchemy ORM Models
陵水县人民医院慢病管理系统 - 数据库模型(SQLite 兼容版)
"""
from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, Date, Text, Numeric,
    ForeignKey, Index, CheckConstraint, UniqueConstraint, JSON, func, text
)
from sqlalchemy.orm import relationship, DeclarativeBase
from datetime import datetime
import uuid

from app.db.session import Base


class DimRegion(Base):
    """区域字典表"""
    __tablename__ = "dim_region"

    region_code = Column(String(12), primary_key=True)
    region_name = Column(String(100), nullable=False)
    region_level = Column(Integer, nullable=False)
    parent_code = Column(String(12))
    org_code = Column(String(50))
    org_name = Column(String(200))
    created_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))


class DimDiseaseType(Base):
    """疾病类型字典表"""
    __tablename__ = "dim_disease_type"

    disease_code = Column(String(20), primary_key=True)
    disease_name = Column(String(100), nullable=False)
    icd10_code = Column(String(20))
    sort_order = Column(Integer, default=0)


class DimDrug(Base):
    """药品字典表"""
    __tablename__ = "dim_drug"

    drug_id = Column(Integer, primary_key=True, autoincrement=True)
    drug_name = Column(String(200), nullable=False)
    drug_code = Column(String(50))
    specification = Column(String(100))
    unit = Column(String(20))
    drug_class = Column(String(100))
    indication = Column(Text)
    contraindication = Column(Text)
    created_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))


class SysUser(Base):
    """系统用户表"""
    __tablename__ = "sys_user"

    user_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    real_name = Column(String(100), nullable=False)
    id_card_enc = Column(Text)
    phone_enc = Column(Text)
    org_code = Column(String(50), nullable=False)
    region_code = Column(String(12), ForeignKey("dim_region.region_code"))
    role_code = Column(String(20), nullable=False)
    is_active = Column(Boolean, default=True)
    last_login_at = Column(DateTime)
    created_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))


class SysRolePermission(Base):
    """角色权限表"""
    __tablename__ = "sys_role_permission"

    role_code = Column(String(20), primary_key=True)
    role_name = Column(String(100))
    permissions = Column(JSON, nullable=False)
    description = Column(Text)


class SysAuditLog(Base):
    """审计日志表"""
    __tablename__ = "sys_audit_log"

    log_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), ForeignKey("sys_user.user_id"))
    action = Column(String(100), nullable=False)
    resource_type = Column(String(100))
    resource_id = Column(String(100))
    ip_address = Column(String(50))
    user_agent = Column(Text)
    request_data = Column(JSON)
    response_data = Column(JSON)
    created_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))


class Patient(Base):
    """患者主索引表"""
    __tablename__ = "patient"

    patient_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    id_card_enc = Column(Text, nullable=False)
    id_card_hash = Column(String(64), unique=True)
    name_enc = Column(Text, nullable=False)
    gender = Column(String(1))
    birth_date = Column(Date)
    age = Column(Integer)
    phone_enc = Column(Text)
    address = Column(Text)
    village_code = Column(String(12), ForeignKey("dim_region.region_code"))
    manage_org_code = Column(String(50), nullable=False)
    disease_list = Column(JSON, nullable=False, default=list)
    risk_level = Column(String(20))
    is_active = Column(Boolean, default=True)
    empi_status = Column(String(20), default='ACTIVE')
    created_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))

    # Indexes
    __table_args__ = (
        Index('idx_patient_village', village_code),
        Index('idx_patient_org', manage_org_code),
        Index('idx_patient_disease', disease_list),
        Index('idx_patient_id_card_hash', id_card_hash),
    )


class FollowupRecord(Base):
    """通用随访记录表"""
    __tablename__ = "followup_record"

    followup_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String(36), ForeignKey("patient.patient_id"), nullable=False)
    disease_code = Column(String(20), ForeignKey("dim_disease_type.disease_code"), nullable=False)
    followup_no = Column(Integer, nullable=False)
    followup_type = Column(String(20), nullable=False)
    followup_date = Column(Date, nullable=False)
    performed_by = Column(String(36), ForeignKey("sys_user.user_id"), nullable=False)
    org_code = Column(String(50), nullable=False)
    bp_systolic = Column(Integer)
    bp_diastolic = Column(Integer)
    fbg = Column(Numeric(4, 1))
    pbg = Column(Numeric(4, 1))
    hba1c = Column(Numeric(4, 1))
    ldl_c = Column(Numeric(4, 2))
    hdl_c = Column(Numeric(4, 2))
    tc = Column(Numeric(4, 2))
    tg = Column(Numeric(4, 2))
    weight = Column(Numeric(5, 1))
    bmi = Column(Numeric(4, 1))
    heart_rate = Column(Integer)
    medication_adherence = Column(String(20))
    is_controlled = Column(Boolean)
    next_followup_date = Column(Date)
    symptoms = Column(Text)
    signs = Column(Text)
    medication_changed = Column(Boolean, default=False)
    medication_note = Column(Text)
    location_lat = Column(Numeric(10, 6))
    location_lng = Column(Numeric(10, 6))
    audio_record_url = Column(Text)
    device_data = Column(JSON)
    is_audited = Column(Boolean, default=False)
    audited_by = Column(String(36), ForeignKey("sys_user.user_id"))
    audited_at = Column(DateTime)
    audit_note = Column(Text)
    created_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))

    # Relationships
    patient = relationship("Patient", back_populates="followups")

    # Indexes
    __table_args__ = (
        Index('idx_followup_patient', patient_id, disease_code),
        Index('idx_followup_date', followup_date),
        Index('idx_followup_date_range', followup_date, disease_code),
    )


Patient.followups = relationship("FollowupRecord", back_populates="patient")


class DiseaseHypertension(Base):
    """高血压专病表"""
    __tablename__ = "disease_hypertension"

    disease_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String(36), ForeignKey("patient.patient_id"), nullable=False)
    diagnosis_date = Column(Date, nullable=False)
    diagnosis_doctor = Column(String(36), ForeignKey("sys_user.user_id"))
    diagnosis_org = Column(String(50))
    icd10_code = Column(String(20), default='I10')
    risk_stratification = Column(String(20))
    risk_score = Column(Integer)
    ecg_result = Column(Text)
    ucr_result = Column(Text)
    echo_result = Column(Text)
    imt_result = Column(Text)
    drug_class_1 = Column(String(50))
    drug_name_1 = Column(String(200))
    drug_dose_1 = Column(String(100))
    drug_class_2 = Column(String(50))
    drug_name_2 = Column(String(200))
    drug_dose_2 = Column(String(100))
    drug_class_3 = Column(String(50))
    drug_name_3 = Column(String(200))
    drug_dose_3 = Column(String(100))
    has_diabetes = Column(Boolean, default=False)
    has_ckd = Column(Boolean, default=False)
    has_cad = Column(Boolean, default=False)
    has_stroke = Column(Boolean, default=False)
    has_copd = Column(Boolean, default=False)
    target_sbp = Column(Integer, default=140)
    target_dbp = Column(Integer, default=90)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))

    # Indexes
    __table_args__ = (
        Index('idx_hypertension_patient', patient_id, is_active),
        Index('idx_hypertension_active', is_active, diagnosis_date),
    )


class FollowupHypertension(Base):
    """高血压随访扩展表"""
    __tablename__ = "followup_hypertension"

    followup_id = Column(String(36), ForeignKey("followup_record.followup_id"), primary_key=True)
    bp_grade = Column(String(20))
    cv_risk_updated = Column(String(20))
    drug_adjust_reason = Column(Text)
    is_urgent_alert = Column(Boolean, default=False)


class DiseaseDiabetes(Base):
    """糖尿病专病表"""
    __tablename__ = "disease_diabetes"

    disease_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String(36), ForeignKey("patient.patient_id"), nullable=False)
    diagnosis_date = Column(Date, nullable=False)
    diagnosis_type = Column(String(20))
    who_1999_type = Column(String(50))
    hba1c_at_diagnosis = Column(Numeric(4, 1))
    risk_score = Column(Integer)
    need_ogtt = Column(Boolean, default=False)
    cv_risk_stratification = Column(String(20))
    target_fbg = Column(Numeric(4, 1), default=4.4)
    target_pbg = Column(Numeric(4, 1), default=10.0)
    target_hba1c = Column(Numeric(4, 1), default=7.0)
    target_bp_sbp = Column(Integer, default=130)
    target_bp_dbp = Column(Integer, default=80)
    target_ldl_c = Column(Numeric(4, 2), default=2.6)
    metformin_dose = Column(String(50))
    glp1_ra_name = Column(String(200))
    sglt2i_name = Column(String(200))
    insulin_name = Column(String(200))
    insulin_dose = Column(String(100))
    other_drug = Column(Text)
    eye_exam_date = Column(Date)
    foot_exam_date = Column(Date)
    dnp_status = Column(String(20))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))

    # Indexes
    __table_args__ = (
        Index('idx_diabetes_patient', patient_id, is_active),
        Index('idx_diabetes_active', is_active, diagnosis_date),
    )


class FollowupDiabetes(Base):
    """糖尿病随访扩展表"""
    __tablename__ = "followup_diabetes"

    followup_id = Column(String(36), ForeignKey("followup_record.followup_id"), primary_key=True)
    hypoglycemia_event = Column(Boolean, default=False)
    hypoglycemia_count = Column(Integer, default=0)
    adverse_reaction = Column(Text)
    new_complication = Column(Text)


class DiseaseCoronaryHeartDisease(Base):
    """冠心病专病表"""
    __tablename__ = "disease_coronary_heart_disease"

    disease_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String(36), ForeignKey("patient.patient_id"), nullable=False)
    diagnosis_date = Column(Date, nullable=False)
    chd_type = Column(String(50))
    timi_score = Column(Integer)
    timi_risk = Column(String(20))
    grace_score = Column(Integer)
    grace_risk = Column(String(20))
    dapt_start_date = Column(Date)
    dapt_end_date = Column(Date)
    dapt_reminder_sent = Column(Boolean, default=False)
    target_ldl_c = Column(Numeric(4, 2))
    ldl_target_level = Column(String(20))
    statin_name = Column(String(200))
    antiplatelet_drug = Column(String(200))
    beta_blocker = Column(String(200))
    acei_arb_name = Column(String(200))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))

    # Indexes
    __table_args__ = (
        Index('idx_chd_patient', patient_id, is_active),
        Index('idx_chd_active', is_active, diagnosis_date),
    )


class DiseaseStroke(Base):
    """脑卒中专病表"""
    __tablename__ = "disease_stroke"

    disease_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String(36), ForeignKey("patient.patient_id"), nullable=False)
    diagnosis_date = Column(Date, nullable=False)
    stroke_type = Column(String(50))
    nihss_score = Column(Integer)
    fast_score = Column(Integer)
    befast_score = Column(Integer)
    need_referral = Column(Boolean)
    fu_3m_date = Column(Date)
    fu_6m_date = Column(Date)
    fu_1y_date = Column(Date)
    fu_3m_done = Column(Boolean, default=False)
    fu_6m_done = Column(Boolean, default=False)
    fu_1y_done = Column(Boolean, default=False)
    mrs_score = Column(Integer)
    barthel_index = Column(Integer)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))

    # Indexes
    __table_args__ = (
        Index('idx_stroke_patient', patient_id, is_active),
        Index('idx_stroke_active', is_active, diagnosis_date),
    )


class DiseaseCopd(Base):
    """慢阻肺专病表"""
    __tablename__ = "disease_copd"

    disease_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String(36), ForeignKey("patient.patient_id"), nullable=False)
    diagnosis_date = Column(Date, nullable=False)
    copd_gold_grade = Column(String(20))
    fev1_percent = Column(Numeric(5, 2))
    fev1_fvc_ratio = Column(Numeric(4, 2))
    mmrc_grade = Column(Integer)
    cat_score = Column(Integer)
    followup_per_year = Column(Integer)
    need_spirometry = Column(Boolean, default=False)
    last_spirometry_date = Column(Date)
    lama_name = Column(String(200))
    laba_name = Column(String(200))
    ics_name = Column(String(200))
    exacerbation_count = Column(Integer, default=0)
    last_exacerbation_date = Column(Date)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))

    # Indexes
    __table_args__ = (
        Index('idx_copd_patient', patient_id, is_active),
        Index('idx_copd_active', is_active, diagnosis_date),
    )


class DiseaseCkd(Base):
    """慢性肾脏病专病表"""
    __tablename__ = "disease_ckd"
    
    disease_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String(36), ForeignKey("patient.patient_id"), nullable=False)
    diagnosis_date = Column(Date, nullable=False)
    egfr = Column(Numeric(6, 2))
    egfr_last_check = Column(Date)
    egfr_prev = Column(Numeric(6, 2))
    egfr_declined = Column(Boolean, default=False)
    ckd_stage = Column(Integer)
    ckd_risk_level = Column(String(20))
    need_urinalysis = Column(Boolean, default=False)
    need_uacr = Column(Boolean, default=False)
    need_renal_function = Column(Boolean, default=False)
    need_electrolyte = Column(Boolean, default=False)
    need_renal_us = Column(Boolean, default=False)
    last_urinalysis_date = Column(Date)
    last_uacr_date = Column(Date)
    last_renal_function_date = Column(Date)
    last_electrolyte_date = Column(Date)
    last_renal_us_date = Column(Date)
    contraind_metformin = Column(Boolean, default=False)
    contraind_acei_arb = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))
    
    # Indexes
    __table_args__ = (
        Index('idx_ckd_patient', patient_id, is_active),
        Index('idx_ckd_active', is_active, diagnosis_date),
    )


class ReferralRecord(Base):
    """双向转诊记录表"""
    __tablename__ = "referral_record"

    referral_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String(36), ForeignKey("patient.patient_id"), nullable=False)
    disease_code = Column(String(20), ForeignKey("dim_disease_type.disease_code"))
    referral_type = Column(String(10), nullable=False)
    apply_org_code = Column(String(50), nullable=False)
    apply_doctor = Column(String(36), ForeignKey("sys_user.user_id"))
    apply_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))
    referral_reason = Column(Text)
    match_criteria = Column(JSON)
    is_eligible = Column(Boolean)
    reject_reason = Column(Text)
    down_plan = Column(JSON)
    receive_org_code = Column(String(50))
    receive_doctor = Column(String(36), ForeignKey("sys_user.user_id"))
    receive_at = Column(DateTime)
    status = Column(String(20), default='PENDING')
    timeout_alert_sent = Column(Boolean, default=False)
    completed_at = Column(DateTime)
    post_referral_fu_id = Column(String(36), ForeignKey("followup_record.followup_id"))
    created_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))

    # Indexes
    __table_args__ = (
        Index('idx_referral_patient', patient_id),
        Index('idx_referral_status', status),
        Index('idx_referral_status_org', status, receive_org_code),
    )


class AnnualAssessment(Base):
    """年度评估表"""
    __tablename__ = "annual_assessment"

    assessment_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String(36), ForeignKey("patient.patient_id"), nullable=False)
    disease_code = Column(String(20), ForeignKey("dim_disease_type.disease_code"), nullable=False)
    assessment_year = Column(Integer, nullable=False)
    bp_controlled_rate = Column(Numeric(5, 2))
    bg_controlled_rate = Column(Numeric(5, 2))
    lipid_controlled_rate = Column(Numeric(5, 2))
    followup_completion_rate = Column(Numeric(5, 2))
    eye_exam_done = Column(Boolean)
    foot_exam_done = Column(Boolean)
    echo_done = Column(Boolean)
    report_content = Column(Text)
    report_url = Column(Text)
    assessed_by = Column(String(36), ForeignKey("sys_user.user_id"))
    assessed_at = Column(DateTime)
    created_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))

    # Indexes
    __table_args__ = (
        Index('idx_annual_patient', patient_id),
        Index('idx_annual_year', assessment_year),
        Index('idx_annual_disease', disease_code, assessment_year),
    )


class KpiOrgStats(Base):
    """机构考核统计表"""
    __tablename__ = "kpi_org_stats"

    stats_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    org_code = Column(String(50), nullable=False)
    region_code = Column(String(12))
    stats_period = Column(String(20), nullable=False)
    period_type = Column(String(10), nullable=False)
    total_patients = Column(Integer)
    registered_count = Column(Integer)
    registration_rate = Column(Numeric(5, 2))
    screened_count = Column(Integer)
    screening_rate = Column(Numeric(5, 2))
    assessed_count = Column(Integer)
    assessment_rate = Column(Numeric(5, 2))
    contract_count = Column(Integer)
    contract_rate = Column(Numeric(5, 2))
    bp_controlled_count = Column(Integer)
    bp_controlled_rate = Column(Numeric(5, 2))
    bg_controlled_count = Column(Integer)
    bg_controlled_rate = Column(Numeric(5, 2))
    lipid_controlled_count = Column(Integer)
    lipid_controlled_rate = Column(Numeric(5, 2))
    followup_planned = Column(Integer)
    followup_done = Column(Integer)
    followup_completion_rate = Column(Numeric(5, 2))
    down_referral_count = Column(Integer)
    down_referral_growth = Column(Numeric(5, 2))
    warning_count = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))


class AlertRecord(Base):
    """预警记录表"""
    __tablename__ = "alert_record"

    alert_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String(36), ForeignKey("patient.patient_id"))
    org_code = Column(String(50))
    alert_type = Column(String(50), nullable=False)
    alert_level = Column(String(20), nullable=False)
    alert_title = Column(String(200), nullable=False)
    alert_content = Column(Text, nullable=False)
    is_handled = Column(Boolean, default=False)
    handled_by = Column(String(36), ForeignKey("sys_user.user_id"))
    handled_at = Column(DateTime)
    handle_note = Column(Text)
    created_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))

    # Indexes
    __table_args__ = (
        Index('idx_alert_org', org_code, created_at),
        Index('idx_alert_patient', patient_id, created_at),
        Index('idx_alert_unhandled', is_handled, created_at),
    )


class PatientWechat(Base):
    """患者微信绑定表"""
    __tablename__ = "patient_wechat"

    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(String(36), ForeignKey("patient.patient_id"), nullable=False)
    openid = Column(String(100), nullable=False)
    unionid = Column(String(100))
    nickname = Column(String(200))
    avatar_url = Column(Text)
    is_active = Column(Boolean, default=True)
    bound_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))


class PatientSelfReport(Base):
    """患者自主上报记录表"""
    __tablename__ = "patient_self_report"

    report_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String(36), ForeignKey("patient.patient_id"), nullable=False)
    report_date = Column(Date, nullable=False)
    bp_systolic = Column(Integer)
    bp_diastolic = Column(Integer)
    bg_value = Column(Numeric(4, 1))
    bg_type = Column(String(20))
    weight = Column(Numeric(5, 1))
    symptoms = Column(Text)
    medication_taken = Column(Boolean)
    report_source = Column(String(20), default='MINI_PROGRAM')
    device_id = Column(String(100))
    created_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))

    # Indexes
    __table_args__ = (
        Index('idx_self_report_patient', patient_id, report_date),
        Index('idx_self_report_date', report_date),
    )


class FollowupReminder(Base):
    """随访提醒表"""
    __tablename__ = "followup_reminder"

    reminder_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String(36), ForeignKey("patient.patient_id"), nullable=False)
    followup_id = Column(String(36), ForeignKey("followup_record.followup_id"))
    reminder_type = Column(String(20), nullable=False)
    remind_at = Column(DateTime, nullable=False)
    is_sent = Column(Boolean, default=False)
    sent_at = Column(DateTime)
    created_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))

    # Indexes
    __table_args__ = (
        Index('idx_reminder_patient', patient_id, remind_at),
        Index('idx_reminder_unsent', is_sent, remind_at),
    )


class TcmRecord(Base):
    """中医管理记录表 - 扩展支持完整中医临床路径"""
    __tablename__ = "tcm_record"

    tcm_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String(36), ForeignKey("patient.patient_id"), nullable=False)
    disease_code = Column(String(20), ForeignKey("dim_disease_type.disease_code"))
    record_date = Column(Date, nullable=False)

    # 辨证信息
    syndrome_type = Column(String(100))
    syndrome_name = Column(String(200))
    syndrome_differentiation = Column(Text)
    tcm_disease = Column(String(100))

    # 四诊信息
    inspection = Column(Text)
    auscultation = Column(Text)
    interrogation = Column(Text)
    palpation = Column(Text)
    tongue_body = Column(String(100))
    tongue_coating = Column(String(100))
    tongue_coat = Column(Text)
    pulse = Column(String(100))
    pulse_status = Column(Text)

    # 中医治疗
    treatment_method = Column(Text)
    prescription = Column(Text)
    tcm_prescription = Column(Text)
    herbs = Column(Text)
    tcm_herbs = Column(JSON)
    patent_medicine = Column(Text)

    # 其他疗法
    acupuncture = Column(Text)
    moxibustion = Column(Text)
    tuina = Column(Text)
    other_therapy = Column(Text)
    therapy_type = Column(JSON)
    therapy_note = Column(Text)

    # 养生调护
    diet_therapy = Column(Text)
    exercise_therapy = Column(Text)
    emotion_therapy = Column(Text)
    lifestyle_guidance = Column(Text)

    # Indexes
    __table_args__ = (
        Index('idx_tcm_patient', patient_id, record_date),
        Index('idx_tcm_disease', disease_code, record_date),
    )

    # 疗效与随访
    efficacy_evaluation = Column(Text)
    next_visit_date = Column(Date)

    # 就诊信息
    visit_date = Column(Date)
    visit_doctor = Column(String(100))
    recorded_by = Column(String(36), ForeignKey("sys_user.user_id"))
    created_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))


class EmergencyAlert(Base):
    """急救联动表"""
    __tablename__ = "emergency_alert"

    alert_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    patient_id = Column(String(36), ForeignKey("patient.patient_id"), nullable=False)
    alert_type = Column(String(20), nullable=False)
    trigger_by = Column(String(36), ForeignKey("sys_user.user_id"))
    trigger_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))
    patient_history = Column(Text)
    medications = Column(Text)
    allergies = Column(Text)
    vital_signs = Column(JSON)
    target_org = Column(String(50))
    target_dept = Column(String(50))
    estimated_arrival = Column(DateTime)
    status = Column(String(20), default='ACTIVATED')
    created_at = Column(DateTime, server_default=text("CURRENT_TIMESTAMP"))

    # Indexes
    __table_args__ = (
        Index('idx_emergency_patient', patient_id, trigger_at),
        Index('idx_emergency_status', status, trigger_at),
        Index('idx_emergency_unsent', status, trigger_at),
    )
