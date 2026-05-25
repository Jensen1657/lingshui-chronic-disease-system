"""
质控校验服务 - 对应评估报告要求
- 必填项校验
- 逻辑校验（用药禁忌、数值范围）
- 真实性校验（定位打卡、随访录音）
- 转诊标准校验
"""
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta


class QualityControlService:
    """质控校验服务"""

    # ================================================================
    # 一、必填项定义（按业务模块）
    # ================================================================

    REQUIRED_FIELDS = {
        # 患者建档必填
        "patient_profile": {
            "name_enc": "患者姓名(加密)",
            "id_card_hash": "身份证哈希",
            "gender": "性别",
            "birth_date": "出生日期",
            "phone_enc": "联系电话(加密)",
            "manage_org_code": "管理机构编码",
            "disease_list": "疾病列表",
            "risk_level": "风险等级",
        },
        # 高血压随访必填
        "hypertension_followup": {
            "followup_date": "随访日期",
            "followup_type": "随访方式",
            "sbp": "收缩压(mmHg)",
            "dbp": "舒张压(mmHg)",
            "heart_rate": "心率(次/分)",
            "medication_adherence": "用药依从性",
            "symptoms": "症状描述",
            "next_followup_date": "下次随访日期",
        },
        # 糖尿病随访必填
        "diabetes_followup": {
            "followup_date": "随访日期",
            "followup_type": "随访方式",
            "fasting_glucose": "空腹血糖(mmol/L)",
            "hba1c": "糖化血红蛋白(%)",
            "weight": "体重(kg)",
            "medication_adherence": "用药依从性",
            "next_followup_date": "下次随访日期",
        },
        # 双向转诊必填
        "referral": {
            "patient_id": "患者ID",
            "referral_type": "转诊类型(上转/下转)",
            "from_org_code": "转出机构",
            "to_org_code": "转入机构",
            "referral_reason": "转诊原因",
            "referral_diagnosis": "转诊诊断",
            "urgency_level": "紧急程度",
        },
        # 年度评估必填
        "annual_assessment": {
            "assessment_year": "评估年度",
            "assessment_type": "评估类型",
            "overall_evaluation": "总体评价",
            "treatment_effect": "治疗效果评价",
            "risk_reassessment": "风险再评估",
            "next_year_plan": "下年度计划",
        },
    }

    @classmethod
    def check_required_fields(cls, module: str, data: dict) -> Dict[str, Any]:
        """
        必填项校验

        Args:
            module: 模块名称 (patient_profile / hypertension_followup / ...)
            data: 待校验数据

        Returns:
            {"passed": bool, "missing": [缺失字段列表], "warnings": []}
        """
        required = cls.REQUIRED_FIELDS.get(module, {})
        if not required:
            return {"passed": True, "missing": [], "warnings": []}

        missing = []
        for field, label in required.items():
            value = data.get(field)
            if value is None or value == "" or value == []:
                missing.append({"field": field, "label": label})

        return {
            "passed": len(missing) == 0,
            "missing": missing,
            "warnings": [] if not missing else [f"缺少{len(missing)}个必填字段"],
        }

    # ================================================================
    # 二、逻辑校验规则
    # ================================================================

    LOGIC_RULES = {
        "vital_signs": [
            {
                "rule": "sbp_range",
                "field": "sbp",
                "check": lambda v: 60 <= (v or 0) <= 300,
                "message": "收缩压应在60-300mmHg之间",
                "level": "error",
            },
            {
                "rule": "dbp_range",
                "field": "dbp",
                "check": lambda v: 30 <= (v or 0) <= 200,
                "message": "舒张压应在30-200mmHg之间",
                "level": "error",
            },
            {
                "rule": "sbp_gt_dbp",
                "fields": ["sbp", "dbp"],
                "check": lambda sbp, dbp: (sbp or 0) >= (dbp or 0),
                "message": "收缩压应≥舒张压",
                "level": "error",
            },
            {
                "rule": "pp_normal",  # 脉压差
                "fields": ["sbp", "dbp"],
                "check": lambda sbp, dbp: ((sbp or 0) - (dbp or 0)) >= 20,
                "message": "脉压差异常(<20mmHg)，请确认测量值",
                "level": "warning",
            },
            {
                "rule": "heart_rate_range",
                "field": "heart_rate",
                "check": lambda v: 30 <= (v or 0) <= 220,
                "message": "心率应在30-220次/分之间",
                "level": "error",
            },
        ],
        "glucose": [
            {
                "rule": "fasting_glucose_range",
                "field": "fasting_glucose",
                "check": lambda v: (v is None) or (1.1 <= v <= 33.3),
                "message": "空腹血糖应在1.1-33.3 mmol/L之间",
                "level": "error",
            },
            {
                "rule": "hba1c_range",
                "field": "hba1c",
                "check": lambda v: (v is None) or (3.0 <= v <= 15.0),
                "message": "HbA1c应在3.0-15.0%之间",
                "level": "error",
            },
            {
                "rule": "postprandial_glucose_range",
                "field": "postprandial_glucose",
                "check": lambda v: (v is None) or (1.1 <= v <= 33.3),  # noqa: LE715
                "message": "餐后2h血糖应在1.1-33.3 mmol/L之间",
                "level": "error",
            },
        ],
        "bmi": [
            {
                "rule": "bmi_range",
                "field": "bmi",
                "check": lambda v: (v is None) or (10.0 <= v <= 60.0),
                "message": "BMI应在10.0-60.0 kg/m²之间",
                "level": "error",
            },
            {
                "rule": "height_range",
                "field": "height_cm",
                "check": lambda v: (v is None) or (50.0 <= v <= 250.0),
                "message": "身高应在50-250cm之间",
                "level": "error",
            },
            {
                "rule": "weight_range",
                "field": "weight_kg",
                "check": lambda v: (v is None) or (2.0 <= v <= 300.0),
                "message": "体重应在2-300kg之间",
                "level": "error",
            },
        ],
    }

    @classmethod
    def validate_logic(cls, category: str, data: dict) -> Dict[str, Any]:
        """
        逻辑校验

        Args:
            category: 校验类别 (vital_signs / glucose / bmi)
            data: 待校验数据

        Returns:
            {"passed": bool, "errors": [], "warnings": []}
        """
        rules = cls.LOGIC_RULES.get(category, [])
        errors = []
        warnings = []

        for rule in rules:
            try:
                fields = rule.get("fields", [])
                if len(fields) >= 2:
                    values = [data.get(f) for f in fields]
                    passed = rule["check"](*values)
                else:
                    field = rule["field"]
                    value = data.get(field)
                    passed = rule["check"](value)

                if not passed:
                    entry = {
                        "rule": rule["rule"],
                        "message": rule["message"],
                        "level": rule.get("level", "error"),
                    }
                    if rule.get("level") == "warning":
                        warnings.append(entry)
                    else:
                        errors.append(entry)
            except Exception as e:
                errors.append({
                    "rule": rule["rule"],
                    "message": f"校验异常: {str(e)}",
                    "level": "error",
                })

        return {
            "passed": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
        }

    # ================================================================
    # 三、用药禁忌/相互作用校验
    # ================================================================

    DRUG_INTERACTIONS = {
        # ACEI + ARB 禁止联用
        ("ACEI", "ARB"): {
            "severity": "contraindicated",
            "message": "ACEI与ARB禁止联用，增加高钾血症和肾损伤风险",
        },
        # 硝酸甘油 + PDE5抑制剂
        ("nitrate", "PDE5i"): {
            "severity": "contraindicated",
            "message": "硝酸酯类与PDE5抑制剂联用可导致严重低血压",
        },
        # 氯吡格雷 + PPI（奥美拉唑）
        ("clopidogrel", "omeprazole"): {
            "severity": "caution",
            "message": "奥美拉唑可能降低氯吡格雷疗效，建议换用泮托拉唑",
        },
        # 二甲双胍禁忌
        ("metformin", "ckd_eGFR<30"): {
            "severity": "contraindicated",
            "message": "eGFR<30时二甲双胍禁用，eGFR30-45需减量",
        },
        # NSAIDs + ACEI/ARB
        ("NSAID", "ACEI"): {
            "severity": "caution",
            "message": "NSAIDs可能减弱ACEI降压效果并增加肾损伤风险",
        },
        # β受体阻滞剂 + 哮喘/COPD
        ("beta_blocker", "copd"): {
            "severity": "caution",
            "message": "非选择性β阻滞剂可能诱发支气管痉挛，COPD患者慎用",
        },
    }

    @classmethod
    def check_drug_interactions(cls, current_drugs: List[str], conditions: List[str] = None) -> Dict[str, Any]:
        """药物相互作用检查"""
        interactions = []
        drug_lower = [d.lower() for d in current_drugs]
        condition_lower = [c.lower() for c in (conditions or [])]

        for (drug_a, drug_b), info in cls.DRUG_INTERACTIONS.items():
            a_match = any(drug_a.lower() in d for d in drug_lower)
            b_match = any(drug_b.lower() in d for d in drug_lower)
            b_cond = any(drug_b.lower() in c for c in condition_lower)

            if a_match and (b_match or b_cond):
                interactions.append({
                    "drugs": (drug_a, drug_b),
                    "severity": info["severity"],
                    "message": info["message"],
                })

        return {
            "hasInteraction": len(interactions) > 0,
            "interactions": interactions,
            "checkedAt": datetime.now().isoformat(),
        }

    # ================================================================
    # 四、转诊标准校验
    # ================================================================

    REFERRAL_CRITERIA = {
        "UP": {  # 上转标准
            "hypertension": [
                {"condition": "sbp_ge_180", "label": "收缩压≥180mmHg", "check": lambda d: (d.get('sbp') or 0) >= 180},
                {"condition": "dbp_ge_110", "label": "舒张压≥110mmHg", "check": lambda d: (d.get('dbp') or 0) >= 110},
                {"condition": "hypertensive_urgency", "label": "高血压急症(靶器官损害)", "check": lambda d: d.get('hypertensive_urgency')},
                {"condition": "suspected_secondary", "label": "疑似继发性高血压", "check": lambda d: d.get('suspected_secondary_htn')},
                {"condition": "treatment_resistant", "label": "三种药联合仍不达标", "check": lambda d: (d.get('medication_count') or 0) >= 3 and not d.get('target_met')},
            ],
            "diabetes": [
                {"condition": "fg_lt_3.9", "label": "空腹血糖<3.9mmol/L(严重低血糖)", "check": lambda d: (d.get('fasting_glucose') or 99) < 3.9},
                {"condition": "fg_gt_16.7", "label": "空腹血糖>16.7mmol/L", "check": lambda d: (d.get('fasting_glucose') or 0) > 16.7},
                {"condition": "ketosis_dka", "label": "疑似酮症酸中毒(DKA)", "check": lambda d: d.get('suspected_dka')},
                {"condition": "hhs", "label": "高渗高血糖状态(HHS)", "check": lambda d: d.get('suspected_hhs')},
                {"condition": "new_onset_complications", "label": "新发严重并发症", "check": lambda d: d.get('new_severe_complications')},
            ],
            "stroke": [
                {"condition": "fast_positive", "label": "FAST筛查阳性", "check": lambda d: d.get('fast_positive')},
                {"condition": "time_window_ok", "label": "发病时间窗内", "check": lambda d: (d.get('symptom_minutes') or 999) <= 360},
            ],
            "general": [
                {"condition": "unknown_diagnosis", "label": "诊断不明需专科检查", "check": lambda d: d.get('need_specialist_eval')},
                {"condition": "treatment_failure", "label": "规范治疗无效", "check": lambda d: d.get('treatment_failure')},
                {"condition": "patient_request", "label": "患者或家属要求上转", "check": lambda d: d.get('patient_request_up')},
            ],
        },
        "DOWN": {  # 下转标准
            "general": [
                {"condition": "stable", "label": "病情稳定，治疗方案明确", "check": lambda d: d.get('is_stable')},
                {"condition": "rehab_phase", "label": "进入康复期", "check": lambda d: d.get('in_rehab_phase')},
                {"condition": "followup_only", "label": "仅需常规随访管理", "check": lambda d: d.get('followup_only_needed')},
                {"condition": "patient_request_down", "label": "患者或家属要求下转", "check": lambda d: d.get('patient_request_down')},
            ],
        },
    }

    @classmethod
    def validate_referral(cls, referral_type: str, disease_type: str, patient_data: dict) -> Dict[str, Any]:
        """
        转诊标准校验

        Args:
            referral_type: UP / DOWN
            disease_type: hypertension / diabetes / stroke / general
            patient_data: 患者当前数据

        Returns:
            {"meetsCriteria": bool, "matchedCriteria": [...], "allCriteria": [...]}
        """
        type_criteria = cls.REFERRAL_CRITERIA.get(referral_type, {})
        disease_criteria = type_criteria.get(disease_type, [])
        general_criteria = type_criteria.get("general", [])

        all_criteria = disease_criteria + general_criteria
        matched = []

        for criterion in all_criteria:
            try:
                if criterion["check"](patient_data):
                    matched.append(criterion)
            except Exception:
                pass

        return {
            "meetsCriteria": len(matched) > 0,
            "matchedCriteria": [{"condition": c["condition"], "label": c["label"]} for c in matched],
            "allCriteriaLabels": [c["label"] for c in all_criteria],
            "referralType": referral_type,
            "diseaseType": disease_type,
        }

    # ================================================================
    # 五、预警规则引擎
    # ================================================================

    ALERT_RULES = [
        # 高血压急症
        {
            "alertCode": "HTN_EMERGENCY",
            "alertName": "高血压急症预警",
            "category": "hypertension",
            "severity": "CRITICAL",
            "condition": lambda d: (d.get('sbp') or 0) >= 180 and (d.get('dbp') or 0) >= 110,
            "message": "血压{sbp}/{dbp}mmHg，达到高血压急症标准！需立即处理！",
            "actionRequired": "立即复查确认 → 必要时静脉降压 → 监测靶器官损害",
        },
        # 高血压高危
        {
            "alertCode": "HTN_HIGH_RISK",
            "alertName": "血压偏高预警",
            "category": "hypertension",
            "severity": "WARNING",
            "condition": lambda d: (d.get('sbp') or 0) >= 160 or (d.get('dbp') or 0) >= 100,
            "message": "血压{sbp}/{dbp}mmHg偏高，需关注",
            "actionRequired": "调整用药方案，3天内随访",
        },
        # 低血糖
        {
            "alertCode": "DM_HYPOGLYCEMIA",
            "alertName": "低血糖预警",
            "category": "diabetes",
            "severity": "CRITICAL",
            "condition": lambda d: (d.get('fasting_glucose') or 99) < 3.9 or (d.get('random_glucose') or 99) < 3.9,
            "message": "血糖{glucose}mmol/L，存在低血糖风险！",
            "actionRequired": "立即补充葡萄糖，调整降糖方案",
        },
        # 高血糖危象
        {
            "alertCode": "DM_HYPERGLYCEMIA",
            "alertName": "高血糖危象预警",
            "category": "diabetes",
            "severity": "CRITICAL",
            "condition": lambda d: (d.get('fasting_glucose') or 0) > 16.7 or (d.get('random_glucose') or 0) > 20.0,
            "message": "血糖{glucose}mmol/L严重超标！",
            "actionRequired": "排查DKA/HHS，必要时急诊",
        },
        # eGFR 急剧下降
        {
            "alertCode": "CKD_EGFR_DROP",
            "alertName": "肾功能急剧下降预警",
            "category": "ckd",
            "severity": "CRITICAL",
            "condition": lambda d: (d.get('egfr_drop_percent') or 0) >= 25,
            "message": "eGFR较前次下降{drop}%，需立即关注！",
            "actionRequired": "排查急性肾损伤原因，必要时肾内科会诊",
        },
        # 随访逾期
        {
            "alertCode": "FOLLOWUP_OVERDUE",
            "alertName": "随访逾期提醒",
            "category": "followup",
            "severity": "INFO",
            "condition": lambda d: (d.get('days_overdue') or 0) >= 7,
            "message": "已超下次随访日期{days}天",
            "actionRequired": "安排随访或联系患者",
        },
        # 转诊超时未处理
        {
            "alertCode": "REFERRAL_TIMEOUT",
            "alertName": "转诊超时预警",
            "category": "referral",
            "severity": "WARNING",
            "condition": lambda d: (d.get('hours_since_referral') or 0) >= 48,
            "message": "转诊已超过48小时未接收确认",
            "actionRequired": "联系接收机构确认状态",
        },
        # 机构随访完成率低于80%
        {
            "alertCode": "ORG_FOLLOWUP_RATE_LOW",
            "alertName": "机构随访完成率偏低",
            "category": "quality",
            "severity": "WARNING",
            "condition": lambda d: (d.get('completion_rate') or 100) < 80,
            "message": "{org_name}本月随访完成率仅{rate}%，低于80%标准",
            "actionRequired": "分析原因，加强随访管理",
        },
    ]

    @classmethod
    def evaluate_alert_rules(cls, data: dict) -> List[Dict[str, Any]]:
        """
        执行所有预警规则

        Args:
            data: 包含各项临床数据的字典

        Returns:
            触发的预警列表
        """
        triggered = []

        for rule in cls.ALERT_RULES:
            try:
                if rule["condition"](data):
                    msg = rule["message"]
                    # 动态替换消息中的变量
                    msg = msg.replace("{sbp}", str(data.get('sbp', '')))
                    msg = msg.replace("{dbp}", str(data.get('dbp', '')))
                    msg = msg.replace("{glucose}", str(data.get('fasting_glucose') or data.get('random_glucose', '')))
                    msg = msg.replace("{drop}", str(data.get('egfr_drop_percent', '')))
                    msg = msg.replace("{days}", str(data.get('days_overdue', '')))
                    msg = msg.replace("{rate}", str(data.get('completion_rate', '')))
                    msg = msg.replace("{org_name}", str(data.get('org_name', '')))

                    triggered.append({
                        "alertCode": rule["alertCode"],
                        "alertName": rule["alertName"],
                        "category": rule["category"],
                        "severity": rule["severity"],
                        "message": msg,
                        "actionRequired": rule["actionRequired"],
                        "triggeredAt": datetime.now().isoformat(),
                    })
            except Exception:
                pass

        # 按严重程度排序
        severity_order = {"CRITICAL": 0, "WARNING": 1, "INFO": 2}
        triggered.sort(key=lambda x: severity_order.get(x["severity"], 99))

        return triggered

    # ================================================================
    # 六、综合质控检查（一次性执行全部）
    # ================================================================

    @classmethod
    def full_quality_check(cls, module: str, data: dict, extra_checks: dict = None) -> Dict[str, Any]:
        """
        综合质控检查

        Args:
            module: 业务模块
            data: 业务数据
            extra_checks: 额外配置 {"logic_categories": [...], "drugs": [...], "conditions": [...]}

        Returns:
            完整的质控报告
        """
        report = {
            "module": module,
            "checkedAt": datetime.now().isoformat(),
            "overallPassed": True,
            "requiredFields": cls.check_required_fields(module, data),
            "logicChecks": [],
            "alerts": [],
        }

        # 逻辑校验
        extra = extra_checks or {}
        for cat in extra.get("logic_categories", ["vital_signs"]):
            result = cls.validate_logic(cat, data)
            report["logicChecks"].append(result)
            if not result["passed"]:
                report["overallPassed"] = False

        # 必填项
        if not report["requiredFields"]["passed"]:
            report["overallPassed"] = False

        # 预警规则
        report["alerts"] = cls.evaluate_alert_rules(data)

        # 如果有CRITICAL级别预警，整体不通过
        if any(a["severity"] == "CRITICAL" for a in report["alerts"]):
            report["overallPassed"] = False

        return report
