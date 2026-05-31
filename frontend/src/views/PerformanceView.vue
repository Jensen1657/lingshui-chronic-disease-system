<template>
  <div class="performance-page">
    <div class="page-header">
      <h2>📊 医护绩效考核</h2>
      <div class="header-controls">
        <el-select v-model="period" @change="loadAll" style="width:120px">
          <el-option label="本月" value="month" />
          <el-option label="本季度" value="quarter" />
          <el-option label="本年" value="year" />
        </el-select>
        <el-select v-model="selectedOrg" placeholder="全部机构" clearable @change="loadAll" style="width:180px" filterable>
          <el-option label="🏥 全部机构" value="" />
          <el-option v-for="org in orgList" :key="org.orgCode" :label="org.orgName" :value="org.orgCode" />
        </el-select>
      </div>
    </div>

    <!-- 总览卡片 -->
    <el-row :gutter="20" class="overview-cards" v-loading="loading">
      <el-col :xs="12" :sm="6" v-for="card in overviewCards" :key="card.label">
        <el-card shadow="hover" class="overview-card" :style="{ borderLeft: `4px solid ${card.color}` }">
          <div class="ov-value">{{ card.value }}</div>
          <div class="ov-label">{{ card.label }}</div>
          <div class="ov-icon" :style="{ color: card.color }">{{ card.icon }}</div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 人员排名表 -->
    <el-card shadow="never" class="staff-card">
      <template #header>
        <div class="card-header">
          <span>🏅 医护人员排名</span>
          <el-tag size="small">{{ periodLabel }}</el-tag>
        </div>
      </template>
      <el-table :data="staffList" v-loading="staffLoading" stripe highlight-current-row
        @row-click="showDetail" style="cursor:pointer">
        <el-table-column type="index" label="排名" width="60">
          <template #default="{ $index }">
            <el-tag v-if="$index === 0" type="danger" size="small">🥇</el-tag>
            <el-tag v-else-if="$index === 1" type="warning" size="small">🥈</el-tag>
            <el-tag v-else-if="$index === 2" type="info" size="small">🥉</el-tag>
            <span v-else>{{ $index + 1 }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="staff_name" label="姓名" min-width="100">
          <template #default="{ row }">
            <strong>{{ row.staff_name }}</strong>
          </template>
        </el-table-column>
        <el-table-column prop="completion_rate" label="随访完成率" width="130" sortable>
          <template #default="{ row }">
            <el-progress :percentage="Math.round(row.completion_rate)" :status="row.completion_rate >= 80 ? 'success' : row.completion_rate >= 60 ? 'warning' : 'exception'" />
          </template>
        </el-table-column>
        <el-table-column prop="managed_patients" label="管理患者" width="100" sortable />
        <el-table-column prop="total_followups" label="随访次数" width="100" sortable />
        <el-table-column prop="completed_followups" label="已完成" width="80" />
        <el-table-column prop="active_days" label="活跃天数" width="90" />
        <el-table-column prop="quality_good_count" label="优质记录" width="90">
          <template #default="{ row }">{{ row.quality_good_count || 0 }}</template>
        </el-table-column>
        <el-table-column label="综合评级" width="100">
          <template #default="{ row }">
            <el-tag v-if="row.completion_rate >= 85" type="success">优秀</el-tag>
            <el-tag v-else-if="row.completion_rate >= 70" type="warning">良好</el-tag>
            <el-tag v-else type="danger">待改进</el-tag>
          </template>
        </el-table-column>
      </el-table>
      <el-pagination v-if="staffTotal > pageSize" v-model:current-page="page" :page-size="pageSize"
        :total="staffTotal" layout="prev, pager, next" @current-change="loadStaff" style="margin-top:16px" small />
    </el-card>

    <!-- 人员详情弹窗 -->
    <el-dialog v-model="detailVisible" :title="'📋 ' + (detailStaff?.stats?.staff_name || '详情')" width="700px" destroy-on-close>
      <template v-if="detailStaff">
        <el-descriptions :column="3" border size="small">
          <el-descriptions-item label="随访完成率">{{ detailStaff.stats.completion_rate }}%</el-descriptions-item>
          <el-descriptions-item label="管理患者数">{{ detailStaff.stats.managed_patients }}</el-descriptions-item>
          <el-descriptions-item label="总随访次数">{{ detailStaff.stats.total_followups }}</el-descriptions-item>
          <el-descriptions-item label="已完成随访">{{ detailStaff.stats.completed_followups }}</el-descriptions-item>
          <el-descriptions-item label="活跃天数">{{ detailStaff.stats.active_days }}</el-descriptions-item>
          <el-descriptions-item label="优质记录">{{ detailStaff.stats.quality_good_count || 0 }}</el-descriptions-item>
        </el-descriptions>

        <!-- 风险分布 -->
        <h4 style="margin-top:20px">管理患者风险分布</h4>
        <el-row :gutter="12" v-if="detailStaff.risk_distribution">
          <el-col :span="6" v-for="(count, level) in detailStaff.risk_distribution" :key="level">
            <el-statistic :title="level" :value="count">
              <template #suffix>人</template>
            </el-statistic>
          </el-col>
        </el-row>

        <!-- 每日趋势 -->
        <h4 style="margin-top:20px">随访趋势（近30天）</h4>
        <div v-if="detailStaff.daily_trend?.length" class="mini-trend">
          <div v-for="(d, i) in detailStaff.daily_trend" :key="i" class="trend-bar-col">
            <div class="trend-bar-fill" :style="{ height: (d.count / maxDaily) * 80 + 'px' }" :title="d.date + ': ' + d.count + '次'">
              <span v-if="d.count > 0">{{ d.count }}</span>
            </div>
            <span class="trend-date">{{ d.date.slice(5) }}</span>
          </div>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import request from '@/api/request'

const period = ref('month')
const selectedOrg = ref('')
const loading = ref(true)
const staffLoading = ref(false)
const staffList = ref<any[]>([])
const staffTotal = ref(0)
const page = ref(1)
const pageSize = ref(15)
const detailVisible = ref(false)
const detailStaff = ref<any>(null)
const overview = ref<any>({})
const orgList = ref<any[]>([])

const periodLabel = computed(() => ({ month: '本月', quarter: '本季度', year: '本年' }[period.value]))

const overviewCards = computed(() => [
  { label: '医护人员数', value: overview.value?.total_staff || 0, icon: '👨‍⚕️', color: '#409EFF' },
  { label: '管理患者数', value: overview.value?.managed_patients || 0, icon: '👥', color: '#67C23A' },
  { label: '随访完成率', value: (overview.value?.avg_followup_completion_rate || 0) + '%', icon: '📋', color: '#E6A23C' },
  { label: '用药依从率', value: (overview.value?.avg_medication_compliance_rate || 0) + '%', icon: '💊', color: '#B37FEB' },
])

const maxDaily = computed(() => {
  if (!detailStaff.value?.daily_trend?.length) return 1
  return Math.max(...detailStaff.value.daily_trend.map((d: any) => d.count), 1)
})

async function loadOverview() {
  const params: any = { period: period.value }
  if (selectedOrg.value) params.org_code = selectedOrg.value
  const res = await request.get('/v1/performance/overview', { params })
  overview.value = res.data
}

async function loadStaff() {
  staffLoading.value = true
  const params: any = { period: period.value, page: page.value, page_size: pageSize.value }
  if (selectedOrg.value) params.org_code = selectedOrg.value
  const res = await request.get('/v1/performance/staff', { params })
  staffList.value = res.data.items || []
  staffTotal.value = res.data.total || 0
  staffLoading.value = false
}

async function loadOrgs() {
  try {
    const res = await request.get('/v1/dashboard/orgs')
    orgList.value = res.data || []
  } catch { /* not critical */ }
}

async function loadAll() {
  loading.value = true
  await Promise.all([loadOverview(), loadStaff(), loadOrgs()])
  loading.value = false
}

async function showDetail(row: any) {
  const res = await request.get(`/v1/performance/staff/${encodeURIComponent(row.staff_name)}`, { params: { period: period.value } })
  detailStaff.value = res.data
  detailVisible.value = true
}

onMounted(loadAll)
</script>

<style scoped>
.performance-page { padding: 0; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.page-header h2 { margin: 0; font-size: 20px; }
.header-controls { display: flex; gap: 12px; }

.overview-cards { margin-bottom: 20px; }
.overview-card { position: relative; overflow: hidden; }
.ov-value { font-size: 28px; font-weight: 700; color: #333; }
.ov-label { font-size: 13px; color: #999; margin-top: 4px; }
.ov-icon { position: absolute; right: 16px; top: 16px; font-size: 32px; opacity: 0.2; }

.staff-card { margin-top: 0; }
.card-header { display: flex; justify-content: space-between; align-items: center; }

.mini-trend { display: flex; gap: 3px; align-items: flex-end; height: 100px; margin-top: 12px; }
.trend-bar-col { display: flex; flex-direction: column; align-items: center; flex: 1; min-width: 12px; }
.trend-bar-fill {
  background: linear-gradient(180deg, #409EFF, #a0cfff);
  border-radius: 3px 3px 0 0;
  width: 100%;
  position: relative;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  font-size: 9px;
  color: #fff;
  padding-top: 2px;
  min-height: 6px;
}
.trend-date { font-size: 8px; color: #bbb; margin-top: 3px; transform: rotate(-45deg); white-space: nowrap; }
</style>