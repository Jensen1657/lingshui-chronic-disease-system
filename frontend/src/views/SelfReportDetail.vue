<template>
  <div class="self-report-detail">
    <el-page-header @back="goBack" content="自报数据详情" />

    <el-alert v-if="notFound" title="自报记录不存在" type="error" show-icon :closable="false" style="margin-top: 16px;" />

    <el-card v-loading="loading" style="margin-top: 20px;" v-if="!notFound">
      <el-descriptions :column="2" border v-if="record">
        <el-descriptions-item label="患者姓名">{{ record.patient_name }}</el-descriptions-item>
        <el-descriptions-item label="上报日期">{{ formatDate(record.report_date) }}</el-descriptions-item>
        <el-descriptions-item label="上报类型">{{ getReportTypeLabel(record.report_type) }}</el-descriptions-item>
        <el-descriptions-item label="审核状态">
          <el-tag :type="getStatusType(record.status)">{{ getStatusLabel(record.status) }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="血压（mmHg）">{{ record.blood_pressure || '未测' }}</el-descriptions-item>
        <el-descriptions-item label="血糖（mmol/L）">{{ record.blood_sugar || '未测' }}</el-descriptions-item>
        <el-descriptions-item label="心率（次/分）">{{ record.heart_rate || '未测' }}</el-descriptions-item>
        <el-descriptions-item label="体重（kg）">{{ record.weight || '未测' }}</el-descriptions-item>
        <el-descriptions-item label="症状" :span="2">{{ record.symptoms || '无' }}</el-descriptions-item>
        <el-descriptions-item label="用药情况" :span="2">{{ record.medication || '无' }}</el-descriptions-item>
        <el-descriptions-item label="审核人">{{ record.reviewer_name || '未审核' }}</el-descriptions-item>
        <el-descriptions-item label="审核时间">{{ formatDateTime(record.reviewed_at) }}</el-descriptions-item>
        <el-descriptions-item label="审核意见" :span="2">{{ record.review_comment || '无' }}</el-descriptions-item>
      </el-descriptions>

      <div style="margin-top: 20px; text-align: center;">
        <el-button type="primary" @click="handleEdit" v-if="record.status === 'pending'">编辑</el-button>
        <el-button type="success" @click="handleApprove" v-if="record.status === 'pending'">通过</el-button>
        <el-button type="danger" @click="handleReject" v-if="record.status === 'pending'">拒绝</el-button>
        <el-button @click="goBack">返回</el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useSelfReportStore } from '@/stores/selfReport'
import { selfReportApi } from '@/api/self-report'
import type { SelfReportRecord } from '@/types/self-report'

const route = useRoute()
const router = useRouter()
const selfReportStore = useSelfReportStore()

const record = ref<SelfReportRecord | null>(null)
const loading = ref(false)
const notFound = ref(false)

const recordId = route.params.id as string

onMounted(async () => {
  await loadRecord()
})

async function loadRecord() {
  loading.value = true
  notFound.value = false
  try {
    const res = await selfReportApi.getById(recordId)
    record.value = res
  } catch (error: any) {
    if (error?.response?.status === 404 || error?.status === 404) {
      notFound.value = true
    } else {
      ElMessage.error('加载自报记录失败')
    }
  } finally {
    loading.value = false
  }
}

function goBack() {
  router.push('/self-reports')
}

function handleEdit() {
  router.push(`/self-reports/${recordId}/edit`)
}

async function handleApprove() {
  try {
    await ElMessageBox.confirm('确定通过此自报数据吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    loading.value = true
    await selfReportStore.approveRecord(recordId)
    ElMessage.success('自报数据已通过')
    await loadRecord()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('操作失败')
    }
  } finally {
    loading.value = false
  }
}

async function handleReject() {
  try {
    const { value } = await ElMessageBox.prompt('请输入拒绝原因', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      inputPlaceholder: '请输入拒绝原因'
    })

    loading.value = true
    await selfReportStore.rejectRecord(recordId, value)
    ElMessage.success('自报数据已拒绝')
    await loadRecord()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('操作失败')
    }
  } finally {
    loading.value = false
  }
}

function getReportTypeLabel(type: string) {
  const map: Record<string, string> = {
    'daily': '日常监测',
    'symptom': '症状上报',
    'medication': '用药反馈',
    'emergency': '紧急上报'
  }
  return map[type] || '未知'
}

function getStatusType(status: string) {
  const map: Record<string, string> = {
    'pending': 'warning',
    'approved': 'success',
    'rejected': 'danger'
  }
  return map[status] || 'info'
}

function getStatusLabel(status: string) {
  const map: Record<string, string> = {
    'pending': '待审核',
    'approved': '已通过',
    'rejected': '已拒绝'
  }
  return map[status] || '未知'
}

function formatDate(dateStr: string) {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString('zh-CN')
}

function formatDateTime(dateStr: string) {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleString('zh-CN')
}
</script>

<style scoped>
.self-report-detail {
  padding: 20px;
}
</style>