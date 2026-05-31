"""
专病管理 API — 为 Dashboard / 专病详情页提供病种级别的聚合数据
GET /api/v1/disease/{type}           → 总览
GET /api/v1/disease/{type}/patients  → 患者列表（带专病字段）
GET /api/v1/disease/{type}/stats     → 病种统计
GET /api/v1/disease/{type}/followups → 专病随访
"""
from fastapi import APIRouter, Depends, Query
from typing import Optional
from datetime import date

from app.dependencies.auth import get_current_active_user
from app.db.session import get_db

router = APIRouter(prefix="/disease", tags=["专病管理"])

VALID_TYPES = {
    "hypertension": {"table": "disease_hypertension", "icd": "I10", "name": "高血压"},
    "diabetes":     {"table": "disease_diabetes",   "icd": "E11", "name": "糖尿病"},
    "chd":          {"table": "disease_coronary_heart_disease", "icd": "I20", "name": "冠心病"},
    "stroke":       {"table": "disease_stroke",       "icd": "I63", "name": "脑卒中"},
    "copd":         {"table": "disease_copd",         "icd": "J44", "name": "慢阻肺"},
    "ckd":          {"table": "disease_ckd",          "icd": "N18", "name": "慢性肾脏病"},
}


@router.get("/{disease_type}")
async def disease_overview(
    disease_type: str,
    org_code: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_active_user),
):
    """病种总览：患者数、达标率、风险分布、最近随访"""
    import sqlite3
    from app.config import settings

    if disease_type not in VALID_TYPES:
        return {"error": f"不支持的病种类型: {disease_type}", "valid_types": list(VALID_TYPES.keys())}
    cfg = VALID_TYPES[disease_type]
    table = cfg["table"]

    db_path = str(settings.DATABASE_URL).split(":///", 1)[1] if ":///" in str(settings.DATABASE_URL) else "slow_disease.db"
    conn = sqlite3.connect(db_path or "slow_disease.db")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # 专病表记录数
    org_filter = ""
    org_params = []
    if org_code:
        # 患者表筛选机构
        q = "SELECT patient_id FROM patient WHERE manage_org_code LIKE ?"
        org_filter = " AND patient_id IN (SELECT patient_id FROM patient WHERE manage_org_code LIKE ?)"
        org_params = [org_code + "%"]

    cur.execute(f"SELECT COUNT(*) FROM {cfg['table']} WHERE is_active = 1{org_filter}", org_params)
    total = cur.fetchone()[0]

    # 患者总数（含该ICD码）
    cur.execute(
        f"SELECT COUNT(*) FROM {cfg['table']} d JOIN patient p ON d.patient_id = p.patient_id WHERE d.is_active = 1{org_filter}",
        org_params,
    )
    patient_count = cur.fetchone()[0]

    # 达标率 — 不同病种不同指标
    control_rate = _calc_control(cur, disease_type, cfg, org_filter, org_params)

    # 风险分布
    cur.execute(
        f"SELECT p.risk_level, COUNT(*) cnt FROM {cfg['table']} d JOIN patient p ON d.patient_id = p.patient_id WHERE d.is_active = 1{org_filter} AND p.risk_level IS NOT NULL GROUP BY p.risk_level",
        org_params,
    )
    risk_dist = {r["risk_level"]: r["cnt"] for r in cur.fetchall()}

    conn.close()
    return {
        "disease_type": disease_type,
        "disease_name": cfg["name"],
        "total_patients": patient_count,
        "special_table_count": total,
        "control_rate": control_rate,
        "risk_distribution": risk_dist,
    }


def _calc_control(cur, dtype, cfg, org_filter, org_params):
    """计算病种达标率"""
    try:
        if dtype == "hypertension":
            cur.execute(
                f"SELECT AVG(CASE WHEN target_sbp IS NOT NULL AND target_dbp IS NOT NULL THEN 100.0 ELSE 0 END) AS r FROM {cfg['table']} WHERE is_active=1{org_filter}",
                org_params,
            )
            r = cur.fetchone()
            return round(r["r"] or 0, 1)
        elif dtype in ("diabetes",):
            cur.execute(
                f"SELECT AVG(CASE WHEN hba1c_at_diagnosis <= 7.0 THEN 100.0 ELSE 0 END) AS r FROM {cfg['table']} WHERE is_active=1{org_filter}",
                org_params,
            )
            r = cur.fetchone()
            return round(r["r"] or 0, 1)
        elif dtype == "chd":
            cur.execute(
                f"SELECT AVG(CASE WHEN ldl_c <= 1.8 THEN 100.0 ELSE 0 END) AS r FROM {cfg['table']} WHERE is_active=1{org_filter}",
                org_params,
            )
            r = cur.fetchone()
            return round(r["r"] or 0, 1)
        elif dtype == "stroke":
            cur.execute(
                f"SELECT AVG(CASE WHEN mrs_score <= 2 THEN 100.0 ELSE 0 END) AS r FROM {cfg['table']} WHERE is_active=1{org_filter}",
                org_params,
            )
            r = cur.fetchone()
            return round(r["r"] or 0, 1)
        elif dtype == "copd":
            cur.execute(
                f"SELECT AVG(CASE WHEN cat_score < 10 THEN 100.0 ELSE 0 END) AS r FROM {cfg['table']} WHERE is_active=1{org_filter}",
                org_params,
            )
            r = cur.fetchone()
            return round(r["r"] or 0, 1)
        elif dtype == "ckd":
            cur.execute(
                f"SELECT AVG(CASE WHEN egfr >= 60 THEN 100.0 ELSE 0 END) AS r FROM {cfg['table']} WHERE is_active=1{org_filter}",
                org_params,
            )
            r = cur.fetchone()
            return round(r["r"] or 0, 1)
    except Exception:
        pass
    return 0.0


@router.get("/{disease_type}/patients")
async def disease_patients(
    disease_type: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    keyword: Optional[str] = Query(None),
    risk_level: Optional[str] = Query(None),
    org_code: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_active_user),
):
    """病种患者列表（含专病表字段）"""
    import sqlite3
    from app.config import settings

    if disease_type not in VALID_TYPES:
        return {"error": f"不支持的病种类型: {disease_type}"}
    cfg = VALID_TYPES[disease_type]
    table = cfg["table"]

    db_path = str(settings.DATABASE_URL).split(":///", 1)[1] if ":///" in str(settings.DATABASE_URL) else "slow_disease.db"
    conn = sqlite3.connect(db_path or "slow_disease.db")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    where = []
    params = []

    if keyword:
        where.append("(p.patient_id LIKE ?)")
        params.extend([f"%{keyword}%"])
    if risk_level:
        where.append("p.risk_level = ?")
        params.append(risk_level)
    if org_code:
        where.append("p.manage_org_code LIKE ?")
        params.append(org_code + "%")

    wsql = " AND ".join(where) if where else "1=1"

    # 确定专病表 JOIN 与额外字段（必须在 COUNT 和 SELECT 之前定义）
    extra_cols = ""
    join_clause = ""
    if disease_type == "hypertension":
        extra_cols = ", dh.risk_stratification AS bp_risk, dh.ecg_result, dh.echo_result"
        join_clause = f"JOIN disease_hypertension dh ON p.patient_id = dh.patient_id"
    elif disease_type == "diabetes":
        extra_cols = ", dd.hba1c_at_diagnosis AS hba1c, dd.diagnosis_type AS dm_type"
        join_clause = f"JOIN disease_diabetes dd ON p.patient_id = dd.patient_id"
    elif disease_type == "chd":
        extra_cols = ", dch.target_ldl_c AS ldl_c, dch.timi_risk AS chd_risk, dch.grace_risk"
        join_clause = f"JOIN disease_coronary_heart_disease dch ON p.patient_id = dch.patient_id"
    elif disease_type == "stroke":
        extra_cols = ", ds.nihss_score, ds.mrs_score, ds.barthel_index"
        join_clause = f"JOIN disease_stroke ds ON p.patient_id = ds.patient_id"
    elif disease_type == "copd":
        extra_cols = ", dco.fev1_percent, dco.cat_score, dco.exacerbation_count"
        join_clause = f"JOIN disease_copd dco ON p.patient_id = dco.patient_id"
    elif disease_type == "ckd":
        extra_cols = ", dck.egfr, dck.ckd_stage, dck.ckd_risk_level"
        join_clause = f"JOIN disease_ckd dck ON p.patient_id = dck.patient_id"

    # Count（JOIN 病种表，只统计该病种患者）
    cur.execute(f"SELECT COUNT(*) FROM patient p {join_clause} WHERE {wsql}", params)
    total = cur.fetchone()[0]

    offset = (page - 1) * page_size
    cur.execute(
        f"SELECT p.patient_id, p.name_enc AS name, p.gender, p.age, p.village_code, p.risk_level, "
        f"p.manage_org_code, p.phone_enc AS phone{extra_cols} "
        f"FROM patient p {join_clause} "
        f"WHERE {wsql} ORDER BY p.risk_level DESC, p.patient_id LIMIT ? OFFSET ?",
        params + [page_size, offset],
    )
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()

    return {"items": rows, "total": total, "page": page, "page_size": page_size}


@router.get("/{disease_type}/stats")
async def disease_stats(
    disease_type: str,
    org_code: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_active_user),
):
    """病种核心指标统计"""
    import sqlite3
    from app.config import settings

    if disease_type not in VALID_TYPES:
        return {"error": f"不支持的病种类型: {disease_type}"}
    cfg = VALID_TYPES[disease_type]
    table = cfg["table"]

    db_path = str(settings.DATABASE_URL).split(":///", 1)[1] if ":///" in str(settings.DATABASE_URL) else "slow_disease.db"
    conn = sqlite3.connect(db_path or "slow_disease.db")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    org_filter = ""
    org_params = []
    if org_code:
        org_filter = " AND patient_id IN (SELECT patient_id FROM patient WHERE org_code LIKE ?)"
        org_params = [org_code + "%"]

    table = cfg["table"]

    stats = {}

    if disease_type == "hypertension":
        cur.execute(f"SELECT AVG(target_sbp) avg_sbp, AVG(target_dbp) avg_dbp, COUNT(*) total FROM {table} WHERE is_active=1{org_filter}", org_params)
        r = cur.fetchone()
        stats = {"avg_target_sbp": round(r["avg_sbp"], 1) if r["avg_sbp"] else None, "avg_target_dbp": round(r["avg_dbp"], 1) if r["avg_dbp"] else None, "total": r["total"]}
    elif disease_type == "diabetes":
        cur.execute(f"SELECT AVG(hba1c_at_diagnosis) avg_hba1c, COUNT(*) total FROM {table} WHERE is_active=1{org_filter}", org_params)
        r = cur.fetchone()
        stats = {"avg_hba1c": round(r["avg_hba1c"], 1) if r["avg_hba1c"] else None, "total": r["total"]}
    elif disease_type == "chd":
        cur.execute(f"SELECT AVG(target_ldl_c) avg_ldl, COUNT(*) total FROM {table} WHERE is_active=1{org_filter}", org_params)
        r = cur.fetchone()
        stats = {"avg_ldl_c": round(r["avg_ldl"], 2) if r["avg_ldl"] else None, "total": r["total"]}
    elif disease_type == "stroke":
        cur.execute(f"SELECT AVG(nihss_score) avg_nihss, AVG(mrs_score) avg_mrs, COUNT(*) total FROM {table} WHERE is_active=1{org_filter}", org_params)
        r = cur.fetchone()
        stats = {"avg_nihss": round(r["avg_nihss"], 1) if r["avg_nihss"] else None, "avg_mrs": round(r["avg_mrs"], 1) if r["avg_mrs"] else None, "total": r["total"]}
    elif disease_type == "copd":
        cur.execute(f"SELECT AVG(fev1_percent) avg_fev1, AVG(cat_score) avg_cat, SUM(exacerbation_count) total_exacerbations, COUNT(*) total FROM {table} WHERE is_active=1{org_filter}", org_params)
        r = cur.fetchone()
        stats = {"avg_fev1": round(r["avg_fev1"], 1) if r["avg_fev1"] else None, "avg_cat": round(r["avg_cat"], 1) if r["avg_cat"] else None, "total_exacerbations": r["total_exacerbations"] or 0, "total": r["total"]}
    elif disease_type == "ckd":
        cur.execute(f"SELECT AVG(egfr) avg_egfr, COUNT(*) total FROM {table} WHERE is_active=1{org_filter}", org_params)
        r = cur.fetchone()
        stats = {"avg_egfr": round(r["avg_egfr"], 1) if r["avg_egfr"] else None, "total": r["total"]}

    conn.close()
    return stats


@router.get("/{disease_type}/followups")
async def disease_followups(
    disease_type: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    org_code: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_active_user),
):
    """病种随访记录"""
    import sqlite3
    from app.config import settings

    if disease_type not in VALID_TYPES:
        return {"error": f"不支持的病种类型: {disease_type}"}
    cfg = VALID_TYPES[disease_type]
    table = cfg["table"]

    db_path = str(settings.DATABASE_URL).split(":///", 1)[1] if ":///" in str(settings.DATABASE_URL) else "slow_disease.db"
    conn = sqlite3.connect(db_path or "slow_disease.db")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    where = []
    params = []

    if org_code:
        where.append("p.manage_org_code LIKE ?")
        params.append(org_code + "%")

    wsql = " AND ".join(where) if where else "1=1"

    cur.execute(
        f"SELECT f.followup_id, f.patient_id, p.patient_id AS patient_name, f.followup_date, "
        f"f.followup_type, f.bp_systolic, f.bp_diastolic, f.fbg, f.performed_by, f.symptoms as notes "
        f"FROM followup_record f "
        f"JOIN patient p ON f.patient_id = p.patient_id "
        f"JOIN {table} d ON f.patient_id = d.patient_id "
        f"WHERE d.is_active = 1{' AND ' + wsql if wsql != '1=1' else ''} ORDER BY f.followup_date DESC LIMIT ? OFFSET ?",
        params + [page_size, (page - 1) * page_size],
    )
    items = [dict(r) for r in cur.fetchall()]

    cur.execute(
        f"SELECT COUNT(*) FROM followup_record f "
        f"JOIN patient p ON f.patient_id = p.patient_id "
        f"JOIN {table} d ON f.patient_id = d.patient_id "
        f"WHERE d.is_active = 1{' AND ' + wsql if wsql != '1=1' else ''}",
        params,
    )
    total = cur.fetchone()[0]
    conn.close()

    return {"items": items, "total": total, "page": page, "page_size": page_size}
