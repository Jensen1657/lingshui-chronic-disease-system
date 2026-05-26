<template>
  <div class="patient-detail">
    <el-page-header @back="goBack" content="患者详情" />

    <el-alert v-if="notFound" title="患者不存在" type="error" show-icon :closable="false" style="margin-top: 16px;" />

    <el-tabs v-model="activeTab" style="margin-top: 20px;" v-if="!notFound">
      <el-tab-pane label="基本信息" name="basic">
        <el-card v-loading="loading">
          <el-descriptions :column="2" border v-if="patient">
            <el-descriptions-item label="患者编号">{{ patient.patient_id }}</el-descriptions-item>
            <el-descriptions-item label="姓名">{{ patient.name }}</el-descriptions-item>
            <el-descriptions-item label="性别">{{ patient.gender === 'M' ? '男' : patient.gender === 'F' ? '女' : '其他' }}</el-descriptions-item>
            <el-descriptions-item label="年龄">{{ patient.age }}</el-descriptions-item>
            <el-descriptions-item label="出生日期">{{ patient.birth_date }}</el-descriptions-item>
            <el-descriptions-item label="联系电话">{{ patient.phone }}</el-descriptions-item>
            <el-descriptions-item label="地址" :span="2">{{ patient.address || '-' }}</el-descriptions-item>
            <el-descriptions-item label="村编码">{{ patient.village_code || '-' }}</el-descriptions-item>
            <el-descriptions-item label="所属机构">{{ patient.manage_org_name || '-' }}</el-descriptions-item>
            <el-descriptions-item label="慢病类型" :span="2">
              <el-tag v-for="disease in patient.disease_list" :key="disease" size="small" style="margin-right: 4px">
                {{ diseaseLabel(disease) }}
              </el-tag>
              <span v-if="!patient.disease_list || patient.disease_list.length === 0">-</span>
            </el-descriptions-item>
            <el-descriptions-item label="风险等级">
              <el-tag :type="getRiskType(patient.risk_level)">{{ riskLevelLabel(patient.risk_level) }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="管理状态">
              <el-tag :type="patient.is_active ? 'success' : 'info'">
                {{ patient.is_active ? '管理中' : '已退出' }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="EMPI状态">{{ patient.empi_status || '-' }}</el-descriptions-item>
            <el-descriptions-item label="纳入管理时间">{{ formatDate(patient.created_at) }}</el-descriptions-item>
          </el-descriptions>

          <div style="margin-top: 20px; text-align: center;">
            <el-button type="primary" @click="handleEdit">编辑信息</el-button>
            <el-button type="success" @click="goToFollowup">新建随访</el-button>
            <el-button type="warning" @click="goToAssessment">年度评估</el-button>
          </div>
        </el-card>
      </el-tab-pane>

      <el-tab-pane label="随访记录" name="followups">
        <el-card v-loading="loadingFollowups">
          <el-table :data="followupList" style="width: 100%">
            <el-table-column prop="followup_date" label="随访日期" width="120" />
            <el-table-column prop="followup_type" label="随访方式" width="100" />
            <el-table-column prop="symptoms" label="症状" />
            <el-table-column prop="next_followup_date" label="下次随访日期" width="140" />
            <el-table-column label="操作" width="120">
              <template #default="{ row }">
                <el-button size="small" @click="viewFollowup(row.id || row.followup_id)">查看</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-tab-pane>

      <el-tab-pane label="年度评估" name="assessments">
        <el-card v-loading="loadingAssessments">
          <el-table :data="assessmentList" style="width: 100%">
            <el-table-column prop="assessment_date" label="评估日期" width="120" />
            <el-table-column prop="total_score" label="总分" width="80" />
            <el-table-column prop="risk_level" label="风险分级" width="100">
              <template #default="{ row }">
                <el-tag :type="getRiskType(row.risk_level)">{{ getRiskLabel(row.risk_level) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="next_assessment_date" label="下次评估日期" width="140" />
            <el-table-column label="操作" width="120">
              <template #default="{ row }">
                <el-button size="small" @click="viewAssessment(row.id || row.assessment_id)">查看</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-tab-pane>

      <el-tab-pane label="转诊记录" name="referrals">
        <el-card v-loading="loadingReferrals">
          <el-table :data="referralList" style="width: 100%">
            <el-table-column prop="apply_date" label="申请日期" width="120" />
            <el-table-column prop="referral_type" label="转诊类型" width="100" />
            <el-table-column prop="apply_org_name" label="转出机构" />
            <el-table-column prop="receive_org_name" label="接收机构" />
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="getStatusType(row.status)" size="small">{{ getStatusText(row.status) }}</el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-tab-pane>

      <el-tab-pane label="预警记录" name="alerts">
        <el-card v-loading="loadingAlerts">
          <el-table :data="alertList" style="width: 100%">
            <el-table-column prop="alert_time" label="预警时间" width="160" />
            <el-table-column prop="alert_type" label="预警类型" width="120">
              <template #default="{ row }">
                {{ alertTypeLabel(row.alert_type) }}
              </template>
            </el-table-column>
            <el-table-column prop="alert_level" label="等级" width="80">
              <template #default="{ row }">
                <el-tag :type="row.alert_level === 'HIGH' ? 'danger' : row.alert_level === 'MEDIUM' ? 'warning' : 'info'" size="small">{{ row.alert_level === 'HIGH' ? '高' : row.alert_level === 'MEDIUM' ? '中' : '低' }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="alert_content" label="预警内容" />
            <el-table-column prop="is_handled" label="状态" width="80">
              <template #default="{ row }">
                <el-tag :type="row.is_handled ? 'success' : 'warning'" size="small">{{ row.is_handled ? '已处理' : '待处理' }}</el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { usePatientStore } from '@/stores/patient'
import { patientApi } from '@/api/patient'
import { followupApi } from '@/api/followup'
import { assessmentApi } from '@/api/assessment'
import request from '@/api/request'
import type { Patient } from '@/types/patient'

const route = useRoute()
const router = useRouter()
const patientStore = usePatientStore()

const patient = ref<Patient | null>(null)
const loading = ref(false)
const loadingFollowups = ref(false)
const loadingAssessments = ref(false)
const notFound = ref(false)
const activeTab = ref('basic')
const followupList = ref<any[]>([])
const assessmentList = ref<any[]>([])
const referralList = ref<any[]>([])
const alertList = ref<any[]>([])
const loadingReferrals = ref(false)
const loadingAlerts = ref(false)

const patientId = route.params.id as string

onMounted(async () => {
  await loadPatient()
  await Promise.all([loadFollowups(), loadAssessments(), loadReferrals(), loadAlerts()])
})

async function loadPatient() {
  loading.value = true
  notFound.value = false
  try {
    const res = await patientApi.getById(patientId)
    patient.value = res
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

async function loadFollowups() {
  loadingFollowups.value = true
  try {
    const res = await followupApi.getList({ patient_id: patientId, page: 1, page_size: 100 })
    followupList.value = res.items || []
  } catch (error) {
    console.error('Failed to load followups:', error)
  } finally {
    loadingFollowups.value = false
  }
}

async function loadAssessments() {
  loadingAssessments.value = true
  try {
    const res = await assessmentApi.getList({ patient_id: patientId, page: 1, page_size: 100 })
    assessmentList.value = res.items || []
  } catch (error) {
    console.error('Failed to load assessments:', error)
  } finally {
    loadingAssessments.value = false
  }
}

async function loadReferrals() {
  loadingReferrals.value = true
  try {
    const res = await request.get(`/v1/referrals`, { params: { patient_id: patientId, page: 1, page_size: 100 } })
    referralList.value = res.data?.items || []
  } catch (error) {
    console.error('Failed to load referrals:', error)
  } finally {
    loadingReferrals.value = false
  }
}

async function loadAlerts() {
  loadingAlerts.value = true
  try {
    const res = await request.get(`/v1/alerts`, { params: { patient_id: patientId, page: 1, page_size: 100 } })
    alertList.value = res.data?.items || []
  } catch (error) {
    console.error('Failed to load alerts:', error)
  } finally {
    loadingAlerts.value = false
  }
}

function getStatusType(status: string) {
  const map: Record<string, string> = { PENDING: 'warning', ACCEPTED: '', COMPLETED: 'success', REJECTED: 'danger' }
  return map[status] || 'info'
}

function getStatusText(status: string) {
  const map: Record<string, string> = { PENDING: '待接收', ACCEPTED: '已接收', COMPLETED: '已完成', REJECTED: '已拒绝' }
  return map[status] || status
}

function alertTypeLabel(type: string) {
  const map: Record<string, string> = { OVERDUE: '逾期未访', ABNORMAL: '指标异常', RISK: '风险升级', MEDICATION: '用药提醒' }
  return map[type] || type
}

function goBack() {
  router.push('/patients')
}

function handleEdit() {
  router.push(`/patients/${patientId}/edit`)
}

function goToFollowup() {
  router.push(`/followups/create?patient_id=${patientId}`)
}

function goToAssessment() {
  router.push(`/assessments/create?patient_id=${patientId}`)
}

function viewFollowup(id: string) {
  router.push(`/followups/${id}`)
}

function viewAssessment(id: string) {
  router.push(`/assessments/${id}`)
}

function getRiskType(level: string) {
  const map: Record<string, string> = {
    'LOW': 'success',
    'MEDIUM': 'warning',
    'HIGH': 'danger',
    'VERY_HIGH': 'danger'
  }
  return map[level] || 'info'
}

function riskLevelLabel(level: string) {
  const map: Record<string, string> = {
    'LOW': '低风险',
    'MEDIUM': '中风险',
    'HIGH': '高风险',
    'VERY_HIGH': '极高风险'
  }
  return map[level] || level
}

function diseaseLabel(disease: string) {
  const map: Record<string, string> = {
    'HYPERTENSION': '高血压',
    'DIABETES': '糖尿病',
    'CORONARY_HEART_DISEASE': '冠心病',
    'STROKE': '脑卒中',
    'COPD': '慢阻肺',
    'CKD': '慢性肾病'
  }
  return map[disease] || disease
}

function formatDate(dateStr: string) {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN')
}

function getRiskLabel(level: string) {
  return riskLevelLabel(level)
}
</script>

<style scoped>
.patient-detail {
  padding: 20px;
}
</style>