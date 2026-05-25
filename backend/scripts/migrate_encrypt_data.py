#!/usr/bin/env python3
"""
种子数据加密迁移脚本
将患者表的明文敏感字段（name_enc、id_card_enc、phone_enc）加密为密文

支持：
- SQLite（同步）
- PostgreSQL（同步）

使用方法：
    cd backend
    python scripts/migrate_encrypt_data.py
"""
import os
import sys
import base64
import random
from datetime import datetime
from pathlib import Path

# 添加项目根目录到 Python 路径
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import create_engine, text, update
from sqlalchemy.orm import sessionmaker

# 导入加密服务和模型
from app.services.encryption_service import get_encryption_service
from app.config import settings


# 敏感字段列表
ENCRYPT_FIELDS = ['name_enc', 'id_card_enc', 'phone_enc']


def is_encrypted(value: str) -> bool:
    """
    判断字段值是否已加密（Fernet 密文格式）
    
    Fernet 密文特征：
    - base64 urlsafe 编码
    - 长度通常 > 30（Fernet token 最小长度约 100+）
    - 包含 Fernet 版本前缀（base64 编码后）
    """
    if not value:
        return True  # 空值视为已处理
    
    if len(value) <= 30:
        return False  # 太短，不是 Fernet 密文
    
    # 尝试 base64 解码验证
    try:
        # Fernet 密文是 urlsafe base64 编码的
        decoded = base64.urlsafe_b64decode(value)
        # Fernet token 最小长度约 116 字节（加密后的最小长度）
        return len(decoded) > 30
    except Exception:
        return False


def get_sync_engine():
    """
    根据数据库类型创建同步引擎
    
    SQLite: 使用 pysqlite（内置）
    PostgreSQL: 使用 psycopg2
    """
    db_url = os.getenv('DATABASE_URL', settings.DATABASE_URL)
    
    # 转换异步 URL 为同步 URL
    if db_url.startswith('sqlite+aiosqlite'):
        # SQLite 异步转同步
        sync_url = db_url.replace('sqlite+aiosqlite', 'sqlite')
        return create_engine(sync_url, echo=False)
    elif db_url.startswith('postgresql+asyncpg'):
        # PostgreSQL 异步转同步
        # asyncpg -> psycopg2
        sync_url = db_url.replace('postgresql+asyncpg', 'postgresql+psycopg2')
        return create_engine(sync_url, echo=False, pool_size=5, max_overflow=10)
    else:
        # 已经是同步 URL 或其他格式
        return create_engine(db_url, echo=False)


def count_patients_need_encryption(engine) -> dict:
    """统计需要加密的患者数量"""
    with engine.connect() as conn:
        # 查询所有患者
        result = conn.execute(text("""
            SELECT patient_id, name_enc, id_card_enc, phone_enc
            FROM patient
        """))
        
        total = 0
        need_encrypt = 0
        already_encrypted = 0
        
        for row in result:
            total += 1
            # 检查是否有字段需要加密
            has_plain = False
            for field_idx, field in enumerate(['name_enc', 'id_card_enc', 'phone_enc']):
                value = row[field_idx + 1]  # row[1], row[2], row[3]
                if value and not is_encrypted(value):
                    has_plain = True
                    break
            
            if has_plain:
                need_encrypt += 1
            else:
                already_encrypted += 1
        
        return {
            'total': total,
            'need_encrypt': need_encrypt,
            'already_encrypted': already_encrypted
        }


def migrate_encrypt(engine) -> dict:
    """
    执行加密迁移
    
    返回：成功、失败、跳过的数量
    """
    encryption_service = get_encryption_service()
    
    success_count = 0
    fail_count = 0
    skip_count = 0
    
    with engine.connect() as conn:
        # 查询所有患者
        result = conn.execute(text("""
            SELECT patient_id, name_enc, id_card_enc, phone_enc
            FROM patient
        """))
        patients = result.fetchall()
        
        now = datetime.utcnow()
        
        for row in patients:
            patient_id = row[0]
            name_enc = row[1]
            id_card_enc = row[2]
            phone_enc = row[3]
            
            # 检查是否需要加密
            fields_to_encrypt = {}
            
            try:
                # 加密姓名
                if name_enc and not is_encrypted(name_enc):
                    fields_to_encrypt['name_enc'] = encryption_service.encrypt(name_enc)
                
                # 加密身份证
                if id_card_enc and not is_encrypted(id_card_enc):
                    fields_to_encrypt['id_card_enc'] = encryption_service.encrypt(id_card_enc)
                
                # 加密手机号
                if phone_enc and not is_encrypted(phone_enc):
                    fields_to_encrypt['phone_enc'] = encryption_service.encrypt(phone_enc)
                
                if fields_to_encrypt:
                    # 构建更新 SQL
                    set_clauses = []
                    values = {}
                    
                    for field, encrypted_value in fields_to_encrypt.items():
                        set_clauses.append(f"{field} = :{field}")
                        values[field] = encrypted_value
                    
                    # 添加更新时间
                    set_clauses.append("updated_at = :updated_at")
                    values['updated_at'] = now
                    values['patient_id'] = patient_id
                    
                    update_sql = text(f"""
                        UPDATE patient 
                        SET {', '.join(set_clauses)}
                        WHERE patient_id = :patient_id
                    """)
                    
                    conn.execute(update_sql, values)
                    conn.commit()
                    success_count += 1
                else:
                    skip_count += 1
                    
            except Exception as e:
                print(f"  ✗ 加密失败 patient_id={patient_id}: {e}")
                fail_count += 1
    
    return {
        'success': success_count,
        'fail': fail_count,
        'skip': skip_count
    }


def verify_encryption(engine, sample_size: int = 3) -> bool:
    """
    验证加密数据：随机抽取样本解密验证
    
    返回：验证是否成功
    """
    encryption_service = get_encryption_service()
    
    with engine.connect() as conn:
        # 随机抽取样本
        result = conn.execute(text("""
            SELECT patient_id, name_enc, id_card_enc, phone_enc
            FROM patient
            ORDER BY RANDOM()
            LIMIT :limit
        """), {'limit': sample_size})
        
        samples = result.fetchall()
        
        if not samples:
            print("  ⚠ 数据库中没有患者记录，跳过验证")
            return True
        
        print(f"\n验证 {len(samples)} 条随机记录的解密：")
        
        all_passed = True
        for row in samples:
            patient_id = row[0]
            name_enc = row[1]
            id_card_enc = row[2]
            phone_enc = row[3]
            
            try:
                # 尝试解密
                name_dec = encryption_service.decrypt(name_enc) if name_enc else None
                id_card_dec = encryption_service.decrypt(id_card_enc) if id_card_enc else None
                phone_dec = encryption_service.decrypt(phone_enc) if phone_enc else None
                
                # 验证解密结果
                print(f"  ✓ patient_id={patient_id[:8]}...")
                if name_dec:
                    print(f"    姓名: {name_dec[:1]}** (已验证)")
                if id_card_dec:
                    print(f"    身份证: {id_card_dec[:3]}****{id_card_dec[-4:]} (已验证)")
                if phone_dec:
                    print(f"    手机: {phone_dec[:3]}****{phone_dec[-4:]} (已验证)")
                    
            except Exception as e:
                print(f"  ✗ 解密失败 patient_id={patient_id}: {e}")
                all_passed = False
        
        return all_passed


def main():
    """主函数"""
    print("=" * 60)
    print("患者敏感数据加密迁移脚本")
    print("=" * 60)
    
    # 获取数据库类型
    db_url = os.getenv('DATABASE_URL', settings.DATABASE_URL)
    is_sqlite = 'sqlite' in db_url.lower()
    db_type = "SQLite" if is_sqlite else "PostgreSQL"
    
    print(f"\n数据库类型: {db_type}")
    print(f"数据库 URL: {db_url.split('/')[-1] if is_sqlite else db_url[:50] + '...'}")
    
    # 创建同步引擎
    print("\n正在连接数据库...")
    engine = get_sync_engine()
    print("✓ 数据库连接成功")
    
    # 统计需要加密的记录
    print("\n正在扫描患者数据...")
    stats = count_patients_need_encryption(engine)
    
    print("\n" + "-" * 60)
    print("加密前统计：")
    print(f"  总患者数: {stats['total']}")
    print(f"  需要加密: {stats['need_encrypt']}")
    print(f"  已加密/无需加密: {stats['already_encrypted']}")
    print("-" * 60)
    
    if stats['need_encrypt'] == 0:
        print("\n✓ 所有敏感字段已加密，无需迁移")
        return
    
    # 执行加密迁移
    print(f"\n开始加密 {stats['need_encrypt']} 条记录...")
    result = migrate_encrypt(engine)
    
    print("\n" + "-" * 60)
    print("加密后统计：")
    print(f"  成功: {result['success']}")
    print(f"  失败: {result['fail']}")
    print(f"  跳过: {result['skip']}")
    print("-" * 60)
    
    # 验证加密结果
    print("\n正在验证加密结果...")
    verify_passed = verify_encryption(engine, sample_size=3)
    
    if verify_passed and result['fail'] == 0:
        print("\n" + "=" * 60)
        print("✓ 加密迁移完成！所有验证通过")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("⚠ 加密迁移完成，但存在问题")
        print(f"  验证: {'通过' if verify_passed else '失败'}")
        print(f"  失败记录数: {result['fail']}")
        print("=" * 60)
        sys.exit(1)


if __name__ == '__main__':
    main()
