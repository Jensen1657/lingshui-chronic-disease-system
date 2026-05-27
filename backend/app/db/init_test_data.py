"""
初始化测试数据 - 陵水县人民医院慢性病管理系统
（兼容当前模型版本 2026-05-27）
"""
import sys
import os
from datetime import datetime, date, timedelta
import random
import hashlib
import logging

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/../..')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.models import (
    Patient, DimDiseaseType, DimDrug, SysUser, PatientWechat,
    FollowupRecord, ReferralRecord, AnnualAssessment, AlertRecord,
    FollowupReminder, PatientSelfReport, TcmRecord, EmergencyAlert,
    DiseaseHypertension, DiseaseDiabetes, DiseaseCoronaryHeartDisease,
    DiseaseStroke, DiseaseCopd, DiseaseCkd,
    FollowupHypertension, FollowupDiabetes,
)
from app.services.encryption_service import get_encryption_service
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def init_test_data():
    """初始化测试数据"""
    db_url = settings.DATABASE_URL
    if db_url.startswith("sqlite+aiosqlite"):
        db_url = db_url.replace("sqlite+aiosqlite://", "sqlite://")
    
    engine = create_engine(db_url)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        # 检查是否已初始化
        existing_admin = db.query(SysUser).filter(SysUser.username == 'admin').first()
        if existing_admin:
            patient_cnt = db.query(Patient).count()
            fu_cnt = db.query(FollowupRecord).count()
            if patient_cnt > 0 and fu_cnt > 0:
                print(f"测试数据已存在（患者={patient_cnt}, 随访={fu_cnt}），跳过")
                return
            else:
                print(f"admin 存在但数据不完整（患者={patient_cnt}, 随访={fu_cnt}），继续初始化...")

        enc_svc = get_encryption_service()

        # 1. 疾病类型字典
        print("创建疾病类型字典...")
        disease_defs = [
            ('HYPERTENSION', '原发性高血压', 'I10', 1),
            ('DIABETES', '2型糖尿病', 'E11', 2),
            ('CORONARY', '冠心病', 'I20', 3),
            ('STROKE', '脑卒中', 'I63', 4),
            ('COPD', '慢性阻塞性肺疾病', 'J44', 5),
            ('CKD', '慢性肾脏病', 'N18', 6),
        ]
        for code, name, icd, order in disease_defs:
            if not db.query(DimDiseaseType).filter(DimDiseaseType.disease_code == code).first():
                db.add(DimDiseaseType(disease_code=code, disease_name=name, icd10_code=icd, sort_order=order))
        db.commit()
        print("  ✓ 疾病类型就绪")

        # 2. 测试账号
        print("创建测试账号...")
        if not existing_admin:
            users = [
                SysUser(username='admin', password_hash='8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918',
                       real_name='系统管理员', role_code='ADMIN', org_code='469028', is_active=True),
                SysUser(username='doctor1', password_hash='8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918',
                       real_name='张医生', role_code='DOCTOR', org_code='469028', is_active=True),
                SysUser(username='doctor2', password_hash='8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918',
                       real_name='李医生', role_code='DOCTOR', org_code='469028', is_active=True),
            ]
            db.add_all(users)
            db.commit()
            print(f"  ✓ 创建了 3 个测试账号")
        else:
            print("  ✓ 测试账号已存在")

        # 3. 测试患者（含加密字段）
        print("创建测试患者...")
        patients_data = [
            {'id': 'p_0001', 'name': '王建国', 'gender': 'M', 'age': 65, 'phone': '13800138001',
             'id_card': '469028195906011234', 'diseases': ['HYPERTENSION'], 'risk': '中危'},
            {'id': 'p_0002', 'name': '李秀英', 'gender': 'F', 'age': 72, 'phone': '13800138002',
             'id_card': '469028194307021234', 'diseases': ['HYPERTENSION'], 'risk': '高危'},
            {'id': 'p_0003', 'name': '陈大明', 'gender': 'M', 'age': 58, 'phone': '13800138003',
             'id_card': '469028196507031234', 'diseases': ['HYPERTENSION'], 'risk': '低危'},
            {'id': 'p_0004', 'name': '赵桂兰', 'gender': 'F', 'age': 61, 'phone': '13800138004',
             'id_card': '469028196407041234', 'diseases': ['DIABETES'], 'risk': '中危'},
            {'id': 'p_0005', 'name': '刘志强', 'gender': 'M', 'age': 55, 'phone': '13800138005',
             'id_card': '469028197008051234', 'diseases': ['DIABETES'], 'risk': '低危'},
            {'id': 'p_0006', 'name': '孙美华', 'gender': 'F', 'age': 68, 'phone': '13800138006',
             'id_card': '469028195802061234', 'diseases': ['HYPERTENSION', 'DIABETES'], 'risk': '高危'},
            {'id': 'p_0007', 'name': '周文龙', 'gender': 'M', 'age': 70, 'phone': '13800138007',
             'id_card': '469028195401071234', 'diseases': ['CORONARY'], 'risk': '高危'},
            {'id': 'p_0008', 'name': '吴丽萍', 'gender': 'F', 'age': 66, 'phone': '13800138008',
             'id_card': '469028195906081234', 'diseases': ['STROKE'], 'risk': '中高危'},
            {'id': 'p_0009', 'name': '郑明亮', 'gender': 'M', 'age': 74, 'phone': '13800138009',
             'id_card': '469028194907091234', 'diseases': ['COPD'], 'risk': '中危'},
            {'id': 'p_0010', 'name': '黄淑珍', 'gender': 'F', 'age': 63, 'phone': '13800138010',
             'id_card': '469028196205101234', 'diseases': ['CKD'], 'risk': '高危'},
        ]

        village_codes = ['469028001', '469028002', '469028003', '469028004']
        patients = []
        for pdata in patients_data:
            id_card_hash = hashlib.sha256(pdata['id_card'].encode()).hexdigest()
            patient = Patient(
                patient_id=pdata['id'],
                id_card_enc=enc_svc.encrypt(pdata['id_card']),
                id_card_hash=id_card_hash,
                name_enc=enc_svc.encrypt(pdata['name']),
                gender=pdata['gender'],
                birth_date=date.today() - timedelta(days=pdata['age'] * 365),
                age=pdata['age'],
                phone_enc=enc_svc.encrypt(pdata['phone']),
                address=f'海南省陵水黎族自治县{["椰林镇","光坡镇","三才镇","英州镇"][len(patients) % 4]}',
                village_code=random.choice(village_codes),
                manage_org_code='469028',
                disease_list=pdata['diseases'],
                risk_level=pdata['risk'],
                is_active=True,
                empi_status='ACTIVE',
            )
            patients.append(patient)
            db.add(patient)

        db.commit()
        print(f"  ✓ 创建了 {len(patients)} 个测试患者")

        # 4. 专病记录
        print("创建专病记录...")
        disease_records = []
        for p in patients:
            if 'HYPERTENSION' in p.disease_list:
                disease_records.append(DiseaseHypertension(
                    patient_id=p.patient_id,
                    diagnosis_date=date.today() - timedelta(days=random.randint(30, 365)),
                    risk_stratification=random.choice(['低危', '中危', '高危']),
                    is_active=True,
                ))
            if 'DIABETES' in p.disease_list:
                disease_records.append(DiseaseDiabetes(
                    patient_id=p.patient_id,
                    diagnosis_date=date.today() - timedelta(days=random.randint(30, 365)),
                    who_1999_type='2型',
                    hba1c_at_diagnosis=round(random.uniform(6.5, 11.0), 1),
                    is_active=True,
                ))
            if 'CORONARY' in p.disease_list:
                disease_records.append(DiseaseCoronaryHeartDisease(
                    patient_id=p.patient_id,
                    diagnosis_date=date.today() - timedelta(days=random.randint(30, 730)),
                    timi_score=random.randint(0, 7),
                    grace_score=random.randint(0, 140),
                    is_active=True,
                ))
            if 'STROKE' in p.disease_list:
                disease_records.append(DiseaseStroke(
                    patient_id=p.patient_id,
                    diagnosis_date=date.today() - timedelta(days=random.randint(30, 365)),
                    is_active=True,
                ))
            if 'COPD' in p.disease_list:
                disease_records.append(DiseaseCopd(
                    patient_id=p.patient_id,
                    diagnosis_date=date.today() - timedelta(days=random.randint(30, 365)),
                    is_active=True,
                ))
            if 'CKD' in p.disease_list:
                disease_records.append(DiseaseCkd(
                    patient_id=p.patient_id,
                    diagnosis_date=date.today() - timedelta(days=random.randint(30, 365)),
                    is_active=True,
                ))
        db.add_all(disease_records)
        db.commit()
        print(f"  ✓ 创建了 {len(disease_records)} 条专病记录")

        # 5. 随访记录（按正确模型字段）
        print("创建随访记录...")
        followups = []
        followup_no_map = {}
        for p in patients:
            num_fu = random.randint(1, 3)
            for i in range(num_fu):
                fu_date = date.today() - timedelta(days=random.randint(0, 180))
                # followup_no 按患者递增
                key = p.patient_id
                followup_no_map[key] = followup_no_map.get(key, 0) + 1
                
                fu = FollowupRecord(
                    patient_id=p.patient_id,
                    disease_code=p.disease_list[0],
                    followup_no=followup_no_map[key],
                    followup_type=random.choice(['REGULAR', 'EMERGENCY', 'PHONE']),
                    followup_date=fu_date,
                    performed_by=2,  # doctor1
                    org_code='469028',
                    bp_systolic=random.randint(120, 170) if 'HYPERTENSION' in p.disease_list else None,
                    bp_diastolic=random.randint(70, 100) if 'HYPERTENSION' in p.disease_list else None,
                    fbg=round(random.uniform(5.0, 13.0), 1) if 'DIABETES' in p.disease_list else None,
                    hba1c=round(random.uniform(6.0, 10.0), 1) if 'DIABETES' in p.disease_list else None,
                    symptoms=random.choice([None, '无症状', '头晕', '乏力', '胸闷']),
                    medication_adherence=random.choice(['良好', '一般', '差']),
                    is_controlled=random.choice([True, False]),
                    next_followup_date=fu_date + timedelta(days=random.randint(30, 90)),
                )
                followups.append(fu)
                db.add(fu)
                db.flush()  # 获取 followup_id

                # 高血压随访扩展
                if 'HYPERTENSION' in p.disease_list:
                    db.add(FollowupHypertension(
                        followup_id=fu.followup_id,
                        bp_grade=random.choice(['正常', '正常高值', '1级', '2级', '3级']),
                        cv_risk_updated=random.choice(['低危', '中危', '高危', None]),
                        is_urgent_alert=random.choice([True, False]),
                    ))

                # 糖尿病随访扩展
                if 'DIABETES' in p.disease_list:
                    db.add(FollowupDiabetes(
                        followup_id=fu.followup_id,
                        hypoglycemia_event=random.choice([True, False]),
                        hypoglycemia_count=random.randint(0, 3),
                        adverse_reaction=random.choice([None, '胃肠道反应', '低血糖']),
                    ))

        db.commit()
        print(f"  ✓ 创建了 {len(followups)} 条随访记录")

        # 6. 转诊记录
        print("创建转诊记录...")
        referrals = []
        for i, p in enumerate(patients[:6]):
            ref = ReferralRecord(
                patient_id=p.patient_id,
                disease_code=p.disease_list[0],
                referral_type='UP' if i % 2 == 0 else 'DOWN',
                apply_org_code='469028',
                apply_doctor=2,
                receive_org_code='469001' if i % 2 == 0 else '469028',
                referral_reason=random.choice(['病情复杂', '需要进一步检查', '康复期随访', '急性加重']),
                status=random.choice(['PENDING', 'ACCEPTED', 'COMPLETED']),
                is_eligible=True,
            )
            if ref.status in ['ACCEPTED', 'COMPLETED']:
                ref.receive_at = datetime.now() - timedelta(days=random.randint(1, 7))
                ref.receive_doctor = 3
            if ref.status == 'COMPLETED':
                ref.completed_at = datetime.now() - timedelta(days=random.randint(0, 3))
            referrals.append(ref)
            db.add(ref)

        db.commit()
        print(f"  ✓ 创建了 {len(referrals)} 条转诊记录")

        # 7. 预警记录
        print("创建预警记录...")
        alerts = []
        alert_types = ['血压异常', '血糖异常', '随访逾期', '检验异常', '用药不良反应']
        for i in range(10):
            p = patients[i % len(patients)]
            alert_handled = random.choice([True, False])
            alerts.append(AlertRecord(
                patient_id=p.patient_id,
                org_code='469028',
                alert_type=alert_types[i % len(alert_types)],
                alert_level=random.choice(['LOW', 'MEDIUM', 'HIGH']),
                alert_title=f'{alert_types[i % len(alert_types)]}预警',
                alert_content=f'{p.name_enc}的健康指标需要关注',
                is_handled=alert_handled,
                handled_by=2 if not alert_handled else None,
                created_at=datetime.now() - timedelta(days=random.randint(0, 14)),
            ))
        db.add_all(alerts)
        db.commit()
        print(f"  ✓ 创建了 {len(alerts)} 条预警记录")

        print("\n" + "="*50)
        print("测试数据初始化完成！")
        print("="*50)
        print(f"患者数: {len(patients)}")
        print(f"随访记录: {len(followups)}")
        print(f"转诊记录: {len(referrals)}")
        print(f"预警记录: {len(alerts)}")
        print(f"专病记录: {len(disease_records)}")
        print("="*50)

    except Exception as e:
        db.rollback()
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == '__main__':
    init_test_data()
