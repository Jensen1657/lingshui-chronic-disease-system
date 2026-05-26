import TableSkeleton from "@/components/TableSkeleton.vue"
<template>
  <div class="followup-list">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>随访记录列表</span>
          <div>
            <el-button type="success" @click="handleExport" :loading="exporting">导出</el-button>
            <el-button type="primary" @click="handleCreate">新增随访</el-button>
          </div>
        </div>
      </template>

      <!-- 搜索表单 -->
      <el-form :model="searchForm" inline>
        <el-form-item label="患者编号">
          <el-input v-model="searchForm.patient_id" placeholder="请输入患者编号" clearable />
        </el-form-item>
        <el-form-item label="慢病类型">
          <el-select v-model="searchForm.disease_code" placeholder="请选择慢病类型" clearable>
            <el-option label="高血压" value="HYPERTENSION" />
            <el-option label="糖尿病" value="DIABETES" />
            <el-option label="冠心病" value="CORONARY_HEART_DISEASE" />
            <el-option label="脑卒中" value="STROKE" />
            <el-option label="慢阻肺" value="COPD" />
            <el-option label="慢性肾病" value="CKD" />
          </el-select>
        </el-form-item>
        <el-form-item label="控制状态">
          <el-select v-model="searchForm.is_controlled" placeholder="请选择状态" clearable>
            <el-option label="达标" :value="true" />
            <el-option label="未达标" :value="false" />
          </el-select>
        </el-form-item>
        <el-form-item label="审核状态">
          <el-select v-model="searchForm.is_audited" placeholder="请选择状态" clearable>
            <el-option label="已审核" :value="true" />
            <el-option label="待审核" :value="false" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">搜索</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>

      <!-- 随访表格 -->
      <TableSkeleton v-if="loading" :rows="8" />
        <el-table v-else :data="followupStore.records" v-loading="followupStore.loading" style="width: 100%">
        <el-table-column prop="followup_id" label="随访编号" width="120" />
        <el-table-column prop="patient_id" label="患者编号" width="100" />
        <el-table-column prop="patient_name" label="患者姓名" width="100" />
        <el-table-column prop="disease_code" label="慢病类型" width="100">
          <template #default="{ row }">
            <el-tag size="small">{{ diseaseLabel(row.disease_code) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="followup_date" label="随访日期" width="120" />
        <el-table-column label="血压(mmHg)" width="100">
          <template #default="{ row }">
            <span v-if="row.bp_systolic">{{ row.bp_systolic }}/{{ row.bp_diastolic }}</span>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="fbg" label="空腹血糖" width="100">
          <template #default="{ row }">
            <span v-if="row.fbg">{{ row.fbg }} mmol/L</span>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="is_controlled" label="控制状态" width="90">
          <template #default="{ row }">
            <el-tag :type="row.is_controlled ? 'success' : 'warning'" size="small">
              {{ row.is_controlled ? '达标' : '未达标' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="performed_by" label="随访医生" width="100" />
        <el-table-column prop="org_name" label="所属机构" width="140" />
        <el-table-column prop="is_audited" label="审核状态" width="90">
          <template #default="{ row }">
            <el-tag :type="row.is_audited ? 'success' : 'info'" size="small">
              {{ row.is_audited ? '已审核' : '待审核' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="next_followup_date" label="下次随访" width="120" />
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="handleView(row)">查看</el-button>
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
          :total="followupStore.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useFollowupStore } from '@/stores/followup'
import type { FollowupRecord } from '@/types/followup'

const router = useRouter()
const followupStore = useFollowupStore()
const exporting = ref(false)

const searchForm = reactive({
  patient_id: '',
  disease_code: '',
  is_controlled: '' as boolean | '',
  is_audited: '' as boolean | ''
})

const pagination = reactive({
  page: 1,
  page_size: 20
})

const handleCreate = () => {
  router.push('/followups/create')
}

const handleView = (row: FollowupRecord) => {
  router.push(`/followups/${row.followup_id}`)
}

const handleEdit = (row: FollowupRecord) => {
  router.push(`/followups/${row.followup_id}/edit`)
}

const handleSearch = () => {
  pagination.page = 1
  loadData()
}

const handleReset = () => {
  Object.assign(searchForm, {
    patient_id: '',
    disease_code: '',
    is_controlled: '',
    is_audited: ''
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

const handleExport = async () => {
  try {
    exporting.value = true
    ElMessage.info('正在导出数据，请稍候...')
    
    // 构建查询参数
    const params = new URLSearchParams()
    if (searchForm.patient_id) params.append('patient_id', searchForm.patient_id)
    if (searchForm.disease_code) params.append('disease_code', searchForm.disease_code)
    if (searchForm.is_controlled !== '') params.append('is_controlled', String(searchForm.is_controlled))
    if (searchForm.is_audited !== '') params.append('is_audited', String(searchForm.is_audited))
    
    const response = await fetch(`/api/v1/followups/export?${params.toString()}`, {
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
    link.setAttribute('download', `随访记录_${new Date().toISOString().split('T')[0]}.csv`)
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
  const params: any = {
    page: pagination.page,
    page_size: pagination.page_size
  }

  if (searchForm.patient_id) params.patient_id = searchForm.patient_id
  if (searchForm.disease_code) params.disease_code = searchForm.disease_code
  if (searchForm.is_controlled !== '') params.is_controlled = searchForm.is_controlled
  if (searchForm.is_audited !== '') params.is_audited = searchForm.is_audited

  await followupStore.fetchRecords(params)
}

function diseaseLabel(disease: string) {
  const map: Record<string, string> = {
    'HYPERTENSION': '高血压',
    'DIABETES': '糖尿病',
    'CORONARY': '冠心病',
    'CORONARY_HEART_DISEASE': '冠心病',
    'I10': '高血压',
    'E11': '糖尿病',
    'I20': '冠心病',
    'STROKE': '脑卒中',
    'COPD': '慢阻肺',
    'CKD': '慢性肾病'
  }
  return map[disease] || disease
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.followup-list {
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
</style>
