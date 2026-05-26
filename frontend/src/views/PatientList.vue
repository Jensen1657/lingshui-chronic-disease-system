import TableSkeleton from "@/components/TableSkeleton.vue"
<template>
  <div class="patient-list">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>患者列表</span>
          <div>
            <el-button type="success" @click="handleExport" :loading="exporting">导出</el-button>
            <el-button type="primary" @click="handleCreate">新增患者</el-button>
          </div>
        </div>
      </template>

      <!-- 搜索表单 -->
      <el-form :model="searchForm" inline>
        <el-form-item label="搜索患者">
          <el-input v-model="searchForm.search" placeholder="请输入患者姓名 / ID / 手机号码" clearable style="width: 280px" />
        </el-form-item>
        <el-form-item label="机构编码">
          <el-input v-model="searchForm.manage_org_code" placeholder="请输入机构编码" clearable />
        </el-form-item>
        <el-form-item label="慢病类型">
          <el-select v-model="searchForm.disease_code" placeholder="请选择慢病类型" clearable>
            <el-option label="高血压" value="HYPERTENSION" />
            <el-option label="糖尿病" value="DIABETES" />
            <el-option label="冠心病" value="CORONARY" />
            <el-option label="脑卒中" value="STROKE" />
            <el-option label="慢阻肺" value="COPD" />
            <el-option label="慢性肾病" value="CKD" />
          </el-select>
        </el-form-item>
        <el-form-item label="风险等级">
          <el-select v-model="searchForm.risk_level" placeholder="请选择风险等级" clearable>
            <el-option label="低风险" value="LOW" />
            <el-option label="中风险" value="MEDIUM" />
            <el-option label="高风险" value="HIGH" />
            <el-option label="极高风险" value="VERY_HIGH" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="searchForm.is_active" placeholder="请选择状态" clearable>
            <el-option label="活跃" :value="true" />
            <el-option label="非活跃" :value="false" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">搜索</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>

      <!-- 患者表格 -->
      <TableSkeleton v-if="patientStore.loading" :rows="8" />
        <el-table v-else :data="patientStore.patients"  style="width: 100%">
        <el-table-column prop="patient_id" label="患者编号" width="120" />
        <el-table-column prop="name" label="姓名" width="100" />
        <el-table-column prop="gender" label="性别" width="60">
          <template #default="{ row }">
            {{ row.gender === 'M' ? '男' : row.gender === 'F' ? '女' : '其他' }}
          </template>
        </el-table-column>
        <el-table-column prop="age" label="年龄" width="60" />
        <el-table-column prop="phone" label="联系电话" width="120" />
        <el-table-column prop="disease_names" label="慢病类型" width="150">
          <template #default="{ row }">
            <el-tag v-for="(disease, idx) in (row.disease_names && row.disease_names.length ? row.disease_names : row.disease_list)" :key="idx" size="small" style="margin-right: 4px">
              {{ diseaseLabel(disease) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="manage_org_name" label="所属机构" width="150" />
        <el-table-column prop="risk_level" label="风险等级" width="100">
          <template #default="{ row }">
            <el-tag :type="getRiskLevelType(row.risk_level)">{{ riskLevelLabel(row.risk_level) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="handleView(row)">查看</el-button>
            <el-button type="warning" size="small" @click="handleEdit(row)">编辑</el-button>
            <el-button type="danger" size="small" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.page_size"
          :page-sizes="[10, 20, 50, 100]"
          :total="patientStore.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- 新增/编辑对话框 -->
    <PatientForm
      :model-value="dialogVisible"
      @update:model-value="dialogVisible = $event"
      :patient="currentPatient"
      @success="handleSuccess"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { usePatientStore } from '@/stores/patient'
import PatientForm from '@/components/PatientForm.vue'
import type { Patient } from '@/types/patient'

const router = useRouter()
const patientStore = usePatientStore()
const exporting = ref(false)

const dialogVisible = ref(false)
const currentPatient = ref<Patient | null>(null)

const searchForm = reactive({
  search: '',
  manage_org_code: '',
  disease_code: '',
  risk_level: '',
  is_active: true
})

const pagination = reactive({
  skip: 0,
  limit: 20,
  page: 1
})

const handleCreate = () => {
  currentPatient.value = null
  dialogVisible.value = true
}

const handleView = (row: Patient) => {
  router.push(`/patients/${row.patient_id}`)
}

const handleEdit = (row: Patient) => {
  currentPatient.value = row
  dialogVisible.value = true
}

const handleDelete = async (row: Patient) => {
  try {
    await ElMessageBox.confirm('确定要删除该患者吗？', '提示', { type: 'warning' })
    await patientStore.deletePatient(row.patient_id)
    ElMessage.success('删除成功')
    loadData()
  } catch (error: any) {
    // 错误已由 request.ts 拦截器统一提示
  }
}

const handleSearch = () => { pagination.skip = 0; pagination.page = 1; loadData() }

const handleReset = () => {
  searchForm.search = ''
  searchForm.manage_org_code = ''
  searchForm.disease_code = ''
  searchForm.risk_level = ''
  searchForm.is_active = true
  pagination.skip = 0
  pagination.page = 1
  loadData()
}

const handleSizeChange = (val: number) => {
  pagination.limit = val
  pagination.skip = (pagination.page - 1) * val
  loadData()
}

const handleCurrentChange = (val: number) => {
  pagination.page = val
  pagination.skip = (val - 1) * pagination.limit
  loadData()
}

const handleSuccess = () => { dialogVisible.value = false; loadData() }

const handleExport = async () => {
  try {
    exporting.value = true
    ElMessage.info('正在导出数据，请稍候...')
    
    // 调用导出 API
    const params = new URLSearchParams()
    if (searchForm.search) params.append('search', searchForm.search)
    if (searchForm.manage_org_code) params.append('manage_org_code', searchForm.manage_org_code)
    if (searchForm.disease_code) params.append('disease_code', searchForm.disease_code)
    if (searchForm.risk_level) params.append('risk_level', searchForm.risk_level)
    if (searchForm.is_active !== null && searchForm.is_active !== undefined) {
      params.append('is_active', String(searchForm.is_active))
    }
    
    const response = await fetch(`/api/v1/patients/export?${params.toString()}`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    })
    
    if (!response.ok) {
      throw new Error('导出失败')
    }
    
    const data = await response.json()
    
    // 创建 Blob 并触发下载
    const blob = new Blob([data.reportText], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    const url = URL.createObjectURL(blob)
    link.setAttribute('href', url)
    link.setAttribute('download', `患者列表_${new Date().toISOString().split('T')[0]}.csv`)
    link.style.visibility = 'hidden'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    
    ElMessage.success('导出成功')
  } catch (error: any) {
    // 错误已由 request.ts 拦截器统一提示
  } finally {
    exporting.value = false
  }
}

const loadData = async () => {
  await patientStore.fetchPatients({
    ...searchForm,
    skip: pagination.skip,
    limit: pagination.limit
  })
}

const getRiskLevelType = (riskLevel: string) => {
  const map: Record<string, string> = { 'LOW': 'success', 'MEDIUM': 'warning', 'HIGH': 'danger', 'VERY_HIGH': 'danger' }
  return map[riskLevel] || 'info'
}

const riskLevelLabel = (riskLevel: string) => {
  const map: Record<string, string> = { 'LOW': '低风险', 'MEDIUM': '中风险', 'HIGH': '高风险', 'VERY_HIGH': '极高风险' }
  return map[riskLevel] || riskLevel
}

const diseaseLabel = (disease: string) => {
  const map: Record<string, string> = {
    'HYPERTENSION': '高血压',
    'DIABETES': '糖尿病',
    'CORONARY': '冠心病',
    'CORONARY_HEART_DISEASE': '冠心病',
    'STROKE': '脑卒中',
    'COPD': '慢阻肺',
    'CKD': '慢性肾病',
    'I10': '高血压',
    'I11': '高血压性心脏病',
    'E11': '2型糖尿病',
    'E10': '1型糖尿病',
    '高血压': '高血压',
    '糖尿病': '糖尿病',
    '冠心病': '冠心病',
    '脑卒中': '脑卒中',
    '慢阻肺': '慢阻肺',
    '慢性肾病': '慢性肾病'
  }
  return map[disease] || disease
}

const formatDate = (dateStr: string) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN')
}

onMounted(() => { loadData() })
</script>

<style scoped>
.patient-list { padding: 0; }

.patient-list :deep(.el-card) {
  border-radius: 14px !important;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
  font-size: 16px;
  color: var(--text-primary);
}

.patient-list :deep(.el-form--inline .el-form-item) {
  margin-right: 16px;
  margin-bottom: 12px;
}

/* 操作按钮组 */
.patient-list :deep(.el-table .el-button) {
  padding: 5px 12px;
  font-size: 12px;
}

/* 慢病标签颜色 */
.patient-list :deep(.el-tag) {
  border-radius: 6px !important;
  font-weight: 500 !important;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>
