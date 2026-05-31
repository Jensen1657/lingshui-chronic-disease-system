<template>
  <div class="disease-detail">
    <div class="page-header">
      <h2>{{ diseaseName }} 专病管理</h2>
      <el-tag :type="controlTagType" size="large">达标率 {{ controlRate }}%</el-tag>
    </div>

    <el-skeleton v-if="loading" :rows="6" animated />

    <template v-else>
      <el-row :gutter="20" class="stat-cards">
        <el-col :xs="12" :sm="6" v-for="(card, idx) in statCards" :key="idx">
          <el-card shadow="hover" class="stat-card" :style="{ borderTop: '3px solid ' + card.color }">
            <div class="stat-value">{{ card.value }}</div>
            <div class="stat-label">{{ card.label }}</div>
            <div class="stat-icon" :style="{ color: card.color }">{{ card.icon }}</div>
          </el-card>
        </el-col>
      </el-row>

      <el-card shadow="never" class="section-card">
        <template #header>
          <div class="section-header">
            <span>患者列表（{{ totalPatients }}人）</span>
            <el-input v-model="searchName" placeholder="搜索姓名/手机号" clearable style="width:200px" @input="onSearch" />
          </div>
        </template>
        <el-table :data="patients" v-loading="tableLoading" stripe max-height="420">
          <el-table-column prop="name" label="姓名" min-width="90" />
          <el-table-column prop="gender" label="性别" width="60">
            <template #default="{ row }">{{ row.gender === 'M' ? '男' : row.gender === 'F' ? '女' : row.gender }}</template>
          </el-table-column>
          <el-table-column prop="age" label="年龄" width="60" />
          <el-table-column prop="village" label="村/社区" min-width="110" />
          <el-table-column prop="risk_level" label="风险等级" width="90">
            <template #default="{ row }">
              <el-tag :type="riskTag(row.risk_level)" size="small">{{ riskText(row.risk_level) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="专病指标" min-width="110">
            <template #default="{ row }">
              <span v-if="diseaseType === 'hypertension'">{{ row.bp_risk || '-' }}</span>
              <span v-else-if="diseaseType === 'diabetes'">{{ row.hba1c ? row.hba1c + '%' : '-' }}</span>
              <span v-else-if="diseaseType === 'chd'">{{ row.ldl_c ? row.ldl_c + ' mmol/L' : '-' }}</span>
              <span v-else-if="diseaseType === 'stroke'">{{ row.mrs_score ?? '-' }}</span>
              <span v-else-if="diseaseType === 'copd'">{{ row.cat_score ?? '-' }}</span>
              <span v-else-if="diseaseType === 'ckd'">{{ row.egfr ?? '-' }}</span>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="70" fixed="right">
            <template #default="{ row }"><el-button size="small" @click="goTo('/patients/' + row.patient_id)">详情</el-button></template>
          </el-table-column>
        </el-table>
        <el-pagination v-if="totalPatients > pageSize" v-model:current-page="page" :page-size="pageSize"
          :total="totalPatients" layout="prev, pager, next" @current-change="loadPatients" style="margin-top:12px" small />
      </el-card>

      <el-row :gutter="20" class="chart-row">
        <el-col :span="12" :xs="24">
          <el-card shadow="never">
            <template #header><span>风险等级分布</span></template>
            <div v-if="riskData.length > 0">
              <div v-for="r in riskData" :key="r.level" class="risk-row">
                <span class="risk-badge" :class="'risk-' + r.level">{{ riskText(r.level) }}</span>
                <span class="risk-num">{{ r.count }} 人</span>
                <el-progress :percentage="Math.round(r.count / maxRisk * 100)" :stroke-width="12" :color="riskColor(r.level)" />
              </div>
            </div>
            <el-empty v-else description="暂无数据" />
          </el-card>
        </el-col>
        <el-col :span="12" :xs="24">
          <el-card shadow="never">
            <template #header><span>专病核心指标</span></template>
            <div v-if="diseaseStats" class="stats-panel">
              <div v-if="diseaseType === 'hypertension'" class="stat-row">
                <span>平均目标收缩压</span><strong>{{ diseaseStats.avg_target_sbp ?? '-' }}</strong>
              </div>
              <div v-if="diseaseType === 'hypertension'" class="stat-row">
                <span>平均目标舒张压</span><strong>{{ diseaseStats.avg_target_dbp ?? '-' }}</strong>
              </div>
              <div v-if="diseaseType === 'diabetes'" class="stat-row">
                <span>平均确诊HbA1c</span><strong>{{ diseaseStats.avg_hba1c ?? '-' }}%</strong>
              </div>
              <div v-if="diseaseType === 'chd'" class="stat-row">
                <span>平均LDL-C</span><strong>{{ diseaseStats.avg_ldl_c ?? '-' }} mmol/L</strong>
              </div>
              <div v-if="diseaseType === 'stroke'" class="stat-row">
                <span>平均NIHSS</span><strong>{{ diseaseStats.avg_nihss ?? '-' }}</strong>
              </div>
              <div v-if="diseaseType === 'stroke'" class="stat-row">
                <span>平均mRS</span><strong>{{ diseaseStats.avg_mrs ?? '-' }}</strong>
              </div>
              <div v-if="diseaseType === 'copd'" class="stat-row">
                <span>平均FEV1%</span><strong>{{ diseaseStats.avg_fev1 ?? '-' }}%</strong>
              </div>
              <div v-if="diseaseType === 'copd'" class="stat-row">
                <span>平均CAT评分</span><strong>{{ diseaseStats.avg_cat ?? '-' }}</strong>
              </div>
              <div v-if="diseaseType === 'ckd'" class="stat-row">
                <span>平均eGFR</span><strong>{{ diseaseStats.avg_egfr ?? '-' }}</strong>
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
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import request from '@/api/request'

const route = useRoute()
const router = useRouter()

const diseaseMap: Record<string, { name: string; code: string }> = {
  hypertension: { name: '高血压', code: 'HYPERTENSION' },
  diabetes: { name: '糖尿病', code: 'DIABETES' },
  chd: { name: '冠心病', code: 'CHD' },
  stroke: { name: '脑卒中', code: 'STROKE' },
  copd: { name: '慢阻肺', code: 'COPD' },
  ckd: { name: '慢性肾脏病', code: 'CKD' },
}

const diseaseType = computed(() => (route.params.type as string || '').toLowerCase())
const diseaseInfo = computed(() => diseaseMap[diseaseType.value] || { name: diseaseType.value, code: diseaseType.value.toUpperCase() })
const diseaseName = computed(() => diseaseInfo.value.name)

const loading = ref(true)
const tableLoading = ref(false)
const patients = ref<any[]>([])
const totalPatients = ref(0)
const page = ref(1)
const pageSize = ref(15)
const searchName = ref('')
const riskData = ref<{ level: string; count: number }[]>([])
const controlRate = ref(0)
const highRiskCount = ref(0)
const followupRate = ref(0)
const diseaseStats = ref<any>(null)

const statCards = computed(() => [
  { label: '患者总数', value: totalPatients.value, icon: '👥', color: '#409EFF' },
  { label: '控制达标率', value: controlRate.value + '%', icon: '🎯', color: '#67C23A' },
  { label: '随访完成率', value: followupRate.value + '%', icon: '📋', color: '#E6A23C' },
  { label: '高危患者', value: highRiskCount.value, icon: '⚠️', color: '#F56C6C' },
])
const controlTagType = computed(() => controlRate.value >= 80 ? 'success' : controlRate.value >= 60 ? 'warning' : 'danger')
const maxRisk = computed(() => Math.max(...riskData.value.map(r => r.count), 1))

function riskText(l: string) { const m: Record<string, string> = { 'LOW': '低危', 'MEDIUM': '中危', 'HIGH': '高危', 'VERY_HIGH': '极高危' }; return m[l] || l || '未知' }
function riskTag(l: string) { const m: Record<string, string> = { 'LOW': 'success', 'MEDIUM': 'warning', 'HIGH': 'danger', 'VERY_HIGH': 'danger' }; return m[l] || '' }
function riskColor(l: string) { const c: Record<string, string> = { 'LOW': '#67C23A', 'MEDIUM': '#E6A23C', 'HIGH': '#F56C6C', 'VERY_HIGH': '#F56C6C' }; return c[l] || '#909399' }
function goTo(path: string) { router.push(path) }

async function loadPatients() {
  tableLoading.value = true
  try {
    const params: any = { page: page.value, page_size: pageSize.value }
    if (searchName.value.trim()) params.keyword = searchName.value.trim()
    const res = await request.get(`/v1/disease/${diseaseType.value}/patients`, { params })
    patients.value = res?.items || []
    totalPatients.value = res?.total || 0
  } catch { patients.value = []; totalPatients.value = 0 }
  finally { tableLoading.value = false }
}

async function loadStats() {
  try {
    const [overview, stats] = await Promise.all([
      request.get(`/v1/disease/${diseaseType.value}`),
      request.get(`/v1/disease/${diseaseType.value}/stats`),
    ])
    controlRate.value = overview?.control_rate || 0
    totalPatients.value = overview?.total_patients || 0
    diseaseStats.value = stats || null

    const rd = overview?.risk_distribution || {}
    riskData.value = Object.entries(rd).map(([level, count]) => ({ level, count: count as number }))
    highRiskCount.value = (rd['HIGH'] || 0) + (rd['VERY_HIGH'] || 0)

    try {
      const kd = await request.get('/v1/dashboard/kpi')
      followupRate.value = kd?.随访指标?.completionRate || 0
    } catch { followupRate.value = 0 }
  } catch (e) { console.error('DiseaseDetail loadStats error:', e) }
}

let searchTimer: any = null
function onSearch() { clearTimeout(searchTimer); searchTimer = setTimeout(() => { page.value = 1; loadPatients() }, 300) }
watch(diseaseType, () => { page.value = 1; loadAll() })
async function loadAll() { loading.value = true; await Promise.all([loadPatients(), loadStats()]); loading.value = false }
onMounted(() => loadAll())
</script>

<style scoped>
.disease-detail { padding: 0; }
.page-header { display: flex; align-items: center; gap: 16px; margin-bottom: 24px; }
.page-header h2 { margin: 0; font-size: 22px; font-weight: 700; color: var(--text-primary); }
.stat-cards { margin-bottom: 24px; }
.stat-card { min-height: 100px; border-radius: 14px !important; position: relative; cursor: default; }
.stat-value { font-size: 30px; font-weight: 800; color: var(--text-primary); line-height: 1.2; }
.stat-label { font-size: 13px; color: var(--text-secondary); margin-top: 4px; }
.stat-icon { position: absolute; right: 16px; top: 50%; transform: translateY(-50%); font-size: 32px; opacity: 0.8; }
.section-card { border-radius: 14px !important; margin-bottom: 24px; }
.section-header { display: flex; justify-content: space-between; align-items: center; }
.chart-row { margin-bottom: 24px; }
.chart-row .el-card { border-radius: 14px !important; }
.risk-row { margin-bottom: 16px; display: flex; align-items: center; gap: 8px; }
.risk-badge { display: inline-block; padding: 2px 10px; border-radius: 6px; font-size: 12px; font-weight: 600; min-width: 52px; text-align: center; }
.risk-badge.risk-LOW { background: #E8F5E9; color: #2E7D32; }
.risk-badge.risk-MEDIUM { background: #FFF3E0; color: #E65100; }
.risk-badge.risk-HIGH, .risk-badge.risk-VERY_HIGH { background: #FFEBEE; color: #C62828; }
.risk-num { font-size: 13px; color: var(--text-regular); min-width: 40px; }
.stats-panel { display: flex; flex-direction: column; gap: 12px; }
.stat-row { display: flex; justify-content: space-between; align-items: center; padding: 10px 0; border-bottom: 1px solid var(--border-light); }
.stat-row:last-child { border-bottom: none; }
</style>