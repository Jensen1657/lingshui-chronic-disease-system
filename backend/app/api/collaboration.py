"""
县乡协同管理 API
机构对比、排名、县乡数据同步
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import Optional
from datetime import date

from app.db.session import get_db
from app.models import KpiOrgStats, Patient, DimRegion

router = APIRouter()


@router.get("/org-ranking")
async def get_org_ranking(
    stats_period: str = Query("2026-05", description="统计周期，如 2026-05"),
    metric: str = Query("registration_rate", description="排序指标"),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """
    机构排名（按指定指标排序）
    可选指标: registration_rate, screening_rate, bp_controlled_rate, bg_controlled_rate, followup_completion_rate
    """
    # 获取列映射
    col_map = {
        "registration_rate": KpiOrgStats.registration_rate,
        "screening_rate": KpiOrgStats.screening_rate,
        "bp_controlled_rate": KpiOrgStats.bp_controlled_rate,
        "bg_controlled_rate": KpiOrgStats.bg_controlled_rate,
        "followup_completion_rate": KpiOrgStats.followup_completion_rate,
        "assessment_rate": KpiOrgStats.assessment_rate,
        "contract_rate": KpiOrgStats.contract_rate,
    }
    sort_col = col_map.get(metric, KpiOrgStats.registration_rate)

    q = (
        select(KpiOrgStats)
        .where(KpiOrgStats.stats_period == stats_period)
        .order_by(sort_col.desc())
        .limit(limit)
    )
    results = (await db.execute(q)).scalars().all()

    return [
        {
            "org_code": r.org_code,
            "region_code": r.region_code,
            "stats_period": r.stats_period,
            "total_patients": r.total_patients or 0,
            "registered_count": r.registered_count or 0,
            "registration_rate": float(r.registration_rate or 0),
            "screened_count": r.screened_count or 0,
            "screening_rate": float(r.screening_rate or 0),
            "bp_controlled_rate": float(r.bp_controlled_rate or 0),
            "bg_controlled_rate": float(r.bg_controlled_rate or 0),
            "followup_completion_rate": float(r.followup_completion_rate or 0),
        }
        for r in results
    ]


@router.get("/county-summary")
async def get_county_summary(
    db: AsyncSession = Depends(get_db),
):
    """县级汇总统计"""
    # 按区域汇总患者数
    q = (
        select(
            Patient.village_code,
            func.count().label("patient_count"),
        )
        .group_by(Patient.village_code)
    )
    results = (await db.execute(q)).all()

    region_map = {}
    region_q = select(DimRegion.region_code, DimRegion.region_name, DimRegion.org_name)
    for r in (await db.execute(region_q)).all():
        region_map[r.region_code] = {
            "region_name": r.region_name,
            "org_name": r.org_name,
        }

    summary = []
    for r in results:
        info = region_map.get(r.village_code, {})
        summary.append({
            "village_code": r.village_code,
            "region_name": info.get("region_name", ""),
            "org_name": info.get("org_name", ""),
            "patient_count": r.patient_count,
        })

    summary.sort(key=lambda x: x["patient_count"], reverse=True)
    return summary


@router.get("/org-comparison")
async def compare_orgs(
    org_codes: str = Query(..., description="机构代码，逗号分隔"),
    stats_period: str = Query("2026-05"),
    db: AsyncSession = Depends(get_db),
):
    """对比多个机构的核心指标"""
    codes = [c.strip() for c in org_codes.split(",")]
    q = select(KpiOrgStats).where(
        and_(
            KpiOrgStats.org_code.in_(codes),
            KpiOrgStats.stats_period == stats_period,
        )
    )
    results = (await db.execute(q)).scalars().all()

    return [
        {
            "org_code": r.org_code,
            "registration_rate": float(r.registration_rate or 0),
            "screening_rate": float(r.screening_rate or 0),
            "assessment_rate": float(r.assessment_rate or 0),
            "bp_controlled_rate": float(r.bp_controlled_rate or 0),
            "bg_controlled_rate": float(r.bg_controlled_rate or 0),
            "followup_completion_rate": float(r.followup_completion_rate or 0),
            "down_referral_count": r.down_referral_count or 0,
        }
        for r in results
    ]
