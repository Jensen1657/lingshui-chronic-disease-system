<template>
  <div class="referral-detail">
    <el-page-header @back="goBack" content="转诊详情" />

    <el-alert v-if="notFound" title="转诊记录不存在" type="error" show-icon :closable="false" style="margin-top: 16px;" />

    <el-card v-loading="loading" style="margin-top: 20px;" v-if="!notFound">
      <el-descriptions :column="2" border v-if="record">
        <el-descriptions-item label="患者姓名">{{ record.patient_name }}</el-descriptions-item>
        <el-descriptions-item label="转诊类型">{{ getReferralTypeLabel(record.referral_type) }}</el-descriptions-item>
        <el-descriptions-item label="转出机构">{{ record.from_organization }}</el-descriptions-item>
        <el-descriptions-item label="转入机构">{{ record.to_organization }}</el-descriptions-item>
        <el-descriptions-item label="转诊原因">{{ record.reason || '无' }}</el-descriptions-item>
        <el-descriptions-item label="转诊状态">
          <el-tag :type="getStatusType(record.status)">{{ getStatusLabel(record.status) }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="申请时间">{{ formatDate(record.created_at) }}</el-descriptions-item>
        <el-descriptions-item label="处理时间">{{ formatDate(record.processed_at) }}</el-descriptions-item>
        <el-descriptions-item label="处理意见">{{ record.process_note || '无' }}</el-descriptions-item>
      </el-descriptions>

      <div style="margin-top: 20px; text-align: center;">
        <el-button type="primary" @click="handleEdit" v-if="record.status === 'pending'">处理转诊</el-button>
        <el-button type="success" @click="handleApprove" v-if="record.status === 'pending'">通过</el-button>
        <el-button type="danger" @click="handleReject" v-if="record.status === 'pending'">拒绝</el-button>
        <el-button type="warning" @click="handleComplete" v-if="record.status === 'approved'">完成</el-button>
        <el-button @click="goBack">返回</el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useReferralStore } from '@/stores/referral'
import type { ReferralRecord } from '@/types/referral'

const route = useRoute()
const router = useRouter()
const referralStore = useReferralStore()

const record = ref<ReferralRecord | null>(null)
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
    const result = await referralStore.getById(recordId)
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
  router.push('/referrals')
}

function handleEdit() {
  router.push(`/referrals/${recordId}/edit`)
}

async function handleApprove() {
  try {
    await ElMessageBox.confirm('确定通过此转诊申请吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    loading.value = true
    await referralStore.approveRecord(recordId)
    ElMessage.success('转诊申请已通过')
    await loadRecord()
  } catch (error) {
    if (error !== 'cancel') {
      // 错误已由 request.ts 拦截器统一提示
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
    await referralStore.rejectRecord(recordId, value)
    ElMessage.success('转诊申请已拒绝')
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
    await ElMessageBox.confirm('确定完成此转诊吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })

    loading.value = true
    await referralStore.completeRecord(recordId)
    ElMessage.success('转诊已完成')
    await loadRecord()
  } catch (error) {
    if (error !== 'cancel') {
      // 错误已由 request.ts 拦截器统一提示
    }
  } finally {
    loading.value = false
  }
}

function getReferralTypeLabel(type: string) {
  const map: Record<string, string> = {
    'upward': '上转',
    'downward': '下转'
  }
  return map[type] || '未知'
}

function getStatusType(status: string) {
  const map: Record<string, string> = {
    'pending': 'warning',
    'approved': 'success',
    'rejected': 'danger',
    'completed': 'info'
  }
  return map[status] || 'info'
}

function getStatusLabel(status: string) {
  const map: Record<string, string> = {
    'pending': '待处理',
    'approved': '已通过',
    'rejected': '已拒绝',
    'completed': '已完成'
  }
  return map[status] || '未知'
}

function formatDate(dateStr: string) {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString('zh-CN')
}
</script>

<style scoped>
.referral-detail {
  padding: 20px;
}
</style>