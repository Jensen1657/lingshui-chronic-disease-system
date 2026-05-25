import asyncio
import sys
sys.path.insert(0, '.')

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import text, select
from app.core.config import settings
from app.models import Patient, AlertRecord, EmergencyAlert

async def cleanup():
    engine = create_async_engine(settings.DATABASE_URL)
    
    async with AsyncSession(engine) as db:
        # 1. 查找测试患者
        result = await db.execute(
            select(Patient).where(
                (Patient.id.like('%测试%')) | 
                (Patient.name_enc.like('%测试%'))
            )
        )
        test_patients = result.scalars().all()
        print(f'找到 {len(test_patients)} 个测试患者')
        
        for patient in test_patients:
            pid = patient.id
            # 删除关联的预警和急救记录
            await db.execute(text(f"DELETE FROM alert_record WHERE patient_id = '{pid}'"))
            await db.execute(text(f"DELETE FROM emergency_alert WHERE patient_id = '{pid}'"))
            await db.delete(patient)
            print(f'  ✅ 删除患者 {pid}')
        
        # 2. 删除测试创建的预警（通过 ID）
        test_alert_ids = [
            '883114a5-2738-4eb0-a6c3-f6f85631c2ac',
            '2d73a3e2-13e0-43b3-a5e8-6639511da938'
        ]
        
        for aid in test_alert_ids:
            result = await db.execute(
                select(AlertRecord).where(AlertRecord.id == aid)
            )
            alert = result.scalar_one_or_none()
            if alert:
                await db.delete(alert)
                print(f'  ✅ 删除测试预警 {aid}')
        
        # 3. 删除测试创建的急救预警
        test_emergency_ids = ['2d73a3e2-13e0-43b3-a5e8-6639511da938']
        for eid in test_emergency_ids:
            result = await db.execute(
                select(EmergencyAlert).where(EmergencyAlert.id == eid)
            )
            emergency = result.scalar_one_or_none()
            if emergency:
                await db.delete(emergency)
                print(f'  ✅ 删除测试急救预警 {eid}')
        
        await db.commit()
        print('\n✅ 测试数据清理完成')
    
    await engine.dispose()

if __name__ == '__main__':
    asyncio.run(cleanup())
