<template>
  <div class="alert-detail">
    <el-page-header @back="goBack" content="预警详情" />

    <el-alert v-if="notFound" title="预警记录不存在" type="error" show-icon :closable="false" style="margin-top: 16px;" />

    <el-card v-loading="loading" style="margin-top: 20px;" v-if="!notFound">
      <el-descriptions :column="2" border v-if="record">
        <el-descriptions-item label="患者姓名">{{ record.patient_name }}</el-descriptions-item>
        <el-descriptions-item label="预警类型">{{ getAlertTypeLabel(record.alert_type) }}</el-descriptions-item>
        <el-descriptions-item label="预警级别">
          <el-tag :type="getSeverityType(record.severity)" size="large">{{ getSeverityLabel(record.severity) }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="预警标题">{{ record.title }}</el-descriptions-item>
        <el-descriptions-item label="预警描述" :span="2">{{ record.description || '无' }}</el-descriptions-item>
        <el-descriptions-item label="阅读状态">
          <el-tag :type="record.is_read ? 'success' : 'warning'">
            {{ record.is_read ? '已读' : '未读' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="触发时间">{{ formatDateTime(record.triggered_at) }}</el-descriptions-item>
        <el-descriptions-item label="处理状态">
          <el-tag :type="getStatusType(record.status)">{{ getStatusLabel(record.status) }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="处理结果" :span="2">{{ record.handling_result || '未处理' }}</el-descriptions-item>
        <el-descriptions-item label="处理人">{{ record.handled_by || '未分配' }}</el-descriptions-item>
        <el-descriptions-item label="处理时间">{{ formatDateTime(record.handled_at) }}</el-descriptions-item>
      </el-descriptions>

      <div style="margin-top: 20px; text-align: center;">
        <el-button type="primary" @click="handleMarkAsRead" v-if="!record.is_read">标记已读</el-button>
        <el-button type="success" @click="handleProcess" v-if="record.status === 'pending'">处理预警</el-button>
        <el-button @click="goBack">返回</el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAlertStore } from '@/stores/alert'
import type { AlertRecord } from '@/types/alert'

const route = useRoute()
const router = useRouter()
const alertStore = useAlertStore()

const record = ref<AlertRecord | null>(null)
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
    const result = await alertStore.getById(recordId)
    record.value = result
  } catch (error: any) {
    if (error?.response?.status === 404 || error?.status === 404) {
      notFound.value = true
    } else {
      // 错误已由 request.ts 拦截器统一提示
    }
  } finally {
    loading.value = false
  }
}

function goBack() {
  router.push('/alerts')
}

async function handleMarkAsRead() {
  loading.value = true
  try {
    await alertStore.markAsRead(recordId)
    ElMessage.success('已标记为已读')
    await loadRecord()
  } catch (error) {
    // 错误已由 request.ts 拦截器统一提示
  } finally {
    loading.value = false
  }
}

async function handleProcess() {
  try {
    const { value } = await ElMessageBox.prompt('请输入处理结果', '处理预警', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      inputPlaceholder: '请输入处理结果'
    })

    loading.value = true
    await alertStore.updateRecord(recordId, {
      status: 'processed',
      handling_result: value,
      handled_at: new Date().toISOString()
    })
    ElMessage.success('预警已处理')
    await loadRecord()
  } catch (error) {
    if (error !== 'cancel') {
      // 错误已由 request.ts 拦截器统一提示
    }
  } finally {
    loading.value = false
  }
}

function getAlertTypeLabel(type: string) {
  const map: Record<string, string> = {
    'blood_pressure': '血压异常',
    'blood_sugar': '血糖异常',
    'missed_visit': '漏访预警',
    'medication': '用药预警',
    'emergency': '急救预警'
  }
  return map[type] || '未知'
}

function getSeverityType(severity: string) {
  const map: Record<string, string> = {
    'low': 'info',
    'medium': 'warning',
    'high': 'danger',
    'critical': 'danger'
  }
  return map[severity] || 'info'
}

function getSeverityLabel(severity: string) {
  const map: Record<string, string> = {
    'low': '低',
    'medium': '中',
    'high': '高',
    'critical': '紧急'
  }
  return map[severity] || '未知'
}

function getStatusType(status: string) {
  const map: Record<string, string> = {
    'pending': 'warning',
    'processing': 'primary',
    'processed': 'success',
    'closed': 'info'
  }
  return map[status] || 'info'
}

function getStatusLabel(status: string) {
  const map: Record<string, string> = {
    'pending': '待处理',
    'processing': '处理中',
    'processed': '已处理',
    'closed': '已关闭'
  }
  return map[status] || '未知'
}

function formatDateTime(dateStr: string) {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleString('zh-CN')
}
</script>

<style scoped>
.alert-detail {
  padding: 20px;
}
</style>