# 种子数据补充完成

**时间**: 2026-05-29 18:47
**状态**: ✅ 11张空表全部填充

## 填充数据

| 表 | 行数 | 说明 |
|----|------|------|
| dim_drug | 29 | 高血压/糖尿病/冠心病/脑卒中/慢阻肺/CKD 6类慢病常用药 |
| health_education_record | 60 | 4种渠道(WECHAT/SMS/APP/PRINT)发送+阅读+反馈 |
| prescription_review | 30 | 4种审核类型+5种审核结果 |
| disease_hypertension | 25 | 含用药方案、合并症、靶目标值 |
| disease_diabetes | 15 | 含诊断分型、靶目标值、胰岛素方案 |
| disease_coronary_heart_disease | 12 | 含抗血小板/他汀/β-blocker方案 |
| disease_stroke | 10 | 含NIHSS评分、3月随访计划 |
| disease_copd | 8 | 含肺功能指标、吸入剂方案 |
| disease_ckd | 5 | 含eGFR趋势、检查计划、禁忌标记 |
| followup_hypertension | 25 | 血压分级、药物调整原因 |
| followup_diabetes | 15 | 低血糖事件、不良反应 |

## 技术要点
- 列发现方法：PRAGMA table_info 动态匹配，避免手动数列
- 数据关联：patient_id/medication_id/template_id/user_id 从现有数据中提取
- 时间分布：宣教记录 2026/1-5，处方审核 2025/6-2026/5
