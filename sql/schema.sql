-- =====================================================
-- 陵水县人民医院慢病管理系统 — SQLite Schema
-- PostgreSQL → SQLite 兼容版本
-- =====================================================

-- =====================================================
-- 一、基础字典表
-- =====================================================

CREATE TABLE dim_region (
    region_code    VARCHAR(12)  PRIMARY KEY,
    region_name    VARCHAR(100) NOT NULL,
    region_level   SMALLINT     NOT NULL,
    parent_code    VARCHAR(12),
    org_code       VARCHAR(50),
    org_name       VARCHAR(200),
    created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE dim_disease_type (
    disease_code   VARCHAR(20)  PRIMARY KEY,
    disease_name  VARCHAR(100) NOT NULL,
    icd10_code    VARCHAR(20),
    sort_order    INTEGER DEFAULT 0
);

INSERT INTO dim_disease_type (disease_code, disease_name, icd10_code) VALUES
('HYPERTENSION', '高血压', 'I10'),
('DIABETES', '糖尿病', 'E11'),
('CORONARY_HEART_DISEASE', '冠心病', 'I20-I25'),
('STROKE', '脑卒中', 'I60-I69'),
('COPD', '慢阻肺', 'J44'),
('CKD', '慢性肾脏病', 'N18');

CREATE TABLE dim_drug (
    drug_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    drug_name       VARCHAR(200) NOT NULL,
    drug_code       VARCHAR(50),
    specification   VARCHAR(100),
    unit            VARCHAR(20),
    drug_class      VARCHAR(100),
    indication      TEXT,
    contraindication TEXT,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- 二、用户与权限
-- =====================================================

CREATE TABLE sys_user (
    user_id         TEXT PRIMARY KEY,
    username        VARCHAR(50)  NOT NULL UNIQUE,
    password_hash   VARCHAR(255) NOT NULL,
    real_name       VARCHAR(100) NOT NULL,
    id_card_enc     TEXT,
    phone_enc       TEXT,
    org_code        VARCHAR(50)  NOT NULL,
    region_code     VARCHAR(12),
    role_code       VARCHAR(20)  NOT NULL,
    is_active       INTEGER DEFAULT 1,
    last_login_at   TIMESTAMP,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE sys_role_permission (
    role_code       VARCHAR(20) PRIMARY KEY,
    role_name       VARCHAR(100),
    permissions     TEXT NOT NULL,
    description     TEXT
);

INSERT INTO sys_role_permission (role_code, role_name, permissions, description) VALUES
('VILLAGE_DOCTOR', '村卫生室医生', '["followup:create", "screening:create", "referral:apply"]', '随访录入、高危筛查、上转申请'),
('TOWN_DOCTOR', '乡镇卫生院医生', '["patient:manage", "followup:manage", "referral:apply", "referral:receive", "report:basic"]', '患者管理、上转申请、基础报表、下转接收'),
('COUNTY_DOCTOR', '县级医院医生', '["diagnosis:edit", "referral:down", "treatment:audit", "patient:view_all"]', '诊断调整、下转方案制定、治疗方案审核'),
('ADMIN', '管理中心管理员', '["*"]', '全量数据查看、考核统计、系统配置'),
('PATIENT', '患者', '["self:view", "self:report"]', '查看自己的健康数据、自助上报');

CREATE TABLE sys_audit_log (
    log_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         TEXT,
    action          VARCHAR(100) NOT NULL,
    resource_type   VARCHAR(100),
    resource_id     VARCHAR(100),
    ip_address      TEXT,
    user_agent      TEXT,
    request_data    TEXT,
    response_data   TEXT,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- 三、患者主索引（EMPI）
-- =====================================================

CREATE TABLE patient (
    patient_id      TEXT PRIMARY KEY,
    id_card_enc     TEXT NOT NULL,
    id_card_hash    VARCHAR(64) UNIQUE,
    name_enc        TEXT NOT NULL,
    gender          VARCHAR(1),
    birth_date      DATE,
    age             INTEGER,
    phone_enc       TEXT,
    address         TEXT,
    village_code    VARCHAR(12),
    manage_org_code VARCHAR(50) NOT NULL,
    disease_list    TEXT NOT NULL DEFAULT '{}',
    risk_level      VARCHAR(20),
    is_active       INTEGER DEFAULT 1,
    empi_status     VARCHAR(20) DEFAULT 'ACTIVE',
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_patient_village ON patient(village_code);
CREATE INDEX idx_patient_org ON patient(manage_org_code);
CREATE INDEX idx_patient_disease ON patient(disease_list);
CREATE INDEX idx_patient_id_card_hash ON patient(id_card_hash);

-- =====================================================
-- 四、通用随访记录表
-- =====================================================

CREATE TABLE followup_record (
    followup_id      TEXT PRIMARY KEY,
    patient_id       TEXT NOT NULL,
    disease_code     VARCHAR(20) NOT NULL,
    followup_no      INTEGER NOT NULL,
    followup_type   VARCHAR(20) NOT NULL,
    followup_date   DATE NOT NULL,
    performed_by    TEXT NOT NULL,
    org_code        VARCHAR(50) NOT NULL,
    bp_systolic     INTEGER,
    bp_diastolic    INTEGER,
    fbg             NUMERIC(4,1),
    pbg             NUMERIC(4,1),
    hba1c           NUMERIC(4,1),
    ldl_c           NUMERIC(4,2),
    hdl_c           NUMERIC(4,2),
    tc              NUMERIC(4,2),
    tg              NUMERIC(4,2),
    weight           NUMERIC(5,1),
    bmi             NUMERIC(4,1),
    heart_rate      INTEGER,
    medication_adherence VARCHAR(20),
    is_controlled   INTEGER DEFAULT 0,
    next_followup_date DATE,
    symptoms        TEXT,
    signs           TEXT,
    medication_changed INTEGER DEFAULT 0,
    medication_note TEXT,
    location_lat    NUMERIC(10,6),
    location_lng    NUMERIC(10,6),
    audio_record_url TEXT,
    device_data     TEXT,
    is_audited      INTEGER DEFAULT 0,
    audited_by      TEXT,
    audited_at      TIMESTAMP,
    audit_note      TEXT,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_followup_patient ON followup_record(patient_id, disease_code);
CREATE INDEX idx_followup_date ON followup_record(followup_date);

-- =====================================================
-- 五、高血压专病表
-- =====================================================

CREATE TABLE disease_hypertension (
    disease_id           TEXT PRIMARY KEY,
    patient_id          TEXT NOT NULL,
    diagnosis_date      DATE NOT NULL,
    diagnosis_doctor   TEXT,
    diagnosis_org      VARCHAR(50),
    icd10_code         VARCHAR(20) DEFAULT 'I10',
    risk_stratification VARCHAR(20),
    risk_score         INTEGER,
    ecg_result         TEXT,
    ucr_result         TEXT,
    echo_result        TEXT,
    imt_result         TEXT,
    drug_class_1       VARCHAR(50),
    drug_name_1        VARCHAR(200),
    drug_dose_1        VARCHAR(100),
    drug_class_2       VARCHAR(50),
    drug_name_2        VARCHAR(200),
    drug_dose_2        VARCHAR(100),
    drug_class_3       VARCHAR(50),
    drug_name_3        VARCHAR(200),
    drug_dose_3        VARCHAR(100),
    has_diabetes       INTEGER DEFAULT 0,
    has_ckd            INTEGER DEFAULT 0,
    has_cad            INTEGER DEFAULT 0,
    has_stroke         INTEGER DEFAULT 0,
    has_copd           INTEGER DEFAULT 0,
    target_sbp         INTEGER DEFAULT 140,
    target_dbp         INTEGER DEFAULT 90,
    is_active          INTEGER DEFAULT 1,
    created_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE followup_hypertension (
    followup_id         TEXT PRIMARY KEY,
    bp_grade           VARCHAR(20),
    cv_risk_updated    VARCHAR(20),
    drug_adjust_reason  TEXT,
    is_urgent_alert    INTEGER DEFAULT 0
);

-- =====================================================
-- 六、糖尿病专病表
-- =====================================================

CREATE TABLE disease_diabetes (
    disease_id              TEXT PRIMARY KEY,
    patient_id             TEXT NOT NULL,
    diagnosis_date         DATE NOT NULL,
    diagnosis_type         VARCHAR(20),
    who_1999_type         VARCHAR(50),
    hba1c_at_diagnosis   NUMERIC(4,1),
    risk_score             INTEGER,
    need_ogtt             INTEGER DEFAULT 0,
    cv_risk_stratification VARCHAR(20),
    target_fbg            NUMERIC(4,1) DEFAULT 4.4,
    target_pbg            NUMERIC(4,1) DEFAULT 10.0,
    target_hba1c          NUMERIC(4,1) DEFAULT 7.0,
    target_bp_sbp         INTEGER DEFAULT 130,
    target_bp_dbp         INTEGER DEFAULT 80,
    target_ldl_c          NUMERIC(4,2) DEFAULT 2.6,
    metformin_dose        VARCHAR(50),
    glp1_ra_name          VARCHAR(200),
    sglt2i_name           VARCHAR(200),
    insulin_name           VARCHAR(200),
    insulin_dose           VARCHAR(100),
    other_drug             TEXT,
    eye_exam_date          DATE,
    foot_exam_date         DATE,
    dnp_status             VARCHAR(20),
    is_active              INTEGER DEFAULT 1,
    created_at             TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at             TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE followup_diabetes (
    followup_id          TEXT PRIMARY KEY,
    hypoglycemia_event   INTEGER DEFAULT 0,
    hypoglycemia_count   INTEGER DEFAULT 0,
    adverse_reaction     TEXT,
    new_complication     TEXT
);

-- =====================================================
-- 七、冠心病专病表
-- =====================================================

CREATE TABLE disease_coronary_heart_disease (
    disease_id          TEXT PRIMARY KEY,
    patient_id          TEXT NOT NULL,
    diagnosis_date      DATE NOT NULL,
    chd_type            VARCHAR(50),
    timi_score          INTEGER,
    timi_risk           VARCHAR(20),
    grace_score         INTEGER,
    grace_risk          VARCHAR(20),
    dapt_start_date     DATE,
    dapt_end_date       DATE,
    dapt_reminder_sent  INTEGER DEFAULT 0,
    target_ldl_c        NUMERIC(4,2),
    ldl_target_level    VARCHAR(20),
    statin_name         VARCHAR(200),
    antiplatelet_drug   VARCHAR(200),
    beta_blocker        VARCHAR(200),
    acei_arb_name       VARCHAR(200),
    is_active           INTEGER DEFAULT 1,
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- 八、脑卒中专病表
-- =====================================================

CREATE TABLE disease_stroke (
    disease_id        TEXT PRIMARY KEY,
    patient_id        TEXT NOT NULL,
    diagnosis_date    DATE NOT NULL,
    stroke_type       VARCHAR(50),
    nihss_score       INTEGER,
    fast_score        INTEGER,
    befast_score      INTEGER,
    need_referral     INTEGER,
    fu_3m_date        DATE,
    fu_6m_date        DATE,
    fu_1y_date        DATE,
    fu_3m_done        INTEGER DEFAULT 0,
    fu_6m_done        INTEGER DEFAULT 0,
    fu_1y_done        INTEGER DEFAULT 0,
    mrs_score         INTEGER,
    barthel_index     INTEGER,
    is_active         INTEGER DEFAULT 1,
    created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- 九、慢阻肺专病表
-- =====================================================

CREATE TABLE disease_copd (
    disease_id          TEXT PRIMARY KEY,
    patient_id          TEXT NOT NULL,
    diagnosis_date      DATE NOT NULL,
    copd_gold_grade    VARCHAR(20),
    fev1_percent       NUMERIC(5,2),
    fev1_fvc_ratio    NUMERIC(4,2),
    mmrc_grade         INTEGER,
    cat_score          INTEGER,
    followup_per_year  INTEGER,
    need_spirometry    INTEGER DEFAULT 0,
    last_spirometry_date DATE,
    lama_name          VARCHAR(200),
    laba_name          VARCHAR(200),
    ics_name           VARCHAR(200),
    exacerbation_count INTEGER DEFAULT 0,
    last_exacerbation_date DATE,
    is_active          INTEGER DEFAULT 1,
    created_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- 十、慢性肾脏病专病表
-- =====================================================

CREATE TABLE disease_ckd (
    disease_id              TEXT PRIMARY KEY,
    patient_id              TEXT NOT NULL,
    diagnosis_date          DATE NOT NULL,
    egfr                   NUMERIC(6,2),
    egfr_last_check        DATE,
    egfr_prev              NUMERIC(6,2),
    egfr_declined          INTEGER DEFAULT 0,
    ckd_stage              INTEGER,
    ckd_risk_level         VARCHAR(20),
    need_urinalysis        INTEGER DEFAULT 0,
    need_uacr              INTEGER DEFAULT 0,
    need_renal_function    INTEGER DEFAULT 0,
    need_electrolyte       INTEGER DEFAULT 0,
    need_renal_us          INTEGER DEFAULT 0,
    last_urinalysis_date   DATE,
    last_uacr_date         DATE,
    last_renal_function_date DATE,
    last_electrolyte_date  DATE,
    last_renal_us_date     DATE,
    contraind_metformin    INTEGER DEFAULT 0,
    contraind_acei_arb    INTEGER DEFAULT 0,
    is_active              INTEGER DEFAULT 1,
    created_at             TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at             TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- 十一、双向转诊
-- =====================================================

CREATE TABLE referral_record (
    referral_id         TEXT PRIMARY KEY,
    patient_id         TEXT NOT NULL,
    disease_code       VARCHAR(20),
    referral_type      VARCHAR(10) NOT NULL,
    apply_org_code     VARCHAR(50) NOT NULL,
    apply_doctor       TEXT,
    apply_at           TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    referral_reason    TEXT,
    match_criteria     TEXT,
    is_eligible        INTEGER,
    reject_reason      TEXT,
    down_plan          TEXT,
    receive_org_code   VARCHAR(50),
    receive_doctor     TEXT,
    receive_at         TIMESTAMP,
    status             VARCHAR(20) DEFAULT 'PENDING',
    timeout_alert_sent INTEGER DEFAULT 0,
    completed_at       TIMESTAMP,
    post_referral_fu_id TEXT,
    created_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_referral_patient ON referral_record(patient_id);
CREATE INDEX idx_referral_status ON referral_record(status);

-- =====================================================
-- 十二、年度评估
-- =====================================================

CREATE TABLE annual_assessment (
    assessment_id    TEXT PRIMARY KEY,
    patient_id      TEXT NOT NULL,
    disease_code    VARCHAR(20) NOT NULL,
    assessment_year INTEGER NOT NULL,
    bp_controlled_rate    NUMERIC(5,2),
    bg_controlled_rate    NUMERIC(5,2),
    lipid_controlled_rate NUMERIC(5,2),
    followup_completion_rate NUMERIC(5,2),
    eye_exam_done   INTEGER,
    foot_exam_done  INTEGER,
    echo_done       INTEGER,
    report_content  TEXT,
    report_url      TEXT,
    assessed_by     TEXT,
    assessed_at     TIMESTAMP,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- 十三、考核统计
-- =====================================================

CREATE TABLE kpi_org_stats (
    stats_id                TEXT PRIMARY KEY,
    org_code               VARCHAR(50) NOT NULL,
    region_code            VARCHAR(12),
    stats_period           VARCHAR(20) NOT NULL,
    period_type            VARCHAR(10) NOT NULL,
    total_patients         INTEGER,
    registered_count       INTEGER,
    registration_rate      NUMERIC(5,2),
    screened_count         INTEGER,
    screening_rate         NUMERIC(5,2),
    assessed_count         INTEGER,
    assessment_rate        NUMERIC(5,2),
    contract_count         INTEGER,
    contract_rate          NUMERIC(5,2),
    bp_controlled_count   INTEGER,
    bp_controlled_rate     NUMERIC(5,2),
    bg_controlled_count    INTEGER,
    bg_controlled_rate     NUMERIC(5,2),
    lipid_controlled_count INTEGER,
    lipid_controlled_rate  NUMERIC(5,2),
    followup_planned       INTEGER,
    followup_done          INTEGER,
    followup_completion_rate NUMERIC(5,2),
    down_referral_count    INTEGER,
    down_referral_growth   NUMERIC(5,2),
    warning_count          INTEGER DEFAULT 0,
    created_at             TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- 十四、预警记录
-- =====================================================

CREATE TABLE alert_record (
    alert_id      TEXT PRIMARY KEY,
    patient_id    TEXT,
    org_code      VARCHAR(50),
    alert_type    VARCHAR(50) NOT NULL,
    alert_level   VARCHAR(20) NOT NULL,
    alert_title   VARCHAR(200) NOT NULL,
    alert_content TEXT NOT NULL,
    is_handled   INTEGER DEFAULT 0,
    handled_by    TEXT,
    handled_at    TIMESTAMP,
    handle_note   TEXT,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_alert_org ON alert_record(org_code, created_at);
CREATE INDEX idx_alert_patient ON alert_record(patient_id, created_at);
CREATE INDEX idx_alert_unhandled ON alert_record(is_handled, created_at);

-- =====================================================
-- 十五、患者端（小程序/公众号）
-- =====================================================

CREATE TABLE patient_wechat (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id   TEXT NOT NULL,
    openid       VARCHAR(100) NOT NULL,
    unionid      VARCHAR(100),
    nickname     VARCHAR(200),
    avatar_url   TEXT,
    is_active    INTEGER DEFAULT 1,
    bound_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE patient_self_report (
    report_id      TEXT PRIMARY KEY,
    patient_id     TEXT NOT NULL,
    report_date    DATE NOT NULL,
    bp_systolic   INTEGER,
    bp_diastolic  INTEGER,
    bg_value      NUMERIC(4,1),
    bg_type       VARCHAR(20),
    weight         NUMERIC(5,1),
    symptoms      TEXT,
    medication_taken INTEGER,
    report_source VARCHAR(20) DEFAULT 'MINI_PROGRAM',
    device_id     VARCHAR(100),
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE followup_reminder (
    reminder_id   TEXT PRIMARY KEY,
    patient_id    TEXT NOT NULL,
    followup_id   TEXT,
    reminder_type VARCHAR(20) NOT NULL,
    remind_at     TIMESTAMP NOT NULL,
    is_sent       INTEGER DEFAULT 0,
    sent_at       TIMESTAMP,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- 十六、中医药管理
-- =====================================================

CREATE TABLE tcm_record (
    tcm_id         TEXT PRIMARY KEY,
    patient_id     TEXT NOT NULL,
    disease_code   VARCHAR(20),
    record_date    DATE NOT NULL,
    syndrome_type  VARCHAR(100),
    tongue_coat    TEXT,
    pulse_status   TEXT,
    tcm_prescription TEXT,
    tcm_herbs      TEXT,
    therapy_type   TEXT,
    therapy_note   TEXT,
    recorded_by    TEXT,
    created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- 十七、急救联动
-- =====================================================

CREATE TABLE emergency_alert (
    alert_id           TEXT PRIMARY KEY,
    patient_id         TEXT NOT NULL,
    alert_type         VARCHAR(20) NOT NULL,
    trigger_by         TEXT,
    trigger_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    patient_history    TEXT,
    medications        TEXT,
    allergies          TEXT,
    vital_signs        TEXT,
    target_org         VARCHAR(50),
    target_dept        VARCHAR(50),
    estimated_arrival  TIMESTAMP,
    status             VARCHAR(20) DEFAULT 'ACTIVATED',
    created_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
