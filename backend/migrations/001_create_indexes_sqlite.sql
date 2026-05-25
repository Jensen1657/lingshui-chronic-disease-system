-- 慢病管理系统 - 数据库索引优化迁移脚本 (SQLite 兼容版)
-- 创建时间: 2026-05-25
-- 说明: 为高频查询字段添加 B-tree 索引，提升查询性能
-- 注意: SQLite 不支持部分索引 (WHERE 子句)，已移除

-- ===========================================
-- 1. annual_assessment 表索引
-- ===========================================
CREATE INDEX IF NOT EXISTS idx_annual_patient ON annual_assessment(patient_id);
CREATE INDEX IF NOT EXISTS idx_annual_year ON annual_assessment(assessment_year);
CREATE INDEX IF NOT EXISTS idx_annual_disease ON annual_assessment(disease_code, assessment_year);

-- ===========================================
-- 2. patient_self_report 表索引
-- ===========================================
CREATE INDEX IF NOT EXISTS idx_self_report_patient ON patient_self_report(patient_id, report_date);
CREATE INDEX IF NOT EXISTS idx_self_report_date ON patient_self_report(report_date);

-- ===========================================
-- 3. followup_reminder 表索引
-- ===========================================
CREATE INDEX IF NOT EXISTS idx_reminder_patient ON followup_reminder(patient_id, remind_at);
CREATE INDEX IF NOT EXISTS idx_reminder_unsent ON followup_reminder(is_sent, remind_at);

-- ===========================================
-- 4. tcm_record 表索引
-- ===========================================
CREATE INDEX IF NOT EXISTS idx_tcm_patient ON tcm_record(patient_id, record_date);
CREATE INDEX IF NOT EXISTS idx_tcm_disease ON tcm_record(disease_code, record_date);

-- ===========================================
-- 5. emergency_alert 表索引
-- ===========================================
CREATE INDEX IF NOT EXISTS idx_emergency_patient ON emergency_alert(patient_id, trigger_at);
CREATE INDEX IF NOT EXISTS idx_emergency_status ON emergency_alert(status, trigger_at);

-- 注意: SQLite 不支持部分索引，改为全表索引
CREATE INDEX IF NOT EXISTS idx_emergency_unsent ON emergency_alert(status, trigger_at);

-- ===========================================
-- 6. disease_hypertension 表索引
-- ===========================================
CREATE INDEX IF NOT EXISTS idx_hypertension_patient ON disease_hypertension(patient_id, is_active);
CREATE INDEX IF NOT EXISTS idx_hypertension_active ON disease_hypertension(is_active, diagnosis_date);

-- ===========================================
-- 7. disease_diabetes 表索引
-- ===========================================
CREATE INDEX IF NOT EXISTS idx_diabetes_patient ON disease_diabetes(patient_id, is_active);
CREATE INDEX IF NOT EXISTS idx_diabetes_active ON disease_diabetes(is_active, diagnosis_date);

-- ===========================================
-- 8. disease_coronary_heart_disease 表索引
-- ===========================================
CREATE INDEX IF NOT EXISTS idx_chd_patient ON disease_coronary_heart_disease(patient_id, is_active);
CREATE INDEX IF NOT EXISTS idx_chd_active ON disease_coronary_heart_disease(is_active, diagnosis_date);

-- ===========================================
-- 9. disease_stroke 表索引
-- ===========================================
CREATE INDEX IF NOT EXISTS idx_stroke_patient ON disease_stroke(patient_id, is_active);
CREATE INDEX IF NOT EXISTS idx_stroke_active ON disease_stroke(is_active, diagnosis_date);

-- ===========================================
-- 10. disease_copd 表索引
-- ===========================================
CREATE INDEX IF NOT EXISTS idx_copd_patient ON disease_copd(patient_id, is_active);
CREATE INDEX IF NOT EXISTS idx_copd_active ON disease_copd(is_active, diagnosis_date);

-- ===========================================
-- 11. disease_ckd 表索引
-- ===========================================
CREATE INDEX IF NOT EXISTS idx_ckd_patient ON disease_ckd(patient_id, is_active);
CREATE INDEX IF NOT EXISTS idx_ckd_active ON disease_ckd(is_active, diagnosis_date);

-- ===========================================
-- 说明
-- ===========================================
-- 1. SQLite 索引为 B-tree 结构，适合等值查询和范围查询
-- 2. 复合索引遵循最左前缀原则 (patient_id, is_active) 可命中 patient_id 或 (patient_id, is_active)
-- 3. 索引会略微降低 INSERT/UPDATE/DELETE 性能，但慢病管理系统以查询为主，收益显著
-- 4. 执行时间: 小表 <1s，大表 (patient 50条, followup 105条) <1s
-- 5. 可通过 EXPLAIN QUERY PLAN <SQL> 验证索引是否生效

-- 验证索引生效示例:
-- EXPLAIN QUERY PLAN SELECT * FROM patient WHERE manage_org_code = '46012301';
-- 应看到 "SEARCH TABLE patient USING INDEX idx_patient_org"

-- 查看所有索引:
-- .indices
