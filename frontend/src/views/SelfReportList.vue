import TableSkeleton from "@/components/TableSkeleton.vue"
<template>
  <div class="self-report-list">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>自报健康数据列表</span>
          <el-button type="primary" @click="handleCreate">新增自报数据</el-button>
        </div>
      </template>

      <!-- 搜索表单 -->
      <el-form :model="searchForm" inline>
        <el-form-item label="患者ID">
          <el-input v-model="searchForm.patient_id" placeholder="请输入患者ID" clearable />
        </el-form-item>
        <el-form-item label="数据类型">
          <el-select v-model="searchForm.report_type" placeholder="请选择数据类型" clearable>
            <el-option label="血压" value="blood_pressure" />
            <el-option label="血糖" value="blood_sugar" />
            <el-option label="体重" value="weight" />
            <el-option label="心率" value="heart_rate" />
            <el-option label="步数" value="steps" />
            <el-option label="睡眠" value="sleep" />
            <el-option label="症状" value="symptom" />
            <el-option label="用药" value="medication" />
            <el-option label="其他" value="other" />
          </el-select>
        </el-form-item>
        <el-form-item label="核实状态">
          <el-select v-model="searchForm.verified" placeholder="请选择状态" clearable>
            <el-option label="待核实" :value="false" />
            <el-option label="已核实" :value="true" />
          </el-select>
        </el-form-item>
        <el-form-item label="上报日期">
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

      <!-- 自报数据表格 -->
      <TableSkeleton v-if="loading" :rows="8" />
        <el-table v-else :data="selfReportStore.reports" v-loading="selfReportStore.loading" style="width: 100%">
        <el-table-column prop="patient_name" label="患者姓名" width="100" />
        <el-table-column prop="org_name" label="所属机构" width="140" />
        <el-table-column prop="patient_id" label="患者ID" width="100" />
        <el-table-column prop="report_type" label="数据类型" width="100">
          <template #default="{ row }">
            <el-tag>{{ getReportTypeText(row.report_type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="report_date" label="上报日期" width="120" />
        <el-table-column prop="data_source" label="数据来源" width="100">
          <template #default="{ row }">
            <el-tag :type="row.data_source === 'device' ? 'success' : 'info'">
              {{ getDataSourceText(row.data_source) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="verified" label="核实状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.verified ? 'success' : 'warning'">
              {{ row.verified ? '已核实' : '待核实' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="report_value" label="数据值" width="150" show-overflow-tooltip>
          <template #default="{ row }">
            {{ row.report_value }}{{ row.report_unit ? ' ' + row.report_unit : '' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="250" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="handleView(row)">查看</el-button>
            <el-button
              v-if="!row.verified"
              type="success"
              size="small"
              @click="handleVerify(row)"
            >核实</el-button>
            <el-button
              v-if="!row.verified"
              type="danger"
              size="small"
              @click="handleReject(row)"
            >驳回</el-button>
            <el-button type="warning" size="small" @click="handleEdit(row)">编辑</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.page_size"
          :page-sizes="[10, 20, 50, 100]"
          :total="selfReportStore.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- 新增/编辑对话框 -->
    <SelfReportForm
      v-model:visible="dialogVisible"
      :report="currentReport"
      @success="handleSuccess"
    />

    <!-- 核实/驳回对话框 -->
    <el-dialog v-model="verifyDialogVisible" :title="verifyDialogTitle" width="500px">
      <el-form :model="verifyForm" label-width="100px">
        <el-form-item label="核实意见" prop="verification_comment">
          <el-input
            v-model="verifyForm.verification_comment"
            type="textarea"
            :rows="3"
            placeholder="请输入核实意见"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="verifyDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleVerifySubmit" :loading="verifyLoading">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useSelfReportStore } from '@/stores/selfReport'
import SelfReportForm from '@/components/SelfReportForm.vue'
import type { SelfReportRecord } from '@/types/self-report'

const selfReportStore = useSelfReportStore()

const dialogVisible = ref(false)
const currentReport = ref<SelfReportRecord | null>(null)

const verifyDialogVisible = ref(false)
const verifyDialogTitle = ref('')
const verifyLoading = ref(false)
const verifyForm = reactive({
  verification_comment: '',
  is_approved: true
})
const currentVerifyId = ref('')

const searchForm = reactive({
  patient_id: '',
  report_type: '',
  verified: '',
  date_range: []
})

const pagination = reactive({
  page: 1,
  page_size: 20
})

const handleCreate = () => {
  currentReport.value = null
  dialogVisible.value = true
}

const handleView = (row: SelfReportRecord) => {
  console.log('View self-report:', row.id)
}

const handleVerify = (row: SelfReportRecord) => {
  currentVerifyId.value = row.id
  verifyDialogTitle.value = '核实自报数据'
  verifyForm.verification_comment = ''
  verifyForm.is_approved = true
  verifyDialogVisible.value = true
}

const handleReject = (row: SelfReportRecord) => {
  currentVerifyId.value = row.id
  verifyDialogTitle.value = '驳回自报数据'
  verifyForm.verification_comment = ''
  verifyForm.is_approved = false
  verifyDialogVisible.value = true
}

const handleVerifySubmit = async () => {
  try {
    verifyLoading.value = true
    if (verifyForm.is_approved) {
      await selfReportStore.verifyReport(currentVerifyId.value, {
        verification_comment: verifyForm.verification_comment,
        is_approved: true
      })
      ElMessage.success('自报数据已核实')
    } else {
      if (!verifyForm.verification_comment) {
        ElMessage.warning('驳回时请输入核实意见')
        return
      }
      await selfReportStore.rejectReport(currentVerifyId.value, verifyForm.verification_comment)
      ElMessage.success('自报数据已驳回')
    }
    verifyDialogVisible.value = false
    loadData()
  } catch (error) {
    // 错误已由 request.ts 拦截器统一提示
  } finally {
    verifyLoading.value = false
  }
}

const handleEdit = (row: SelfReportRecord) => {
  currentReport.value = row
  dialogVisible.value = true
}

const handleSearch = () => {
  pagination.page = 1
  loadData()
}

const handleReset = () => {
  searchForm.patient_id = ''
  searchForm.report_type = ''
  searchForm.verified = ''
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
  if (searchForm.report_type) params.report_type = searchForm.report_type
  if (searchForm.verified !== '') params.is_verified = searchForm.verified
  if (searchForm.date_range && searchForm.date_range.length === 2) {
    params.start_date = searchForm.date_range[0]
    params.end_date = searchForm.date_range[1]
  }

  await selfReportStore.fetchReports(params)
}

const getReportTypeText = (type: string) => {
  const map: Record<string, string> = {
    'blood_pressure': '血压', 'BLOOD_PRESSURE': '血压',
    'blood_sugar': '血糖', 'BLOOD_SUGAR': '血糖',
    'weight': '体重', 'WEIGHT': '体重',
    'heart_rate': '心率', 'HEART_RATE': '心率',
    'steps': '步数', 'STEPS': '步数',
    'sleep': '睡眠', 'SLEEP': '睡眠',
    'symptom': '症状', 'SYMPTOM': '症状',
    'medication': '用药', 'MEDICATION': '用药',
    'other': '其他', 'OTHER': '其他'
  }
  return map[type] || type
}

const getDataSourceText = (source: string) => {
  const map: Record<string, string> = {
    'manual': '手动录入', 'MANUAL': '手动录入',
    'device': '设备同步', 'DEVICE': '设备同步',
    'wechat': '微信上报', 'WECHAT': '微信上报'
  }
  return map[source] || source
}

const getVerificationStatusType = (status: string) => {
  const map: Record<string, string> = {
    'pending': 'warning',
    'verified': 'success',
    'rejected': 'danger'
  }
  return map[status] || 'info'
}

const getVerificationStatusText = (status: string) => {
  const map: Record<string, string> = {
    'pending': '待核实',
    'verified': '已核实',
    'rejected': '已驳回'
  }
  return map[status] || status
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.self-report-list {
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