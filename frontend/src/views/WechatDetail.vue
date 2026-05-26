<template>
  <div class="wechat-detail">
    <el-page-header @back="goBack" content="微信详情" />

    <el-alert v-if="notFound" title="微信记录不存在" type="error" show-icon :closable="false" style="margin-top: 16px;" />

    <el-card v-loading="loading" style="margin-top: 20px;" v-if="!notFound">
      <el-descriptions :column="2" border v-if="record">
        <el-descriptions-item label="患者姓名">{{ record.patient_name }}</el-descriptions-item>
        <el-descriptions-item label="微信昵称">{{ record.wechat_nickname || '未绑定' }}</el-descriptions-item>
        <el-descriptions-item label="微信号">{{ record.wechat_id || '未绑定' }}</el-descriptions-item>
        <el-descriptions-item label="绑定状态">
          <el-tag :type="getStatusType(record.status)">{{ getStatusLabel(record.status) }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="绑定时间">{{ formatDateTime(record.bound_at) }}</el-descriptions-item>
        <el-descriptions-item label="解绑时间">{{ formatDateTime(record.unbound_at) }}</el-descriptions-item>
        <el-descriptions-item label="推送设置" :span="2">
          <el-tag v-if="record.push_enabled" type="success">已启用</el-tag>
          <el-tag v-else type="info">已禁用</el-tag>
          <span style="margin-left: 10px;">{{ getPushFrequencyLabel(record.push_frequency) }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="最后一次推送">{{ formatDateTime(record.last_push_at) }}</el-descriptions-item>
        <el-descriptions-item label="推送次数">{{ record.push_count || 0 }} 次</el-descriptions-item>
        <el-descriptions-item label="备注" :span="2">{{ record.remarks || '无' }}</el-descriptions-item>
      </el-descriptions>

      <div style="margin-top: 20px; text-align: center;">
        <el-button type="primary" @click="handleEdit" v-if="record.status === 'bound'">编辑</el-button>
        <el-button type="success" @click="handleSendNotification" v-if="record.status === 'bound'">发送通知</el-button>
        <el-button type="warning" @click="handleUnbind" v-if="record.status === 'bound'">解绑</el-button>
        <el-button type="danger" @click="handleDelete" v-if="record.status === 'unbound'">删除记录</el-button>
        <el-button @click="goBack">返回</el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useWechatStore } from '@/stores/wechat'
import type { WechatRecord } from '@/types/wechat'

const route = useRoute()
const router = useRouter()
const wechatStore = useWechatStore()

const record = ref<WechatRecord | null>(null)
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
    const result = await wechatStore.getById(recordId)
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
  router.push('/wechat')
}

function handleEdit() {
  router.push(`/wechat/${recordId}/edit`)
}

async function handleSendNotification() {
  try {
    const { value } = await ElMessageBox.prompt('请输入通知内容', '发送通知', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      inputPlaceholder: '请输入通知内容'
    })

    loading.value = true
    await wechatStore.sendNotification(recordId, value)
    ElMessage.success('通知已发送')
    await loadRecord()
  } catch (error) {
    if (error !== 'cancel') {
      // 错误已由 request.ts 拦截器统一提示
    }
  } finally {
    loading.value = false
  }
}

async function handleUnbind() {
  try {
    await ElMessageBox.confirm('确定解绑该患者的微信吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    loading.value = true
    await wechatStore.unbindWechat(recordId)
    ElMessage.success('微信已解绑')
    await loadRecord()
  } catch (error) {
    if (error !== 'cancel') {
      // 错误已由 request.ts 拦截器统一提示
    }
  } finally {
    loading.value = false
  }
}

async function handleDelete() {
  try {
    await ElMessageBox.confirm('确定删除该微信记录吗？此操作不可恢复！', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    loading.value = true
    await wechatStore.deleteRecord(recordId)
    ElMessage.success('记录已删除')
    router.push('/wechat')
  } catch (error) {
    if (error !== 'cancel') {
      // 错误已由 request.ts 拦截器统一提示
    }
  } finally {
    loading.value = false
  }
}

function getStatusType(status: string) {
  const map: Record<string, string> = {
    'bound': 'success',
    'unbound': 'info',
    'pending': 'warning'
  }
  return map[status] || 'info'
}

function getStatusLabel(status: string) {
  const map: Record<string, string> = {
    'bound': '已绑定',
    'unbound': '已解绑',
    'pending': '待审核'
  }
  return map[status] || '未知'
}

function getPushFrequencyLabel(frequency: string) {
  const map: Record<string, string> = {
    'daily': '每日推送',
    'weekly': '每周推送',
    'monthly': '每月推送',
    'none': '不推送'
  }
  return map[frequency] || '未设置'
}

function formatDateTime(dateStr: string) {
  if (!dateStr) return '无'
  return new Date(dateStr).toLocaleString('zh-CN')
}
</script>

<style scoped>
.wechat-detail {
  padding: 20px;
}
</style>