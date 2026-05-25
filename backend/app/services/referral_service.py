"""
双向转诊闭环服务
包含：转诊资格校验、自动追踪、超时预警、随访关联
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from typing import List, Optional, Dict, Any, Tuple
from uuid import uuid4
from datetime import date, datetime, timedelta

from app.models import ReferralRecord, Patient, FollowupRecord, AlertRecord


# 转诊超时阈值（小时）
UP_REFERRAL_TIMEOUT_HOURS = 48    # 上转：48小时内接收机构响应
DOWN_REFERRAL_TIMEOUT_HOURS = 24  # 下转：24小时内基层机构确认
POST_FU_DEADLINE_DAYS = 7         # 转诊后随访截止天数


class ReferralService:

    # ---------- 资格校验 ----------

    @staticmethod
    async def check_eligibility(
        db: AsyncSession,
        patient_id: str,
        disease_code: str,
        referral_type: str
    ) -> Dict[str, Any]:
        """
        校验转诊资格，返回 is_eligible + reason + match_criteria
        """
        patient_result = await db.execute(
            select(Patient).where(Patient.patient_id == patient_id)
        )
        patient = patient_result.scalar_one_or_none()
        if not patient:
            return {"is_eligible": False, "reason": "患者不存在", "match_criteria": {}}

        criteria = {}
        reasons = []
        eligible = True

        # 规则1：同一患者 30 天内不能重复上转同一病种
        if referral_type == "UP":
            cutoff = datetime.now() - timedelta(days=30)
            dup_q = select(func.count()).select_from(ReferralRecord).where(
                and_(
                    ReferralRecord.patient_id == patient_id,
                    ReferralRecord.disease_code == disease_code,
                    ReferralRecord.referral_type == "UP",
                    ReferralRecord.status.in_(["PENDING", "ACCEPTED", "COMPLETED"]),
                    ReferralRecord.apply_at >= cutoff,
                )
            )
            dup_count = (await db.execute(dup_q)).scalar_one()
            if dup_count > 0:
                eligible = False
                reasons.append(f"30天内已有{dup_count}条同类上转记录")
            criteria["duplicate_30d"] = dup_count

        # 规则2：下转必须有已接受的上转记录
        if referral_type == "DOWN":
            up_q = select(func.count()).select_from(ReferralRecord).where(
                and_(
                    ReferralRecord.patient_id == patient_id,
                    ReferralRecord.disease_code == disease_code,
                    ReferralRecord.referral_type == "UP",
                    ReferralRecord.status == "COMPLETED",
                )
            )
            up_count = (await db.execute(up_q)).scalar_one()
            if up_count == 0:
                eligible = False
                reasons.append("无已完成的上转记录，不满足下转条件")
            criteria["completed_up_count"] = up_count

        # 规则3：患者必须是建档患者
        criteria["is_archived"] = getattr(patient, "is_archived", False)
        if not getattr(patient, "is_archived", True):
            reasons.append("患者未完成建档")

        return {
            "is_eligible": eligible,
            "reason": "；".join(reasons) if reasons else "符合转诊条件",
            "match_criteria": criteria,
        }

    # ---------- 闭环追踪 ----------

    @staticmethod
    async def track_referrals(db: AsyncSession) -> List[Dict[str, Any]]:
        """
        扫描所有 PENDING/ACCEPTED 转诊，检查超时
        返回需要预警的转诊列表
        """
        now = datetime.now()
        alerts = []

        # 上转超时
        up_cutoff = now - timedelta(hours=UP_REFERRAL_TIMEOUT_HOURS)
        up_q = select(ReferralRecord).where(
            and_(
                ReferralRecord.referral_type == "UP",
                ReferralRecord.status == "PENDING",
                ReferralRecord.apply_at < up_cutoff,
                ReferralRecord.timeout_alert_sent == False,
            )
        )
        for r in (await db.execute(up_q)).scalars().all():
            alerts.append({
                "referral_id": r.referral_id,
                "patient_id": r.patient_id,
                "alert_type": "UP_TIMEOUT",
                "message": f"上转已超过{UP_REFERRAL_TIMEOUT_HOURS}小时未响应",
                "apply_at": str(r.apply_at),
                "hours_elapsed": int((now - r.apply_at).total_seconds() / 3600),
            })

        # 下转超时
        down_cutoff = now - timedelta(hours=DOWN_REFERRAL_TIMEOUT_HOURS)
        down_q = select(ReferralRecord).where(
            and_(
                ReferralRecord.referral_type == "DOWN",
                ReferralRecord.status == "ACCEPTED",
                ReferralRecord.receive_at < down_cutoff,
                ReferralRecord.timeout_alert_sent == False,
            )
        )
        for r in (await db.execute(down_q)).scalars().all():
            alerts.append({
                "referral_id": r.referral_id,
                "patient_id": r.patient_id,
                "alert_type": "DOWN_TIMEOUT",
                "message": f"下转已超过{DOWN_REFERRAL_TIMEOUT_HOURS}小时基层未确认",
                "receive_at": str(r.receive_at),
                "hours_elapsed": int((now - r.receive_at).total_seconds() / 3600),
            })

        return alerts

    @staticmethod
    async def generate_timeout_alerts(db: AsyncSession) -> int:
        """
        自动生成超时预警记录到 alert_record 表
        返回生成的预警数量
        """
        alerts = await ReferralService.track_referrals(db)
        count = 0
        for a in alerts:
            alert = AlertRecord(
                alert_id=str(uuid4()),
                patient_id=a["patient_id"],
                alert_type="REFERRAL_TIMEOUT",
                alert_level="HIGH",
                alert_title="转诊超时预警",
                alert_content=a["message"],
                is_handled=False,
            )
            db.add(alert)

            # 标记已发送
            ref_result = await db.execute(
                select(ReferralRecord).where(
                    ReferralRecord.referral_id == a["referral_id"]
                )
            )
            ref = ref_result.scalar_one_or_none()
            if ref:
                ref.timeout_alert_sent = True

            count += 1

        if count > 0:
            await db.commit()
        return count

    # ---------- 随访关联 ----------

    @staticmethod
    async def check_post_fu_deadline(db: AsyncSession) -> List[Dict[str, Any]]:
        """
        检查已完成转诊但尚未关联随访的记录（7天内需完成）
        """
        cutoff = datetime.now() - timedelta(days=POST_FU_DEADLINE_DAYS)
        q = select(ReferralRecord).where(
            and_(
                ReferralRecord.status == "COMPLETED",
                ReferralRecord.completed_at.isnot(None),
                ReferralRecord.completed_at < cutoff,
                ReferralRecord.post_referral_fu_id.is_(None),
            )
        )
        return [
            {
                "referral_id": r.referral_id,
                "patient_id": r.patient_id,
                "completed_at": str(r.completed_at),
                "overdue_days": (datetime.now() - r.completed_at).days,
                "message": f"转诊后随访已逾期{(datetime.now() - r.completed_at).days}天",
            }
            for r in (await db.execute(q)).scalars().all()
        ]

    @staticmethod
    async def link_followup(
        db: AsyncSession,
        referral_id: str,
        followup_id: str
    ) -> Dict[str, Any]:
        """将随访记录关联到已完成转诊"""
        ref_result = await db.execute(
            select(ReferralRecord).where(ReferralRecord.referral_id == referral_id)
        )
        ref = ref_result.scalar_one_or_none()
        if not ref:
            return {"success": False, "message": "转诊记录不存在"}
        if ref.status != "COMPLETED":
            return {"success": False, "message": "只能关联已完成的转诊"}

        fu_result = await db.execute(
            select(FollowupRecord).where(FollowupRecord.followup_id == followup_id)
        )
        fu = fu_result.scalar_one_or_none()
        if not fu:
            return {"success": False, "message": "随访记录不存在"}

        ref.post_referral_fu_id = followup_id
        await db.commit()
        return {"success": True, "message": "随访关联成功", "followup_id": followup_id}

    # ---------- 统计 ----------

    @staticmethod
    async def get_referral_stats(
        db: AsyncSession,
        org_code: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """转诊闭环统计"""
        base_filter = []
        if start_date:
            base_filter.append(ReferralRecord.apply_at >= start_date)
        if end_date:
            base_filter.append(ReferralRecord.apply_at <= end_date)
        if org_code:
            base_filter.append(
                or_(
                    ReferralRecord.apply_org_code == org_code,
                    ReferralRecord.receive_org_code == org_code,
                )
            )

        async def _count(status=None, ref_type=None):
            f = list(base_filter)
            if status:
                f.append(ReferralRecord.status == status)
            if ref_type:
                f.append(ReferralRecord.referral_type == ref_type)
            q = select(func.count()).select_from(ReferralRecord)
            if f:
                q = q.where(and_(*f))
            return (await db.execute(q)).scalar_one()

        total = await _count()
        up = await _count(ref_type="UP")
        down = await _count(ref_type="DOWN")
        pending = await _count(status="PENDING")
        accepted = await _count(status="ACCEPTED")
        completed = await _count(status="COMPLETED")
        rejected = await _count(status="REJECTED")

        # 有随访关联的已完成转诊
        linked_q = select(func.count()).select_from(ReferralRecord).where(
            and_(
                ReferralRecord.status == "COMPLETED",
                ReferralRecord.post_referral_fu_id.isnot(None),
            )
        )
        linked = (await db.execute(linked_q)).scalar_one()

        # 超时预警数
        timeout_q = select(func.count()).select_from(ReferralRecord).where(
            ReferralRecord.timeout_alert_sent == True
        )
        timeout_alerts = (await db.execute(timeout_q)).scalar_one()

        return {
            "total_referrals": total,
            "up_referrals": up,
            "down_referrals": down,
            "pending_count": pending,
            "accepted_count": accepted,
            "completed_count": completed,
            "rejected_count": rejected,
            "completion_rate": round(completed / total * 100, 1) if total > 0 else 0,
            "fu_linked_count": linked,
            "fu_link_rate": round(linked / completed * 100, 1) if completed > 0 else 0,
            "timeout_alert_count": timeout_alerts,
        }
