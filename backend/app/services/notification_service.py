"""
通知服务
支持：微信模板消息 / 短信（备用） / 站内信
当前先实现占位逻辑，后续接入真实通道
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
from datetime import datetime
from app.models import PatientWechat, AlertRecord, ReferralRecord, Patient
import logging

logger = logging.getLogger(__name__)

# 微信模板消息 ID（需前往微信公众平台配置）
TEMPLATE_REFERRAL_ACCEPTED = "tpl_referral_accepted"
TEMPLATE_REFERRAL_REJECTED = "tpl_referral_rejected"
TEMPLATE_REFERRAL_COMPLETED = "tpl_referral_completed"
TEMPLATE_ALERT = "tpl_alert"
TEMPLATE_FOLLOWUP_REMINDER = "tpl_fu_reminder"


class NotificationService:
    """
    统一通知入口
    调用方式：await NotificationService.notify_xxx(db, ...)
    """

    # ---------- 转诊通知 ----------

    @staticmethod
    async def notify_referral_accepted(
        db: AsyncSession,
        referral: ReferralRecord,
        receive_doctor_id: str,
    ) -> bool:
        """
        转诊被接受 → 通知申请医生
        """
        patient = await NotificationService._get_patient(db, referral.patient_id)
        patient_name = patient.name_enc if patient else referral.patient_id

        content = (
            f"【转诊更新】\n"
            f"患者：{patient_name}\n"
            f"转诊已被接收医生接受\n"
            f"请关注后续进展"
        )
        return await NotificationService._send(
            db, referral.patient_id, "REFERRAL_ACCEPTED", content
        )

    @staticmethod
    async def notify_referral_rejected(
        db: AsyncSession,
        referral: ReferralRecord,
        reason: str,
        receive_doctor_id: str,
    ) -> bool:
        """转诊被拒绝 → 通知申请医生"""
        patient = await NotificationService._get_patient(db, referral.patient_id)
        patient_name = patient.name_enc if patient else referral.patient_id

        content = (
            f"【转诊被拒绝】\n"
            f"患者：{patient_name}\n"
            f"原因：{reason}\n"
            f"请重新评估或联系接收机构"
        )
        return await NotificationService._send(
            db, referral.patient_id, "REFERRAL_REJECTED", content
        )

    @staticmethod
    async def notify_referral_completed(
        db: AsyncSession,
        referral: ReferralRecord,
        complete_doctor_id: str,
    ) -> bool:
        """转诊完成 → 通知申请医生（可安排下转/随访）"""
        patient = await NotificationService._get_patient(db, referral.patient_id)
        patient_name = patient.name_enc if patient else referral.patient_id

        content = (
            f"【转诊完成】\n"
            f"患者：{patient_name}\n"
            f"转诊已闭环完成\n"
            f"建议：7天内安排转诊后随访"
        )
        return await NotificationService._send(
            db, referral.patient_id, "REFERRAL_COMPLETED", content
        )

    # ---------- 预警通知 ----------

    @staticmethod
    async def notify_alert(
        db: AsyncSession,
        patient_id: str,
        alert_type: str,
        message: str,
    ) -> bool:
        """预警通知（血压/血糖异常等）"""
        content = f"【健康预警】\n{message}"
        return await NotificationService._send(
            db, patient_id, "ALERT", content
        )

    # ---------- 随访提醒 ----------

    @staticmethod
    async def notify_followup_reminder(
        db: AsyncSession,
        patient_id: str,
        followup_date: datetime,
    ) -> bool:
        """随访即将到期提醒"""
        patient = await NotificationService._get_patient(db, patient_id)
        patient_name = patient.name_enc if patient else patient_id

        content = (
            f"【随访提醒】\n"
            f"患者：{patient_name}\n"
            f"下次随访日期：{followup_date.strftime('%Y-%m-%d')}\n"
            f"请及时完成随访"
        )
        return await NotificationService._send(
            db, patient_id, "FOLLOWUP_REMINDER", content
        )

    # ---------- 内部方法 ----------

    @staticmethod
    async def _get_patient(db: AsyncSession, patient_id: str):
        from app.models import Patient
        result = await db.execute(
            select(Patient).where(Patient.patient_id == patient_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def _send(
        db: AsyncSession,
        patient_id: str,
        notification_type: str,
        content: str,
    ) -> bool:
        """
        统一发送入口
        当前实现：写 alert_record 表（站内信），后续接入微信/短信
        返回：是否发送成功
        """
        try:
            # 1. 查询患者是否绑定微信
            wx_result = await db.execute(
                select(PatientWechat).where(
                    PatientWechat.patient_id == patient_id,
                    PatientWechat.is_active == True,
                )
            )
            wx_bind = wx_result.scalar_one_or_none()

            # 2. 如果绑定了微信，尝试发送模板消息（当前占位）
            if wx_bind:
                logger.info(
                    f"[微信通知占位] openid={wx_bind.openid}, "
                    f"type={notification_type}, content={content[:50]}..."
                )
                # TODO: 接入真实微信模板消息 API
                # await WechatService.send_template_message(
                #     openid=wx_bind.openid,
                #     template_id=...,
                #     data=...,
                # )

            # 3. 同时写入 alert_record（站内信/预警中心）
            from uuid import uuid4
            from app.models import AlertRecord
            alert = AlertRecord(
                alert_id=str(uuid4()),
                patient_id=patient_id,
                alert_type=notification_type,
                severity="MEDIUM",
                message=content,
                is_handled=False,
                created_at=datetime.now(),
            )
            db.add(alert)
            await db.commit()

            logger.info(f"通知已发送：{notification_type} -> {patient_id}")
            return True

        except Exception as e:
            logger.error(f"通知发送失败：{e}", exc_info=True)
            return False

    @staticmethod
    async def send_template_message(
        openid: str,
        template_id: str,
        data: dict,
        url: Optional[str] = None,
    ) -> bool:
        """
        微信模板消息发送（占位实现）
        后续接入：https://api.weixin.qq.com/cgi-bin/message/template/send
        """
        logger.info(
            f"[微信模板消息占位] openid={openid}, "
            f"template_id={template_id}, data={data}"
        )
        # TODO: 真实调用微信 API
        return True
