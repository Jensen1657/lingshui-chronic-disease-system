import TableSkeleton from "@/components/TableSkeleton.vue"
<template>
  <div class="alert-list">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>预警中心</span>
          <div>
            <el-button type="success" @click="handleBatchProcess">批量处理</el-button>
          </div>
        </div>
      </template>

      <!-- 搜索表单 -->
      <el-form :model="searchForm" inline>
        <el-form-item label="患者编号">
          <el-input v-model="searchForm.patient_id" placeholder="请输入患者编号" clearable />
        </el-form-item>
        <el-form-item label="预警类型">
          <el-select v-model="searchForm.alert_type" placeholder="请选择预警类型" clearable>
            <el-option label="血压偏高" value="BP_HIGH" />
            <el-option label="血压偏低" value="BP_LOW" />
            <el-option label="血糖偏高" value="BG_HIGH" />
            <el-option label="血糖偏低" value="BG_LOW" />
            <el-option label="漏随访" value="MISS_FU" />
            <el-option label="超时未随访" value="TIMEOUT_FU" />
            <el-option label="转诊超时" value="REFERRAL_TIMEOUT" />
          </el-select>
        </el-form-item>
        <el-form-item label="预警级别">
          <el-select v-model="searchForm.alert_level" placeholder="请选择预警级别" clearable>
            <el-option label="低" value="LOW" />
            <el-option label="中" value="MEDIUM" />
            <el-option label="高" value="HIGH" />
            <el-option label="严重" value="CRITICAL" />
          </el-select>
        </el-form-item>
        <el-form-item label="处理状态">
          <el-select v-model="searchForm.is_handled" placeholder="请选择状态" clearable>
            <el-option label="未处理" :value="false" />
            <el-option label="已处理" :value="true" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">搜索</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>

      <!-- 预警表格 -->
      <TableSkeleton v-if="loading" :rows="8" />
        <el-table v-else :data="alertStore.records" v-loading="alertStore.loading" style="width: 100%">
        <el-table-column prop="alert_id" label="预警编号" width="140" />
        <el-table-column prop="patient_name" label="患者姓名" width="100" />
        <el-table-column prop="org_name" label="所属机构" width="140" />
        <el-table-column prop="patient_id" label="患者编号" width="100">
          <template #default="{ row }">
            {{ row.patient_id || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="alert_type" label="预警类型" width="120">
          <template #default="{ row }">
            <el-tag size="small">{{ alertTypeLabel(row.alert_type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="alert_level" label="预警级别" width="90">
          <template #default="{ row }">
            <el-tag :type="getLevelType(row.alert_level)" size="small">
              {{ getLevelText(row.alert_level) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="alert_title" label="预警标题" width="200" />
        <el-table-column prop="alert_content" label="预警内容" min-width="250">
          <template #default="{ row }">
            <div class="alert-content">{{ row.alert_content }}</div>
          </template>
        </el-table-column>
        <el-table-column prop="is_handled" label="处理状态" width="90">
          <template #default="{ row }">
            <el-tag :type="row.is_handled ? 'success' : 'warning'" size="small">
              {{ row.is_handled ? '已处理' : '未处理' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="handled_by" label="处理人" width="100">
          <template #default="{ row }">
            {{ row.handled_by || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="160">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="handleView(row)">查看</el-button>
            <el-button
              v-if="!row.is_handled"
              type="success"
              size="small"
              @click="handleProcess(row)"
            >
              处理
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.page_size"
          :page-sizes="[10, 20, 50, 100]"
          :total="alertStore.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { reactive, onMounted } from 'vue'
import { useAlertStore } from '@/stores/alert'
import { ElMessage } from 'element-plus'
import type { Alert } from '@/types/alert'

const alertStore = useAlertStore()

const searchForm = reactive({
  patient_id: '',
  alert_type: '',
  alert_level: '',
  is_handled: '' as boolean | ''
})

const pagination = reactive({
  page: 1,
  page_size: 20
})

const handleBatchProcess = () => {
  ElMessage.warning('请选择要处理的预警记录')
}

const handleView = (row: Alert) => {
  router.push(`/alerts/${row.alert_id}`)
}

const handleProcess = (row: Alert) => {
  router.push(`/alerts/${row.alert_id}/handle`)
}

const handleSearch = () => {
  pagination.page = 1
  loadData()
}

const handleReset = () => {
  Object.assign(searchForm, {
    patient_id: '',
    alert_type: '',
    alert_level: '',
    is_handled: ''
  })
  pagination.page = 1
  loadData()
}

const handleSizeChange = (size: number) => {
  pagination.page_size = size
  loadData()
}

const handleCurrentChange = (page: number) => {
  pagination.page = page
  loadData()
}

const loadData = async () => {
  const params: any = {
    page: pagination.page,
    page_size: pagination.page_size
  }

  if (searchForm.patient_id) params.patient_id = searchForm.patient_id
  if (searchForm.alert_type) params.alert_type = searchForm.alert_type
  if (searchForm.alert_level) params.alert_level = searchForm.alert_level
  if (searchForm.is_handled !== '') params.is_handled = searchForm.is_handled

  await alertStore.fetchRecords(params)
}

function alertTypeLabel(type: string) {
  const map: Record<string, string> = {
    'BP_HIGH': '血压偏高',
    'BP_LOW': '血压偏低',
    'BG_HIGH': '血糖偏高',
    'BG_LOW': '血糖偏低',
    'MISS_FU': '漏随访',
    'TIMEOUT_FU': '超时未随访',
    'REFERRAL_TIMEOUT': '转诊超时',
    'MEDICATION_MISS': '漏服药',
    'RISK_UPGRADE': '风险升级',
    'ABNORMAL_VITALS': '生命体征异常'
  }
  return map[type] || type || '-'
}

function getLevelType(level: string) {
  const map: Record<string, string> = {
    'LOW': 'info',
    'MEDIUM': 'warning',
    'HIGH': 'danger',
    'CRITICAL': 'danger'
  }
  return map[level] || 'info'
}

function getLevelText(level: string) {
  const map: Record<string, string> = {
    'LOW': '低',
    'MEDIUM': '中',
    'HIGH': '高',
    'CRITICAL': '严重'
  }
  return map[level] || level
}

function formatDateTime(dateStr: string) {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.alert-list {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.alert-content {
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}
</style>
