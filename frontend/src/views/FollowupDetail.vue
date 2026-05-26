<template>
  <div class="followup-detail">
    <el-page-header @back="goBack" content="随访详情" />

    <el-alert v-if="notFound" title="随访记录不存在" type="error" show-icon :closable="false" style="margin-top: 16px;" />

    <el-card v-loading="loading" style="margin-top: 20px;" v-if="!notFound">
      <el-descriptions :column="2" border v-if="record">
        <el-descriptions-item label="患者姓名">{{ record.patient_name }}</el-descriptions-item>
        <el-descriptions-item label="随访日期">{{ formatDate(record.followup_date) }}</el-descriptions-item>
        <el-descriptions-item label="随访方式">{{ getFollowupTypeLabel(record.followup_type) }}</el-descriptions-item>
        <el-descriptions-item label="症状">{{ record.symptoms || '无' }}</el-descriptions-item>
        <el-descriptions-item label="体征">{{ record.signs || '无' }}</el-descriptions-item>
        <el-descriptions-item label="用药依从性">{{ getComplianceLabel(record.medication_compliance) }}</el-descriptions-item>
        <el-descriptions-item label="生活方式指导">{{ record.lifestyle_guidance || '无' }}</el-descriptions-item>
        <el-descriptions-item label="下次随访日期">{{ formatDate(record.next_followup_date) }}</el-descriptions-item>
        <el-descriptions-item label="随访医生">{{ record.doctor_name || '未分配' }}</el-descriptions-item>
      </el-descriptions>

      <div style="margin-top: 20px; text-align: center;">
        <el-button type="primary" @click="handleEdit">编辑</el-button>
        <el-button @click="goBack">返回</el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useFollowupStore } from '@/stores/followup'
import type { FollowupRecord } from '@/types/followup'

const route = useRoute()
const router = useRouter()
const followupStore = useFollowupStore()

const record = ref<FollowupRecord | null>(null)
const loading = ref(false)
const notFound = ref(false)

const recordId = route.params.id as string

onMounted(async () => {
  await loadRecord()
})

async function loadRecord() {
  loading.value = true
  notFound.value = false
  const currentToken = localStorage.getItem('token')
  console.log('Loading followup record, ID:', recordId, 'token exists:', !!currentToken, 'token prefix:', currentToken?.substring(0, 20))
  try {
    const result = await followupStore.getById(recordId)
    console.log('Followup API result:', result)
    if (!result || (typeof result === 'object' && Object.keys(result).length === 0)) {
      notFound.value = true
      return
    }
    record.value = result
  } catch (error: any) {
    console.error('Load followup error:', error)
    const status = error?.response?.status || error?.status
    console.log('Error status:', status)
    if (status === 404) {
      notFound.value = true
    } else {
      // 错误已由 request.ts 拦截器统一提示
    }
  } finally {
    loading.value = false
  }
}

function goBack() {
  router.push('/followups')
}

function handleEdit() {
  router.push(`/followups/${recordId}/edit`)
}

function getFollowupTypeLabel(type: string) {
  const map: Record<string, string> = {
    'clinic': '门诊随访',
    'home_visit': '家庭访视',
    'phone': '电话随访',
    'video': '视频随访'
  }
  return map[type] || '未知'
}

function getComplianceLabel(compliance: string) {
  const map: Record<string, string> = {
    'good': '良好',
    'average': '一般',
    'poor': '差'
  }
  return map[compliance] || '未知'
}

function formatDate(dateStr: string) {
  if (!dateStr) return ''
  return new Date(dateStr).toLocaleDateString('zh-CN')
}
</script>

<style scoped>
.followup-detail {
  padding: 20px;
}
</style>