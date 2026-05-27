"""
初始化测试数据 - 陵水县人民医院慢性病管理系统
（兼容当前模型版本）
"""
import sys
import os
from datetime import datetime, date, timedelta
import random
import hashlib

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
        # 检查是否已初始化（只检查 admin 用户是否存在）
        existing_admin = db.query(SysUser).filter(SysUser.username == 'admin').first()
        if existing_admin:
            # 检查是否已有患者数据
            patient_count = db.query(Patient).count()
            if patient_count > 0:
                print(f"测试数据已存在（{patient_count} 个患者），跳过初始化")
                return
            else:
                print("admin 用户存在但无患者数据，继续初始化...")

        # 1. 创建疾病类型字典
        print("创建疾病类型字典...")
        diseases = [
            DimDiseaseType(disease_code='HYPERTENSION', disease_name='原发性高血压', icd10_code='I10', sort_order=1),
            DimDiseaseType(disease_code='DIABETES', disease_name='2型糖尿病', icd10_code='E11', sort_order=2),
            DimDiseaseType(disease_code='CORONARY', disease_name='冠心病', icd10_code='I20', sort_order=3),
            DimDiseaseType(disease_code='STROKE', disease_name='脑卒中', icd10_code='I63', sort_order=4),
            DimDiseaseType(disease_code='COP', disease_name='慢性阻塞性肺疾病', icd10_code='J44', sort_order=5),
            DimDiseaseType(disease_code='CKD', disease_name='慢性肾脏病', icd10_code='N18', sort_order=6),
        ]
        for d in diseases:
            existing = db.query(DimDiseaseType).filter(DimDiseaseType.disease_code == d.disease_code).first()
            if not existing:
                db.add(d)
        db.commit()
        print(f"  ✓ 疾病类型已创建/确认")

        # 2. 创建测试账号（如果不存在）
        print("创建/确认测试账号...")
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
            print(f"  ✓ 测试账号已存在")

        # 3. 创建测试患者（覆盖6类慢病）
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

        patients = []
        for pdata in patients_data:
            # 加密敏感字段
            enc_svc = get_encryption_service()
            id_card_enc = enc_svc.encrypt(pdata['id_card'])
            id_card_hash = hashlib.sha256(pdata['id_card'].encode()).hexdigest()
            name_enc = enc_svc.encrypt(pdata['name'])
            phone_enc = enc_svc.encrypt(pdata['phone'])
            
            birth_date = date.today() - timedelta(days=pdata['age'] * 365)
            village_codes = ['469028001', '469028002', '469028003', '469028004']
            
            patient = Patient(
                patient_id=pdata['id'],
                id_card_enc=id_card_enc,
                id_card_hash=id_card_hash,
                name_enc=name_enc,
                gender=pdata['gender'],
                birth_date=birth_date,
                age=pdata['age'],
                phone_enc=phone_enc,
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

        # 4. 创建随访记录
        print("创建随访记录...")
        followups = []
        followup_types = ['REGULAR', 'EMERGENCY', 'PHONE']
        for p in patients:
            num_fu = random.randint(1, 3)
            for i in range(num_fu):
                fu_date = date.today() - timedelta(days=random.randint(0, 180))
                fu = FollowupRecord(
                    patient_id=p.patient_id,
                    followup_date=fu_date,
                    followup_type=random.choice(followup_types),
                    systolic_pressure=random.randint(120, 170) if 'HYPERTENSION' in p.disease_list else None,
                    diastolic_pressure=random.randint(70, 100) if 'HYPERTENSION' in p.disease_list else None,
                    fasting_glucose=round(random.uniform(5.0, 13.0), 1) if 'DIABETES' in p.disease_list else None,
                    hba1c=round(random.uniform(6.0, 10.0), 1) if 'DIABETES' in p.disease_list else None,
                    symptoms=random.choice([None, '无症状', '头晕', '乏力', '胸闷']),
                    medication_adherence=random.choice(['良好', '一般', '差']),
                    next_followup_date=fu_date + timedelta(days=random.randint(30, 90)),
                    is_completed=True,
                    created_by=2,
                )
                followups.append(fu)
                db.add(fu)
                db.flush()

                # 创建专病随访
                if 'HYPERTENSION' in p.disease_list:
                    hf = FollowupHypertension(
                        followup_id=fu.followup_id,
                        patient_id=p.patient_id,
                        blood_pressure_control=random.choice(['达标', '不达标']),
                        lifestyle_guidance='低盐饮食，适量运动',
                        created_by=2,
                    )
                    db.add(hf)

                if 'DIABETES' in p.disease_list:
                    df = FollowupDiabetes(
                        followup_id=fu.followup_id,
                        patient_id=p.patient_id,
                        glucose_control=random.choice(['达标', '不达标']),
                        diet_guidance='控制碳水摄入，定时定量',
                        created_by=2,
                    )
                    db.add(df)

        db.commit()
        print(f"  ✓ 创建了 {len(followups)} 条随访记录")

        # 5. 创建转诊记录
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
                created_by=2,
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

        # 6. 创建预警记录
        print("创建预警记录...")
        alerts = []
        alert_types = ['血压异常', '血糖异常', '随访逾期', '检验异常', '用药不良反应']
        for i in range(10):
            p = patients[i % len(patients)]
            alert = AlertRecord(
                patient_id=p.patient_id,
                alert_type=alert_types[i % len(alert_types)],
                severity=random.choice(['LOW', 'MEDIUM', 'HIGH']),
                message=f'{p.name_enc}的{"血压" if "血压" in alert_types[i % len(alert_types)] else "健康指标"}需要关注',
                is_handled=random.choice([True, False]),
                handled_by=2 if random.random() > 0.5 else None,
                created_at=datetime.now() - timedelta(days=random.randint(0, 14)),
            )
            alerts.append(alert)
            db.add(alert)

        db.commit()
        print(f"  ✓ 创建了 {len(alerts)} 条预警记录")

        print("\n" + "="*50)
        print("测试数据初始化完成！")
        print("="*50)
        print(f"患者数: {len(patients)}")
        print(f"随访记录: {len(followups)}")
        print(f"转诊记录: {len(referrals)}")
        print(f"预警记录: {len(alerts)}")
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
