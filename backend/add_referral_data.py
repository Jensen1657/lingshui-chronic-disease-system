#!/usr/bin/env python3
"""
补充转诊记录测试数据
陵水县人民医院慢病管理系统
"""
import sys
import os
from datetime import datetime, timedelta
import random

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + '/..')

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config import settings
from app.models import ReferralRecord

def add_referral_data():
    """补充转诊记录"""
    engine = create_engine(settings.DATABASE_URL.replace('sqlite+aiosqlite://', 'sqlite://'))
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        # 检查已有转诊记录
        existing = db.query(ReferralRecord).count()
        print(f"已有转诊记录: {existing} 条")
        
        # 患者ID列表（从已有患者中选）
        patient_ids = [f'p_{str(i).zfill(4)}' for i in range(1, 51)]
        
        # 医务人员ID
        doctor_ids = ['u_admin', 'u_doc1', 'u_doc2']
        
        # 医疗机构代码
        county_org = '46012301'  # 陵水县人民医院
        township_orgs = ['46012305', '46012306', '46012307', '46012308']  # 乡镇卫生院
        
        # 转诊原因
        referral_reasons = [
            '病情控制不稳定，需调整治疗方案',
            '出现并发症，需上级医院诊治',
            '需要特殊检查或治疗',
            '病情稳定，转回社区随访管理',
            '术后恢复期，转回社区随访',
            '患者家属要求转回当地管理',
        ]
        
        # 创建15条新转诊记录
        new_referrals = []
        base_id = existing + 1
        
        for i in range(15):
            is_up = random.choice([True, False])
            patient_id = random.choice(patient_ids)
            apply_org = random.choice(township_orgs) if is_up else county_org
            receive_org = county_org if is_up else random.choice(township_orgs)
            apply_doctor = random.choice(doctor_ids)
            receive_doctor = random.choice(doctor_ids) if i % 3 != 0 else None
            
            days_ago = random.randint(1, 60)
            apply_time = datetime.now() - timedelta(days=days_ago)
            receive_days = random.randint(0, 3) if receive_doctor else 0
            receive_time = apply_time + timedelta(days=receive_days) if receive_doctor else None
            
            status = random.choice(['COMPLETED', 'COMPLETED', 'COMPLETED', 'PENDING', 'CANCELLED'])
            
            referral = ReferralRecord(
                referral_id=f'ref_{str(base_id + i).zfill(3)}',
                patient_id=patient_id,
                disease_code=random.choice(['I10', 'E11', 'I20', 'I63', 'J44', 'N18']),
                referral_type='UP' if is_up else 'DOWN',
                apply_org_code=apply_org,
                apply_doctor=apply_doctor,
                apply_at=apply_time,
                referral_reason=random.choice(referral_reasons),
                match_criteria='符合转诊标准' if random.random() > 0.2 else '病情需要',
                is_eligible=1 if random.random() > 0.2 else 0,
                reject_reason=None if random.random() > 0.2 else '不符合转诊条件',
                down_plan=None if is_up else '继续当前方案治疗，1月后随访',
                receive_org_code=receive_org if status == 'COMPLETED' else None,
                receive_doctor=receive_doctor if status == 'COMPLETED' else None,
                receive_at=receive_time if status == 'COMPLETED' else None,
                status=status,
                timeout_alert_sent=1 if days_ago > 3 and status == 'PENDING' else 0,
                completed_at=apply_time + timedelta(days=random.randint(3, 14)) if status == 'COMPLETED' else None,
                post_referral_fu_id=None,
                created_at=apply_time,
                updated_at=receive_time if receive_time else apply_time,
            )
            new_referrals.append(referral)
            db.add(referral)
        
        db.commit()
        print(f"✅ 成功添加 {len(new_referrals)} 条转诊记录")
        print(f"   总计: {existing + len(new_referrals)} 条转诊记录")
        
        # 显示统计
        stats = db.query(ReferralRecord.status, db.func.count()).group_by(ReferralRecord.status).all()
        print("\n转诊状态统计:")
        for status, count in stats:
            print(f"  {status}: {count} 条")
            
    except Exception as e:
        db.rollback()
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == '__main__':
    add_referral_data()
