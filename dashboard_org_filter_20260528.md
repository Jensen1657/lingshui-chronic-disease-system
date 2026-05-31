# Dashboard 机构筛选器实现 - 2026-05-28 16:30

## 完成内容

### 后端改造（dashboard.py）

#### 1. 新增机构筛选参数
- `/stats?org_code=xxx` - 按机构筛选统计卡片数据
- `/kpi?org_code=xxx` - 按机构筛选考核指标
- `/orgs` - 新增端点，返回所有机构列表 `{orgCode, orgName, regionCode, regionName}`

#### 2. 筛选逻辑
- **患者类**（患者数、活跃数、建档率）：用 `Patient.manage_org_code == org_code`
- **随访/转诊/预警类**：用 `FollowupRecord.org_code == org_code`
- **用药依从率**：用 `PatientMedication.prescribed_org == org_code`
- 不传 `org_code` 或传空 → 查全部（全县级）

#### 3. 缓存策略
- 缓存 key 改为 `dashboard:stats:<org_code|all>` 和 `dashboard:kpi:<org_code|all>`
- `/orgs` 缓存 10 倍 TTL（机构列表变化频率低）

#### 4. 机构列表来源
- 优先从 `dim_region` 表读取 `org_code` + `org_name`
- 回退：从 `patient.manage_org_code` 去重

### 前端改造（Dashboard.vue）

#### 1. 新增机构筛选栏
```html
<el-select v-model="selectedOrg" placeholder="全部机构" clearable filterable>
  <el-option label="🏥 全部机构" value="" />
  <el-option v-for="org in orgList" :key="org.orgCode" ... />
</el-select>
```

#### 2. 数据加载逻辑
- `loadData()` 传入 `params.org_code`
- 首次加载自动拉取 `/orgs` 填充下拉列表
- `onOrgChange()` 切换机构时重新加载全部数据

#### 3. 样式
- `.org-filter-bar`：flex 布局，12px gap
- `.org-select`：宽度 260px

## 验证结果
- ✅ 后端语法检查通过（dashboard.py + quality_control.py）
- ✅ 前端 `vite build` 通过（5.43s，0 error）
- ✅ API 兼容性：`/stats` 和 `/kpi` 不加 `org_code` 参数时行为不变（向后兼容）

## 影响范围
- 文件：`backend/app/api/dashboard.py`（主要），`frontend/src/views/Dashboard.vue`
- API 变更：`/stats`、`/kpi` 新增可选 Query 参数 `org_code`
- 新增端点：`/orgs`（无需鉴权，依赖 `get_current_active_user`）
