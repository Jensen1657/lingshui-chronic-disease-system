# 慢病管理系统 - Railway 部署指南

## 方案选择：Railway（推荐）

### 为什么选择 Railway？
- ✅ 免费额度：$5/月免费额度，足够个人项目
- ✅ 自动部署：连接 GitHub 自动部署
- ✅ 支持 PostgreSQL：免费数据库
- ✅ 支持后端 + 前端：一个项目部署前后端
- ✅ 国内访问速度可接受

---

## 部署步骤（预计 15 分钟）

### 步骤 1：准备 GitHub 仓库

```bash
# 1. 在 GitHub 创建新仓库（不要初始化 README）
# 例如：https://github.com/你的用户名/slow-disease-system

# 2. 初始化本地仓库并推送
cd /Users/shayuen/.qclaw/workspace/slow_disease_system

git init
git add .
git commit -m "Initial commit: 慢病管理系统"

# 添加远程仓库
git remote add origin https://github.com/你的用户名/slow-disease-system.git
git branch -M main
git push -u origin main
```

### 步骤 2：注册 Railway

1. 访问 https://railway.app/
2. 点击 "Start a New Project"
3. 选择 "Deploy from GitHub repo"
4. 授权 Railway 访问你的 GitHub
5. 选择刚才创建的仓库

### 步骤 3：配置环境变量

在 Railway 项目设置中添加以下环境变量：

```env
# 数据库（Railway 会自动提供）
DATABASE_URL=${{Postgres.DATABASE_URL}}

# JWT 密钥（随机生成）
SECRET_KEY=your-secret-key-here-change-this

# 加密密钥（运行下面的命令生成）
# python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
ENCRYPTION_KEY=your-fernet-key-here

# Redis（Railway 插件提供）
REDIS_URL=${{Redis.REDIS_URL}}

# 环境
ENVIRONMENT=production
```

### 步骤 4：添加 PostgreSQL 和 Redis

在 Railway 项目中：
1. 点击 "Add Service" → "Database" → "PostgreSQL"
2. 点击 "Add Service" → "Database" → "Redis"
3. Railway 会自动注入 `DATABASE_URL` 和 `REDIS_URL`

### 步骤 5：部署后端

Railway 会自动检测到 Python 项目并部署。

**构建命令**：`pip install -r backend/requirements.txt`  
**启动命令**：`cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT`

### 步骤 6：部署前端（可选方案）

**方案 A：Railway 部署前端（推荐）**
- 在同一项目中创建新服务
- 根目录：`frontend/`
- 构建命令：`npm install && npm run build`
- 启动命令：`npm run preview -- --host 0.0.0.0 --port $PORT`

**方案 B：Vercel 部署前端（更快）**
1. 访问 https://vercel.com/
2. 导入 GitHub 仓库
3. Root Directory 设置为 `frontend`
4. 自动部署

---

## 简化版：先部署后端（5 分钟快速验证）

如果你想先快速验证后端是否正常：

### 使用 Render（更简单）

1. 访问 https://render.com/
2. 点击 "New" → "Web Service"
3. 连接 GitHub 仓库
4. 配置：
   - **Name**: slow-disease-system
   - **Root Directory**: backend
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Environment**: Python 3
5. 添加 PostgreSQL 数据库（Render 提供）
6. 点击 "Create Web Service"

---

## 当前项目需要修改的文件

### 1. 后端 requirements.txt

确保包含所有依赖：

```txt
fastapi
uvicorn[standard]
sqlalchemy
aiosqlite
asyncpg
pydantic
pydantic-settings
python-jose[cryptography]
passlib[bcrypt]
python-multipart
cryptography
redis
alembic
```

### 2. 后端环境变量处理

修改 `backend/app/db/session.py`：

```python
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Railway 会提供 DATABASE_URL（PostgreSQL 格式）
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./slow_disease.db")

# 如果是 PostgreSQL，需要转换格式
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)

engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
```

### 3. 前端 API 地址配置

修改 `frontend/src/api/request.ts`：

```typescript
import axios from 'axios'

const api = axios.create({
  // Railway 后端地址
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1',
  timeout: 10000,
})

export default api
```

创建 `frontend/.env.production`：

```env
VITE_API_URL=https://your-backend-url.railway.app/api/v1
```

---

## 预估成本

| 服务 | 免费额度 | 备注 |
|------|----------|------|
| Railway 后端 | $5/月 | 约 500 小时运行时间 |
| Railway PostgreSQL | 免费 | 1GB 存储 |
| Railway Redis | 免费 | 30MB 存储 |
| Vercel 前端 | 免费 | 无限制 |

**总计**：免费（个人项目完全够用）

---

## 下一步

我可以帮你：
1. ✅ 生成所需的配置文件
2. ✅ 修改代码以适配云环境
3. ✅ 生成加密密钥
4. ⏳ 需要你提供 GitHub 仓库地址（或我帮你创建）

**现在需要你做什么？**
- 回复你的 GitHub 用户名，我帮你生成完整的推送命令
- 或者告诉我你想先试试哪个平台（Railway/Render/Vercel）
