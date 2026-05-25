# 陵水县人民医院慢病管理系统 - 生产部署指南

**版本**: v1.0.0  
**更新时间**: 2026-05-23  
**适用环境**: Linux Server / Docker / Kubernetes

---

## 📋 目录

1. [环境要求](#环境要求)
2. [部署方式选择](#部署方式选择)
3. [方式1: Docker Compose 部署](#方式1-docker-compose-部署推荐)
4. [方式2: 传统部署](#方式2-传统部署)
5. [方式3: Kubernetes 部署](#方式3-kubernetes-部署)
6. [PostgreSQL 数据迁移](#postgresql-数据迁移)
7. [HTTPS/SSL 配置](#httpsssl-配置)
8. [性能优化](#性能优化)
9. [监控与日志](#监控与日志)
10. [备份与恢复](#备份与恢复)
11. [故障排查](#故障排查)

---

## 环境要求

### 最低配置
- **CPU**: 4 核
- **内存**: 8GB
- **磁盘**: 100GB SSD
- **操作系统**: Ubuntu 22.04 LTS / CentOS 8+

### 软件依赖
- **Docker**: >= 20.10 (推荐)
- **Docker Compose**: >= 2.0 (推荐)
- **PostgreSQL**: >= 14 (传统部署)
- **Nginx**: >= 1.20 (传统部署)
- **Node.js**: >= 20 (前端构建)
- **Python**: >= 3.11 (后端运行)

---

## 部署方式选择

| 方式 | 难度 | 适用场景 | 推荐度 |
|------|------|----------|--------|
| **Docker Compose** | ⭐ 简单 | 中小规模生产环境 | ⭐⭐⭐⭐⭐ |
| **传统部署** | ⭐⭐⭐ 中等 | 已有 PostgreSQL/Nginx 环境 | ⭐⭐⭐ |
| **Kubernetes** | ⭐⭐⭐⭐⭐ 复杂 | 大规模集群部署 | ⭐⭐⭐⭐ |

**推荐**: 使用 **Docker Compose** 部署（最简单、最快速）

---

## 方式1: Docker Compose 部署 (推荐)

### 步骤 1: 安装 Docker 和 Docker Compose

```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
newgrp docker

# 验证安装
docker --version
docker-compose --version
```

### 步骤 2: 获取项目代码

```bash
# 方式 A: 从 Git 克隆
git clone https://github.com/your-repo/slow_disease_system.git
cd slow_disease_system

# 方式 B: 上传压缩包
scp slow_disease_system.tar.gz user@server:/opt/
ssh user@server
cd /opt/
tar -xzf slow_disease_system.tar.gz
cd slow_disease_system
```

### 步骤 3: 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑配置（必须修改这些值！）
nano .env
```

**必须修改的配置项**:

```bash
# 1. 数据库密码 (修改为强密码)
DB_PASSWORD=your-super-secure-password-123456

# 2. JWT 密钥 (至少 32 字符随机字符串)
SECRET_KEY=$(openssl rand -hex 32)

# 3. 加密密钥 (16/24/32 字符)
ENCRYPTION_KEY=$(openssl rand -hex 16)

# 4. 环境标识
ENVIRONMENT=production
```

### 步骤 4: 启动服务

```bash
# 构建并启动所有服务
docker-compose up -d --build

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f backend
```

### 步骤 5: 初始化数据库

```bash
# 等待 PostgreSQL 启动完成 (约 10-30 秒)
docker-compose exec backend alembic upgrade head

# 创建管理员账户
docker-compose exec backend python3 -c "
from app.services.encryption_service import EncryptionService
from app.models import Patient
# ... (见下方"创建初始管理员"章节)
"
```

### 步骤 6: 验证部署

```bash
# 健康检查
curl <http://localhost:8000/health>

# 访问前端
open <http://your-server-ip>

# 登录测试
# 用户名: admin
# 密码: admin123 (首次登录后必须修改！)
```

### 步骤 7: 配置 HTTPS (可选但强烈推荐)

```bash
# 安装 Certbot
sudo apt install certbot python3-certbot-nginx

# 获取 SSL 证书
sudo certbot --nginx -d your-domain.com

# 自动续期
sudo certbot renew --dry-run
```

---

## 方式2: 传统部署

### 步骤 1: 安装 PostgreSQL

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install postgresql postgresql-contrib

# 创建数据库
sudo -u postgres psql
CREATE DATABASE slow_disease;
CREATE USER slow_disease_user WITH PASSWORD 'your-password';
GRANT ALL PRIVILEGES ON DATABASE slow_disease TO slow_disease_user;
\q
```

### 步骤 2: 安装 Redis (可选)

```bash
sudo apt install redis-server
sudo systemctl enable redis
sudo systemctl start redis
```

### 步骤 3: 部署后端

```bash
# 创建用户
sudo useradd -m -s /bin/bash slow_disease
sudo su - slow_disease

# 克隆代码
git clone https://github.com/your-repo/slow_disease_system.git
cd slow_disease_system/backend

# 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt
pip install gunicorn uvloop httptools

# 配置环境变量
cp .env.example .env
nano .env  # 修改 DATABASE_URL 等配置

# 初始化数据库
alembic upgrade head

# 启动后端 (使用 systemd)
sudo nano /etc/systemd/system/slow-disease-backend.service
```

**Systemd 服务文件** (`/etc/systemd/system/slow-disease-backend.service`):

```ini
[Unit]
Description=Slow Disease Management System Backend
After=network.target postgresql.service

[Service]
Type=notify
User=slow_disease
Group=slow_disease
WorkingDirectory=/home/slow_disease/slow_disease_system/backend
Environment="PATH=/home/slow_disease/slow_disease_system/backend/.venv/bin"
ExecStart=/home/slow_disease/slow_disease_system/backend/.venv/bin/gunicorn app.main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --access-logfile /var/log/slow_disease/backend_access.log \
    --error-logfile /var/log/slow_disease/backend_error.log \
    --log-level info
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# 启动服务
sudo systemctl daemon-reload
sudo systemctl enable slow-disease-backend
sudo systemctl start slow-disease-backend
sudo systemctl status slow-disease-backend
```

### 步骤 4: 部署前端

```bash
# 安装 Node.js (使用 nvm)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
source ~/.bashrc
nvm install 20
nvm use 20

# 构建前端
cd /home/slow_disease/slow_disease_system/frontend
npm ci --only=production
echo "VITE_API_BASE_URL=/api" > .env.production
npm run build

# 配置 Nginx
sudo nano /etc/nginx/sites-available/slow-disease
```

**Nginx 配置文件** (`/etc/nginx/sites-available/slow-disease`):

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # 重定向到 HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    # SSL 证书
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    # 前端静态文件
    location / {
        root /home/slow_disease/slow_disease_system/frontend/dist;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    # 后端 API 代理
    location /api/ {
        proxy_pass <http://localhost:8000>;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 健康检查
    location /health {
        proxy_pass <http://localhost:8000/health>;
        access_log off;
    }
}
```

```bash
# 启用配置
sudo ln -s /etc/nginx/sites-available/slow-disease /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## 方式3: Kubernetes 部署

> **适用场景**: 大规模生产环境、需要高可用和自动扩缩容

### 步骤 1: 构建并推送 Docker 镜像

```bash
# 构建镜像
docker build -t your-registry.com/slow-disease-backend:latest ./backend
docker build -t your-registry.com/slow-disease-frontend:latest ./frontend

# 推送镜像
docker push your-registry.com/slow-disease-backend:latest
docker push your-registry.com/slow-disease-frontend:latest
```

### 步骤 2: 创建 Kubernetes 配置

```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: slow-disease
---
# k8s/secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: slow-disease-secret
  namespace: slow-disease
type: Opaque
stringData:
  DATABASE_URL: "postgresql+asyncpg://user:pass@postgres:5432/slow_disease"
  SECRET_KEY: "your-secret-key"
  ENCRYPTION_KEY: "your-encryption-key"
---
# k8s/postgres.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
  namespace: slow-disease
spec:
  serviceName: postgres
  replicas: 1
  template:
    spec:
      containers:
      - name: postgres
        image: postgres:16-alpine
        env:
        - name: POSTGRES_DB
          value: slow_disease
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: slow-disease-secret
              key: POSTGRES_PASSWORD
        ports:
        - containerPort: 5432
        volumeMounts:
        - name: postgres-data
          mountPath: /var/lib/postgresql/data
      volumes:
      - name: postgres-data
        persistentVolumeClaim:
          claimName: postgres-pvc
---
# k8s/backend.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
  namespace: slow-disease
spec:
  replicas: 3
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
    spec:
      containers:
      - name: backend
        image: your-registry.com/slow-disease-backend:latest
        ports:
        - containerPort: 8000
        envFrom:
        - secretRef:
            name: slow-disease-secret
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 30
---
# k8s/frontend.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: frontend
  namespace: slow-disease
spec:
  replicas: 2
  selector:
    matchLabels:
      app: frontend
  template:
    metadata:
      labels:
        app: frontend
    spec:
      containers:
      - name: frontend
        image: your-registry.com/slow-disease-frontend:latest
        ports:
        - containerPort: 80
---
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: slow-disease-ingress
  namespace: slow-disease
  annotations:
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  tls:
  - hosts:
    - your-domain.com
    secretName: slow-disease-tls
  rules:
  - host: your-domain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: frontend
            port:
              number: 80
      - path: /api
        pathType: Prefix
        backend:
          service:
            name: backend
            port:
              number: 8000
```

### 步骤 3: 部署到 Kubernetes

```bash
# 应用配置
kubectl apply -f k8s/

# 查看部署状态
kubectl get pods -n slow-disease
kubectl get svc -n slow-disease
kubectl get ingress -n slow-disease

# 查看日志
kubectl logs -f deployment/backend -n slow-disease
```

---

## PostgreSQL 数据迁移

### 从 SQLite 迁移到 PostgreSQL

#### 步骤 1: 导出 SQLite 数据

```bash
# 激活虚拟环境
cd /Users/shayuen/.qclaw/workspace/slow_disease_system/backend
source .venv/bin/activate

# 运行导出脚本
python3 export_sqlite_data.py > data_export.json
```

**导出脚本** (`export_sqlite_data.py`):

```python
import json
import aiosqlite
from datetime import datetime

async def export_data():
    async with aiosqlite.connect("slow_disease.db") as db:
        db.row_factory = aiosqlite.Row
        
        tables = ["patient", "followup_record", "referral", "assessment", ...]
        data = {}
        
        for table in tables:
            cursor = await db.execute(f"SELECT * FROM {table}")
            rows = await cursor.fetchall()
            data[table] = [dict(row) for row in rows]
        
        # 处理加密字段
        for patient in data.get("patient", []):
            patient["name_enc"] = decrypt(patient["name_enc"])  # 如果需要
        
        print(json.dumps(data, default=str))

if __name__ == "__main__":
    import asyncio
    asyncio.run(export_data())
```

#### 步骤 2: 导入到 PostgreSQL

```bash
# 修改 DATABASE_URL 指向 PostgreSQL
export DATABASE_URL="postgresql+asyncpg://postgres:password@localhost:5432/slow_disease"

# 运行 Alembic 迁移（创建表结构）
alembic upgrade head

# 导入数据
python3 import_to_postgres.py data_export.json
```

**导入脚本** (`import_to_postgres.py`):

```python
import json
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Base, Patient, FollowupRecord, ...

def import_data(json_file):
    # 创建 PostgreSQL 会话
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # 读取 JSON 数据
    with open(json_file) as f:
        data = json.load(f)
    
    # 导入患者数据
    for item in data.get("patient", []):
        patient = Patient(**item)
        session.add(patient)
    
    session.commit()
    print(f"导入完成: {len(data.get('patient', []))} 条患者记录")

if __name__ == "__main__":
    import_data(sys.argv[1])
```

#### 步骤 3: 验证数据完整性

```bash
# 对比记录数
sqlite3 slow_disease.db "SELECT COUNT(*) FROM patient;"
psql -U postgres -d slow_disease -c "SELECT COUNT(*) FROM patient;"

# 对比数据内容（抽样）
sqlite3 slow_disease.db "SELECT patient_id, name_enc FROM patient LIMIT 5;"
psql -U postgres -d slow_disease -c "SELECT patient_id, name_enc FROM patient LIMIT 5;"
```

---

## HTTPS/SSL 配置

### 使用 Let's Encrypt (推荐)

```bash
# 安装 Certbot
sudo apt install certbot python3-certbot-nginx

# 获取证书（自动配置 Nginx）
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# 测试自动续期
sudo certbot renew --dry-run

# 查看证书状态
sudo certbot certificates
```

### 使用自定义证书

```bash
# 将证书放到指定目录
sudo mkdir -p /etc/nginx/ssl
sudo cp fullchain.pem /etc/nginx/ssl/
sudo cp privkey.pem /etc/nginx/ssl/

# 修改 Nginx 配置
sudo nano /etc/nginx/sites-available/slow-disease
# 添加:
# ssl_certificate /etc/nginx/ssl/fullchain.pem;
# ssl_certificate_key /etc/nginx/ssl/privkey.pem;

# 重启 Nginx
sudo systemctl restart nginx
```

---

## 性能优化

### 1. 后端优化

```python
# backend/app/main.py
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

# 添加速率限制
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.get("/api/v1/patients")
@limiter.limit("100/minute")
async def get_patients(request: Request, ...):
    ...
```

```bash
# 使用 Gunicorn + Uvicorn Workers（已在 Dockerfile 中配置）
gunicorn app.main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000
```

### 2. 数据库优化

```sql
-- 添加索引
CREATE INDEX idx_patient_disease_list ON patient USING GIN (disease_list);
CREATE INDEX idx_followup_patient_id ON followup_record (patient_id);
CREATE INDEX idx_followup_date ON followup_record (followup_date);
CREATE INDEX idx_assessment_patient_id ON assessment (patient_id);

-- 分析查询性能
EXPLAIN ANALYZE SELECT * FROM patient WHERE risk_level = 'HIGH';
```

```python
# 使用连接池
# backend/app/db/session.py
from sqlalchemy.pool import NullPool

engine = create_async_engine(
    DATABASE_URL,
    poolclass=NullPool,  # 禁用 SQLAlchemy 连接池（使用 pgBouncer）
    pool_size=20,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=1800,
)
```

### 3. 前端优化

```javascript
// frontend/vite.config.ts
export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          'element-plus': ['element-plus'],
          'vue-vendor': ['vue', 'vue-router', 'pinia'],
        }
      }
    },
    chunkSizeWarningLimit: 1000,
  },
})
```

```bash
# 启用 Gzip 压缩 (Nginx)
sudo nano /etc/nginx/nginx.conf
# 添加:
# gzip on;
# gzip_vary on;
# gzip_min_length 1024;
# gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;
```

### 4. 缓存策略

```python
# backend/app/services/cache_service.py
import redis
import json
from functools import wraps

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def cache(expire_seconds=300):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
            
            result = await func(*args, **kwargs)
            redis_client.setex(cache_key, expire_seconds, json.dumps(result))
            return result
        return wrapper
    return decorator

# 使用缓存
@cache(expire_seconds=600)
async def get_dashboard_kpi(db):
    ...
```

---

## 监控与日志

### 1. 日志配置

```python
# backend/app/main.py
import logging
from logging.handlers import RotatingFileHandler

# 配置日志
handler = RotatingFileHandler(
    '/var/log/slow_disease/backend.log',
    maxBytes=10485760,  # 10MB
    backupCount=10
)
handler.setLevel(logging.INFO)
app.add_middleware(logging middleware)

# Docker 日志
# 已在 docker-compose.yml 中配置 --access-logfile - --error-logfile -
```

### 2. 健康检查

```python
# backend/app/main.py
@app.get("/health")
async def health_check():
    # 检查数据库连接
    try:
        async with async_session() as db:
            await db.execute(text("SELECT 1"))
            db_status = "healthy"
    except:
        db_status = "unhealthy"
    
    return {
        "status": "ok" if db_status == "healthy" else "error",
        "database": db_status,
        "timestamp": datetime.now().isoformat(),
    }
```

### 3. 监控工具

```yaml
# docker-compose.monitoring.yml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
  
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin123
    volumes:
      - grafana_data:/var/lib/grafana

  loki:
    image: grafana/loki:latest
    ports:
      - "3100:3100"
    volumes:
      - ./loki-config.yaml:/etc/loki/local-config.yaml
```

---

## 备份与恢复

### 1. 数据库备份

```bash
# SQLite 备份
cp slow_disease.db slow_disease.db.backup.$(date +%Y%m%d)

# PostgreSQL 备份
pg_dump -U postgres slow_disease > backup_$(date +%Y%m%d).sql

# 压缩备份
pg_dump -U postgres slow_disease | gzip > backup_$(date +%Y%m%d).sql.gz

# 自动化备份（crontab）
# 每天凌晨 2 点备份
0 2 * * * pg_dump -U postgres slow_disease | gzip > /backups/backup_$(date +\%Y\%m\%d).sql.gz
```

### 2. 数据库恢复

```bash
# SQLite 恢复
cp slow_disease.db.backup.20260523 slow_disease.db

# PostgreSQL 恢复
psql -U postgres slow_disease < backup_20260523.sql

# 从压缩文件恢复
gunzip -c backup_20260523.sql.gz | psql -U postgres slow_disease
```

### 3. 文件备份

```bash
# 备份上传的文件
tar -czf uploads_backup_$(date +%Y%m%d).tar.gz uploads/

# 备份配置文件
cp .env .env.backup.$(date +%Y%m%d)
```

---

## 故障排查

### 常见问题

#### 1. 后端无法启动

**症状**: `docker-compose logs backend` 显示错误

**排查**:
```bash
# 检查环境变量
docker-compose exec backend env | grep DATABASE_URL

# 检查数据库连接
docker-compose exec postgres psql -U postgres -d slow_disease -c "SELECT 1"

# 检查端口占用
netstat -tulpn | grep 8000
```

**解决**:
- 确认 `DATABASE_URL` 配置正确
- 确认 PostgreSQL 已启动 (`docker-compose up -d postgres`)
- 确认 Alembic 迁移已执行 (`docker-compose exec backend alembic upgrade head`)

#### 2. 前端无法访问

**症状**: 浏览器显示"无法访问此网站"

**排查**:
```bash
# 检查 Nginx 状态
sudo systemctl status nginx

# 检查 Nginx 配置
sudo nginx -t

# 检查防火墙
sudo ufw status
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
```

**解决**:
- 确认 Nginx 已启动
- 确认防火墙已开放 80/443 端口
- 确认 SSL 证书配置正确

#### 3. API 请求 404

**症状**: 前端请求 `/api/v1/patients` 返回 404

**排查**:
```bash
# 检查 Nginx 代理配置
curl <http://localhost:8000/api/v1/patients>  # 直接访问后端
curl <http://localhost/api/v1/patients>      # 通过 Nginx 访问

# 检查后端路由
docker-compose exec backend curl <http://localhost:8000/docs>
```

**解决**:
- 确认 Nginx `location /api/` 配置正确
- 确认后端服务已启动
- 确认 CORS 配置允许前端域名

#### 4. 数据库迁移失败

**症状**: `alembic upgrade head` 报错

**排查**:
```bash
# 查看 Alembic 版本
docker-compose exec backend alembic heads

# 查看当前版本
docker-compose exec backend alembic current

# 回滚到上一版本
docker-compose exec backend alembic downgrade -1
```

**解决**:
- 确认数据库版本和 Alembic 版本一致
- 手动修复 SQL 错误后继续执行
- 必要时删除数据库重新创建

---

## 附录

### A. 常用命令速查

```bash
# Docker Compose
docker-compose up -d              # 启动所有服务
docker-compose ps                  # 查看服务状态
docker-compose logs -f backend    # 查看后端日志
docker-compose exec backend bash  # 进入后端容器
docker-compose down               # 停止所有服务
docker-compose pull               # 拉取最新镜像

# 数据库
alembic upgrade head              # 执行迁移
alembic revision --autogenerate -m "描述"  # 生成迁移脚本
psql -U postgres -d slow_disease  # 连接数据库

# 系统服务
sudo systemctl status slow-disease-backend  # 查看服务状态
sudo systemctl restart slow-disease-backend # 重启服务
sudo journalctl -u slow-disease-backend -f # 查看服务日志

# Nginx
sudo nginx -t                    # 测试配置
sudo systemctl restart nginx     # 重启 Nginx
sudo tail -f /var/log/nginx/error.log  # 查看错误日志
```

### B. 安全加固清单

- [ ] 修改默认管理员密码 (`admin/admin123`)
- [ ] 配置防火墙 (仅开放 80/443/22)
- [ ] 启用 HTTPS (Let's Encrypt)
- [ ] 配置 CORS (仅允许信任的域名)
- [ ] 配置速率限制 (防止暴力破解)
- [ ] 定期备份数据库
- [ ] 定期更新系统补丁
- [ ] 禁用 root SSH 登录
- [ ] 配置 Fail2ban (防止暴力破解)
- [ ] 审计日志监控 (异常操作告警)

### C. 性能基准

| 指标 | 目标值 | 测试方法 |
|------|--------|----------|
| API 响应时间 | < 200ms (P95) | `ab -n 1000 -c 10 <http://localhost:8000/api/v1/patients>` |
| 数据库查询 | < 50ms (平均) | PostgreSQL `EXPLAIN ANALYZE` |
| 前端首屏加载 | < 2s | Google Lighthouse |
| 并发用户数 | 100+ | `locust -f load_test.py` |

---

**文档版本**: v1.0.0  
**最后更新**: 2026-05-23  
**维护者**: 陵水县人民医院信息科

---

## 支持与联系

**技术支持**: your-email@example.com  
**项目仓库**: <https://github.com/your-repo/slow_disease_system>  
**Issue 追踪**: <https://github.com/your-repo/slow_disease_system/issues>
