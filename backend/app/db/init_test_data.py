"""
初始化测试数据 - 陵水县人民医院慢性病管理系统
创建符合县域慢病管理规范的测试数据
"""
import sys
import os
from datetime import datetime, date, timedelta
import random

# 添加项目路径
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



def init_test_data():
    """初始化测试数据"""
    engine = create_engine(settings.DATABASE_URL.replace('sqlite+aiosqlite://', 'sqlite://'))
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:

        # 检查是否已初始化
        if db.query(SysUser).filter(SysUser.username == 'admin').first():
            print("测试数据已存在，跳过初始化")
            return

        # 1. 创建测试账号
        print("创建测试账号...")
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
        print(f"  ✓ 创建了 {len(users)} 个测试账号")

        # 2. 创建疾病类型字典
        print("创建疾病类型字典...")
        diseases = [
            DimDiseaseType(disease_code='I10', disease_name='原发性高血压', category='慢性病',
                       icd_code='I10', is_high_risk=True, requires_followup=True, followup_interval_days=90),
            DimDiseaseType(disease_code='E11', disease_name='2型糖尿病', category='慢性病',
                       icd_code='E11', is_high_risk=True, requires_followup=True, followup_interval_days=90),
            DimDiseaseType(disease_code='I20', disease_name='冠心病', category='慢性病',
                       icd_code='I20', is_high_risk=True, requires_followup=True, followup_interval_days=180),
            DimDiseaseType(disease_code='I63', disease_name='脑卒中', category='慢性病',
                       icd_code='I63', is_high_risk=True, requires_followup=True, followup_interval_days=180),
            DimDiseaseType(disease_code='J44', disease_name='慢性阻塞性肺疾病', category='慢性病',
                       icd_code='J44', is_high_risk=True, requires_followup=True, followup_interval_days=180),
            DimDiseaseType(disease_code='N18', disease_name='慢性肾脏病', category='慢性病',
                       icd_code='N18', is_high_risk=True, requires_followup=True, followup_interval_days=180),
        ]
        db.add_all(diseases)
        db.commit()
        print(f"  ✓ 创建了 {len(diseases)} 种疾病类型")

        # 3. 创建药品字典（常用降压药、降糖药等）
        print("创建药品字典...")
        drugs = [
            DimDrug(drug_code='C01', drug_name='苯磺酸氨氯地平片', category='降压药',
                     common_dosage='5mg qd', frequency='每日一次'),
            DimDrug(drug_code='C02', drug_name='缬沙坦胶囊', category='降压药',
                     common_dosage='80mg qd', frequency='每日一次'),
            DimDrug(drug_code='C03', drug_name='酒石酸美托洛尔片', category='降压药',
                     common_dosage='25mg bid', frequency='每日两次'),
            DimDrug(drug_code='D01', drug_name='盐酸二甲双胍片', category='降糖药',
                     common_dosage='500mg bid', frequency='每日两次'),
            DimDrug(drug_code='D02', drug_name='格列美脲片', category='降糖药',
                     common_dosage='2mg qd', frequency='每日一次'),
            DimDrug(drug_code='D03', drug_name='阿卡波糖片', category='降糖药',
                     common_dosage='50mg tid', frequency='每日三次'),
        ]
        db.add_all(drugs)
        db.commit()
        print(f"  ✓ 创建了 {len(drugs)} 种药品")

        # 4. 创建测试患者（覆盖6类慢病）
        print("创建测试患者...")
        patients_data = [
            # 高血压
            {'id': 'P001', 'name': '王建国', 'gender': '男', 'age': 65, 'phone': '13800138001',
             'id_card': '469028195906011234', 'disease': 'I10', 'risk': '中危'},
            {'id': 'P002', 'name': '李秀英', 'gender': '女', 'age': 72, 'phone': '13800138002',
             'id_card': '469028194307021234', 'disease': 'I10', 'risk': '高危'},
            {'id': 'P003', 'name': '陈大明', 'gender': '男', 'age': 58, 'phone': '13800138003',
             'id_card': '469028196507031234', 'disease': 'I10', 'risk': '低危'},
            # 糖尿病
            {'id': 'P004', 'name': '赵桂兰', 'gender': '女', 'age': 61, 'phone': '13800138004',
             'id_card': '469028196407041234', 'disease': 'E11', 'risk': '中危'},
            {'id': 'P005', 'name': '刘志强', 'gender': '男', 'age': 55, 'phone': '13800138005',
             'id_card': '469028197008051234', 'disease': 'E11', 'risk': '低危'},
            # 高血压+糖尿病（共病）
            {'id': 'P006', 'name': '孙美华', 'gender': '女', 'age': 68, 'phone': '13800138006',
             'id_card': '469028195802061234', 'disease': 'I10,E11', 'risk': '高危'},
            # 冠心病
            {'id': 'P007', 'name': '周文龙', 'gender': '男', 'age': 70, 'phone': '13800138007',
             'id_card': '469028195401071234', 'disease': 'I20', 'risk': '高危'},
            # 脑卒中
            {'id': 'P008', 'name': '吴丽萍', 'gender': '女', 'age': 66, 'phone': '13800138008',
             'id_card': '469028195906081234', 'disease': 'I63', 'risk': '中高危'},
            # 慢阻肺
            {'id': 'P009', 'name': '郑明亮', 'gender': '男', 'age': 74, 'phone': '13800138009',
             'id_card': '469028194907091234', 'disease': 'J44', 'risk': '中危'},
            # 慢性肾脏病
            {'id': 'P010', 'name': '黄淑珍', 'gender': '女', 'age': 63, 'phone': '13800138010',
             'id_card': '469028196205101234', 'disease': 'N18', 'risk': '高危'},
            # 更多患者（用于统计）
            {'id': 'P011', 'name': '林阿公', 'gender': '男', 'age': 80, 'phone': '13800138011',
             'id_card': '469028194401111234', 'disease': 'I10', 'risk': '高危'},
            {'id': 'P012', 'name': '符阿婆', 'gender': '女', 'age': 76, 'phone': '13800138012',
             'id_card': '469028194807121234', 'disease': 'I10,E11', 'risk': '高危'},
            {'id': 'P013', 'name': '王小燕', 'gender': '女', 'age': 52, 'phone': '13800138013',
             'id_card': '469028197402131234', 'disease': 'E11', 'risk': '低危'},
            {'id': 'P014', 'name': '陈阿伯', 'gender': '男', 'age': 78, 'phone': '13800138014',
             'id_card': '469028194603141234', 'disease': 'I20,I10', 'risk': '高危'},
            {'id': 'P015', 'name': '李小东', 'gender': '男', 'age': 45, 'phone': '13800138015',
             'id_card': '469028198005151234', 'disease': 'I10', 'risk': '低危'},
        ]

        patients = []
        for pdata in patients_data:
            diseases = pdata['disease'].split(',')
            patient = Patient(
                patient_id=pdata['id'],
                name=pdata['name'],
                gender=pdata['gender'],
                birth_date=date.today() - timedelta(days=pdata['age']*365),
                phone=pdata['phone'],
                id_card=pdata['id_card'],
                address=f'海南省陵水黎族自治县{["椰林镇","光坡镇","三才镇","英州镇"][len(patients) % 4]}',
                disease_codes=','.join(diseases),
                risk_level=pdata['risk'],
                status='ACTIVE',
                org_code='469028',
                created_by=2,  # doctor1
            )
            patients.append(patient)
            db.add(patient)

        db.commit()
        print(f"  ✓ 创建了 {len(patients)} 个测试患者")

        # 5. 创建专病记录
        print("创建专病记录...")
        disease_records = []

        # 高血压记录
        for p in patients:
            if 'I10' in p.disease_codes:
                hr = DiseaseHypertension(
                    patient_id=p.patient_id,
                    diagnosis_date=date.today() - timedelta(days=random.randint(30, 365)),
                    systolic_pressure=random.randint(130, 180),
                    diastolic_pressure=random.randint(80, 110),
                    heart_rate=random.randint(60, 100),
                    risk_stratification=random.choice(['低危', '中危', '高危']),
                    target_organ_damage=False,
                    created_by=2,
                )
                disease_records.append(hr)

            if 'E11' in p.disease_codes:
                dr = DiseaseDiabetes(
                    patient_id=p.patient_id,
                    diagnosis_date=date.today() - timedelta(days=random.randint(30, 365)),
                    fasting_glucose=round(random.uniform(6.5, 15.0), 1),
                    hba1c=round(random.uniform(6.5, 11.0), 1),
                    diabetes_type='2型',
                    complications=random.choice([None, '糖尿病肾病', '糖尿病视网膜病变']),
                    created_by=2,
                )
                disease_records.append(dr)

            if 'I20' in p.disease_codes:
                cr = DiseaseCoronaryHeartDisease(
                    patient_id=p.patient_id,
                    diagnosis_date=date.today() - timedelta(days=random.randint(30, 730)),
                    grace_score=random.randint(0, 140),
                    timi_score=random.randint(0, 7),
                    has_pci=random.choice([True, False]),
                    has_cabg=random.choice([True, False]),
                    created_by=2,
                )
                disease_records.append(cr)

            if 'I63' in p.disease_codes:
                sr = DiseaseStroke(
                    patient_id=p.patient_id,
                    diagnosis_date=date.today() - timedelta(days=random.randint(30, 365)),
                    nihss_score=random.randint(0, 15),
                    mrs_score=random.randint(0, 5),
                    stroke_type=random.choice(['缺血性', '出血性']),
                    affected_side=random.choice(['左侧', '右侧', '双侧']),
                    created_by=2,
                )
                disease_records.append(sr)

            if 'J44' in p.disease_codes:
                copr = DiseaseCopd(
                    patient_id=p.patient_id,
                    diagnosis_date=date.today() - timedelta(days=random.randint(30, 365)),
                    gold_stage=random.choice(['I', 'II', 'III', 'IV']),
                    cat_score=random.randint(0, 30),
                    fev1_percent=round(random.uniform(30, 80), 1),
                    created_by=2,
                )
                disease_records.append(copr)

            if 'N18' in p.disease_codes:
                ckr = DiseaseCkd(
                    patient_id=p.patient_id,
                    diagnosis_date=date.today() - timedelta(days=random.randint(30, 365)),
                    egfr=round(random.uniform(15, 90), 1),
                    kdigo_stage=random.choice(['G1', 'G2', 'G3a', 'G3b', 'G4', 'G5']),
                    uacr=round(random.uniform(30, 300), 1),
                    created_by=2,
                )
                disease_records.append(ckr)

        db.add_all(disease_records)
        db.commit()
        print(f"  ✓ 创建了 {len(disease_records)} 条专病记录")

        # 6. 创建随访记录
        print("创建随访记录...")
        followups = []
        followup_types = ['REGULAR', 'EMERGENCY', 'PHONE']
        for p in patients:
            num_followups = random.randint(1, 4)
            for i in range(num_followups):
                fu_date = date.today() - timedelta(days=random.randint(0, 180))
                fu = FollowupRecord(
                    patient_id=p.patient_id,
                    followup_date=fu_date,
                    followup_type=random.choice(followup_types),
                    systolic_pressure=random.randint(120, 170) if 'I10' in p.disease_codes else None,
                    diastolic_pressure=random.randint(70, 100) if 'I10' in p.disease_codes else None,
                    fasting_glucose=round(random.uniform(5.0, 13.0), 1) if 'E11' in p.disease_codes else None,
                    hba1c=round(random.uniform(6.0, 10.0), 1) if 'E11' in p.disease_codes else None,
                    symptoms=random.choice([None, '无症状', '头晕', '乏力', '胸闷']),
                    medication_adherence=random.choice(['良好', '一般', '差']),
                    next_followup_date=fu_date + timedelta(days=random.randint(30, 90)),
                    is_completed=True,
                    created_by=random.choice([2, 3]),
                )
                followups.append(fu)
                db.add(fu)
                db.flush()  # 获取 ID

                # 创建专病随访
                if 'I10' in p.disease_codes:
                    hf = FollowupHypertension(
                        followup_id=fu.followup_id,
                        patient_id=p.patient_id,
                        blood_pressure_control=random.choice(['达标', '不达标']),
                        lifestyle_guidance='低盐饮食，适量运动',
                        created_by=2,
                    )
                    db.add(hf)

                if 'E11' in p.disease_codes:
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

        # 7. 创建转诊记录
        print("创建转诊记录...")
        referrals = []
        for i in range(6):
            p = patients[i % len(patients)]
            ref = ReferralRecord(
                patient_id=p.patient_id,
                disease_code=p.disease_codes.split(',')[0],
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
                ref.post_referral_fu_id = followups[i].followup_id if i < len(followups) else None
            referrals.append(ref)

        db.add_all(referrals)
        db.commit()
        print(f"  ✓ 创建了 {len(referrals)} 条转诊记录")

        # 8. 创建年度评估
        print("创建年度评估...")
        assessments = []
        for p in patients[:8]:
            ass = AnnualAssessment(
                patient_id=p.patient_id,
                assessment_year=date.today().year,
                assessment_date=date.today() - timedelta(days=random.randint(0, 60)),
                bmi=round(random.uniform(18.5, 32.0), 1),
                blood_pressure_controlled=random.choice([True, False]),
                glucose_controlled=random.choice([True, False]) if 'E11' in p.disease_codes else None,
                complication_screening_done=True,
                lifestyle_intervention_done=True,
                medication_review_done=True,
                risk_level=random.choice(['低危', '中危', '高危']),
                next_year_plan='继续规范化管理，3个月随访一次',
                created_by=2,
            )
            assessments.append(ass)

        db.add_all(assessments)
        db.commit()
        print(f"  ✓ 创建了 {len(assessments)} 条年度评估")

        # 9. 创建预警记录
        print("创建预警记录...")
        alerts = []
        alert_types = ['血压异常', '血糖异常', '随访逾期', '检验异常', '用药不良反应']
        for i in range(10):
            p = patients[i % len(patients)]
            alert = AlertRecord(
                patient_id=p.patient_id,
                alert_type=alert_types[i % len(alert_types)],
                severity=random.choice(['LOW', 'MEDIUM', 'HIGH']),
                message=f'{p.name}的{"血压" if "血压" in alert_types[i % len(alert_types)] else "健康指标"}需要关注',
                is_handled=random.choice([True, False]),
                handled_by=2 if random.random() > 0.5 else None,
                created_at=datetime.now() - timedelta(days=random.randint(0, 14)),
            )
            alerts.append(alert)

        db.add_all(alerts)
        db.commit()
        print(f"  ✓ 创建了 {len(alerts)} 条预警记录")

        # 10. 创建随访提醒
        print("创建随访提醒...")
        reminders = []
        for p in patients[:10]:
            rem = FollowupReminder(
                patient_id=p.patient_id,
                due_date=date.today() + timedelta(days=random.randint(-7, 30)),
                is_sent=random.choice([True, False]),
                reminder_type='短信',
                created_by=2,
            )
            reminders.append(rem)

        db.add_all(reminders)
        db.commit()
        print(f"  ✓ 创建了 {len(reminders)} 条随访提醒")

        # 11. 创建中医管理记录
        print("创建中医管理记录...")
        tcm_records = []
        for p in patients[:6]:
            tcm = TcmRecord(
                patient_id=p.patient_id,
                assessment_date=date.today() - timedelta(days=random.randint(0, 90)),
                constitution_type=random.choice(['平和质', '气虚质', '阳虚质', '阴虚质', '痰湿质', '湿热质', '血瘀质', '气郁质']),
                tcm_syndrome=random.choice(['肝阳上亢', '痰湿中阻', '气血亏虚', '肾精不足']),
                intervention_plan='穴位按摩：太冲、风池、百会',
                created_by=2,
            )
            tcm_records.append(tcm)

        db.add_all(tcm_records)
        db.commit()
        print(f"  ✓ 创建了 {len(tcm_records)} 条中医管理记录")

        # 12. 创建急救联动记录
        print("创建急救联动记录...")
        emergencies = []
        for i in range(3):
            p = patients[2*i]
            emr = EmergencyAlert(
                patient_id=p.patient_id,
                event_time=datetime.now() - timedelta(days=random.randint(1, 30)),
                scene_address=f'陵水县人民医院{random.choice(["急诊科","心内科","神经内科"])}',
                consciousness=random.choice(['清醒', '嗜睡', '昏迷']),
                blood_pressure=f'{random.randint(90,180)}/{random.randint(60,110)}',
                heart_rate=random.randint(60, 120),
                is_activated=True,
                activated_at=datetime.now() - timedelta(days=random.randint(0, 30)),
                created_by=2,
            )
            emergencies.append(emr)

        db.add_all(emergencies)
        db.commit()
        print(f"  ✓ 创建了 {len(emergencies)} 条急救联动记录")

        # 13. 创建自报记录
        print("创建自报记录...")
        self_reports = []
        for i in range(5):
            p = patients[i]
            sr = PatientSelfReport(
                patient_id=p.patient_id,
                report_date=date.today() - timedelta(days=random.randint(0, 14)),
                report_type=random.choice(['症状', '体征', '用药']),
                description=f'患者自报：{"头晕不适" if i % 2 == 0 else "血糖偏高"}',
                is_reviewed=random.choice([True, False]),
                reviewed_by=2 if random.random() > 0.5 else None,
                created_by=p.patient_id,
            )
            self_reports.append(sr)

        db.add_all(self_reports)
        db.commit()
        print(f"  ✓ 创建了 {len(self_reports)} 条自报记录")

        # 14. 创建微信绑定记录
        print("创建微信绑定记录...")
        wechat_records = []
        for p in patients[:8]:
            wr = PatientWechat(
                patient_id=p.patient_id,
                openid=f'oxxxxxx{p.patient_id}',
                nickname=p.name,
                is_active=True,
                binded_at=datetime.now() - timedelta(days=random.randint(1, 60)),
            )
            wechat_records.append(wr)

        db.add_all(wechat_records)
        db.commit()
        print(f"  ✓ 创建了 {len(wechat_records)} 条微信绑定记录")

        print("\n" + "="*50)
        print("测试数据初始化完成！")
        print("="*50)
        print(f"患者数: {len(patients)}")
        print(f"随访记录: {len(followups)}")
        print(f"转诊记录: {len(referrals)}")
        print(f"年度评估: {len(assessments)}")
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
