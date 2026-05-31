"""
会议纪要新功能种子数据：用药记录 + 健康宣教模板 + 风险评估
"""
import sys
sys.path.insert(0, "/Users/shayuen/.qclaw/workspace/slow_disease_system/backend")

import asyncio
from app.db.session import _get_factory
from app.models.meeting_models import (
    PatientMedication, HealthEducationTemplate, PatientRiskAssessment
)
from app.models import Patient
from sqlalchemy import select
from datetime import date, datetime, timedelta


MEDICATIONS = [
    {"patient_id": "p_0001", "drug_name": "硝苯地平控释片", "drug_class": "CCB类", "specification": "30mg", "dosage": "30mg", "frequency": "qd", "disease_code": "HYPERTENSION", "start_date": "2025-01-15"},
    {"patient_id": "p_0001", "drug_name": "厄贝沙坦", "drug_class": "ARB类", "specification": "150mg", "dosage": "150mg", "frequency": "qd", "disease_code": "HYPERTENSION", "start_date": "2025-03-01"},
    {"patient_id": "p_0002", "drug_name": "二甲双胍", "drug_class": "双胍类", "specification": "0.5g", "dosage": "0.5g", "frequency": "tid", "disease_code": "DIABETES", "start_date": "2025-02-10"},
    {"patient_id": "p_0002", "drug_name": "格列美脲", "drug_class": "磺脲类", "specification": "2mg", "dosage": "2mg", "frequency": "qd", "disease_code": "DIABETES", "start_date": "2025-05-01"},
    {"patient_id": "p_0003", "drug_name": "阿司匹林", "drug_class": "抗血小板", "specification": "100mg", "dosage": "100mg", "frequency": "qd", "disease_code": "CHD", "start_date": "2025-01-20"},
    {"patient_id": "p_0003", "drug_name": "阿托伐他汀", "drug_class": "他汀类", "specification": "20mg", "dosage": "20mg", "frequency": "qd", "disease_code": "CHD", "start_date": "2025-01-20"},
    {"patient_id": "p_0004", "drug_name": "氯吡格雷", "drug_class": "抗血小板", "specification": "75mg", "dosage": "75mg", "frequency": "qd", "disease_code": "STROKE", "start_date": "2025-06-01"},
    {"patient_id": "p_0005", "drug_name": "沙美特罗替卡松", "drug_class": "吸入剂", "specification": "50μg/250μg", "dosage": "1吸", "frequency": "bid", "disease_code": "COPD", "start_date": "2025-03-15"},
    {"patient_id": "p_0006", "drug_name": "缬沙坦", "drug_class": "ARB类", "specification": "80mg", "dosage": "80mg", "frequency": "qd", "disease_code": "HYPERTENSION", "start_date": "2025-04-10"},
    {"patient_id": "p_0007", "drug_name": "达格列净", "drug_class": "SGLT2i", "specification": "10mg", "dosage": "10mg", "frequency": "qd", "disease_code": "DIABETES", "start_date": "2025-05-20"},
    {"patient_id": "p_0008", "drug_name": "美托洛尔", "drug_class": "β受体阻滞剂", "specification": "25mg", "dosage": "25mg", "frequency": "bid", "disease_code": "HYPERTENSION", "start_date": "2025-06-01"},
    {"patient_id": "p_0009", "drug_name": "阿卡波糖", "drug_class": "α-糖苷酶抑制剂", "specification": "50mg", "dosage": "50mg", "frequency": "tid", "disease_code": "DIABETES", "start_date": "2025-03-20"},
    {"patient_id": "p_0010", "drug_name": "硝酸异山梨酯", "drug_class": "硝酸酯类", "specification": "5mg", "dosage": "5mg", "frequency": "tid", "disease_code": "CHD", "start_date": "2025-02-15"},
    # 标记一些依从性状态
    {"patient_id": "p_0003", "drug_name": "硝酸甘油", "drug_class": "硝酸酯类", "specification": "0.5mg", "dosage": "0.5mg", "frequency": "prn", "disease_code": "CHD", "start_date": "2025-01-20", "adherence_status": "GOOD"},
    {"patient_id": "p_0005", "drug_name": "噻托溴铵", "drug_class": "吸入剂", "specification": "18μg", "dosage": "1吸", "frequency": "qd", "disease_code": "COPD", "start_date": "2025-07-01", "adherence_status": "PARTIAL"},
]

HEALTH_TEMPLATES = [
    {"title": "高血压低盐饮食指南", "category": "DIET", "disease_code": "HYPERTENSION", "risk_level": "MEDIUM", "content_text": "每日盐摄入不超过6克，多吃蔬菜水果，少吃腌制食品。推荐食材：芹菜、菠菜、番茄、燕麦、香蕉。避免：咸菜、腊肉、酱油过量。", "tags": ["饮食", "低盐", "高血压"]},
    {"title": "糖尿病饮食控糖方案", "category": "DIET", "disease_code": "DIABETES", "risk_level": "MEDIUM", "content_text": "控制碳水摄入，主食定量。推荐全谷物、豆类、蔬菜。每日主食≤250g，水果≤200g。避免含糖饮料、糕点。餐后血糖监测。", "tags": ["饮食", "控糖", "糖尿病"]},
    {"title": "冠心病运动康复指导", "category": "EXERCISE", "disease_code": "CHD", "risk_level": "HIGH", "content_text": "适度有氧运动，每周3-5次。推荐：快走、慢跑、太极拳。每次30分钟，心率控制在(220-年龄)×60%~70%。避免剧烈运动和寒冷环境。", "tags": ["运动", "康复", "冠心病"]},
    {"title": "慢阻肺呼吸训练方法", "category": "EXERCISE", "disease_code": "COPD", "risk_level": "HIGH", "content_text": "腹式呼吸：手放腹部，吸气时腹部隆起，呼气时腹部收缩。缩唇呼吸：鼻吸气，口呼气如吹口哨。每日练习2-3次，每次10-15分钟。", "tags": ["呼吸训练", "慢阻肺", "康复"]},
    {"title": "高血压用药依从性教育", "category": "MEDICATION", "disease_code": "HYPERTENSION", "risk_level": "MEDIUM", "content_text": "降压药需长期规律服用，不可自行停药。漏服后如需补服请咨询医生。常见副作用：干咳(普利类)、踝部水肿(地平类)。定期监测血压，记录血压日记。", "tags": ["用药", "依从性", "高血压"]},
    {"title": "糖尿病患者自我监测指南", "category": "MONITORING", "disease_code": "DIABETES", "risk_level": "MEDIUM", "content_text": "空腹血糖目标4.4-7.0mmol/L，餐后2小时<10.0mmol/L。每周至少监测2-3次。糖化血红蛋白每3个月复查一次。记录饮食运动日记。", "tags": ["监测", "血糖", "糖尿病"]},
    {"title": "脑卒中居家康复护理", "category": "LIFESTYLE", "disease_code": "STROKE", "risk_level": "HIGH", "content_text": "患肢功能位摆放，每日关节被动活动。防跌倒、防压疮。吞咽困难者调整食物性状。家属学习基础护理知识，定期随访。", "tags": ["护理", "康复", "脑卒中"]},
    {"title": "慢性肾脏病饮食指导", "category": "DIET", "disease_code": "CKD", "risk_level": "HIGH", "content_text": "优质低蛋白饮食，每日蛋白0.6-0.8g/kg。限盐<5g/天。根据血钾磷水平调整饮食。避免高钾食物如香蕉、土豆、橙子。（晚期）", "tags": ["饮食", "肾脏", "CKD"]},
    {"title": "减盐减油健康生活方式", "category": "LIFESTYLE", "disease_code": None, "risk_level": "LOW", "content_text": "每日食盐<5g，食用油<25g。使用定量盐勺和油壶。多蒸煮少煎炸。戒烟限酒，保持健康体重。每周至少150分钟中等强度运动。", "tags": ["健康生活", "减盐", "预防"]},
    {"title": "慢病管理综合指南(通用)", "category": "GENERAL", "disease_code": None, "risk_level": "LOW", "content_text": "慢病管理三大原则：规律用药、定期随访、健康生活。建立个人健康档案。学会自我监测技能。与家庭医生保持沟通。突发不适及时就诊。", "tags": ["综合", "管理", "通用"]},
]


async def seed():
    async with _get_factory()() as db:
        # === 用药记录 ===
        result = await db.execute(select(PatientMedication).limit(1))
        if result.scalar_one_or_none():
            print("用药记录已存在，跳过")
        else:
            for m in MEDICATIONS:
                obj = PatientMedication(
                    medication_id=f"med_{MEDICATIONS.index(m):04d}",
                    patient_id=m["patient_id"],
                    drug_name=m["drug_name"], drug_class=m["drug_class"],
                    specification=m["specification"], dosage=m["dosage"],
                    frequency=m["frequency"], disease_code=m["disease_code"],
                    start_date=date.fromisoformat(m["start_date"]),
                    is_long_term=True, is_active=True, route="口服",
                    prescribed_org="460123003",
                    adherence_status=m.get("adherence_status", "GOOD"),
                )
                db.add(obj)
            await db.commit()
            print(f"✅ 已创建 {len(MEDICATIONS)} 条用药记录")

        # === 健康宣教模板 ===
        result = await db.execute(select(HealthEducationTemplate).limit(1))
        if result.scalar_one_or_none():
            print("宣教模板已存在，跳过")
        else:
            for t in HEALTH_TEMPLATES:
                obj = HealthEducationTemplate(
                    template_id=f"he_{HEALTH_TEMPLATES.index(t):04d}",
                    title=t["title"], category=t["category"],
                    disease_code=t.get("disease_code"),
                    risk_level=t.get("risk_level"),
                    content_text=t["content_text"], tags=t.get("tags"),
                    usage_count=0, is_active=True,
                )
                db.add(obj)
            await db.commit()
            print(f"✅ 已创建 {len(HEALTH_TEMPLATES)} 条宣教模板")

        # === 风险评估 ===
        result = await db.execute(select(PatientRiskAssessment).limit(1))
        if result.scalar_one_or_none():
            print("风险评估已有数据，跳过")
        else:
            patients = (await db.execute(select(Patient))).scalars().all()
            count = 0
            for p in patients[:50]:  # 前50个患者做评估
                level = p.risk_level or "MEDIUM"
                score_map = {"LOW": 10, "MEDIUM": 25, "HIGH": 45, "CRITICAL": 70}
                manage_map = {"LOW": "VILLAGE", "MEDIUM": "TOWNSHIP", "HIGH": "COUNTY", "CRITICAL": "REFERRAL"}
                obj = PatientRiskAssessment(
                    assessment_id=f"ra_{count:04d}",
                    patient_id=p.patient_id,
                    risk_score=score_map.get(level, 25),
                    risk_level=level,
                    manage_level=manage_map.get(level, "TOWNSHIP"),
                    assigned_org=p.manage_org_code,
                    risk_factors=[("AGE" if getattr(p, 'age', 50) > 65 else "BLOOD_PRESSURE_UNCONTROLLED")] if level != "LOW" else [],
                    assessed_at=datetime.utcnow() - timedelta(days=count % 30),
                    valid_until=date.today() + timedelta(days=90),
                    next_assessment_date=date.today() + timedelta(days=90),
                    followup_frequency="MONTHLY" if level in ("HIGH", "CRITICAL") else "QUARTERLY",
                )
                db.add(obj)
                count += 1
            await db.commit()
            print(f"✅ 已创建 {count} 条风险评估记录")


if __name__ == "__main__":
    asyncio.run(seed())