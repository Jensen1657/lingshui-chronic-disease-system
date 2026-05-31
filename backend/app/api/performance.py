"""
医护绩效考核 API
指标：随访数、控制率、用药依从率、患者管理数、质控审核、响应时效
"""
from fastapi import APIRouter, Depends, Query
from typing import Optional
from app.api.auth import get_current_active_user

router = APIRouter(prefix="/performance", tags=["绩效考核"])


@router.get("/overview")
async def performance_overview(
    period: Optional[str] = Query("month", description="统计周期: month/quarter/year"),
    org_code: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_active_user),
):
    """医护绩效考核总览"""
    import sqlite3
    from app.config import settings

    db_path = str(settings.DATABASE_URL).split(":///", 1)[1] if ":///" in str(settings.DATABASE_URL) else "slow_disease.db"
    conn = sqlite3.connect(db_path or "slow_disease.db")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    date_filter = {
        "month": "AND f.followup_date >= date('now', '-30 days')",
        "quarter": "AND f.followup_date >= date('now', '-90 days')",
        "year": "AND f.followup_date >= date('now', '-365 days')",
    }.get(period, "")

    org_filter = ""
    org_params = []
    if org_code:
        org_filter = "AND p.manage_org_code LIKE ?"
        org_params = [org_code + "%"]

    # 整体指标（所有随访都计入，is_controlled=1 视为达标）
    cur.execute(f"""
        SELECT
            COUNT(DISTINCT f.performed_by) AS total_staff,
            COUNT(DISTINCT f.patient_id) AS managed_patients,
            COUNT(f.followup_id) AS total_followups,
            ROUND(AVG(CASE WHEN f.is_controlled = 1 THEN 100.0 ELSE 0 END), 2) AS avg_control_rate
        FROM followup_record f
        JOIN patient p ON f.patient_id = p.patient_id
        WHERE 1=1 {date_filter} {org_filter}
    """, org_params)
    row = cur.fetchone()

    # 用药依从率（从 followup_record.medication_adherence）
    cur.execute(f"""
        SELECT
            COUNT(*) AS total_with_data,
            ROUND(AVG(CASE WHEN f.medication_adherence = 'good' THEN 100.0 ELSE 0 END), 2) AS avg_compliance_rate
        FROM followup_record f
        JOIN patient p ON f.patient_id = p.patient_id
        WHERE f.medication_adherence IS NOT NULL {date_filter} {org_filter}
    """, org_params)
    med_row = cur.fetchone()

    # 质控审核率
    cur.execute(f"""
        SELECT
            COUNT(*) AS total_followups,
            ROUND(AVG(CASE WHEN f.is_audited = 1 THEN 100.0 ELSE 0 END), 2) AS audit_rate
        FROM followup_record f
        JOIN patient p ON f.patient_id = p.patient_id
        WHERE 1=1 {date_filter} {org_filter}
    """, org_params)
    audit_row = cur.fetchone()

    # 预警处理时效
    cur.execute(f"""
        SELECT
            COUNT(a.alert_id) AS total_alerts,
            ROUND(AVG(CASE WHEN a.handled_at IS NOT NULL
                THEN (julianday(a.handled_at) - julianday(a.created_at)) * 24
                ELSE NULL END), 2) AS avg_resolve_hours
        FROM alert_record a
        JOIN patient p ON a.patient_id = p.patient_id
        WHERE 1=1 {'AND p.manage_org_code LIKE ?' if org_code else ''}
    """, org_params)
    alert_row = cur.fetchone()

    conn.close()
    return {
        "period": period,
        "total_staff": row["total_staff"] or 0,
        "managed_patients": row["managed_patients"] or 0,
        "total_followups": row["total_followups"] or 0,
        "avg_followup_completion_rate": row["avg_control_rate"] or 0,
        "avg_medication_compliance_rate": med_row["avg_compliance_rate"] or 0 if med_row else 0,
        "avg_audit_rate": audit_row["audit_rate"] or 0 if audit_row else 0,
        "total_alerts": alert_row["total_alerts"] or 0,
        "avg_alert_resolve_hours": alert_row["avg_resolve_hours"] or 0 if alert_row and alert_row["avg_resolve_hours"] else None,
    }


@router.get("/staff")
async def performance_staff_list(
    period: Optional[str] = Query("month"),
    org_code: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_active_user),
):
    """按医护人员维度的绩效考核排名"""
    import sqlite3
    from app.config import settings

    db_path = str(settings.DATABASE_URL).split(":///", 1)[1] if ":///" in str(settings.DATABASE_URL) else "slow_disease.db"
    conn = sqlite3.connect(db_path or "slow_disease.db")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    date_filter = {
        "month": "f.followup_date >= date('now', '-30 days')",
        "quarter": "f.followup_date >= date('now', '-90 days')",
        "year": "f.followup_date >= date('now', '-365 days')",
    }.get(period, "1=1")

    org_filter = ""
    org_params = []
    if org_code:
        org_filter = "AND p.manage_org_code LIKE ?"
        org_params = [org_code + "%"]

    cur.execute(f"""
        SELECT
            COALESCE(f.performed_by, '未分配') AS staff_name,
            COUNT(DISTINCT f.patient_id) AS managed_patients,
            COUNT(f.followup_id) AS total_followups,
            COUNT(CASE WHEN f.is_controlled = 1 THEN 1 END) AS controlled_followups,
            ROUND(
                CASE WHEN COUNT(f.followup_id) > 0
                THEN COUNT(CASE WHEN f.is_controlled = 1 THEN 1 END) * 100.0 / COUNT(f.followup_id)
                ELSE 0 END, 2
            ) AS completion_rate,
            COUNT(DISTINCT DATE(f.followup_date)) AS active_days,
            COALESCE(SUM(CASE WHEN f.is_audited = 1 THEN 1 ELSE 0 END), 0) AS audited_count
        FROM followup_record f
        JOIN patient p ON f.patient_id = p.patient_id
        WHERE {date_filter} {org_filter}
        GROUP BY f.performed_by
        ORDER BY completion_rate DESC, total_followups DESC
        LIMIT ? OFFSET ?
    """, org_params + [page_size, (page - 1) * page_size])

    items = [dict(r) for r in cur.fetchall()]

    cur.execute(f"""
        SELECT COUNT(DISTINCT f.performed_by) AS total
        FROM followup_record f
        JOIN patient p ON f.patient_id = p.patient_id
        WHERE {date_filter} {org_filter}
    """, org_params)
    total = cur.fetchone()["total"]

    conn.close()
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get("/staff/{staff_name:path}")
async def performance_staff_detail(
    staff_name: str,
    period: Optional[str] = Query("month"),
    current_user: dict = Depends(get_current_active_user),
):
    """单个医护人员详细绩效"""
    import sqlite3
    from app.config import settings

    db_path = str(settings.DATABASE_URL).split(":///", 1)[1] if ":///" in str(settings.DATABASE_URL) else "slow_disease.db"
    conn = sqlite3.connect(db_path or "slow_disease.db")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    date_filter = {
        "month": "f.followup_date >= date('now', '-30 days')",
        "quarter": "f.followup_date >= date('now', '-90 days')",
        "year": "f.followup_date >= date('now', '-365 days')",
    }.get(period, "1=1")

    cur.execute(f"""
        SELECT
            COALESCE(f.performed_by, '未分配') AS staff_name,
            COUNT(DISTINCT f.patient_id) AS managed_patients,
            COUNT(f.followup_id) AS total_followups,
            COUNT(CASE WHEN f.is_controlled = 1 THEN 1 END) AS controlled_followups,
            ROUND(
                CASE WHEN COUNT(f.followup_id) > 0
                THEN COUNT(CASE WHEN f.is_controlled = 1 THEN 1 END) * 100.0 / COUNT(f.followup_id)
                ELSE 0 END, 2
            ) AS completion_rate,
            COUNT(DISTINCT DATE(f.followup_date)) AS active_days,
            COALESCE(SUM(CASE WHEN f.is_audited = 1 THEN 1 ELSE 0 END), 0) AS audited_count
        FROM followup_record f
        WHERE f.performed_by = ? AND {date_filter}
    """, [staff_name])
    stats = dict(cur.fetchone() or {})

    # 每日随访趋势
    cur.execute(f"""
        SELECT DATE(f.followup_date) AS date, COUNT(*) AS count
        FROM followup_record f
        WHERE f.performed_by = ? AND {date_filter}
        GROUP BY DATE(f.followup_date)
        ORDER BY date DESC LIMIT 30
    """, [staff_name])
    daily = [dict(r) for r in cur.fetchall()]

    # 管理的患者风险分布
    cur.execute(f"""
        SELECT p.risk_level, COUNT(*) AS count
        FROM followup_record f
        JOIN patient p ON f.patient_id = p.patient_id
        WHERE f.performed_by = ? AND {date_filter}
        GROUP BY p.risk_level
    """, [staff_name])
    risk_dist = {r["risk_level"] or "未知": r["count"] for r in cur.fetchall()}

    conn.close()
    return {"stats": stats, "daily_trend": daily, "risk_distribution": risk_dist}
