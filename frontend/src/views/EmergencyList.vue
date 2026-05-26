import TableSkeleton from "@/components/TableSkeleton.vue"
<template>
  <div class="emergency-list">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>急救联动列表</span>
          <el-button type="primary" @click="handleCreate">新增急救记录</el-button>
        </div>
      </template>

      <!-- 搜索表单 -->
      <el-form :model="searchForm" inline>
        <el-form-item label="患者姓名">
          <el-input v-model="searchForm.patient_name" placeholder="请输入患者姓名" clearable />
        </el-form-item>
        <el-form-item label="急救类型">
          <el-select v-model="searchForm.alert_type" placeholder="请选择急救类型" clearable>
            <el-option label="心脏骤停" value="cardiac_arrest" />
            <el-option label="脑卒中" value="stroke" />
            <el-option label="呼吸衰竭" value="respiratory_failure" />
            <el-option label="高血压危象" value="severe_hypertension" />
            <el-option label="低血糖" value="hypoglycemia" />
            <el-option label="高血糖" value="hyperglycemia" />
            <el-option label="其他" value="other" />
          </el-select>
        </el-form-item>
        <el-form-item label="急救状态">
          <el-select v-model="searchForm.status" placeholder="请选择状态" clearable>
            <el-option label="已报告" value="reported" />
            <el-option label="处理中" value="processing" />
            <el-option label="已完成" value="completed" />
            <el-option label="已取消" value="cancelled" />
          </el-select>
        </el-form-item>
        <el-form-item label="急救时间">
          <el-date-picker
            v-model="searchForm.date_range"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">搜索</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>

      <!-- 急救表格 -->
      <TableSkeleton v-if="loading" :rows="8" />
        <el-table v-else :data="emergencyStore.records" v-loading="emergencyStore.loading" style="width: 100%">
        <el-table-column prop="patient_id" label="患者ID" width="90" />
        <el-table-column prop="patient_name" label="患者姓名" width="100" />
        <el-table-column prop="org_name" label="所属机构" width="150" />
        <el-table-column prop="doctor_name" label="在管医生" width="100" />
        <el-table-column prop="alert_type" label="急救类型" width="120">
          <template #default="{ row }">
            <el-tag type="danger">{{ getEmergencyTypeText(row.alert_type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="trigger_at" label="急救时间" width="120" />
        <el-table-column prop="status" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="handleView(row)">查看</el-button>
            <el-button
              v-if="row.status === 'ACTIVATED'"
              type="success"
              size="small"
              @click="handleProcess(row)"
            >处理</el-button>
            <el-button
              v-if="row.status === 'PROCESSING'"
              type="warning"
              size="small"
              @click="handleComplete(row)"
            >完成</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.page_size"
          :page-sizes="[10, 20, 50, 100]"
          :total="emergencyStore.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- 新增/编辑对话框 -->
    <EmergencyForm
      v-model:visible="dialogVisible"
      :record="currentRecord"
      @success="handleSuccess"
    />

    <!-- 处理/完成对话框 -->
    <el-dialog v-model="actionDialogVisible" :title="actionDialogTitle" width="500px">
      <el-form :model="actionForm" label-width="100px">
        <el-form-item v-if="actionType === 'process'" label="处理措施" prop="treatment_measures">
          <el-input
            v-model="actionForm.treatment_measures"
            type="textarea"
            :rows="3"
            placeholder="请输入处理措施"
          />
        </el-form-item>
        <el-form-item v-if="actionType === 'complete'" label="转归" prop="outcome">
          <el-select v-model="actionForm.outcome" placeholder="请选择转归">
            <el-option label="痊愈" value="recovered" />
            <el-option label="好转" value="improved" />
            <el-option label="未变化" value="unchanged" />
            <el-option label="恶化" value="aggravated" />
            <el-option label="死亡" value="died" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="actionType === 'complete'" label="出院诊断" prop="discharge_diagnosis">
          <el-input
            v-model="actionForm.discharge_diagnosis"
            type="textarea"
            :rows="3"
            placeholder="请输入出院诊断"
          />
        </el-form-item>
        <el-form-item v-if="actionType === 'complete'" label="随访计划" prop="followup_plan">
          <el-input
            v-model="actionForm.followup_plan"
            type="textarea"
            :rows="3"
            placeholder="请输入随访计划"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="actionDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleActionSubmit" :loading="actionLoading">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useEmergencyStore } from '@/stores/emergency'
import EmergencyForm from '@/components/EmergencyForm.vue'
import type { EmergencyRecord } from '@/types/emergency'

const emergencyStore = useEmergencyStore()

const dialogVisible = ref(false)
const currentRecord = ref<EmergencyRecord | null>(null)

const actionDialogVisible = ref(false)
const actionDialogTitle = ref('')
const actionType = ref('') // 'process', 'complete'
const actionLoading = ref(false)
const actionForm = reactive({
  treatment_measures: '',
  outcome: '',
  discharge_diagnosis: '',
  followup_plan: ''
})
const currentActionId = ref('')

const searchForm = reactive({
  patient_id: '',
  alert_type: '',
  status: '',
  date_range: []
})

const pagination = reactive({
  page: 1,
  page_size: 20
})

const handleCreate = () => {
  currentRecord.value = null
  dialogVisible.value = true
}

const handleView = (row: EmergencyRecord) => {
  currentRecord.value = row
  dialogVisible.value = true
}

const handleProcess = (row: EmergencyRecord) => {
  currentActionId.value = row.id
  actionType.value = 'process'
  actionDialogTitle.value = '处理急救'
  actionForm.treatment_measures = ''
  actionDialogVisible.value = true
}

const handleComplete = (row: EmergencyRecord) => {
  currentActionId.value = row.id
  actionType.value = 'complete'
  actionDialogTitle.value = '完成急救'
  actionForm.outcome = ''
  actionForm.discharge_diagnosis = ''
  actionForm.followup_plan = ''
  actionDialogVisible.value = true
}

const handleActionSubmit = async () => {
  try {
    actionLoading.value = true

    if (actionType.value === 'process') {
      await emergencyStore.processRecord(currentActionId.value, {
        treatment_measures: actionForm.treatment_measures
      })
      ElMessage.success('急救已开始处理')
    } else if (actionType.value === 'complete') {
      if (!actionForm.outcome) {
        ElMessage.warning('请选择转归')
        return
      }
      await emergencyStore.completeRecord(currentActionId.value, {
        outcome: actionForm.outcome,
        discharge_diagnosis: actionForm.discharge_diagnosis,
        followup_plan: actionForm.followup_plan
      })
      ElMessage.success('急救已完成')
    }

    actionDialogVisible.value = false
    loadData()
  } catch (error) {
    // 错误已由 request.ts 拦截器统一提示
  } finally {
    actionLoading.value = false
  }
}

const handleSearch = () => {
  pagination.page = 1
  loadData()
}

const handleReset = () => {
  searchForm.patient_id = ''
  searchForm.alert_type = ''
  searchForm.status = ''
  searchForm.date_range = []
  pagination.page = 1
  loadData()
}

const handleSizeChange = (val: number) => {
  pagination.page_size = val
  loadData()
}

const handleCurrentChange = (val: number) => {
  pagination.page = val
  loadData()
}

const handleSuccess = () => {
  dialogVisible.value = false
  loadData()
}

const loadData = async () => {
  const params: any = {
    page: pagination.page,
    page_size: pagination.page_size
  }

  if (searchForm.patient_id) params.patient_id = searchForm.patient_id
  if (searchForm.alert_type) params.alert_type = searchForm.alert_type
  if (searchForm.status) params.status = searchForm.status
  if (searchForm.date_range && searchForm.date_range.length === 2) {
    params.start_time = searchForm.date_range[0]
    params.end_time = searchForm.date_range[1]
  }

  await emergencyStore.fetchRecords(params)
}

const getEmergencyTypeText = (type: string) => {
  const map: Record<string, string> = {
    // 小写（搜索表单用）
    'cardiac_arrest': '心脏骤停',
    'stroke': '脑卒中',
    'respiratory_failure': '呼吸衰竭',
    'severe_hypertension': '高血压危象',
    'hypoglycemia': '低血糖',
    'hyperglycemia': '高血糖',
    'other': '其他',
    // 大写（后端返回值）
    'CARDIAC_ARREST': '心脏骤停',
    'STROKE_SUSPECT': '疑似脑卒中',
    'SEVERE_DYSPNEA': '严重呼吸困难',
    'HYPERTENSIVE_CRISIS': '高血压危象',
    'HYPOGLYCEMIA': '低血糖昏迷',
    'HYPERGLYCEMIA': '高血糖危象',
    'SEVERE_ARRHYTHMIA': '严重心律失常',
    'ACUTE_CORONARY': '急性冠脉综合征'
  }
  return map[type] || type
}

const getStatusType = (status: string) => {
  const map: Record<string, string> = {
    'reported': 'danger', 'REPORTED': 'danger',
    'processing': 'warning', 'PROCESSING': 'warning',
    'completed': 'success', 'COMPLETED': 'success',
    'cancelled': 'info', 'CANCELLED': 'info',
    'ACTIVATED': 'danger',
    'ARRIVED': 'success',
    'IN_TRANSIT': 'warning'
  }
  return map[status] || 'info'
}

const getStatusText = (status: string) => {
  const map: Record<string, string> = {
    'reported': '已报告', 'REPORTED': '已报告',
    'processing': '处理中', 'PROCESSING': '处理中',
    'completed': '已完成', 'COMPLETED': '已完成',
    'cancelled': '已取消', 'CANCELLED': '已取消',
    'ACTIVATED': '已激活',
    'ARRIVED': '已到达',
    'IN_TRANSIT': '转运中',
    'PROCESSING': '处理中',
    'CANCELLED': '已取消',
    'COMPLETED': '已完成'
  }
  return map[status] || status
}

const getOutcomeType = (outcome: string) => {
  const map: Record<string, string> = {
    'recovered': 'success',
    'improved': 'success',
    'unchanged': 'warning',
    'aggravated': 'danger',
    'died': 'danger'
  }
  return map[outcome] || 'info'
}

const getOutcomeText = (outcome: string) => {
  const map: Record<string, string> = {
    'recovered': '痊愈',
    'improved': '好转',
    'unchanged': '未变化',
    'aggravated': '恶化',
    'died': '死亡'
  }
  return map[outcome] || outcome
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.emergency-list {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.pagination-container {
  margin-top: 20px;
  text-align: right;
}
</style>