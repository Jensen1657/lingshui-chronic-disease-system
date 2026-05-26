<template>
  <div class="emergency-detail">
    <el-page-header @back="goBack" content="急救详情" />

    <el-alert v-if="notFound" title="急救记录不存在" type="error" show-icon :closable="false" style="margin-top: 16px;" />

    <el-card v-loading="loading" style="margin-top: 20px;" v-if="!notFound">
      <el-descriptions :column="2" border v-if="record">
        <el-descriptions-item label="患者姓名">{{ record.patient_name }}</el-descriptions-item>
        <el-descriptions-item label="急救类型">{{ getEmergencyTypeLabel(record.emergency_type) }}</el-descriptions-item>
        <el-descriptions-item label="发生时间">{{ formatDateTime(record.occurred_at) }}</el-descriptions-item>
        <el-descriptions-item label="发生地点">{{ record.location || '未知' }}</el-descriptions-item>
        <el-descriptions-item label="主要症状" :span="2">{{ record.symptoms || '无' }}</el-descriptions-item>
        <el-descriptions-item label="生命体征" :span="2">{{ record.vital_signs || '未测量' }}</el-descriptions-item>
        <el-descriptions-item label="处理措施" :span="2">{{ record.treatment || '无' }}</el-descriptions-item>
        <el-descriptions-item label="转送医院">{{ record.hospital || '未转送' }}</el-descriptions-item>
        <el-descriptions-item label="联系人">{{ record.contact_person || '无' }}</el-descriptions-item>
        <el-descriptions-item label="联系电话">{{ record.contact_phone || '无' }}</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="getStatusType(record.status)">{{ getStatusLabel(record.status) }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="处理人">{{ record.handler_name || '未分配' }}</el-descriptions-item>
        <el-descriptions-item label="处理时间">{{ formatDateTime(record.handled_at) }}</el-descriptions-item>
      </el-descriptions>

      <div style="margin-top: 20px; text-align: center;">
        <el-button type="primary" @click="handleEdit" v-if="record.status === 'pending'">处理</el-button>
        <el-button type="success" @click="handleActivate" v-if="record.status === 'pending'">启动急救</el-button>
        <el-button type="warning" @click="handleComplete" v-if="record.status === 'processing'">完成</el-button>
        <el-button type="danger" @click="handleCancel" v-if="record.status === 'pending' || record.status === 'processing'">取消</el-button>
        <el-button @click="goBack">返回</el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useEmergencyStore } from '@/stores/emergency'
import type { EmergencyRecord } from '@/types/emergency'

const route = useRoute()
const router = useRouter()
const emergencyStore = useEmergencyStore()

const record = ref<EmergencyRecord | null>(null)
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
    const result = await emergencyStore.getById(recordId)
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
  router.push('/emergencies')
}

function handleEdit() {
  router.push(`/emergencies/${recordId}/edit`)
}

async function handleActivate() {
  try {
    await ElMessageBox.confirm('确定启动急救流程吗？这将通知相关人员和医院！', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    loading.value = true
    await emergencyStore.activateEmergency(record.value!.patient_id, {
      emergency_id: recordId,
      activation_time: new Date().toISOString()
    })
    ElMessage.success('急救流程已启动')
    await loadRecord()
  } catch (error) {
    if (error !== 'cancel') {
      // 错误已由 request.ts 拦截器统一提示
    }
  } finally {
    loading.value = false
  }
}

async function handleComplete() {
  try {
    await ElMessageBox.confirm('确定完成此急救记录吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    loading.value = true
    await emergencyStore.completeRecord(recordId, {
      handled_at: new Date().toISOString(),
      status: 'handled'
    })
    ElMessage.success('急救记录已完成')
    await loadRecord()
  } catch (error) {
    if (error !== 'cancel') {
      // 错误已由 request.ts 拦截器统一提示
    }
  } finally {
    loading.value = false
  }
}

async function handleCancel() {
  try {
    const { value } = await ElMessageBox.prompt('请输入取消原因', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      inputPlaceholder: '请输入取消原因'
    })

    loading.value = true
    await emergencyStore.cancelRecord(recordId, value)
    ElMessage.success('急救记录已取消')
    await loadRecord()
  } catch (error) {
    if (error !== 'cancel') {
      // 错误已由 request.ts 拦截器统一提示
    }
  } finally {
    loading.value = false
  }
}

function getEmergencyTypeLabel(type: string) {
  const map: Record<string, string> = {
    'cardiac_arrest': '心脏骤停',
    'stroke': '脑卒中',
    'respiratory_failure': '呼吸衰竭',
    'severe_hypertension': '重度高血压',
    'hypoglycemia': '低血糖昏迷',
    'other': '其他'
  }
  return map[type] || '未知'
}

function getStatusType(status: string) {
  const map: Record<string, string> = {
    'pending': 'warning',
    'processing': 'primary',
    'handled': 'success',
    'closed': 'info'
  }
  return map[status] || 'info'
}

function getStatusLabel(status: string) {
  const map: Record<string, string> = {
    'pending': '待处理',
    'processing': '处理中',
    'handled': '已处理',
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
.emergency-detail {
  padding: 20px;
}
</style>