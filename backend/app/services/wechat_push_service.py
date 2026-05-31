"""
微信模板消息推送服务
基于微信公众号模板消息 API 或模拟推送（开发/测试环境）
"""
import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


# 模板消息 ID 配置（需在微信公众号后台申请）
WECHAT_TEMPLATES = {
    "HEALTH_EDU": "health_education_001",       # 健康宣教推送
    "MED_REMINDER": "medication_reminder_002",   # 用药提醒
    "FOLLOWUP_REMINDER": "followup_reminder_003", # 随访提醒
    "ALERT_NOTIFY": "alert_notification_004",    # 预警通知
    "REFERRAL_NOTIFY": "referral_notification_005", # 转诊通知
}


class WechatPushService:
    """微信模板消息推送服务
    
    双模式运行：
    1. 生产模式：需配置 WECHAT_APP_ID / WECHAT_APP_SECRET，通过 access_token 调用公众号 API
    2. 模拟模式：日志输出 + 返回模拟结果，用于开发/测试
    """

    @staticmethod
    def is_configured() -> bool:
        """检查是否已配置真实的微信 API"""
        import os
        app_id = os.getenv("WECHAT_APP_ID", "")
        app_secret = os.getenv("WECHAT_APP_SECRET", "")
        return bool(app_id and app_secret)

    @staticmethod
    async def send_health_education(
        patient_id: str,
        openid: str,
        title: str,
        content: str,
        url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """推送健康宣教内容"""
        data = {
            "first": {"value": "📚 健康宣教", "color": "#1677FF"},
            "keyword1": {"value": title, "color": "#333333"},
            "keyword2": {"value": datetime.now().strftime("%Y-%m-%d %H:%M"), "color": "#666666"},
            "remark": {"value": content[:100] + "..." if len(content) > 100 else content, "color": "#999999"},
        }
        return await WechatPushService._push(
            openid, WECHAT_TEMPLATES["HEALTH_EDU"], data, url
        )

    @staticmethod
    async def send_medication_reminder(
        patient_id: str,
        openid: str,
        drug_name: str,
        dosage: str,
        frequency: str,
    ) -> Dict[str, Any]:
        """推送用药提醒"""
        data = {
            "first": {"value": "💊 用药提醒", "color": "#FF6600"},
            "keyword1": {"value": f"{drug_name} {dosage}", "color": "#333333"},
            "keyword2": {"value": frequency, "color": "#666666"},
            "keyword3": {"value": datetime.now().strftime("%m-%d %H:%M"), "color": "#999999"},
            "remark": {"value": "请按时服药，保持健康！", "color": "#52C41A"},
        }
        return await WechatPushService._push(
            openid, WECHAT_TEMPLATES["MED_REMINDER"], data
        )

    @staticmethod
    async def send_followup_reminder(
        patient_id: str,
        openid: str,
        followup_date: str,
        followup_type: str,
        doctor_name: str,
    ) -> Dict[str, Any]:
        """推送随访提醒"""
        data = {
            "first": {"value": "📅 随访提醒", "color": "#E6A23C"},
            "keyword1": {"value": followup_date, "color": "#333333"},
            "keyword2": {"value": followup_type, "color": "#666666"},
            "keyword3": {"value": doctor_name, "color": "#999999"},
            "remark": {"value": "请按时到院随访并携带相关资料。", "color": "#1677FF"},
        }
        return await WechatPushService._push(
            openid, WECHAT_TEMPLATES["FOLLOWUP_REMINDER"], data
        )

    @staticmethod
    async def send_alert_notification(
        patient_id: str,
        openid: str,
        alert_title: str,
        alert_level: str,
        suggestion: str,
    ) -> Dict[str, Any]:
        """推送预警通知"""
        level_color = {"HIGH": "#FF0000", "MEDIUM": "#FF6600", "LOW": "#FF9900"}
        data = {
            "first": {"value": "⚠️ 健康预警", "color": level_color.get(alert_level, "#FF6600")},
            "keyword1": {"value": alert_title, "color": "#333333"},
            "keyword2": {"value": alert_level, "color": level_color.get(alert_level, "#FF6600")},
            "keyword3": {"value": suggestion, "color": "#666666"},
            "remark": {"value": "如有不适请及时就医或联系签约医生。", "color": "#F56C6C"},
        }
        return await WechatPushService._push(
            openid, WECHAT_TEMPLATES["ALERT_NOTIFY"], data
        )

    @staticmethod
    async def _push(
        openid: str,
        template_id: str,
        data: Dict[str, Any],
        url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """底层推送方法"""
        if not WechatPushService.is_configured():
            # 模拟模式
            logger.info(
                f"[WECHAT MOCK] 推送到 {openid} | "
                f"模板 {template_id} | 数据 {json.dumps(data, ensure_ascii=False)}"
            )
            return {
                "success": True,
                "mode": "MOCK",
                "openid": openid,
                "template_id": template_id,
                "sent_at": datetime.now().isoformat(),
                "message": f"模拟推送成功（配置 WECHAT_APP_ID/WECHAT_APP_SECRET 启用真实推送）",
            }

        # 生产模式：调用微信公众号模板消息 API
        try:
            access_token = await WechatPushService._get_access_token()
            message_data = {
                "touser": openid,
                "template_id": template_id,
                "data": data,
            }
            if url:
                message_data["url"] = url

            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={access_token}",
                    json=message_data,
                    timeout=10,
                ) as resp:
                    result = await resp.json()
                    logger.info(f"[WECHAT API] 推送结果: {result}")
                    return {
                        "success": result.get("errcode") == 0,
                        "mode": "PRODUCTION",
                        "openid": openid,
                        "template_id": template_id,
                        "sent_at": datetime.now().isoformat(),
                        "wx_result": result,
                    }
        except Exception as e:
            logger.error(f"[WECHAT ERROR] 推送失败: {e}")
            return {
                "success": False,
                "mode": "PRODUCTION",
                "openid": openid,
                "error": str(e),
            }

    @staticmethod
    async def _get_access_token() -> str:
        """获取微信公众号 access_token（含简易缓存）"""
        import os
        app_id = os.getenv("WECHAT_APP_ID", "")
        app_secret = os.getenv("WECHAT_APP_SECRET", "")

        if not app_id or not app_secret:
            raise ValueError("未配置 WECHAT_APP_ID / WECHAT_APP_SECRET")

        # 简易内存缓存（生产建议用 Redis）
        if hasattr(WechatPushService, "_cached_token"):
            cached = getattr(WechatPushService, "_cached_token", {})
            if cached.get("expires_at", 0) > datetime.now().timestamp():
                return cached["token"]

        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"https://api.weixin.qq.com/cgi-bin/token",
                params={
                    "grant_type": "client_credential",
                    "appid": app_id,
                    "secret": app_secret,
                },
                timeout=10,
            ) as resp:
                result = await resp.json()
                if "access_token" in result:
                    token = result["access_token"]
                    WechatPushService._cached_token = {
                        "token": token,
                        "expires_at": datetime.now().timestamp() + result.get("expires_in", 7200) - 300,
                    }
                    return token
                raise ValueError(f"获取 access_token 失败: {result}")


    @staticmethod
    async def send_prescription(
        patient_id: str,
        openid: str,
        drug_name: str,
        dosage: str,
        frequency: str,
        duration: str = "",
        notes: str = "",
        prescriber: str = "",
    ) -> dict:
        """医生手动评估后一键发送处方给患者"""
        data = {
            "first": {"value": "您有一份新的用药处方", "color": "#173177"},
            "keyword1": {"value": drug_name, "color": "#173177"},
            "keyword2": {"value": f"{dosage} / {frequency}", "color": "#173177"},
            "keyword3": {"value": duration or "遵医嘱", "color": "#173177"},
            "keyword4": {"value": prescriber or "陵水县人民医院", "color": "#173177"},
            "remark": {"value": notes or "请按时服药，如有不适请及时就医", "color": "#666666"},
        }
        logger.info(f"[WECHAT] 发送处方: patient={patient_id} 药品={drug_name} 用法={dosage}")
        return await WechatPushService._push(patient_id, openid, "prescription", data)


# 便捷函数
async def push_health_edu(patient_id: str, openid: str, title: str, content: str, url: Optional[str] = None):
    return await WechatPushService.send_health_education(patient_id, openid, title, content, url)


async def push_med_reminder(patient_id: str, openid: str, drug_name: str, dosage: str, frequency: str):
    return await WechatPushService.send_medication_reminder(patient_id, openid, drug_name, dosage, frequency)


async def push_alert(patient_id: str, openid: str, title: str, level: str, suggestion: str):
    return await WechatPushService.send_alert_notification(patient_id, openid, title, level, suggestion)


async def push_prescription(patient_id: str, openid: str, drug_name: str, dosage: str, frequency: str, duration: str = "", notes: str = "", prescriber: str = ""):
    return await WechatPushService.send_prescription(patient_id, openid, drug_name, dosage, frequency, duration, notes, prescriber)
