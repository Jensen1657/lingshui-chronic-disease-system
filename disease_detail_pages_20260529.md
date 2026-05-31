# Dashboard 精准跳转 — 专病专属页面实现

**日期**: 2026-05-29 17:14-17:18
**状态**: ✅ 全部完成

## 概述
用户反馈 Dashboard 跳转"不够精准，只能跳到某个板块，没有专属页面"。
原来所有病种指标都跳到通用列表页 `/patients?disease=xxx`，现在改为各病种的专属管理页面 `/disease/xxx`。

## 变更清单

### 新建
- `frontend/src/views/DiseaseDetail.vue` — 可复用专病管理页，接受 `route.params.type` 参数
  - diseaseMap: hypertension→高血压, diabetes→糖尿病, chd→冠心病, stroke→脑卒中, copd→慢阻肺, ckd→慢性肾脏病
  - 4张统计卡片 + 患者列表 + 风险分布 + 随访趋势

### 修改
- `router/index.ts` — 新增 6 条 `/disease/:type` 路由，权限: ADMIN/DOCTOR
- `Dashboard.vue` — diseaseRouteMap 值从 CODE 改为路由路径；KPI 血压/血糖达标率指向专病页；移除调试按钮

### 跳转对照表
| Dashboard 元素 | 原跳转 | 新跳转 |
|---------------|--------|--------|
| 血压达标率(KPI) | /followups?disease=HYPERTENSION&status=controlled | /disease/hypertension |
| 血糖达标率(KPI) | /followups?disease=DIABETES&status=controlled | /disease/diabetes |
| 慢病分布-高血压 | /patients?disease=HYPERTENSION | /disease/hypertension |
| 慢病分布-糖尿病 | /patients?disease=DIABETES | /disease/diabetes |
| 慢病分布-冠心病 | /patients?disease=CHD | /disease/chd |
| 慢病分布-脑卒中 | /patients?disease=STROKE | /disease/stroke |
| 慢病分布-慢阻肺 | /patients?disease=COPD | /disease/copd |
| 慢病分布-慢性肾脏病 | /patients?disease=CKD | /disease/ckd |

## 验证
- vite build: 5.47s, 0 errors
- dev server: http://localhost:3000, HTTP 200
- 后端: uvicorn on port 8000
