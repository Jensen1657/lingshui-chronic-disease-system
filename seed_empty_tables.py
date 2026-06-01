#!/usr/bin/env python3
"""
填充空表种子数据：dim_drug + health_education_record + prescription_review
适配服务器 SQLite schema，列名精确匹配
"""
import sqlite3, uuid, random, os
from datetime import datetime, timedelta

DB = os.getenv('DB_PATH', '/opt/lingshui/backend/lingshui.db')
ENV = os.getenv('SEED_ENV', 'server')  # 'local' or 'server'

now = datetime.now()
c = sqlite3.connect(DB)

# ========== 1. dim_drug — 药品字典 (50种慢病常用药) ==========
DRUGS = [
    # 高血压 (class: 降压药)
    (1, '硝苯地平控释片', 'NIF30', '30mg', '片', '降压药(CCB)', '原发性高血压', '心源性休克', datetime.now()),
    (2, '氨氯地平片', 'AML5', '5mg', '片', '降压药(CCB)', '高血压', '严重低血压', datetime.now()),
    (3, '厄贝沙坦片', 'IRB150', '150mg', '片', '降压药(ARB)', '原发性高血压', '妊娠期', datetime.now()),
    (4, '缬沙坦胶囊', 'VAL80', '80mg', '粒', '降压药(ARB)', '高血压', '妊娠期/双侧肾动脉狭窄', datetime.now()),
    (5, '卡托普利片', 'CAP25', '25mg', '片', '降压药(ACEI)', '高血压/心力衰竭', '妊娠期/血管神经性水肿', datetime.now()),
    (6, '依那普利片', 'ENA10', '10mg', '片', '降压药(ACEI)', '高血压', '妊娠期', datetime.now()),
    (7, '美托洛尔缓释片', 'METO47', '47.5mg', '片', '降压药(β-RB)', '高血压/心绞痛', 'II-III度房室传导阻滞', datetime.now()),
    (8, '比索洛尔片', 'BIS5', '5mg', '片', '降压药(β-RB)', '高血压/冠心病', '心源性休克', datetime.now()),
    (9, '氢氯噻嗪片', 'HCT25', '25mg', '片', '降压药(利尿剂)', '高血压/水肿', '痛风/无尿', datetime.now()),
    (10, '螺内酯片', 'SPI20', '20mg', '片', '降压药(利尿剂)', '高血压/水肿', '高钾血症/无尿', datetime.now()),
    # 糖尿病 (class: 降糖药)
    (11, '二甲双胍缓释片', 'MET500', '500mg', '片', '降糖药(双胍类)', '2型糖尿病', '严重肾功能不全(eGFR<30)', datetime.now()),
    (12, '格列美脲片', 'GLIM2', '2mg', '片', '降糖药(磺脲类)', '2型糖尿病', '1型糖尿病/酮症酸中毒', datetime.now()),
    (13, '阿卡波糖片', 'ACA50', '50mg', '片', '降糖药(α糖苷酶抑制剂)', '2型糖尿病', '肠梗阻/严重肾功能不全', datetime.now()),
    (14, '西格列汀片', 'SITA100', '100mg', '片', '降糖药(DPP-4i)', '2型糖尿病', '对本品过敏', datetime.now()),
    (15, '达格列净片', 'DAPA10', '10mg', '片', '降糖药(SGLT2i)', '2型糖尿病/心衰', '1型糖尿病/酮症酸中毒', datetime.now()),
    (16, '恩格列净片', 'EMP10', '10mg', '片', '降糖药(SGLT2i)', '2型糖尿病', '透析患者', datetime.now()),
    (17, '吡格列酮片', 'PIO15', '15mg', '片', '降糖药(TZD)', '2型糖尿病', '心力衰竭/肝功能不全', datetime.now()),
    (18, '胰岛素注射液(甘精胰岛素)', 'INS100', '100U/ml', '支', '降糖药(胰岛素)', '1型/2型糖尿病', '低血糖', datetime.now()),
    # 冠心病 (class: 心血管)
    (19, '阿司匹林肠溶片', 'ASP100', '100mg', '片', '抗血小板药', '冠心病/脑卒中二级预防', '活动性出血/严重肝病', datetime.now()),
    (20, '氯吡格雷片', 'CLO75', '75mg', '片', '抗血小板药', 'ACS/PCI术后', '活动性出血', datetime.now()),
    (21, '替格瑞洛片', 'TIC90', '90mg', '片', '抗血小板药', 'ACS', '活动性出血/严重肝病', datetime.now()),
    (22, '阿托伐他汀钙片', 'ATV20', '20mg', '片', '调脂药(他汀)', '高脂血症/冠心病', '活动性肝病/妊娠期', datetime.now()),
    (23, '瑞舒伐他汀钙片', 'ROS10', '10mg', '片', '调脂药(他汀)', '高脂血症', '活动性肝病', datetime.now()),
    (24, '非诺贝特胶囊', 'FEN200', '200mg', '粒', '调脂药(贝特)', '高甘油三酯血症', '严重肝肾功能不全', datetime.now()),
    (25, '单硝酸异山梨酯片', 'ISM20', '20mg', '片', '硝酸酯类', '冠心病/心绞痛', '青光眼/严重贫血', datetime.now()),
    (26, '硝酸甘油片', 'NTG0.5', '0.5mg', '片', '硝酸酯类', '心绞痛急性发作', '严重低血压/颅内高压', datetime.now()),
    (27, '曲美他嗪片', 'TRI20', '20mg', '片', '心肌代谢药', '心绞痛辅助用药', '帕金森综合征', datetime.now()),
    # 脑卒中
    (28, '胞磷胆碱钠胶囊', 'CIT0.1', '0.1g', '粒', '神经营养药', '脑卒中后遗症', '高肌张力', datetime.now()),
    (29, '丁苯酞软胶囊', 'BUT0.1', '0.1g', '粒', '脑血管扩张药', '急性缺血性脑卒中', '出血性脑卒中/严重肝肾不全', datetime.now()),
    (30, '依达拉奉注射液', 'EDA30', '30mg', '支', '脑保护剂', '急性脑梗死', '严重肾功能不全', datetime.now()),
    (31, '脑心通胶囊', 'NXT0.4', '0.4g', '粒', '中成药(活血)', '脑卒中/冠心病', '出血性疾病/孕妇', datetime.now()),
    # 慢阻肺
    (32, '沙美特罗替卡松粉吸入剂', 'SER50', '50/250ug', '支', '吸入剂(LABA+ICS)', '慢阻肺/哮喘', '对乳糖过敏', datetime.now()),
    (33, '噻托溴铵粉吸入剂', 'TIO18', '18ug', '粒', '吸入剂(LAMA)', '慢阻肺', '闭角型青光眼', datetime.now()),
    (34, '布地奈德福莫特罗吸入剂', 'BUD160', '160/4.5ug', '支', '吸入剂(ICS+LABA)', '慢阻肺/哮喘', '—', datetime.now()),
    (35, '氨茶碱片', 'AMI100', '100mg', '片', '支气管扩张剂', '慢阻肺/哮喘', '活动性消化性溃疡', datetime.now()),
    (36, '孟鲁司特钠片', 'MON10', '10mg', '片', '白三烯受体拮抗剂', '哮喘/过敏性鼻炎', '—', datetime.now()),
    # 慢性肾脏病 (CKD)
    (37, '药用炭片', 'CHA0.3', '0.3g', '片', '吸附剂', 'CKD高磷血症', '肠梗阻', datetime.now()),
    (38, '复方α-酮酸片', 'KA0.63', '0.63g', '片', '营养补充剂', 'CKD低蛋白饮食辅助', '高钙血症/妊娠期', datetime.now()),
    (39, '琥珀酸亚铁片', 'FE100', '100mg', '片', '抗贫血药', 'CKD贫血', '血色病/非缺铁性贫血', datetime.now()),
    (40, '重组人促红细胞生成素', 'EPO3000', '3000IU', '支', '抗贫血药(ESA)', 'CKD贫血', '未控制的重度高血压', datetime.now()),
    # 通用
    (41, '苯磺酸氨氯地平片', 'AML5V2', '5mg', '片', '降压药(CCB)', '高血压', '严重低血压', datetime.now()),
    (42, '非洛地平缓释片', 'FEL5', '5mg', '片', '降压药(CCB)', '高血压', '不稳定心绞痛', datetime.now()),
    (43, '复方利血平氨苯蝶啶片', 'COM0', '复方', '片', '复方降压药', '高血压', '抑郁/活动性溃疡', datetime.now()),
    (44, '瑞格列奈片', 'REP1', '1mg', '片', '降糖药(格列奈类)', '2型糖尿病', '1型糖尿病/严重肝病', datetime.now()),
    (45, '利伐沙班片', 'RIV20', '20mg', '片', '抗凝药', '房颤抗凝/DVT防治', '活动性出血', datetime.now()),
    (46, '华法林钠片', 'WAR2.5', '2.5mg', '片', '抗凝药', '血栓栓塞性疾病', '出血倾向/妊娠期', datetime.now()),
    (47, '麝香保心丸', 'SXB22.5', '22.5mg', '丸', '中成药(活血)', '冠心病/心绞痛', '孕妇', datetime.now()),
    (48, '速效救心丸', 'SXJ40', '40mg', '丸', '中成药(行气)', '心绞痛/胸闷', '—', datetime.now()),
    (49, '安脑丸', 'ANW3', '3g', '丸', '中成药(开窍)', '脑卒中/高热神昏', '孕妇', datetime.now()),
    (50, '血府逐瘀胶囊', 'XFZY0.4', '0.4g', '粒', '中成药(活血)', '气滞血瘀证/冠心病', '孕妇/月经过多', datetime.now()),
]

c.executemany(
    'INSERT INTO dim_drug (drug_id, drug_name, drug_code, specification, unit, drug_class, indication, contraindication, created_at) VALUES (?,?,?,?,?,?,?,?,?)',
    DRUGS
)
print(f'  dim_drug: {len(DRUGS)} drugs')

# ========== 2. health_education_record — 宣教推送记录 ==========
CHANNELS = ['WECHAT', 'SMS', 'APP', 'WECHAT', 'WECHAT', 'PRINT', 'APP', 'WECHAT', 'SMS', 'WECHAT']
EDU_TITLES = [
    '高血压日常护理指南', '糖尿病饮食9大法则', '冠心病患者运动建议',
    '脑卒中康复训练要点', '慢阻肺家庭氧疗规范', '慢性肾脏病低蛋白饮食',
    '降压药按时服药提醒', '血糖自我监测指南', '心绞痛急救要点', '秋冬季节慢病防护'
]

patients = [row[0] for row in c.execute('SELECT patient_id FROM patient LIMIT 65').fetchall()]
templates = [f'EDU_TMP_{i:04d}' for i in range(1, 11)]

records = []
for i in range(50):
    p = random.choice(patients)
    h = random.randint(0, len(EDU_TITLES) - 1)
    sent_at = now - timedelta(days=random.randint(1, 90), hours=random.randint(0, 23))
    is_read = random.random() > 0.3
    read_at = (sent_at + timedelta(hours=random.randint(1, 72))) if is_read else None
    feedbacks = ['', '', '有效', '', '实用', '已阅读', '咨询问题', '希望更多推送', '感谢医生']
    records.append((
        f'edu_{i+1:04d}', p, templates[h],
        random.choice(CHANNELS),
        f'doc_{random.randint(1, 10):04d}',
        sent_at.isoformat(),
        int(is_read),
        read_at.isoformat() if read_at else None,
        random.choice(feedbacks) if random.random() > 0.6 else None,
        sent_at.isoformat()
    ))

cols = 'record_id,patient_id,template_id,sent_channel,sent_by,sent_at,is_read,read_at,patient_feedback,created_at'
placeholders = ','.join(['?']*10)
c.executemany(f'INSERT INTO health_education_record ({cols}) VALUES ({placeholders})', records)
print(f'  health_education_record: {len(records)} records')

# ========== 3. prescription_review — 处方审核记录 ==========
REVIEW_RESULTS = ['APPROVED', 'APPROVED', 'APPROVED', 'MODIFIED', 'APPROVED', 'REJECTED', 'APPROVED', 'APPROVED', 'MODIFIED', 'APPROVED']
DRUG_NAMES = ['硝苯地平控释片 30mg qd', '二甲双胍片 500mg tid', '阿司匹林肠溶片 100mg qd', '阿托伐他汀片 20mg qn', '沙美特罗替卡松吸入剂 1吸 bid', '缬沙坦胶囊 80mg qd', '格列美脲片 2mg qd', '氯吡格雷片 75mg qd', '胰岛素注射液 10U tid 餐前', '厄贝沙坦片 150mg qd']
SUGGESTIONS = [
    '', '', '', '氨氯地平片 5mg qd（肾功能轻度异常建议CCB替代ACEI）', '',
    '复查血钾后继续用药（螺内酯联合高钾风险）', '', '', '调整为恩格列净10mg qd（肾功能稳定优先SGLT2i）', ''
]
REASONS = [
    '符合指南推荐', '符合指南推荐', '药师审核通过',
    'CKD患者慎用ACEI改用CCB', '符合指南推荐',
    '联合螺内酯需监测血钾', '与饮食运动方案配合良好',
    'PCI术后双抗方案规范', '肾功能稳定优先SGLT2i降糖', 'ARB达标剂量'
]
REVIEW_TYPES = ['AI_ASSIST', 'MANUAL', 'MANUAL', 'AI_ASSIST', 'PHARMACIST', 'AI_ASSIST', 'MANUAL', 'PHARMACIST', 'AI_ASSIST', 'MANUAL']

reviews = []
for i in range(20):
    p = random.choice(patients)
    ridx = random.randint(0, 9)
    rtype = REVIEW_TYPES[ridx]
    rresult = REVIEW_RESULTS[ridx]
    suggestion = SUGGESTIONS[ridx] if rresult in ('MODIFIED', 'REJECTED') else ''
    reviewed_at = now - timedelta(days=random.randint(1, 120))
    is_applied = rresult != 'REJECTED' and random.random() > 0.2
    applied_at = (reviewed_at + timedelta(days=random.randint(1, 7))) if is_applied else None

    reviews.append((
        f'rev_{i+1:04d}', f'med_{random.randint(1, 50):04d}', p,
        rtype,
        DRUG_NAMES[ridx].split(' ')[0] if rtype == 'PHARMACIST' else DRUG_NAMES[ridx],
        DRUG_NAMES[ridx].split(' ')[1] if ' ' in DRUG_NAMES[ridx] else 'qd',
        DRUG_NAMES[ridx].split(' ')[0] if ' ' in DRUG_NAMES[ridx] else DRUG_NAMES[ridx],
        suggestion.split(' ')[0] if suggestion else None,
        suggestion.split(' ')[1] if ' ' in (suggestion or '') else None,
        suggestion if suggestion else None,
        REASONS[ridx],
        rresult,
        f'doc_{random.randint(1, 10):04d}',
        f'ORG_00{random.randint(1, 5)}',
        f'doc_{random.randint(1, 10):04d}',
        reviewed_at.isoformat(),
        int(is_applied),
        applied_at.isoformat() if applied_at else None,
        f'审核意见：{REASONS[ridx]}',
        reviewed_at.isoformat()
    ))

cols2 = 'review_id,medication_id,patient_id,review_type,original_dosage,original_frequency,original_drug,suggested_dosage,suggested_frequency,suggested_drug,review_reason,review_result,reviewed_by,reviewed_org,prescribed_by,reviewed_at,is_applied,applied_at,notes,created_at'
p2 = ','.join(['?']*20)
c.executemany(f'INSERT INTO prescription_review ({cols2}) VALUES ({p2})', reviews)
print(f'  prescription_review: {len(reviews)} records')

c.commit()
# Verify
for t in ['dim_drug', 'health_education_record', 'prescription_review']:
    cnt = c.execute(f'SELECT count(*) FROM {t}').fetchone()[0]
    print(f'  VERIFY {t}: {cnt} rows')

c.close()
print('\nSEED_OK')