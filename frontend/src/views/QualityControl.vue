<template>
  <div class="quality-control">
    <!-- Loading 遮罩 -->
    <div v-loading="dataLoading" class="loading-overlay" />
    
    <el-card class="header-card">
      <template #header>
        <div class="card-header">
          <span>质量控制管理</span>
          <el-button type="primary" @click="runFullCheck">执行全面检查</el-button>
        </div>
      </template>

      <el-row :gutter="20">
        <el-col :span="6">
          <el-card class="stat-card" shadow="hover">
            <el-statistic title="规则总数" :value="stats.totalRules" />
            <div v-if="dataLoading" class="loading-text">加载中...</div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card success" shadow="hover">
            <el-statistic title="通过数" :value="stats.passed" />
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card warning" shadow="hover">
            <el-statistic title="警告数" :value="stats.warnings" />
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card danger" shadow="hover">
            <el-statistic title="错误数" :value="stats.errors" />
          </el-card>
        </el-col>
      </el-row>
    </el-card>

    <el-card class="rules-card">
      <template #header>
        <div class="card-header">
          <span>质控规则配置</span>
          <el-radio-group v-model="ruleType" size="small">
            <el-radio-button label="alert">预警规则</el-radio-button>
            <el-radio-button label="referral">转诊标准</el-radio-button>
            <el-radio-button label="fields">必填字段</el-radio-button>
          </el-radio-group>
        </div>
      </template>

      <!-- 预警规则 -->
      <div v-if="ruleType === 'alert'">
        <el-table :data="alertRules" stripe v-loading="dataLoading">
          <el-table-column prop="rule_id" label="规则ID" width="100" />
          <el-table-column prop="rule_name" label="规则名称" />
          <el-table-column prop="disease_code" label="适用慢病" width="100">
            <template #default="{ row }">
              <el-tag size="small">{{ row.disease_code || '通用' }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="severity" label="严重程度" width="100">
            <template #default="{ row }">
              <el-tag :type="severityType(row.severity)">{{ getSeverityText(row.severity) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="description" label="规则说明" />
          <el-table-column prop="is_active" label="状态" width="80">
            <template #default="{ row }">
              <el-switch v-model="row.is_active" @change="toggleRule(row)" />
            </template>
          </el-table-column>
        </el-table>
      </div>

      <!-- 转诊标准 -->
      <div v-if="ruleType === 'referral'">
        <el-table :data="referralCriteria" stripe v-loading="dataLoading">
          <el-table-column prop="criterion_id" label="标准ID" width="100" />
          <el-table-column prop="disease_code" label="慢病类型" width="100">
            <template #default="{ row }">
              <el-tag size="small">{{ row.disease_code }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="direction" label="转诊方向" width="100">
            <template #default="{ row }">
              <el-tag :type="row.direction === 'UP' ? 'warning' : 'success'">
                {{ row.direction === 'UP' ? '上转' : '下转' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="conditions" label="转诊条件">
            <template #default="{ row }">
              <div class="conditions-cell">{{ formatConditions(row.conditions) }}</div>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <!-- 必填字段 -->
      <div v-if="ruleType === 'fields'">
        <el-form :inline="true" class="module-filter">
          <el-form-item label="模块">
            <el-select v-model="selectedModule" placeholder="选择模块" @change="loadRequiredFields">
              <el-option label="患者信息" value="patient" />
              <el-option label="随访记录" value="followup" />
              <el-option label="转诊记录" value="referral" />
              <el-option label="年度评估" value="assessment" />
            </el-select>
          </el-form-item>
        </el-form>

        <el-table :data="requiredFields" stripe>
          <el-table-column prop="field_name" label="字段名" />
          <el-table-column prop="field_label" label="字段标签" />
          <el-table-column prop="data_type" label="数据类型" width="100" />
          <el-table-column prop="validation_rule" label="校验规则" />
        </el-table>
      </div>
    </el-card>

    <!-- 质控检查结果 -->
    <el-card v-if="checkResult" class="result-card">
      <template #header>
        <div class="card-header">
          <span>检查结果</span>
          <el-tag :type="overallType">{{ checkResult.overall_status }}</el-tag>
        </div>
      </template>

      <el-collapse>
        <el-collapse-item 
          v-for="(moduleResult, moduleName) in checkResult.modules" 
          :key="moduleName"
          :name="moduleName"
        >
          <template #title>
            <div class="module-title">
              <span>{{ moduleName }}</span>
              <el-tag 
                :type="moduleStatusType(moduleResult.status)" 
                size="small"
                style="margin-left: 10px"
              >
                {{ moduleResult.status }}
              </el-tag>
              <span class="issue-count">{{ moduleResult.issues?.length || 0 }} 个问题</span>
            </div>
          </template>

          <el-table v-if="moduleResult.issues?.length" :data="moduleResult.issues" size="small">
            <el-table-column prop="level" label="级别" width="80">
              <template #default="{ row }">
                <el-tag :type="issueLevelType(row.level)" size="small">{{ row.level }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="field" label="字段" width="120" />
            <el-table-column prop="message" label="问题描述" />
            <el-table-column prop="value" label="当前值" width="120" />
          </el-table>

          <el-empty v-else description="无问题" :image-size="60" />
        </el-collapse-item>
      </el-collapse>
    </el-card>

    <!-- 药物相互作用检查 -->
    <el-card class="drug-card">
      <template #header>
        <div class="card-header">
          <span>药物相互作用检查</span>
        </div>
      </template>

      <el-form :inline="true">
        <el-form-item label="药物列表">
          <el-select 
            v-model="selectedDrugs" 
            multiple 
            filterable 
            placeholder="选择药物"
            style="width: 400px"
          >
            <el-option 
              v-for="drug in commonDrugs" 
              :key="drug" 
              :label="drug" 
              :value="drug" 
            />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="checkDrugInteractions">检查相互作用</el-button>
        </el-form-item>
      </el-form>

      <el-alert
        v-if="drugResult && drugResult.interactions?.length"
        :title="`发现 ${drugResult.interactions.length} 个潜在相互作用`"
        type="warning"
        :closable="false"
        show-icon
        style="margin-top: 20px"
      >
        <ul style="margin: 10px 0">
          <li v-for="(interaction, idx) in drugResult.interactions" :key="idx">
            <strong>{{ interaction.drug1 }}</strong> + <strong>{{ interaction.drug2 }}</strong>
            : {{ interaction.description }}
            <el-tag size="small" :type="interaction.severity === '严重' ? 'danger' : 'warning'">
              {{ interaction.severity }}
            </el-tag>
          </li>
        </ul>
      </el-alert>

      <el-alert
        v-else-if="drugResult"
        title="未发现药物相互作用"
        type="success"
        :closable="false"
        show-icon
        style="margin-top: 20px"
      />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import request from '@/api/request'

const loading = ref(false)
const dataLoading = ref(false)
const ruleType = ref('alert')
const selectedModule = ref('patient')
const checkResult = ref<any>(null)
const drugResult = ref<any>(null)

const stats = ref({
  totalRules: 0,
  passed: 0,
  warnings: 0,
  errors: 0,
})

const alertRules = ref<any[]>([])
const referralCriteria = ref<any[]>([])

const requiredFields = ref([
  { field_name: 'name_enc', field_label: '患者姓名', data_type: 'string', validation_rule: '非空' },
  { field_name: 'gender', field_label: '性别', data_type: 'string', validation_rule: 'M/F/O' },
  { field_name: 'birth_date', field_label: '出生日期', data_type: 'date', validation_rule: '非空' },
  { field_name: 'id_card_enc', field_label: '身份证号', data_type: 'string', validation_rule: '18位' },
  { field_name: 'phone_enc', field_label: '联系电话', data_type: 'string', validation_rule: '11位' },
])

const selectedDrugs = ref<string[]>([])
const commonDrugs = [
  '阿司匹林', '氯吡格雷', '阿托伐他汀', '氨氯地平', '硝苯地平',
  '美托洛尔', '厄贝沙坦', '缬沙坦', '二甲双胍', '格列美脲',
  '胰岛素', '阿卡波糖', '华法林', '利伐沙班', '奥美拉唑',
]

const overallType = computed(() => {
  if (!checkResult.value) return 'info'
  const status = checkResult.value.overall_status
  if (status === 'PASS') return 'success'
  if (status === 'WARNING') return 'warning'
  return 'danger'
})

function severityType(severity: string) {
  const map: Record<string, any> = {
    'HIGH': 'danger',
    'MEDIUM': 'warning',
    'LOW': 'info',
  }
  return map[severity] || 'info'
}

function getSeverityText(severity: string) {
  const map: Record<string, string> = {
    'HIGH': '高',
    'MEDIUM': '中',
    'LOW': '低',
  }
  return map[severity] || severity || '-'
}

function moduleStatusType(status: string) {
  const map: Record<string, any> = {
    'PASS': 'success',
    'WARNING': 'warning',
    'ERROR': 'danger',
  }
  return map[status] || 'info'
}

function issueLevelType(level: string) {
  const map: Record<string, any> = {
    'ERROR': 'danger',
    'WARNING': 'warning',
    'INFO': 'info',
  }
  return map[level] || 'info'
}

function formatConditions(conditions: any) {
  return Object.entries(conditions)
    .map(([k, v]) => `${k} ${v}`)
    .join(', ')
}

async function toggleRule(rule: any) {
  try {
    await request.put(`/v1/quality-control/rules/alert-rules/${rule.rule_id}`, { is_active: rule.is_active })
    ElMessage.success('规则状态已更新')
  } catch (error) {
    rule.is_active = !rule.is_active // 回滚
    // 错误已由 request.ts 拦截器统一提示
  }
}

async function loadRequiredFields() {
  try {
    const moduleMap: Record<string, string> = { patient: 'patient_profile', followup: 'hypertension_followup', referral: 'referral_record', assessment: 'annual_assessment' }
    const response = await request.get(`/v1/quality-control/rules/required-fields/${moduleMap[selectedModule.value] || selectedModule.value}`)
    requiredFields.value = response || []
  } catch (error) {
    // 使用默认数据
  }
}

async function runFullCheck() {
  loading.value = true
  try {
    const response = await request.post('/v1/quality-control/full-check', {
      modules: ['patient', 'followup', 'referral', 'assessment']
    })
    checkResult.value = response
    
    // 更新统计
    stats.value.passed = response.summary?.passed || 0
    stats.value.warnings = response.summary?.warnings || 0
    stats.value.errors = response.summary?.errors || 0
    
    ElMessage.success('检查完成')
  } catch (error: any) {
    // 错误已由 request.ts 拦截器统一提示
  } finally {
    loading.value = false
  }
}

async function checkDrugInteractions() {
  if (selectedDrugs.value.length < 2) {
    ElMessage.warning('请选择至少2种药物')
    return
  }

  try {
    const response = await request.post('/v1/quality-control/drug-interactions', {
      drugs: selectedDrugs.value
    })
    drugResult.value = response
  } catch (error: any) {
    // 错误已由 request.ts 拦截器统一提示
  }
}

onMounted(async () => {
  await Promise.all([
    loadAlertRules(),
    loadReferralCriteria(),
    loadRequiredFields(),
  ])
})

async function loadAlertRules() {
  dataLoading.value = true
  try {
    const response = await request.get('/v1/quality-control/rules/alert-rules')
    alertRules.value = response || []
    stats.value.totalRules = alertRules.value.length
  } catch (error: any) {
    // 错误已由 request.ts 拦截器统一提示
    alertRules.value = []
  } finally {
    dataLoading.value = false
  }
}

async function loadReferralCriteria() {
  try {
    const response = await request.get('/v1/quality-control/rules/referral-criteria')
    referralCriteria.value = response || []
  } catch (error: any) {
    // 错误已由 request.ts 拦截器统一提示
    referralCriteria.value = []
  }
}
</script>

<style scoped>
.quality-control {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-card, .rules-card, .result-card, .drug-card {
  margin-bottom: 20px;
}

.stat-card {
  text-align: center;
  padding: 20px;
}

.stat-card.success :deep(.el-statistic__number) {
  color: #67c23a;
}

.stat-card.warning :deep(.el-statistic__number) {
  color: #e6a23c;
}

.stat-card.danger :deep(.el-statistic__number) {
  color: #f56c6c;
}

.module-title {
  display: flex;
  align-items: center;
}

.issue-count {
  margin-left: auto;
  color: #909399;
  font-size: 12px;
}

.loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 9999;
}

.loading-text {
  font-size: 12px;
  color: #909399;
  margin-top: 5px;
}

.conditions-cell {
  font-size: 12px;
  line-height: 1.5;
}

.module-filter {
  margin-bottom: 20px;
}
</style>
