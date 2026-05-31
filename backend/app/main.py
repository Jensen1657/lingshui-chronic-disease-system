"""
FastAPI 主应用入口
慢性病管理系统 - 陵水县人民医院
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pathlib import Path
from app.config import settings
from app.db.session import engine, Base
from app.middleware.audit_log import AuditLogMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时：创建数据库表
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # 关闭时：清理资源（如需要）


# 创建 FastAPI 应用
app = FastAPI(
    title="慢性病管理系统",
    description="陵水县人民医院慢性病健康管理系统",
    version="1.0.0",
    redirect_slashes=False,  # axios 不跟随 307 重定向，必须关闭
    lifespan=lifespan
)

# CORS 配置（修正拼写错误：allow_origins → allow_origins）
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 审计日志中间件（自动记录所有 API 请求）
app.add_middleware(AuditLogMiddleware)

# 健康检查
@app.get("/health")
async def health_check():
    return {"status": "ok", "message": "慢性病管理系统运行正常"}


# 根路径
@app.get("/")
async def root():
    frontend_dist = Path(__file__).parent.parent.parent / "frontend" / "dist"
    index_file = frontend_dist / "index.html"
    if index_file.exists():
        return HTMLResponse(content=index_file.read_text(encoding="utf-8"))
    return {
        "system": "慢性病管理系统",
        "version": "1.0.0",
        "hospital": "陵水县人民医院",
        "docs": "/docs",
        "openapi": "/openapi.json"
    }


# 导入路由
from app.api import auth, patient
app.include_router(auth.router, prefix="/api/v1/auth", tags=["认证"])
app.include_router(patient.router, prefix="/api/v1/patients", tags=["患者管理"])

# 导入其他路由
from app.api import followup, referral
app.include_router(followup.router, prefix="/api/v1/followups", tags=["随访管理"])
app.include_router(referral.router, prefix="/api/v1/referrals", tags=["双向转诊"])

# 导入年度评估路由
from app.api import assessment
app.include_router(assessment.router, prefix="/api/v1/assessments", tags=["年度评估"])

# 导入预警管理路由
from app.api import alert
app.include_router(alert.router, prefix="/api/v1/alerts", tags=["预警管理"])

# 导入中医管理路由
from app.api import tcm
app.include_router(tcm.router, prefix="/api/v1/tcm", tags=["中医管理"])

# 导入急救联动路由
from app.api import emergency
app.include_router(emergency.router, prefix="/api/v1/emergency", tags=["急救联动"])

# 导入患者自主上报路由
from app.api import self_report
app.include_router(self_report.router, prefix="/api/v1/self-reports", tags=["患者自主上报"])

# 导入随访提醒路由
from app.api import reminder
app.include_router(reminder.router, prefix="/api/v1/reminders", tags=["随访提醒"])

# 导入微信绑定路由
from app.api import wechat
app.include_router(wechat.router, prefix="/api/v1/wechat", tags=["微信绑定"])
from app.api.dashboard import router as dashboard_router
app.include_router(dashboard_router, prefix="/api/v1/dashboard")

# 导入临床评分路由（评估报告要求：6类慢病评分工具）
from app.api import scoring
app.include_router(scoring.router, prefix="/api/v1/scoring")

# 导入质控校验路由（评估报告要求：必填/逻辑/真实性校验）
from app.api import quality_control, collaboration, audit_log
app.include_router(quality_control.router, prefix="/api/v1/quality-control")
app.include_router(collaboration.router, prefix="/api/v1/collaboration", tags=["县乡协同"])
app.include_router(audit_log.router, prefix="/api/v1/audit-logs")

from app.api import user_admin
app.include_router(user_admin.router, prefix="/api/v1/admin", tags=["用户管理"])

# 会议纪要新功能路由
from app.api import medication, health_education, prescription_review, risk_assessment
from app.api.disease import router as disease_router
from app.api.performance import router as performance_router
app.include_router(medication.router, prefix="/api/v1/medications", tags=["用药记录"])
app.include_router(health_education.router, prefix="/api/v1/health-education", tags=["健康宣教"])
app.include_router(prescription_review.router, prefix="/api/v1/prescription-reviews", tags=["处方审核"])
app.include_router(risk_assessment.router, prefix="/api/v1/risk-assessment", tags=["风险评估"])
app.include_router(disease_router, prefix="/api/v1", tags=["专病管理"])
app.include_router(performance_router, prefix="/api/v1", tags=["绩效考核"])

# ============ 前端静态文件服务 ============
import os
# 前端构建产物目录（相对于 backend/）
frontend_dist = Path(__file__).parent.parent.parent / "frontend" / "dist"
if frontend_dist.exists():
    # 服务静态文件（JS/CSS/图片等）
    app.mount("/assets", StaticFiles(directory=frontend_dist / "assets"), name="assets")
    
    # SPA 兜底：非 API 的 GET 请求返回 index.html
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # 排除 API 路径（避免捕获 /api/v1/* 的 GET 请求）
        if full_path.startswith("api/"):
            from fastapi.responses import JSONResponse
            return JSONResponse({"detail": f"API 端点不存在: /{full_path}"}, status_code=404)
        index_file = frontend_dist / "index.html"
        if index_file.exists():
            return HTMLResponse(content=index_file.read_text(encoding="utf-8"))
        return {"error": "前端未构建，请运行 npm run build"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
