"""
重置所有非 admin 用户的密码为 123456（bcrypt hash）
用法: python scripts/reset_passwords.py
"""
import sqlite3
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import bcrypt

DB_PATH = "/Users/shayuen/.qclaw/workspace/slow_disease_system/backend/slow_disease.db"
NEW_PASSWORD = "123456"


def reset_passwords():
    # Generate bcrypt hash of "123456"
    password_hash = bcrypt.hashpw(NEW_PASSWORD.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    print(f"Generated bcrypt hash: {password_hash}")
    print()

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Find all non-admin users
    cursor.execute(
        "SELECT user_id, username, real_name, role_code, password_hash FROM sys_user WHERE role_code != 'ADMIN'"
    )
    users = cursor.fetchall()

    if not users:
        print("⚠️  未找到非 admin 用户")
        conn.close()
        return

    print(f"找到 {len(users)} 个非 admin 用户，将统一重置密码为: {NEW_PASSWORD}")
    print()
    print(f"{'用户名':<20} {'姓名':<15} {'角色':<10} {'原密码格式'}")
    print("-" * 70)

    for user in users:
        old_hash = user['password_hash']
        old_fmt = "bcrypt" if old_hash.startswith('$') else "SHA256/其他"
        print(f"{user['username']:<20} {user['real_name']:<15} {user['role_code']:<10} {old_fmt}")

    print()
    print("正在重置密码...")

    for user in users:
        cursor.execute(
            "UPDATE sys_user SET password_hash = ? WHERE user_id = ?",
            (password_hash, user['user_id'])
        )
        print(f"  ✅ 已重置: {user['username']} ({user['real_name']})")

    conn.commit()

    # Verify
    cursor.execute(
        "SELECT user_id, username, real_name, role_code FROM sys_user WHERE role_code != 'ADMIN'"
    )
    updated_users = cursor.fetchall()
    print()
    print("验证 - 更新后的密码格式（应全为 bcrypt $2b$）:")
    for u in updated_users:
        cursor.execute("SELECT password_hash FROM sys_user WHERE user_id = ?", (u['user_id'],))
        h = cursor.fetchone()['password_hash']
        ok = "✅ bcrypt" if h.startswith('$') else "❌ 非 bcrypt"
        print(f"  {ok}  {u['username']}")

    # Also verify admin password is unchanged
    cursor.execute("SELECT username, password_hash FROM sys_user WHERE role_code = 'ADMIN'")
    admins = cursor.fetchall()
    print()
    print("Admin 用户密码未变动:")
    for a in admins:
        print(f"  {a['username']}: {a['password_hash'][:30]}...")

    conn.close()
    print()
    print("🎉 密码重置完成！所有非 admin 用户的新密码为: 123456")


if __name__ == "__main__":
    print("=" * 60)
    print("陵水县慢病管理系统 - 批量重置用户密码")
    print("=" * 60)
    print()
    reset_passwords()
