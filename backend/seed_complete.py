"""
完整种子数据：50 患者 + 105 随访 + 用药记录 + 告警
"""
import sys, os, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import asyncio
from app.db.session import _get_factory
from app.models import Patient, FollowupRecord
from app.models.meeting_models import PatientMedication
from app.models.__init__ import AlertRecord
from app.services.encryption_service import encryption_service
from sqlalchemy import select, func
from datetime import date, datetime, timedelta
import random

random.seed(42)

# 陵水县 460123 机构代码
ORG_HOSPITAL = "460123001"  # 县人民医院
ORG_TOWNSHIP = "460123003"  # 乡镇卫生院
VILLAGE_CODES = ["460123001001", "460123001002", "460123001003", "460123001004",
                 "460123003001", "460123003002", "460123003003"]

# 患者姓名库
NAMES = [
    "王明德","李秀芳","陈建国","张桂英","刘文强","赵玉兰","黄伟雄","周丽华",
    "吴志强","林美珍","郑金水","谢雅文","马建军","何春花","罗永福","梁小芬",
    "潘海龙","谭淑芳","陆志远","邱碧云","苏国栋","赖桂珍","钟耀明","余秋霞",
    "温振华","高晓红","蔡志辉","朱玉琴","叶伟杰","宋月梅","唐明辉","姚丽萍",
    "杜鸿飞","廖桂花","沈志刚","沈美莲","农国庆","范雪婷","钱国栋","卢晓燕",
    "蒋建华","曹秋菊","彭德胜","蓝秀云","傅国强","袁春花","汪永康","姜慧芳",
    "覃志勇","任婉清"
]

GENDERS = ["M","F","M","F","M","F","M","F","M","F","M","F","M","F","M","F",
           "M","F","M","F","M","F","M","F","M","F","M","F","M","F","M","F",
           "M","F","M","F","M","F","M","F","M","F","M","F","M","F","M","F"]

# 疾病配置: (disease_list, comorbid_disease 可选)
# 共50条：HYPERTENSION 20, DIABETES 12, CHD 6, STROKE 5, COPD 4, CKD 3
DISEASE_CONFIGS = [
    (["HYPERTENSION"], ["DIABETES"]), (["HYPERTENSION"], ["DIABETES"]), (["HYPERTENSION"], ["DIABETES"]),
    (["HYPERTENSION"], ["CHD"]), (["HYPERTENSION"], ["CHD"]),
    (["HYPERTENSION"], ["STROKE"]), (["HYPERTENSION"], ["STROKE"]), (["HYPERTENSION"], ["STROKE"]),
    (["HYPERTENSION"], []), (["HYPERTENSION"], []), (["HYPERTENSION"], []),
    (["HYPERTENSION"], []), (["HYPERTENSION"], []), (["HYPERTENSION"], []),
    (["HYPERTENSION"], []), (["HYPERTENSION"], []), (["HYPERTENSION"], []),
    (["HYPERTENSION"], []), (["HYPERTENSION"], []), (["HYPERTENSION"], []),
    # DIABETES (12)
    (["DIABETES"], ["HYPERTENSION"]), (["DIABETES"], ["HYPERTENSION"]), (["DIABETES"], ["HYPERTENSION"]),
    (["DIABETES"], ["CKD"]), (["DIABETES"], ["CKD"]),
    (["DIABETES"], []), (["DIABETES"], []), (["DIABETES"], []),
    (["DIABETES"], []), (["DIABETES"], []), (["DIABETES"], []), (["DIABETES"], []),
    # CHD (6)
    (["CHD"], ["HYPERTENSION"]), (["CHD"], ["HYPERTENSION"]), (["CHD"], ["HYPERTENSION"]),
    (["CHD"], []), (["CHD"], []), (["CHD"], []),
    # STROKE (5)
    (["STROKE"], ["HYPERTENSION"]), (["STROKE"], ["HYPERTENSION"]), (["STROKE"], ["HYPERTENSION"]),
    (["STROKE"], []), (["STROKE"], []),
    # COPD (4)
    (["COPD"], []), (["COPD"], []), (["COPD"], []), (["COPD"], []),
    # CKD (3)
    (["CKD"], ["HYPERTENSION"]), (["CKD"], ["HYPERTENSION"]), (["CKD"], []),
]

# 风险等级分布: LOW 15%, MEDIUM 40%, HIGH 30%, CRITICAL 15%
RISK_LEVELS = (["LOW"]*7 + ["MEDIUM"]*20 + ["HIGH"]*15 + ["CRITICAL"]*8)

# 血压血糖参考值
BP_VALUES = {
    "LOW": (125, 82), "MEDIUM": (142, 88), "HIGH": (158, 95), "CRITICAL": (175, 102)
}
BG_VALUES = {
    "LOW": (5.6, 7.2), "MEDIUM": (7.8, 9.5), "HIGH": (10.5, 13.0), "CRITICAL": (14.5, 16.8)
}

# 高血压药物
HTN_DRUGS = [
    ("硝苯地平控释片", "CCB类", "30mg", "30mg qd"),
    ("氨氯地平", "CCB类", "5mg", "5mg qd"),
    ("厄贝沙坦", "ARB类", "150mg", "150mg qd"),
    ("缬沙坦", "ARB类", "80mg", "80mg qd"),
    ("依那普利", "ACEI类", "10mg", "10mg bid"),
    ("美托洛尔", "β受体阻滞剂", "25mg", "25mg bid"),
    ("氢氯噻嗪", "利尿剂", "12.5mg", "12.5mg qd"),
    ("培哚普利", "ACEI类", "4mg", "4mg qd"),
]

DIABETES_DRUGS = [
    ("二甲双胍", "双胍类", "0.5g", "0.5g tid"),
    ("格列美脲", "磺脲类", "2mg", "2mg qd"),
    ("阿卡波糖", "α-糖苷酶抑制剂", "50mg", "50mg tid"),
    ("达格列净", "SGLT2i", "10mg", "10mg qd"),
    ("西格列汀", "DPP-4i", "100mg", "100mg qd"),
    ("胰岛素", "胰岛素类", "预混30R", "早12u晚8u"),
]


async def seed():
    enc = encryption_service
    async with _get_factory()() as db:
        # === 1. 创建患者 ===
        existing = (await db.execute(select(func.count(Patient.patient_id)))).scalar()
        if existing > 10:
            print(f"已有 {existing} 名患者，仅添加缺失数据")
            need_patients = list(range(existing, 50))
        elif existing == 0:
            need_patients = list(range(50))
        else:
            need_patients = list(range(50))

        new_patients = 0
        for i in need_patients:
            pid = f"p_{i+1:04d}"
            name = NAMES[i % len(NAMES)]
            gender = GENDERS[i % len(GENDERS)]
            birth_year = random.randint(1940, 1990)
            birth_month = random.randint(1, 12)
            birth_day = random.randint(1, 28)
            bd = date(birth_year, birth_month, birth_day)
            age = 2026 - birth_year
            phone = f"138{random.randint(10000000,99999999)}"
            id_card = f"460123{birth_year}{birth_month:02d}{birth_day:02d}{random.randint(1000,9999)}"
            id_hash = hashlib.sha256(id_card.encode()).hexdigest()

            dc = DISEASE_CONFIGS[i % len(DISEASE_CONFIGS)]
            if isinstance(dc, tuple):
                disease_list = [d for d in dc[0] if isinstance(d, str)]
            else:
                disease_list = ["HYPERTENSION"]

            risk_idx = i % len(RISK_LEVELS)
            risk = RISK_LEVELS[risk_idx]

            village = VILLAGE_CODES[i % len(VILLAGE_CODES)]
            manage_org = ORG_TOWNSHIP if i % 3 == 0 else ORG_HOSPITAL

            # 检查是否已存在
            check = (await db.execute(select(Patient).where(Patient.patient_id == pid))).scalar_one_or_none()
            if check:
                continue

            p = Patient(
                patient_id=pid,
                id_card_enc=enc.encrypt(id_card),
                id_card_hash=id_hash,
                name_enc=enc.encrypt(name),
                gender=gender,
                birth_date=bd,
                age=age,
                phone_enc=enc.encrypt(phone),
                address=f"陵水县{'椰林镇' if i%2==0 else '光坡镇'}行政村{i%7+1}组{i%10+10}号",
                village_code=village,
                manage_org_code=manage_org,
                disease_list=disease_list,
                risk_level=risk,
                is_active=True,
                empi_status='ACTIVE',
            )
            db.add(p)
            new_patients += 1

        await db.commit()
        print(f"✅ 新增 {new_patients} 名患者")

        # === 2. 创建随访记录 ===
        existing_fu = (await db.execute(select(func.count(FollowupRecord.followup_id)))).scalar()
        if existing_fu > 20:
            print(f"随访记录已有 {existing_fu} 条，跳过")
        else:
            patients = (await db.execute(select(Patient))).scalars().all()
            fu_count = 0
            for p in patients:
                diseases = p.disease_list
                if isinstance(diseases, str):
                    try:
                        import json
                        diseases = json.loads(diseases)
                    except:
                        diseases = [diseases]
                if not diseases:
                    diseases = ["HYPERTENSION"]
                for d in diseases[:2]:  # 每种疾病最多2条随访
                    for fi in range(random.randint(1, 3)):
                        days_ago = random.randint(5, 150)
                        f_date = date.today() - timedelta(days=days_ago)
                        bp = BP_VALUES.get(p.risk_level or "MEDIUM", (145, 90))
                        bg = BG_VALUES.get(p.risk_level or "MEDIUM", (8.0, 10.0))
                        obj = FollowupRecord(
                            followup_id=f"fu_{fu_count:04d}",
                            patient_id=p.patient_id,
                            disease_code=d,
                            followup_no=fi+1,
                            followup_type="REGULAR",
                            followup_date=f_date,
                            systolic_bp=bp[0] + random.randint(-10, 10),
                            diastolic_bp=bp[1] + random.randint(-5, 5),
                            fasting_glucose=round(bg[0] + random.uniform(-2, 3), 1) if d == "DIABETES" else None,
                            postprandial_glucose=round(bg[1] + random.uniform(-3, 4), 1) if d == "DIABETES" else None,
                            medication_compliance=random.choice(["GOOD", "PARTIAL", "GOOD"]),
                            adverse_reactions=random.choice(["无", None, None]),
                            assessment=f"病情稳定，继续{sorted(diseases)[0]}常规管理",
                            followup_plan="按计划随访",
                            followup_doctor_id="u_0001",
                            org_code=p.manage_org_code,
                            created_at=datetime.utcnow() - timedelta(days=days_ago),
                        )
                        db.add(obj)
                        fu_count += 1
            await db.commit()
            print(f"✅ 新增 {fu_count} 条随访记录")

        # === 3. 告警记录 ===
        existing_alert = (await db.execute(select(func.count(AlertRecord.alert_id)))).scalar()
        if existing_alert < 5:
            patients = (await db.execute(select(Patient))).scalars().all()
            alert_count = 0
            alert_types = ["BLOOD_PRESSURE", "BLOOD_PRESSURE", "BLOOD_GLUCOSE", "FOLLOWUP_OVERDUE", "DRUG_INTERACTION", "LAB_ABNORMAL"]
            levels = ["CRITICAL", "HIGH", "HIGH", "MEDIUM", "HIGH", "MEDIUM"]
            for p in patients:
                if p.risk_level in ("HIGH", "CRITICAL"):
                    a = AlertRecord(
                        alert_id=f"al_{alert_count:04d}",
                        patient_id=p.patient_id,
                        alert_type=alert_types[alert_count % len(alert_types)],
                        alert_level=levels[alert_count % len(levels)],
                        alert_title=f"患者{alert_count+1}预警",
                        alert_content=f"{'高血压未控制' if alert_types[alert_count%6]=='BLOOD_PRESSURE' else '随访逾期'}预警，请及时处理",
                        alert_source="AUTO",
                        is_resolved=False,
                        resolved_at=None,
                        created_at=datetime.utcnow() - timedelta(days=random.randint(0, 3)),
                    )
                    db.add(a)
                    alert_count += 1
            await db.commit()
            print(f"✅ 新增 {alert_count} 条告警")

        # === 4. 用药记录（前15名患者） ===
        existing_med = (await db.execute(select(func.count(PatientMedication.medication_id)))).scalar()
        if existing_med < 5:
            patients = (await db.execute(select(Patient))).scalars().all()
            med_count = 0
            for p in patients[:15]:
                diseases = p.disease_list
                if isinstance(diseases, str):
                    try:
                        import json
                        diseases = json.loads(diseases)
                    except:
                        diseases = [diseases]
                for d in diseases:
                    drug_pool = HTN_DRUGS if d == "HYPERTENSION" else DIABETES_DRUGS
                    num_meds = random.randint(1, min(2, len(drug_pool)))
                    chosen = random.sample(drug_pool, num_meds)
                    for drug in chosen:
                        m = PatientMedication(
                            medication_id=f"med_{med_count:04d}",
                            patient_id=p.patient_id,
                            drug_name=drug[0],
                            drug_class=drug[1],
                            specification=drug[2],
                            dosage=drug[2],
                            frequency=drug[3].split(" ")[-1] if " " in drug[3] else drug[3],
                            disease_code=d,
                            start_date=date(2025, random.randint(1, 6), random.randint(1, 28)),
                            is_long_term=True,
                            is_active=True,
                            route="口服",
                            prescribed_org=p.manage_org_code,
                            adherence_status=random.choice(["GOOD", "GOOD", "PARTIAL"]),
                        )
                        db.add(m)
                        med_count += 1
            await db.commit()
            print(f"✅ 新增 {med_count} 条用药记录")

        # 统计
        total_p = (await db.execute(select(func.count(Patient.patient_id)))).scalar()
        total_f = (await db.execute(select(func.count(FollowupRecord.followup_id)))).scalar()
        print(f"\n📊 汇总: {total_p} 患者, {total_f} 随访")


if __name__ == "__main__":
    asyncio.run(seed())