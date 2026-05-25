import TableSkeleton from "@/components/TableSkeleton.vue"
<template>
  <div class="referral-list">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>转诊记录列表</span>
          <el-button type="primary" @click="handleCreate">新增转诊</el-button>
        </div>
      </template>

      <!-- 搜索表单 -->
      <el-form :model="searchForm" inline>
        <el-form-item label="患者编号">
          <el-input v-model="searchForm.patient_id" placeholder="请输入患者编号" clearable />
        </el-form-item>
        <el-form-item label="转诊类型">
          <el-select v-model="searchForm.referral_type" placeholder="请选择转诊类型" clearable>
            <el-option label="上转" value="UP" />
            <el-option label="下转" value="DOWN" />
          </el-select>
        </el-form-item>
        <el-form-item label="转诊状态">
          <el-select v-model="searchForm.status" placeholder="请选择状态" clearable>
            <el-option label="待处理" value="PENDING" />
            <el-option label="已接受" value="ACCEPTED" />
            <el-option label="已拒绝" value="REJECTED" />
            <el-option label="已完成" value="COMPLETED" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">搜索</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>

      <!-- 转诊表格 -->
      <TableSkeleton v-if="loading" :rows="8" />
        <el-table v-else :data="referralStore.records" v-loading="referralStore.loading" style="width: 100%">
        <el-table-column prop="referral_id" label="转诊编号" width="120" />
        <el-table-column prop="patient_name" label="患者姓名" width="100" />
        <el-table-column prop="patient_id" label="患者编号" width="100" />
        <el-table-column prop="disease_code" label="慢病类型" width="100">
          <template #default="{ row }">
            <el-tag size="small">{{ diseaseLabel(row.disease_code) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="referral_type" label="转诊类型" width="80">
          <template #default="{ row }">
            <el-tag :type="row.referral_type === 'UP' ? 'warning' : 'success'" size="small">
              {{ row.referral_type === 'UP' ? '上转' : '下转' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="apply_org_name" label="申请机构" width="140" />
        <el-table-column prop="receive_org_name" label="接收机构" width="140">
          <template #default="{ row }">
            {{ row.receive_org_name || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="apply_at" label="申请时间" width="160">
          <template #default="{ row }">
            {{ formatDateTime(row.apply_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="is_eligible" label="资格" width="80">
          <template #default="{ row }">
            <el-tag v-if="row.is_eligible === true" type="success" size="small">符合</el-tag>
            <el-tag v-else-if="row.is_eligible === false" type="danger" size="small">不符</el-tag>
            <span v-else>-</span>
          </template>
        </el-table-column>
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
          :total="referralStore.total"
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
import { useRouter } from 'vue-router'
import { useReferralStore } from '@/stores/referral'
import { ElMessage } from 'element-plus'
import type { ReferralRecord } from '@/types/referral'

const router = useRouter()
const referralStore = useReferralStore()

const searchForm = reactive({
  patient_id: '',
  referral_type: '',
  status: ''
})

const pagination = reactive({
  page: 1,
  page_size: 20
})

const handleCreate = () => {
  router.push('/referrals/create')
}

const handleView = (row: ReferralRecord) => {
  router.push(`/referrals/${row.referral_id}`)
}

const handleEdit = (row: ReferralRecord) => {
  router.push(`/referrals/${row.referral_id}/edit`)
}

const handleSearch = () => {
  pagination.page = 1
  loadData()
}

const handleReset = () => {
  Object.assign(searchForm, {
    patient_id: '',
    referral_type: '',
    status: ''
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
  if (searchForm.referral_type) params.referral_type = searchForm.referral_type
  if (searchForm.status) params.status = searchForm.status

  await referralStore.fetchRecords(params)
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
  return map[disease] || disease || '-'
}

function getStatusType(status: string) {
  const map: Record<string, string> = {
    'PENDING': 'warning',
    'ACCEPTED': 'primary',
    'REJECTED': 'danger',
    'COMPLETED': 'success'
  }
  return map[status] || 'info'
}

function getStatusText(status: string) {
  const map: Record<string, string> = {
    'PENDING': '待处理',
    'ACCEPTED': '已接受',
    'REJECTED': '已拒绝',
    'COMPLETED': '已完成',
    'CANCELLED': '已取消',
    'IN_PROGRESS': '转诊中'
  }
  return map[status] || status
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
.referral-list {
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
