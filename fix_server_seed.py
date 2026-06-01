#!/usr/bin/env python3
"""陵水慢病系统 - 服务器端一键数据填充脚本"""
import sys, os
sys.path.insert(0, '/opt/lingshui/backend')
os.chdir('/opt/lingshui/backend')

from app.services.encryption_service import encryption_service
import sqlite3, json, random
from datetime import date, datetime, timedelta

random.seed(42)
DB = 'lingshui.db'
now = datetime.now()
nows = now.strftime('%Y-%m-%d %H:%M:%S')
today = date.today()

DISEASES = ['HYPERTENSION', 'DIABETES', 'CHD', 'STROKE', 'COPD', 'CKD']
DISEASE_CN = {'HYPERTENSION':'高血压','DIABETES':'糖尿病','CHD':'冠心病',
              'STROKE':'脑卒中','COPD':'慢阻肺','CKD':'慢性肾脏病'}
ORG_CODES = ['460123001','460123002','460123003','460123004',
             '460123','460123','460123','460123']
ORG_NAMES = {'460123':'陵水县人民医院','460123001':'椰林镇卫生院',
             '460123002':'英州镇卫生院','460123003':'新村镇卫生院',
             '460123004':'黎安镇卫生院'}
VILLAGE_CODES = ['460123001001','460123001002','460123002001','460123002002',
                 '460123003001','460123004001','460123000001','460123000002']
LNS = ['陈','李','张','王','刘','黄','林','吴','周','杨']
FNS = ['伟','芳','强','敏','杰','丽','军','静','磊','洋',
       '勇','艳','涛','鑫','玲','明','娟','鹏','华','秀英']

DRUGS = [
    ('氨氯地平','HYPER1','CCB','5mg/片','5mg','qd','口服'),
    ('硝苯地平','HYPER2','CCB','30mg/片','30mg','qd','口服'),
    ('厄贝沙坦','HYPER3','ARB','150mg/片','150mg','qd','口服'),
    ('美托洛尔','HYPER4','BB','25mg/片','25mg','bid','口服'),
    ('二甲双胍','DM1','Biguanide','500mg/片','500mg','bid','口服'),
    ('格列齐特','DM2','SU','30mg/片','30mg','qd','口服'),
    ('阿卡波糖','DM3','AGI','50mg/片','50mg','tid','口服'),
    ('达格列净','DM4','SGLT2i','10mg/片','10mg','qd','口服'),
    ('阿托伐他汀','LIPID1','Statin','20mg/片','20mg','qd','口服'),
    ('阿司匹林','ANTI1','NSAID','100mg/片','100mg','qd','口服'),
]
FREQ_MAP = {'qd':'每日一次','bid':'每日两次','tid':'每日三次'}

c = sqlite3.connect(DB)
tables_to_clear = ['patient','followup_record','alert_record','patient_medication',
    'referral_record','health_education_record','health_education_template',
    'patient_risk_assessment','patient_self_report','followup_reminder',
    'emergency_alert','tcm_record','patient_wechat','prescription_review']
for t in tables_to_clear:
    try: c.execute(f'DELETE FROM {t}')
    except: pass
c.commit()
print("Cleared all data tables")

fid=aid=mid=0

for i in range(65):
    pid = f'p_{i+1:04d}'
    name = random.choice(LNS)+random.choice(FNS)
    ename = encryption_service.encrypt(name)
    id_hash = f'simhash_{i:04d}'
    gender = random.choice(['M','F'])
    age = random.randint(35,82)
    birth = date(today.year-age, random.randint(1,12), random.randint(1,28))
    phone = f'1{random.randint(30,99):02d}{random.randint(10000000,99999999):08d}'
    ephone = encryption_service.encrypt(phone)
    idc = f'{random.randint(460000,469999)}{random.randint(1950,2005)}{random.randint(1000,1299)}{random.randint(1000,1999)}'
    eidc = encryption_service.encrypt(idc)
    org = random.choice(ORG_CODES)
    addr = f'陵水县{ORG_NAMES.get(org,"某镇")}{random.choice(["人民路","中山路"])}{random.randint(1,299)}号'
    n_d = 1 if random.random()<0.55 else (2 if random.random()<0.7 else random.randint(1,3))
    ds = random.sample(DISEASES,k=min(n_d,len(DISEASES)))
    risk = random.choice(['LOW','MEDIUM','HIGH','CRITICAL'])
    active = 1 if random.random()>0.08 else 0

    c.execute('''INSERT INTO patient(
        patient_id,id_card_enc,id_card_hash,name_enc,
        gender,birth_date,age,phone_enc,address,village_code,manage_org_code,
        disease_list,risk_level,is_active,empi_status,created_at,updated_at)
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
        (pid,eidc,id_hash,ename,gender,birth.isoformat(),age,ephone,addr,
         random.choice(VILLAGE_CODES),org,json.dumps(ds,ensure_ascii=False),
         risk,active,'active' if active else 'deceased',nows,nows))

    # Followups (2-4) - 37 fields matching actual table schema
    for j in range(random.randint(2,4)):
        fid+=1
        fd = today-timedelta(days=random.randint(1,180))
        bp_s=random.randint(110,185);bp_d=random.randint(60,110)
        c.execute('''INSERT INTO followup_record(
            followup_id,patient_id,disease_code,followup_no,followup_type,
            followup_date,performed_by,org_code,bp_systolic,bp_diastolic,
            fbg,pbg,hba1c,ldl_c,hdl_c,tc,tg,weight,bmi,heart_rate,
            medication_adherence,is_controlled,next_followup_date,symptoms,signs,
            medication_changed,medication_note,location_lat,location_lng,
            audio_record_url,device_data,is_audited,audited_by,audited_at,
            audit_note,created_at,updated_at)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
            (f'fu_{fid:05d}',pid,ds[0],j+1,
             random.choice(['门诊','上门','电话','在线']),
             fd.isoformat(),'system',org,bp_s,bp_d,
             round(random.uniform(4,12),1),round(random.uniform(5,16),1),
             round(random.uniform(5,10.5),1),round(random.uniform(1.5,5),2),
             round(random.uniform(0.8,2),2),round(random.uniform(3,7),2),
             round(random.uniform(0.5,3.5),2),
             round(random.uniform(45,95),1),
             round(random.uniform(45,95)/random.uniform(1.5,1.85)**2,1),
             random.randint(55,105),
             random.choice(['regular','irregular','missed']),
             random.choice([0,0,1]),
             (fd+timedelta(days=random.randint(30,90))).isoformat(),
             '无特殊不适','血压偏高' if bp_s>140 else '无异常',
             random.choice([0,0,0,1]),'',18.5,110.0,
             '','{}',0,'',nows,'',nows,nows))

    # Alerts - 12 fields matching actual table schema
    if random.random()<0.35:
        aid+=1
        c.execute('''INSERT INTO alert_record(
            alert_id,patient_id,org_code,alert_type,alert_level,
            alert_title,alert_content,is_handled,handled_by,handled_at,
            handle_note,created_at)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?)''',
            (f'al_{aid:05d}',pid,org,
             random.choice(['BP','BG','Followup','Medication']),
             random.choice(['LOW','MEDIUM','HIGH','CRITICAL']),
             f'{DISEASE_CN[ds[0]]}{random.choice(["血压","血糖","随访","用药"])}预警',
             f'患者指标{random.choice(["偏高","偏低","异常","到期未复查"])}，需关注',
             0 if random.random()>0.2 else 1,
             'system' if random.random()>0.2 else '',nows if random.random()>0.2 else '',
             '',nows))

    # Medications - 25 fields matching actual table schema
    for j in range(random.randint(1,2)):
        mid+=1
        drug = random.choice(DRUGS)
        drug_name, drug_code, drug_class, specification, dosage, freq, route = drug
        start_d = today-timedelta(days=random.randint(30,365))
        c.execute('''INSERT INTO patient_medication(
            medication_id,patient_id,disease_code,drug_name,drug_code,
            drug_class,specification,dosage,frequency,route,start_date,end_date,
            is_long_term,is_active,prescribed_by,prescribed_org,adjust_reason,
            adjust_date,is_ai_recommended,ai_confidence,adherence_status,
            side_effects,notes,created_at,updated_at)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
            (f'med_{mid:05d}',pid,ds[0],drug_name,drug_code,
             drug_class,specification,dosage,freq,route,
             start_d.isoformat(),None,
             1,1,'system',org,'',
             None,0,0.0,
             random.choice(['compliant','partial','non_compliant']),
             '','',nows,nows))

    if i%15==0:
        c.commit()
        print(f'  {i+1}/65 patients... fups={fid} alerts={aid} meds={mid}')

c.commit()
print(f'\nDone!')
print(f'  Patients: {i+1}')
print(f'  Followups: {fid}')
print(f'  Alerts: {aid}')
print(f'  Medications: {mid}')

for t in ['patient','followup_record','alert_record','patient_medication']:
    cnt=c.execute(f'SELECT count(*) FROM {t}').fetchone()[0]
    print(f'  DB {t}: {cnt}')
c.close()
print('SEED_OK')