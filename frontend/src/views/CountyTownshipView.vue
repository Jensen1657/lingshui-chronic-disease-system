<template>
  <div class="county-township-view">
    <el-card class="header-card" shadow="never">
      <div class="header">
        <h2>🏥 县乡协同管理</h2>
        <el-tag type="success" size="large">协作评分：{{ stats.collaborationScore }}分</el-tag>
      </div>
    </el-card>

    <!-- 县级医院统计 -->
    <el-card class="section-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <span>🏥 陵水县人民医院（县级医院）</span>
        </div>
      </template>
      <el-row :gutter="20">
        <el-col :span="6">
          <el-statistic title="总患者数" :value="stats.countyHospital.totalPatients" />
        </el-col>
        <el-col :span="6">
          <el-statistic title="在管患者" :value="stats.countyHospital.activePatients" />
        </el-col>
        <el-col :span="6">
          <el-statistic title="上转数" :value="stats.countyHospital.upReferrals" />
        </el-col>
        <el-col :span="6">
          <el-statistic title="下转数" :value="stats.countyHospital.downReferrals" />
        </el-col>
      </el-row>
      <el-progress
        :percentage="stats.countyHospital.completionRate"
        :color="stats.countyHospital.completionRate >= 90 ? '#67C23A' : stats.countyHospital.completionRate >= 75 ? '#E6A23C' : '#F56C6C'"
        style="margin-top: 20px"
      />
      <div style="text-align: center; margin-top: 5px;">转诊完成率</div>
    </el-card>

    <!-- 乡镇卫生院列表 -->
    <el-card class="section-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <span>🏥 基层医疗机构（乡镇卫生院）</span>
          <el-button type="primary" size="small">+ 新增机构</el-button>
        </div>
      </template>
      <el-table :data="stats.townshipClinics" border stripe style="width: 100%">
        <el-table-column prop="name" label="机构名称" min-width="200" />
        <el-table-column prop="totalPatients" label="总患者" width="100" sortable />
        <el-table-column prop="activePatients" label="在管患者" width="100" sortable />
        <el-table-column prop="pendingReferrals" label="待处理转诊" width="120" sortable>
          <template #default="{ row }">
            <el-tag :type="row.pendingReferrals > 0 ? 'warning' : 'success'">
              {{ row.pendingReferrals }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="completedFollowups" label="已完成随访" width="120" sortable />
        <el-table-column prop="lastMonthReferrals" label="上月转诊" width="100" sortable />
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="viewClinic(row)">查看详情</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 转诊流向统计 -->
    <el-card class="section-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <span>📊 转诊流向统计</span>
        </div>
      </template>
      <el-row :gutter="20">
        <el-col :span="12">
          <h4>月度转诊趋势</h4>
          <div v-for="(item, index) in stats.referralFlow.monthlyTrend" :key="index" class="trend-item">
            <span class="month">{{ item.month }}</span>
            <span class="up-count">↑上转：{{ item.upCount }}</span>
            <span class="down-count">↓下转：{{ item.downCount }}</span>
            <span class="rate">完成率：{{ item.completionRate }}%</span>
          </div>
        </el-col>
        <el-col :span="12">
          <h4>响应时效分布</h4>
          <div v-for="(item, index) in responseTimeData" :key="index" class="time-item">
            <span class="range">{{ item.range }}</span>
            <el-progress
              :percentage="Math.round(item.count / totalResponseCount * 100)"
              :stroke-width="10"
              style="flex: 1; margin: 0 10px;"
            />
            <span class="count">{{ item.count }}例</span>
          </div>
          <div style="margin-top: 20px;">
            <el-statistic label="平均响应时间" :value="stats.referralFlow.avgResponseTime" suffix="小时" />
            <el-statistic label="及时响应率" :value="stats.referralFlow.timelyRate" suffix="%" style="margin-top: 10px;" />
          </div>
        </el-col>
      </el-row>
    </el-card>

    <!-- 协同评分详情 -->
    <el-card class="section-card" shadow="hover">
      <template #header>
        <div class="card-header">
          <span>📈 县乡协同评分详情</span>
        </div>
      </template>
      <el-descriptions :column="2" border>
        <el-descriptions-item label="转诊完成率">{{ stats.countyHospital.completionRate }}%</el-descriptions-item>
        <el-descriptions-item label="及时响应率">{{ stats.referralFlow.timelyRate }}%</el-descriptions-item>
        <el-descriptions-item label="基层就诊率">{{ townshipVisitRate }}%</el-descriptions-item>
        <el-descriptions-item label="上转占比">{{ (stats.referralFlow.totalUp / (stats.referralFlow.totalUp + stats.referralFlow.totalDown) * 100).toFixed(1) }}%</el-descriptions-item>
        <el-descriptions-item label="下转占比">{{ (stats.referralFlow.totalDown / (stats.referralFlow.totalUp + stats.referralFlow.totalDown) * 100).toFixed(1) }}%</el-descriptions-item>
        <el-descriptions-item label="综合评分">
          <el-tag :type="stats.collaborationScore >= 90 ? 'success' : stats.collaborationScore >= 75 ? 'warning' : 'danger'" size="large">
            {{ stats.collaborationScore }}分
          </el-tag>
        </el-descriptions-item>
      </el-descriptions>
    </el-card>
    <!-- 机构详情对话框 -->
    <el-dialog v-model="clinicVisible" :title="selectedClinic?.name || '机构详情'" width="700px">
      <el-descriptions :column="2" border v-if="selectedClinic">
        <el-descriptions-item label="机构名称">{{ selectedClinic.name }}</el-descriptions-item>
        <el-descriptions-item label="机构代码">{{ selectedClinic.code }}</el-descriptions-item>
        <el-descriptions-item label="总患者数">{{ selectedClinic.totalPatients }}</el-descriptions-item>
        <el-descriptions-item label="在管患者">{{ selectedClinic.activePatients }}</el-descriptions-item>
        <el-descriptions-item label="待处理转诊">
          <el-tag :type="selectedClinic.pendingReferrals > 0 ? 'warning' : 'success'">
            {{ selectedClinic.pendingReferrals }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="已完成随访">{{ selectedClinic.completedFollowups }}</el-descriptions-item>
        <el-descriptions-item label="上月转诊">{{ selectedClinic.lastMonthReferrals }}</el-descriptions-item>
        <el-descriptions-item label="响应时效">
          <el-progress
            :percentage="selectedClinic.completionRate || 0"
            :stroke-width="14"
            :text-inside="true"
          />
        </el-descriptions-item>
      </el-descriptions>
      <template #footer>
        <el-button @click="clinicVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { getCountyTownshipStats, getTownshipVisitRate, getReferralResponseTime } from '@/api/county-township'
import { CountyTownshipStats, ResponseTimeRange } from '@/types/county-township'

const stats = ref<CountyTownshipStats>({
  countyHospital: {
    name: '',
    code: '',
    totalPatients: 0,
    activePatients: 0,
    upReferrals: 0,
    downReferrals: 0,
    completionRate: 0,
  },
  townshipClinics: [],
  referralFlow: {
    totalUp: 0,
    totalDown: 0,
    avgResponseTime: 0,
    timelyRate: 0,
    monthlyTrend: [],
  },
  collaborationScore: 0,
})

const townshipVisitRate = ref<number>(0)
const responseTimeData = ref<ResponseTimeRange[]>([])

const totalResponseCount = computed(() => {
  return responseTimeData.value.reduce((sum, item) => sum + item.count, 0)
})

const loadData = async () => {
  try {
    const [statsRes, rateRes, timeRes] = await Promise.all([
      getCountyTownshipStats(),
      getTownshipVisitRate(),
      getReferralResponseTime(),
    ])
    stats.value = statsRes
    townshipVisitRate.value = rateRes
    responseTimeData.value = timeRes
  } catch (error) {
    console.error('加载县乡协同数据失败：', error)
  }
}

const clinicVisible = ref(false)
const selectedClinic = ref<any>(null)

const viewClinic = (clinic: any) => {
  selectedClinic.value = clinic
  clinicVisible.value = true
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.county-township-view {
  padding: 20px;
}

.header-card {
  margin-bottom: 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.header-card h2 {
  color: white;
  margin: 0;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.section-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: bold;
}

.trend-item {
  display: flex;
  justify-content: space-between;
  padding: 10px;
  border-bottom: 1px solid #ebeef5;
}

.trend-item:last-child {
  border-bottom: none;
}

.month {
  font-weight: bold;
  width: 100px;
}

.up-count {
  color: #f56c6c;
  width: 120px;
}

.down-count {
  color: #67c23a;
  width: 120px;
}

.rate {
  color: #409eff;
}

.time-item {
  display: flex;
  align-items: center;
  padding: 10px;
  border-bottom: 1px solid #ebeef5;
}

.time-item:last-child {
  border-bottom: none;
}

.range {
  width: 80px;
  font-weight: bold;
}

.count {
  width: 80px;
  text-align: right;
  color: #909399;
}
</style>
