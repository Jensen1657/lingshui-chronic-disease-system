-- 慢病管理系统 - 数据库索引优化迁移脚本
-- 创建时间: 2026-05-25
-- 说明: 为高频查询字段添加 B-tree 索引，提升查询性能

-- ============================================
-- 1. annual_assessment 表索引
-- ============================================
CREATE INDEX IF NOT EXISTS idx_annual_patient ON annual_assessment(patient_id);
CREATE INDEX IF NOT EXISTS idx_annual_year ON annual_assessment(assessment_year);
CREATE INDEX IF NOT EXISTS idx_annual_disease ON annual_assessment(disease_code, assessment_year);

-- ============================================
-- 2. patient_self_report 表索引
-- ============================================
CREATE INDEX IF NOT EXISTS idx_self_report_patient ON patient_self_report(patient_id, report_date);
CREATE INDEX IF NOT EXISTS idx_self_report_date ON patient_self_report(report_date);

-- ============================================
-- 3. followup_reminder 表索引
-- ============================================
CREATE INDEX IF NOT EXISTS idx_reminder_patient ON followup_reminder(patient_id, remind_at);
CREATE INDEX IF NOT EXISTS idx_reminder_unsent ON followup_reminder(is_sent, remind_at) WHERE is_sent = false;

-- ============================================
-- 4. tcm_record 表索引
-- ============================================
CREATE INDEX IF NOT EXISTS idx_tcm_patient ON tcm_record(patient_id, record_date);
CREATE INDEX IF NOT EXISTS idx_tcm_disease ON tcm_record(disease_code, record_date);

-- ============================================
-- 5. emergency_alert 表索引
-- ============================================
CREATE INDEX IF NOT EXISTS idx_emergency_patient ON emergency_alert(patient_id, trigger_at);
CREATE INDEX IF NOT EXISTS idx_emergency_status ON emergency_alert(status, trigger_at);
CREATE INDEX IF NOT EXISTS idx_emergency_unsent ON emergency_alert(status, trigger_at) WHERE status = 'ACTIVATED';

-- ============================================
-- 6. disease_hypertension 表索引
-- ============================================
CREATE INDEX IF NOT EXISTS idx_hypertension_patient ON disease_hypertension(patient_id, is_active);
CREATE INDEX IF NOT EXISTS idx_hypertension_active ON disease_hypertension(is_active, diagnosis_date);

-- ============================================
-- 7. disease_diabetes 表索引
-- ============================================
CREATE INDEX IF NOT EXISTS idx_diabetes_patient ON disease_diabetes(patient_id, is_active);
CREATE INDEX IF NOT EXISTS idx_diabetes_active ON disease_diabetes(is_active, diagnosis_date);

-- ============================================
-- 8. disease_coronary_heart_disease 表索引
-- ============================================
CREATE INDEX IF NOT EXISTS idx_chd_patient ON disease_coronary_heart_disease(patient_id, is_active);
CREATE INDEX IF NOT EXISTS idx_chd_active ON disease_coronary_heart_disease(is_active, diagnosis_date);

-- ============================================
-- 9. disease_stroke 表索引
-- ============================================
CREATE INDEX IF NOT EXISTS idx_stroke_patient ON disease_stroke(patient_id, is_active);
CREATE INDEX IF NOT EXISTS idx_stroke_active ON disease_stroke(is_active, diagnosis_date);

-- ============================================
-- 10. disease_copd 表索引
-- ============================================
CREATE INDEX IF NOT EXISTS idx_copd_patient ON disease_copd(patient_id, is_active);
CREATE INDEX IF NOT EXISTS idx_copd_active ON disease_copd(is_active, diagnosis_date);

-- ============================================
-- 11. disease_ckd 表索引
-- ============================================
CREATE INDEX IF NOT EXISTS idx_ckd_patient ON disease_ckd(patient_id, is_active);
CREATE INDEX IF NOT EXISTS idx_ckd_active ON disease_ckd(is_active, diagnosis_date);

-- ============================================
-- 说明
-- ============================================
-- 1. 部分索引 (WHERE 子句) 仅适用于 PostgreSQL，SQLite 不支持
-- 2. 如果使用的是 SQLite，请删除 WHERE 子句后运行
-- 3. 索引创建时间取决于表大小，大表可能需要几分钟
-- 4. 建议在维护窗口执行，避免锁表影响业务

-- SQLite 兼容版本 (如果需要):
-- CREATE INDEX IF NOT EXISTS idx_reminder_unsent ON followup_reminder(is_sent, remind_at);
-- CREATE INDEX IF NOT EXISTS idx_emergency_unsent ON emergency_alert(status, trigger_at);
