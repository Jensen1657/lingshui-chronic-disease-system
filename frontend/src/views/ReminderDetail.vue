<template>
  <div class="reminder-detail">
    <el-page-header @back="goBack" content="提醒详情" />

    <el-alert v-if="notFound" title="提醒记录不存在" type="error" show-icon :closable="false" style="margin-top: 16px;" />

    <el-card v-loading="loading" style="margin-top: 20px;" v-if="!notFound">
      <el-descriptions :column="2" border v-if="record">
        <el-descriptions-item label="患者姓名">{{ record.patient_name }}</el-descriptions-item>
        <el-descriptions-item label="提醒类型">{{ getReminderTypeLabel(record.reminder_type) }}</el-descriptions-item>
        <el-descriptions-item label="提醒标题">{{ record.title }}</el-descriptions-item>
        <el-descriptions-item label="提醒内容" :span="2">{{ record.content || '无' }}</el-descriptions-item>
        <el-descriptions-item label="提醒时间">{{ formatDateTime(record.reminder_time) }}</el-descriptions-item>
        <el-descriptions-item label="提醒状态">
          <el-tag :type="getStatusType(record.status)">{{ getStatusLabel(record.status) }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="发送状态">
          <el-tag :type="record.is_sent ? 'success' : 'warning'">
            {{ record.is_sent ? '已发送' : '未发送' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="完成状态">
          <el-tag :type="record.is_completed ? 'success' : 'info'">
            {{ record.is_completed ? '已完成' : '未完成' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ formatDateTime(record.created_at) }}</el-descriptions-item>
        <el-descriptions-item label="发送时间">{{ formatDateTime(record.sent_at) }}</el-descriptions-item>
        <el-descriptions-item label="完成时间">{{ formatDateTime(record.completed_at) }}</el-descriptions-item>
      </el-descriptions>

      <div style="margin-top: 20px; text-align: center;">
        <el-button type="primary" @click="handleEdit" v-if="record.status === 'pending'">编辑</el-button>
        <el-button type="success" @click="handleMarkSent" v-if="!record.is_sent && record.status === 'pending'">标记已发送</el-button>
        <el-button type="warning" @click="handleMarkCompleted" v-if="!record.is_completed && record.status === 'pending'">标记已完成</el-button>
        <el-button @click="goBack">返回</el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useReminderStore } from '@/stores/reminder'
import type { ReminderRecord } from '@/types/reminder'

const route = useRoute()
const router = useRouter()
const reminderStore = useReminderStore()

const record = ref<ReminderRecord | null>(null)
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
    const result = await reminderStore.getById(recordId)
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
  router.push('/reminders')
}

function handleEdit() {
  router.push(`/reminders/${recordId}/edit`)
}

async function handleMarkSent() {
  loading.value = true
  try {
    await reminderStore.markAsSent(recordId)
    ElMessage.success('已标记为已发送')
    await loadRecord()
  } catch (error) {
    // 错误已由 request.ts 拦截器统一提示
  } finally {
    loading.value = false
  }
}

async function handleMarkCompleted() {
  loading.value = true
  try {
    await reminderStore.markAsCompleted(recordId)
    ElMessage.success('已标记为已完成')
    await loadRecord()
  } catch (error) {
    // 错误已由 request.ts 拦截器统一提示
  } finally {
    loading.value = false
  }
}

function getReminderTypeLabel(type: string) {
  const map: Record<string, string> = {
    'followup': '随访提醒',
    'medication': '用药提醒',
    'assessment': '评估提醒',
    'examination': '检查提醒',
    'consultation': '复诊提醒'
  }
  return map[type] || '未知'
}

function getStatusType(status: string) {
  const map: Record<string, string> = {
    'pending': 'warning',
    'sent': 'primary',
    'completed': 'success',
    'cancelled': 'info'
  }
  return map[status] || 'info'
}

function getStatusLabel(status: string) {
  const map: Record<string, string> = {
    'pending': '待发送',
    'sent': '已发送',
    'completed': '已完成',
    'cancelled': '已取消'
  }
  return map[status] || '未知'
}

function formatDateTime(dateStr: string) {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleString('zh-CN')
}
</script>

<style scoped>
.reminder-detail {
  padding: 20px;
}
</style>