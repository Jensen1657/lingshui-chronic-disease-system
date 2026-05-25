# PostgreSQL 生产环境迁移指南

## 概述

本文档说明如何将慢病管理系统从 SQLite 开发数据库迁移到 PostgreSQL 生产环境。

---

## 1. 环境准备

### 1.1 安装 PostgreSQL

```bash
# macOS
brew install postgresql@15
brew services start postgresql@15

# Ubuntu/Debian
sudo apt install postgresql-15
sudo systemctl start postgresql

# CentOS/RHEL
sudo yum install postgresql15-server
sudo postgresql-setup initdb
sudo systemctl start postgresql
```

### 1.2 创建数据库和用户

```sql
-- 连接 PostgreSQL
psql -U postgres

-- 创建用户
CREATE USER slow_disease_user WITH PASSWORD 'your_secure_password';

-- 创建数据库
CREATE DATABASE slow_disease_db OWNER slow_disease_user;

-- 授权
GRANT ALL PRIVILEGES ON DATABASE slow_disease_db TO slow_disease_user;
```

---

## 2. 修改配置

### 2.1 环境变量

修改 `backend/.env`:

```env
# 数据库配置
DATABASE_URL=postgresql+asyncpg://slow_disease_user:your_secure_password@localhost:5432/slow_disease_db

# JWT 配置
JWT_SECRET_KEY=your_production_secret_key_at_least_32_characters
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=480

# 加密密钥
ENCRYPTION_KEY=your_fernet_key_generate_with_python_fernet_generate_key

# CORS
CORS_ORIGINS=["https://your-domain.com"]
```

### 2.2 生成加密密钥

```python
from cryptography.fernet import Fernet
print(Fernet.generate_key().decode())
```

### 2.3 依赖安装

```bash
pip install asyncpg psycopg2-binary
```

---

## 3. 数据迁移

### 3.1 生成迁移脚本

```bash
cd backend

# 配置 alembic/env.py 使用 PostgreSQL URL
# 修改 sqlalchemy.url 为 PostgreSQL 连接字符串

# 生成迁移
alembic revision --autogenerate -m "Production migration"

# 执行迁移
alembic upgrade head
```

### 3.2 数据导入

从 SQLite 导出数据并导入 PostgreSQL:

```bash
# 导出 SQLite 数据
sqlite3 slow_disease.db .dump > dump.sql

# 转换 SQL 语法（需要调整）
# - INTEGER PRIMARY KEY → SERIAL PRIMARY KEY
# - TEXT → VARCHAR/TEXT
# - TIMESTAMP → TIMESTAMP
# - 布尔值 0/1 → FALSE/TRUE

# 导入 PostgreSQL
psql -U slow_disease_user -d slow_disease_db < dump_converted.sql
```

---

## 4. 应用部署

### 4.1 启动后端

```bash
# 使用 Gunicorn + Uvicorn
pip install gunicorn

gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile - \
  --error-logfile -
```

### 4.2 Nginx 配置

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # 前端
    location / {
        root /path/to/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    # API
    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # WebSocket（如需要）
    location /ws {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### 4.3 Systemd 服务

创建 `/etc/systemd/system/slow-disease.service`:

```ini
[Unit]
Description=Slow Disease Management System
After=network.target postgresql.service

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/opt/slow_disease_system/backend
Environment="PATH=/opt/slow_disease_system/backend/.venv/bin"
ExecStart=/opt/slow_disease_system/backend/.venv/bin/gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
Restart=always

[Install]
WantedBy=multi-user.target
```

启动服务:

```bash
sudo systemctl daemon-reload
sudo systemctl enable slow-disease
sudo systemctl start slow-disease
```

---

## 5. 安全加固

### 5.1 数据库安全

```sql
-- 限制连接数
ALTER USER slow_disease_user CONNECTION LIMIT 20;

-- 只授予必要权限
REVOKE ALL ON DATABASE slow_disease_db FROM PUBLIC;
GRANT CONNECT ON DATABASE slow_disease_db TO slow_disease_user;
```

### 5.2 防火墙

```bash
# 只允许本地访问数据库
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### 5.3 SSL/TLS

使用 Let's Encrypt:

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

---

## 6. 监控和备份

### 6.1 日志

```bash
# 应用日志
journalctl -u slow-disease -f

# PostgreSQL 日志
tail -f /var/log/postgresql/postgresql-15-main.log
```

### 6.2 数据库备份

```bash
# 每日备份脚本
#!/bin/bash
BACKUP_DIR="/backup/postgresql"
DATE=$(date +%Y%m%d)
pg_dump -U slow_disease_user slow_disease_db > $BACKUP_DIR/slow_disease_$DATE.sql

# 保留最近 30 天
find $BACKUP_DIR -name "*.sql" -mtime +30 -delete
```

### 6.3 Cron 定时备份

```bash
# 每天凌晨 2 点备份
0 2 * * * /opt/slow_disease_system/scripts/backup.sh
```

---

## 7. 验证清单

- [ ] PostgreSQL 服务运行正常
- [ ] 数据库用户权限正确
- [ ] 环境变量配置完成
- [ ] 加密密钥已生成
- [ ] 数据迁移成功
- [ ] 后端服务启动正常
- [ ] Nginx 配置正确
- [ ] SSL 证书安装
- [ ] 防火墙规则设置
- [ ] 定时备份配置
- [ ] 日志监控正常

---

## 8. 常见问题

### 8.1 连接失败

```bash
# 检查 PostgreSQL 是否运行
sudo systemctl status postgresql

# 检查连接
psql -U slow_disease_user -d slow_disease_db -h localhost
```

### 8.2 权限问题

```sql
-- 检查权限
\l slow_disease_db
\du slow_disease_user

-- 重新授权
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO slow_disease_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO slow_disease_user;
```

### 8.3 性能优化

```sql
-- 创建索引
CREATE INDEX idx_patient_disease_list ON patient USING GIN (disease_list);
CREATE INDEX idx_followup_date ON followup_record (followup_date);

-- 分析表
ANALYZE patient;
ANALYZE followup_record;
```

---

**文档版本**: 1.0  
**更新日期**: 2026-05-23  
**适用版本**: 慢病管理系统 v1.0.0
