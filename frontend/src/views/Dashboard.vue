<template>
  <div class="dashboard">
    <!-- 机构筛选栏 -->
    <div class="org-filter-bar" v-if="!loading">
      <el-select v-model="selectedOrg" placeholder="全部机构" clearable filterable @change="onOrgChange" class="org-select">
        <el-option label="🏥 全部机构" value="" />
        <el-option v-for="org in orgList" :key="org.orgCode" :label="org.orgName" :value="org.orgCode" />
      </el-select>
    </div>

    <!-- 骨架屏 -->
    <template v-if="loading">
      <el-row :gutter="20" class="stat-cards">
        <el-col :xs="12" :sm="8" :md="6" :lg="3" v-for="i in 8" :key="i">
          <el-card shadow="hover" class="stat-card"><el-skeleton animated /></el-card>
        </el-col>
      </el-row>
      <el-card shadow="never" style="margin-top:20px"><el-skeleton :rows="4" animated /></el-card>
      <el-row :gutter="20" style="margin-top:20px">
        <el-col :span="12"><el-card><el-skeleton :rows="5" animated /></el-card></el-col>
        <el-col :span="12"><el-card><el-skeleton :rows="5" animated /></el-card></el-col>
      </el-row>
    </template>

    <!-- 实际内容 -->
    <template v-else>

    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stat-cards">
      <el-col :xs="12" :sm="8" :md="6" :lg="3" v-for="(card, idx) in statCards" :key="idx">
        <el-card shadow="hover" class="stat-card" :style="{ borderTop: '3px solid ' + card.color }">
          <div style="cursor:pointer" @click="goTo(card.route, card.query)">
            <div class="stat-card-body">
              <div class="stat-value">{{ card.value }}</div>
              <div class="stat-label">{{ card.label }} →</div>
            </div>
            <div class="stat-icon" :style="{ color: card.color }">{{ card.icon }}</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- KPI 考核指标 -->
    <el-card shadow="never" class="kpi-section" v-if="!kpiLoading">
      <template #header>
        <div class="kpi-header">
          <span style="cursor:pointer" @click="goTo('/quality-control')">考核指标 →</span>
          <el-tag :type="kpiGrade.type" size="large" style="cursor:pointer" @click.stop="goTo('/quality-control')">
            {{ kpiGrade.label }} ({{ kpiGrade.score }}分)
          </el-tag>
        </div>
      </template>
      <el-row :gutter="16">
        <el-col :xs="12" :sm="8" :md="6" v-for="item in kpiItems" :key="item.key">
          <div class="kpi-item" :class="{ 'kpi-clickable': item.route }"
            @click="item.route && goTo(item.route, item.query || {})">
            <div class="kpi-label">{{ item.label }}</div>
            <div class="kpi-value" :style="{ color: item.color }">{{ formatKpi(item.key) }}</div>
          </div>
        </el-col>
      </el-row>
    </el-card>

    <!-- 图表区域 -->
    <el-row :gutter="20" class="chart-row">
      <!-- 慢病分布 -->
      <el-col :span="8" :xs="24">
        <el-card shadow="never">
          <template #header>
            <span style="cursor:pointer" @click="goTo('/patients')">慢病类型分布 →</span>
          </template>
          <div v-if="Object.keys(diseaseStats).length > 0" class="disease-list">
            <div v-for="(count, name) in diseaseStats" :key="name" class="disease-item"
              style="cursor:pointer" @click="goTo(diseaseRouteMap[name])">
              <span class="disease-name">{{ name }}</span>
              <el-progress :percentage="Math.round(count / maxDisease * 100)" :stroke-width="16" :color="getDiseaseColor(name)">
                <span>{{ count }} 人</span>
              </el-progress>
            </div>
          </div>
          <el-empty v-else description="暂无数据" />
        </el-card>
      </el-col>

      <!-- 风险等级 -->
      <el-col :span="8" :xs="24">
        <el-card shadow="never">
          <template #header>
            <span style="cursor:pointer" @click="goTo('/risk-assessment')">患者风险等级分布 →</span>
          </template>
          <div v-if="Object.keys(riskDistribution).length > 0" class="risk-list">
            <div v-for="(count, level) in riskDistribution" :key="level" class="risk-item"
              style="cursor:pointer" @click="goTo('/risk-assessment', { risk: riskRouteMap[level] || '' })">
              <span class="risk-badge" :class="'risk-' + (level || 'unknown')">{{ getRiskText(level) }}</span>
              <span class="risk-count">{{ count }} 人</span>
              <el-progress :percentage="Math.round(count / totalRiskPatients * 100)" :stroke-width="14" :color="getRiskColor(level)" />
            </div>
          </div>
          <el-empty v-else description="暂无数据" />
        </el-card>
      </el-col>

      <!-- 随访趋势图 -->
      <el-col :span="8" :xs="24">
        <el-card shadow="never">
          <template #header>
            <span style="cursor:pointer" @click="goTo('/followups')">随访趋势（近30天） →</span>
          </template>
          <div v-if="followupTrend.length > 0" class="trend-chart">
            <div class="trend-bars">
              <div v-for="(item, idx) in followupTrend.slice(-30)" :key="idx" class="trend-bar-wrapper"
                style="cursor:pointer" @click="goTo('/followups', { date: item.date })">
                <div class="trend-bar" :style="{ height: (item.count / maxTrendCount * 100) + '%' }">
                  <span class="trend-value">{{ item.count }}</span>
                </div>
                <span class="trend-label">{{ item.date.slice(5) }}</span>
              </div>
            </div>
          </div>
          <el-empty v-else description="暂无数据" />
        </el-card>
      </el-col>
    </el-row>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import request from '@/api/request'

const router = useRouter()

interface KpiData {
  基础指标?: { totalPatients?: number; activePatients?: number; filingRate?: number; screeningCoverage?: number }
  随访指标?: { totalFollowups?: number; monthFollowups?: number; completionRate?: number; followupAuthenticityRate?: number }
  转诊指标?: { totalReferrals?: number; referralCompletionRate?: number; timelyReferralRate?: number }
  达标率指标?: { hypertensionControlRate?: number; diabetesControlRate?: number }
  预警指标?: { unresolvedAlerts?: number }
  县乡协同指标?: { townshipVisitRate?: number }
  患者满意度?: { patientSatisfactionRate?: number }
  质控指标?: { [key: string]: number | undefined }
  考核等级?: { score?: number; level?: string }
}

interface DashboardStats {
  patientCount: number; todayPatients: number; followupCount: number; pendingFollowups: number
  alertCount: number; referralCount: number; assessmentCount: number
  diseaseStats: Record<string, number>; followupTrend: { date: string; count: number }[]; riskDistribution: Record<string, number>
}

const kpi = ref<KpiData>({})
const stats = ref<DashboardStats>({ patientCount: 0, todayPatients: 0, followupCount: 0, pendingFollowups: 0, alertCount: 0, referralCount: 0, assessmentCount: 0, diseaseStats: {}, followupTrend: [], riskDistribution: {} })
const loading = ref(true)
const kpiLoading = ref(false)
const qcMetrics = ref({ medicationCompliance: 0, followupQuality: 0 })
const selectedOrg = ref('')
const orgList = ref<{ orgCode: string; orgName: string }[]>([])

// 计算属性
const diseaseStats = computed(() => stats.value.diseaseStats || {})
const riskDistribution = computed(() => stats.value.riskDistribution || {})
const followupTrend = computed(() => stats.value.followupTrend || [])
const maxDisease = computed(() => Math.max(...Object.values(diseaseStats.value), 1))
const totalRiskPatients = computed(() => Object.values(riskDistribution.value).reduce((s, c) => s + c, 0) || 1)
const maxTrendCount = computed(() => { const t = followupTrend.value; return t.length ? Math.max(...t.map(x => x.count), 1) : 1 })

// 导航函数 - 强制用 window.location 跳转，确保一定能导航
function goTo(path: string, query?: Record<string, string>) {
  console.log('[goTo] 点击了:', path, query)
  // 先弹窗确认点击事件确实触发了（测试完可以删掉这行）
  // alert('点击事件触发！即将跳转到: ' + path)
  const base = (import.meta.env.BASE_URL as string) || '/'
  const qs = query && Object.values(query).some(v => v) ? '?' + new URLSearchParams(query).toString() : ''
  const fullPath = base.replace(/\/$/, '') + path + qs
  console.log('[goTo] 跳转完整路径:', fullPath)
  // 直接用 window.location.assign，强制全页刷新导航
  window.location.assign(fullPath)
}

const diseaseRouteMap: Record<string, string> = {
  '高血压': '/disease/hypertension', '糖尿病': '/disease/diabetes', '冠心病': '/disease/chd',
  '脑卒中': '/disease/stroke', '慢阻肺': '/disease/copd', '慢性肾脏病': '/disease/ckd',
}
const riskRouteMap: Record<string, string> = { 'LOW': 'LOW', 'MEDIUM': 'MEDIUM', 'HIGH': 'HIGH', 'VERY_HIGH': 'CRITICAL' }

const statCards = computed(() => [
  { label: '患者总数', value: kpi.value?.基础指标?.totalPatients || 0, icon: '👥', color: '#409EFF', route: '/patients', query: {} },
  { label: '活跃患者', value: kpi.value?.基础指标?.activePatients || 0, icon: '✓', color: '#67C23A', route: '/patients', query: { status: 'active' } },
  { label: '随访记录', value: kpi.value?.随访指标?.totalFollowups || 0, icon: '📋', color: '#E6A23C', route: '/followups', query: {} },
  { label: '本月随访', value: stats.value?.followupTrend?.slice(-1)?.[0]?.count || 0, icon: '📅', color: '#F56C6C', route: '/followups', query: { period: 'this_month' } },
  { label: '转诊记录', value: kpi.value?.转诊指标?.totalReferrals || 0, icon: '🔄', color: '#B37FEB', route: '/referrals', query: {} },
  { label: '未处理预警', value: kpi.value?.预警指标?.unresolvedAlerts || 0, icon: '⚠️', color: '#FF6600', route: '/alerts', query: { status: 'unresolved' } },
  { label: '用药依从率', value: qcMetrics.value.medicationCompliance + '%', icon: '💊', color: '#00B4D8', route: '/quality-control', query: { tab: 'medication' } },
  { label: '随访达标率', value: qcMetrics.value.followupQuality + '%', icon: '📊', color: '#7209B7', route: '/quality-control', query: { tab: 'followup' } },
])

const kpiGrade = computed(() => {
  const score = kpi.value?.考核等级?.score || 0
  const level = kpi.value?.考核等级?.level || '未知'
  const typeMap: Record<string, string> = { '优秀': 'success', '良好': '', '合格': 'warning', '不合格': 'danger' }
  return { label: level, score: score.toFixed(1), type: typeMap[level] || 'info' }
})

const kpiItems = [
  { key: '基础指标.filingRate', label: '建档率', color: '#409EFF', route: '/patients', query: {} },
  { key: '基础指标.screeningCoverage', label: '筛查覆盖率', color: '#67C23A', route: '/patients', query: { status: 'screened' } },
  { key: '随访指标.completionRate', label: '随访完成率', color: '#E6A23C', route: '/followups', query: { status: 'completed' } },
  { key: '随访指标.followupAuthenticityRate', label: '随访真实率', color: '#F56C6C', route: '/quality-control', query: { tab: 'followup' } },
  { key: '达标率指标.hypertensionControlRate', label: '血压达标率', color: '#F56C6C', route: '/disease/hypertension', query: {} },
  { key: '达标率指标.diabetesControlRate', label: '血糖达标率', color: '#909399', route: '/disease/diabetes', query: {} },
  { key: '转诊指标.referralCompletionRate', label: '转诊完成率', color: '#B37FEB', route: '/referrals', query: { status: 'completed' } },
  { key: '转诊指标.timelyReferralRate', label: '及时转诊率', color: '#409EFF', route: '/referrals', query: { status: 'timely' } },
  { key: '县乡协同指标.townshipVisitRate', label: '县乡协同率', color: '#67C23A', route: '/county-township', query: {} },
  { key: '患者满意度.patientSatisfactionRate', label: '患者满意度', color: '#E6A23C', route: '/assessments', query: {} },
  { key: '质控指标.用药依从率', label: '用药依从率', color: '#00B4D8', route: '/quality-control', query: { tab: 'medication' } },
  { key: '质控指标.处方审核率', label: '处方审核率', color: '#7209B7', route: '/prescription-reviews', query: {} },
]

function formatKpi(key: string): string {
  let val: any = kpi.value
  for (const k of key.split('.')) val = val?.[k]
  if (val == null) return '0%'
  return typeof val === 'number' ? val.toFixed(1) + '%' : String(val)
}
function getDiseaseColor(name: string) {
  const c: Record<string, string> = { '高血压': '#409EFF', '糖尿病': '#67C23A', '冠心病': '#E6A23C', '脑卒中': '#F56C6C', '慢阻肺': '#909399', '慢性肾脏病': '#B37FEB' }
  return c[name] || '#409EFF'
}
function getRiskText(level: string) {
  const m: Record<string, string> = { 'LOW': '低危', 'MEDIUM': '中危', 'HIGH': '高危', 'VERY_HIGH': '极高危' }
  return m[level] || level || '未知'
}
function getRiskColor(level: string) {
  const c: Record<string, string> = { 'LOW': '#67C23A', 'MEDIUM': '#E6A23C', 'HIGH': '#F56C6C', 'VERY_HIGH': '#F56C6C' }
  return c[level] || '#909399'
}

async function loadData() {
  try {
    loading.value = true
    const params: Record<string, string> = {}
    if (selectedOrg.value) params.org_code = selectedOrg.value
    const [kd, sd, mc, fq, og] = await Promise.all([
      request.get('/v1/dashboard/kpi', { params }),
      request.get('/v1/dashboard/stats', { params }),
      request.get('/v1/quality-control/metrics/medication-compliance', { params }),
      request.get('/v1/quality-control/metrics/followup-quality', { params }),
      request.get('/v1/dashboard/orgs'),
    ])
    kpi.value = kd; stats.value = sd
    qcMetrics.value = { medicationCompliance: mc?.compliance_rate || 0, followupQuality: fq?.quality_rate || 0 }
    if (!kpi.value.质控指标) kpi.value.质控指标 = {} as any
    kpi.value.质控指标!['用药依从率'] = mc?.compliance_rate || 0
    kpi.value.质控指标!['处方审核率'] = fq?.quality_rate || 0
    if (orgList.value.length === 0 && og && Array.isArray(og)) orgList.value = og
  } catch (e) { console.error('Dashboard load error:', e) }
  finally { loading.value = false }
}

onMounted(() => loadData())
async function onOrgChange() { await loadData() }
</script>

<style scoped>
.dashboard { padding: 0; }
.org-filter-bar { display: flex; align-items: center; margin-bottom: 20px; gap: 12px; }
.org-select { width: 260px; }
.stat-cards { margin-bottom: 24px; }
.stat-card { min-height: 110px; border-radius: 14px !important; overflow: hidden; transition: all 0.3s ease; cursor: pointer; }
.stat-card:hover { transform: translateY(-4px); box-shadow: 0 8px 24px rgba(64, 158, 255, 0.25); }
.stat-card-body { padding-right: 48px; }
.stat-value { font-size: 32px; font-weight: 800; color: var(--text-primary); letter-spacing: -0.5px; line-height: 1.2; }
.stat-label { font-size: 13px; color: var(--text-secondary); margin-top: 6px; font-weight: 500; }
.stat-icon { position: absolute; right: 18px; top: 50%; transform: translateY(-50%); font-size: 36px; opacity: 0.85; }
.kpi-section { margin-bottom: 24px; border-radius: 14px !important; }
.kpi-header { display: flex; justify-content: space-between; align-items: center; font-weight: 600; font-size: 16px; }
.kpi-item { padding: 16px 8px; text-align: center; border-bottom: 1px solid #F5F5F7; transition: all 0.2s; border-radius: 8px; cursor: pointer; }
.kpi-item:hover { background: #F0F7FF; }
.kpi-item:last-child { border-bottom: none; }
.kpi-label { font-size: 13px; color: var(--text-secondary); margin-bottom: 8px; font-weight: 500; }
.kpi-value { font-size: 22px; font-weight: 700; letter-spacing: -0.3px; }
.chart-row { margin-bottom: 24px; }
.chart-row .el-card { border-radius: 14px !important; }
.disease-list, .risk-list { padding: 0 8px; }
.disease-item, .risk-item { margin-bottom: 18px; }
.disease-name { display: block; margin-bottom: 8px; font-size: 14px; color: var(--text-regular); font-weight: 500; }
.risk-badge { display: inline-block; padding: 3px 10px; border-radius: 6px; font-size: 12px; font-weight: 600; margin-right: 10px; }
.risk-badge.risk-LOW { background: #E8F5E9; color: #2E7D32; }
.risk-badge.risk-MEDIUM { background: #FFF3E0; color: #E65100; }
.risk-badge.risk-HIGH, .risk-badge.risk-VERY_HIGH { background: #FFEBEE; color: #C62828; }
.risk-badge.risk-unknown { background: #F5F5F5; color: #616161; }
.risk-count { font-size: 14px; color: var(--text-regular); margin-right: 12px; font-weight: 500; }
.trend-chart { padding: 8px; }
.trend-bars { display: flex; align-items: flex-end; height: 260px; gap: 3px; padding-top: 24px; overflow-x: auto; }
.trend-bar-wrapper { display: flex; flex-direction: column; align-items: center; flex: 1; min-width: 18px; height: 100%; justify-content: flex-end; }
.trend-bar { width: 100%; min-height: 3px; background: linear-gradient(to top, var(--primary), var(--primary-light)); border-radius: 3px 3px 0 0; position: relative; transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); }
.trend-bar:hover { background: linear-gradient(to top, var(--primary-dark), var(--primary)); transform: scaleX(1.3); }
.trend-value { position: absolute; top: -20px; left: 50%; transform: translateX(-50%); font-size: 10px; color: var(--text-secondary); font-weight: 600; white-space: nowrap; }
.trend-label { font-size: 9px; color: var(--text-placeholder); margin-top: 6px; text-align: center; }
</style>