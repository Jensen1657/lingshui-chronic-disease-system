<template>
  <div class="tcm-detail">
    <el-page-header @back="goBack" content="中医详情" />

    <el-alert v-if="notFound" title="中医记录不存在" type="error" show-icon :closable="false" style="margin-top: 16px;" />

    <el-card v-loading="loading" style="margin-top: 20px;" v-if="!notFound && record">
      <el-descriptions :column="2" border>
        <el-descriptions-item label="患者ID">{{ record.patient_id }}</el-descriptions-item>
        <el-descriptions-item label="就诊日期">{{ formatDate(record.record_date || record.visit_date) }}</el-descriptions-item>
        <el-descriptions-item label="证型/体质">{{ getSyndromeTypeText(record.syndrome_type) }}</el-descriptions-item>
        <el-descriptions-item label="就诊医生">{{ record.visit_doctor || record.recorded_by || '无' }}</el-descriptions-item>
        <el-descriptions-item label="中医病名" :span="2">{{ record.tcm_disease || '无' }}</el-descriptions-item>

        <el-descriptions-item label="辨证分型" :span="2">{{ record.syndrome_differentiation || '无' }}</el-descriptions-item>
        <el-descriptions-item label="主要症状" :span="2">{{ record.syndrome_name || '无' }}</el-descriptions-item>

        <el-descriptions-item label="望诊">{{ record.inspection || '无' }}</el-descriptions-item>
        <el-descriptions-item label="闻诊">{{ record.auscultation || '无' }}</el-descriptions-item>
        <el-descriptions-item label="问诊">{{ record.interrogation || '无' }}</el-descriptions-item>
        <el-descriptions-item label="切诊">{{ record.palpation || '无' }}</el-descriptions-item>

        <el-descriptions-item label="舌质">{{ record.tongue_body || '无' }}</el-descriptions-item>
        <el-descriptions-item label="舌苔">{{ record.tongue_coating || record.tongue_coat || '无' }}</el-descriptions-item>
        <el-descriptions-item label="脉象">{{ record.pulse || record.pulse_status || '无' }}</el-descriptions-item>

        <el-descriptions-item label="治法">{{ record.treatment_method || '无' }}</el-descriptions-item>
        <el-descriptions-item label="治疗方案" :span="2">{{ record.treatment_plan || '无' }}</el-descriptions-item>

        <el-descriptions-item label="中药处方" :span="2">{{ record.prescription || record.tcm_prescription || '无' }}</el-descriptions-item>
        <el-descriptions-item label="中药组成" :span="2">{{ formatHerbs(record.herbs || record.tcm_herbs) }}</el-descriptions-item>
        <el-descriptions-item label="中成药">{{ record.patent_medicine || '无' }}</el-descriptions-item>

        <el-descriptions-item label="针灸">{{ record.acupuncture || '无' }}</el-descriptions-item>
        <el-descriptions-item label="艾灸">{{ record.moxibustion || '无' }}</el-descriptions-item>
        <el-descriptions-item label="推拿">{{ record.tuina || '无' }}</el-descriptions-item>
        <el-descriptions-item label="其他疗法">{{ record.other_therapy || '无' }}</el-descriptions-item>

        <el-descriptions-item label="饮食疗法" :span="2">{{ record.diet_therapy || '无' }}</el-descriptions-item>
        <el-descriptions-item label="运动疗法" :span="2">{{ record.exercise_therapy || '无' }}</el-descriptions-item>
        <el-descriptions-item label="情志疗法" :span="2">{{ record.emotion_therapy || '无' }}</el-descriptions-item>
        <el-descriptions-item label="生活方式指导" :span="2">{{ record.lifestyle_guidance || '无' }}</el-descriptions-item>

        <el-descriptions-item label="疗效评价" :span="2">{{ record.efficacy_evaluation || '待评估' }}</el-descriptions-item>
        <el-descriptions-item label="下次复诊日期">{{ formatDate(record.next_visit_date) }}</el-descriptions-item>
        <el-descriptions-item label="记录时间">{{ formatDate(record.created_at) }}</el-descriptions-item>
      </el-descriptions>

      <div style="margin-top: 20px; text-align: center;">
        <el-button type="primary" @click="handleEdit">编辑</el-button>
        <el-button @click="goBack">返回</el-button>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="tsx">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useTcmStore } from '@/stores/tcm'
import type { TcmRecord } from '@/types/tcm'

const route = useRoute()
const router = useRouter()
const tcmStore = useTcmStore()

const record = ref<TcmRecord | null>(null)
const loading = ref(false)
const notFound = ref(false)

const recordId = (route.params.id as string)

onMounted(async () => {
  await loadRecord()
})

async function loadRecord() {
  loading.value = true
  notFound.value = false
  try {
    const result = await tcmStore.getById(recordId)
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
  router.push('/tcm')
}

function handleEdit() {
  router.push(`/tcm/${recordId}/edit`)
}

function formatDate(dateStr: string | undefined) {
  if (!dateStr) return '无'
  try {
    return new Date(dateStr).toLocaleDateString('zh-CN')
  } catch {
    return dateStr
  }
}

function formatHerbs(herbs: any) {
  if (!herbs) return '无'
  if (typeof herbs === 'string') {
    try { herbs = JSON.parse(herbs) } catch { return herbs }
  }
  if (Array.isArray(herbs)) {
    return herbs.map((h: any) => typeof h === 'string' ? h : h.name || JSON.stringify(h)).join('、')
  }
  return String(herbs)
}

function getSyndromeTypeText(type: string | undefined) {
  if (!type) return '无'
  const map: Record<string, string> = {
    'qi_deficiency': '气虚质',
    'yang_deficiency': '阳虚质',
    'yin_deficiency': '阴虚质',
    'blood_stasis': '血瘀质',
    'phlegm_dampness': '痰湿质',
    'damp_heat': '湿热质',
    'qi_stagnation': '气郁质',
    'blood_deficiency': '血虚质',
    'special_constitution': '特禀质',
    'gentleness': '平和质',
    '气阴两虚证': '气阴两虚证',
    '肝阳上亢证': '肝阳上亢证',
    '痰湿壅盛证': '痰湿壅盛证',
    '阴阳两虚证': '阴阳两虚证',
  }
  return map[type] || type
}
</script>

<style scoped>
.tcm-detail {
  padding: 20px;
}
</style>
