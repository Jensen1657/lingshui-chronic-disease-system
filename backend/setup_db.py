"""
数据库初始化脚本 - SQLite 版本
运行方式: python setup_db.py
"""
import sqlite3
import os
import sys

DB_PATH = "/tmp/slow_disease_system/backend/slow_disease.db"
SCHEMA_PATH = "/tmp/slow_disease_system/sql/schema.sql"


def init_db():
    # 确保目录存在
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

    # 删除旧数据库（如果存在）
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print(f"已删除旧数据库: {DB_PATH}")

    # 连接 SQLite
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # 启用外键约束
    cursor.execute("PRAGMA foreign_keys = ON;")

    # 读取 schema 文件
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    # 分割并执行每个 SQL 语句
    statements = []
    current = ""
    for line in schema_sql.split("\n"):
        stripped = line.strip()
        # 跳过注释和空行
        if not stripped or stripped.startswith("--"):
            continue
        current += line + "\n"
        # 如果这一行以分号结尾，说明是一个完整的语句
        if stripped.endswith(";"):
            statements.append(current.strip())
            current = ""

    # 执行每个语句
    total = len(statements)
    for i, stmt in enumerate(statements):
        try:
            cursor.execute(stmt)
            if (i + 1) % 5 == 0:
                print(f"  进度: {i + 1}/{total} 语句已执行")
        except Exception as e:
            print(f"  ⚠️  执行出错: {e}")
            print(f"  语句: {stmt[:200]}")
            raise

    conn.commit()

    # 验证：统计表数量
    cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table';")
    table_count = cursor.fetchone()[0]
    print(f"\n✅ 数据库初始化完成！")
    print(f"   数据库路径: {DB_PATH}")
    print(f"   表数量: {table_count}")

    # 创建默认管理员账号
    import hashlib
    from datetime import datetime

    # 密码: admin123 -> bcrypt hash
    # 简化：使用 SHA256 演示（生产环境用 bcrypt）
    password_hash = hashlib.sha256("admin123".encode()).hexdigest()
    admin_id = "00000000-0000-0000-0000-000000000001"

    cursor.execute(
        """
        INSERT INTO sys_user (user_id, username, password_hash, real_name, org_code, region_code, role_code, is_active)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (admin_id, "admin", password_hash, "系统管理员", "460034001", "460034", "ADMIN", 1),
    )
    conn.commit()
    print(f"   默认管理员: admin / admin123")

    # 验证表列表
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
    tables = [row[0] for row in cursor.fetchall()]
    print(f"\n📋 表清单:")
    for t in tables:
        print(f"   - {t}")

    conn.close()
    print("\n🎉 全部完成！")


if __name__ == "__main__":
    print("=" * 50)
    print("陵水县人民医院慢病管理系统 - 数据库初始化")
    print("=" * 50)
    init_db()
