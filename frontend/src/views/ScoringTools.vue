<template>
  <div class="scoring-tools">
    <el-card class="header-card">
      <template #header>
        <div class="card-header">
          <span>临床评分工具</span>
          <el-tag>12个评分量表</el-tag>
        </div>
      </template>
      
      <el-row :gutter="20">
        <el-col :span="6" v-for="tool in tools" :key="tool.id">
          <el-card 
            class="tool-card" 
            :class="{ active: selectedTool?.id === tool.id }"
            @click="selectTool(tool)"
            shadow="hover"
          >
            <div class="tool-icon">{{ tool.icon }}</div>
            <div class="tool-name">{{ tool.name }}</div>
            <div class="tool-desc">{{ tool.desc }}</div>
          </el-card>
        </el-col>
      </el-row>
    </el-card>

    <!-- 评分表单 -->
    <el-card v-if="selectedTool" class="form-card">
      <template #header>
        <div class="card-header">
          <span>{{ selectedTool.name }}</span>
          <el-button text @click="selectedTool = null">关闭</el-button>
        </div>
      </template>

      <!-- 高血压 -->
      <div v-if="selectedTool.id === 'hypertension'">
        <el-form :model="hypertensionForm" label-width="120px">
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="收缩压">
                <el-input-number v-model="hypertensionForm.sbp" :min="80" :max="250" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="舒张压">
                <el-input-number v-model="hypertensionForm.dbp" :min="40" :max="150" />
              </el-form-item>
            </el-col>
          </el-row>
          <el-form-item label="年龄">
            <el-input-number v-model="hypertensionForm.age" :min="18" :max="120" />
          </el-form-item>
          <el-divider content-position="left">危险因素</el-divider>
          <el-checkbox-group v-model="hypertensionForm.riskFactors">
            <el-checkbox label="has_diabetes">糖尿病</el-checkbox>
            <el-checkbox label="dyslipidemia">血脂异常</el-checkbox>
            <el-checkbox label="smoking">吸烟</el-checkbox>
          </el-checkbox-group>
          <el-divider content-position="left">靶器官损害</el-divider>
          <el-checkbox-group v-model="hypertensionForm.clinicalConditions">
            <el-checkbox label="has_chd">冠心病</el-checkbox>
            <el-checkbox label="has_stroke">脑卒中</el-checkbox>
            <el-checkbox label="has_ckd">慢性肾病</el-checkbox>
          </el-checkbox-group>
        </el-form>
      </div>

      <!-- 糖尿病 -->
      <div v-if="selectedTool.id === 'diabetes'">
        <el-form :model="diabetesForm" label-width="120px">
          <el-row :gutter="20">
            <el-col :span="8">
              <el-form-item label="空腹血糖">
                <el-input-number v-model="diabetesForm.fasting_glucose" :min="3" :max="30" :precision="1" />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="糖化血红蛋白">
                <el-input-number v-model="diabetesForm.hba1c" :min="4" :max="15" :precision="1" />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="年龄">
                <el-input-number v-model="diabetesForm.age" :min="18" :max="120" />
              </el-form-item>
            </el-col>
          </el-row>
          <el-form-item label="病程(年)">
            <el-input-number v-model="diabetesForm.disease_duration_years" :min="0" :max="50" />
          </el-form-item>
          <el-divider content-position="left">并发症</el-divider>
          <el-checkbox-group v-model="diabetesForm.complications">
            <el-checkbox label="has_hypertension">高血压</el-checkbox>
            <el-checkbox label="has_retinopathy">视网膜病变</el-checkbox>
            <el-checkbox label="has_nephropathy">肾病</el-checkbox>
            <el-checkbox label="has_neuropathy">神经病变</el-checkbox>
          </el-checkbox-group>
        </el-form>
      </div>

      <!-- COPD CAT -->
      <div v-if="selectedTool.id === 'cat'">
        <el-form :model="catForm" label-width="150px">
          <el-form-item label="咳嗽">
            <el-slider v-model="catForm.cough_score" :min="0" :max="5" show-stops />
          </el-form-item>
          <el-form-item label="咳痰">
            <el-slider v-model="catForm.sputum_score" :min="0" :max="5" show-stops />
          </el-form-item>
          <el-form-item label="胸闷">
            <el-slider v-model="catForm.chest_tightness" :min="0" :max="5" show-stops />
          </el-form-item>
          <el-form-item label="气促">
            <el-slider v-model="catForm.breathlessness" :min="0" :max="5" show-stops />
          </el-form-item>
          <el-form-item label="活动受限">
            <el-slider v-model="catForm.activity_limitation" :min="0" :max="5" show-stops />
          </el-form-item>
          <el-form-item label="外出信心">
            <el-slider v-model="catForm.confidence" :min="0" :max="5" show-stops />
          </el-form-item>
          <el-form-item label="睡眠影响">
            <el-slider v-model="catForm.sleep_disturbance" :min="0" :max="5" show-stops />
          </el-form-item>
          <el-form-item label="精力">
            <el-slider v-model="catForm.energy" :min="0" :max="5" show-stops />
          </el-form-item>
        </el-form>
      </div>

      <!-- 其他评分工具简化显示 -->
      <div v-if="!['hypertension', 'diabetes', 'cat'].includes(selectedTool.id)">
        <el-empty description="该评分工具正在开发中..." />
      </div>

      <div class="action-bar">
        <el-button type="primary" @click="calculate" :loading="loading">
          开始评分
        </el-button>
        <el-button @click="resetForm">重置</el-button>
      </div>
    </el-card>

    <!-- 评分结果 -->
    <el-card v-if="result" class="result-card">
      <template #header>
        <div class="card-header">
          <span>评分结果</span>
          <el-tag :type="resultType">{{ result.riskLevelName || getImpactText(result.impactLevel) }}</el-tag>
        </div>
      </template>

      <el-descriptions :column="2" border>
        <el-descriptions-item label="评分结果">
          <el-tag size="large" :type="resultType">
            {{ result.riskLevelName || getImpactText(result.impactLevel) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="得分">
          {{ result.riskScore || result.totalScore }} 分
        </el-descriptions-item>
        <el-descriptions-item label="血压分级" v-if="result.bpCategory">
          {{ result.bpCategory }}
        </el-descriptions-item>
        <el-descriptions-item label="建议" :span="2">
          <ul class="recommendations">
            <li v-for="(rec, idx) in result.recommendations" :key="idx">{{ rec }}</li>
          </ul>
        </el-descriptions-item>
      </el-descriptions>

      <!-- CAT评分详情 -->
      <div v-if="result.items" class="cat-details">
        <el-divider>评分详情</el-divider>
        <el-row :gutter="10">
          <el-col :span="6" v-for="(score, item) in result.items" :key="item">
            <el-statistic :title="item" :value="score" suffix="分" />
          </el-col>
        </el-row>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import request from '@/api/request'

const loading = ref(false)
const selectedTool = ref<any>(null)
const result = ref<any>(null)

const tools = [
  { id: 'hypertension', name: '高血压风险分层', desc: 'WHO/ISH心血管风险', icon: '🩺' },
  { id: 'diabetes', name: '糖尿病评估', desc: 'ADA 2024综合风险', icon: '💉' },
  { id: 'cat', name: 'CAT评分', desc: 'COPD评估测试', icon: '🌬️' },
  { id: 'mmrc', name: 'mMRC评分', desc: '呼吸困难分级', icon: '😮' },
  { id: 'gold', name: 'GOLD分级', desc: 'COPD严重程度', icon: '📊' },
  { id: 'timi', name: 'TIMI评分', desc: '急性冠脉综合征', icon: '❤️' },
  { id: 'grace', name: 'GRACE评分', desc: 'ACS风险预测', icon: '🏥' },
  { id: 'fast', name: 'FAST评估', desc: '脑卒中识别', icon: '🧠' },
  { id: 'nihss', name: 'NIHSS评分', desc: '卒中严重程度', icon: '📋' },
  { id: 'egfr', name: 'eGFR计算', desc: '肾功能评估', icon: '🫘' },
  { id: 'unified', name: '综合评分', desc: '统一评分接口', icon: '🎯' },
  { id: 'tools', name: '工具列表', desc: '可用工具查询', icon: '📝' },
]

// 表单数据
const hypertensionForm = ref({
  sbp: 140,
  dbp: 90,
  age: 50,
  riskFactors: [],
  clinicalConditions: [],
})

const diabetesForm = ref({
  fasting_glucose: 7.0,
  hba1c: 7.0,
  age: 50,
  disease_duration_years: 5,
  complications: [],
})

const catForm = ref({
  cough_score: 0,
  sputum_score: 0,
  chest_tightness: 0,
  breathlessness: 0,
  activity_limitation: 0,
  confidence: 0,
  sleep_disturbance: 0,
  energy: 0,
})

const getImpactText = (level: string) => {
  const map: Record<string, string> = {
    'A': 'A-禁忌',
    'B': 'B-谨慎',
    'C': 'C- minor',
    'D': 'D-无',
    'X': 'X-避免',
    'LOW': '低风险',
    'MEDIUM': '中风险',
    'HIGH': '高风险',
    'Mild': '轻度',
    'Moderate': '中度',
    'Severe': '重度',
  }
  return map[level] || level || '-'
}

const resultType = computed(() => {
  if (!result.value) return 'info'
  const level = result.value.riskLevel || result.value.impactCode
  if (['LOW', 'Mild'].includes(level)) return 'success'
  if (['MEDIUM', 'Moderate'].includes(level)) return 'warning'
  if (['HIGH', 'Severe'].includes(level)) return 'danger'
  return 'info'
})

function selectTool(tool: any) {
  selectedTool.value = tool
  result.value = null
}

function resetForm() {
  hypertensionForm.value = { sbp: 140, dbp: 90, age: 50, riskFactors: [], clinicalConditions: [] }
  diabetesForm.value = { fasting_glucose: 7.0, hba1c: 7.0, age: 50, disease_duration_years: 5, complications: [] }
  catForm.value = { cough_score: 0, sputum_score: 0, chest_tightness: 0, breathlessness: 0, activity_limitation: 0, confidence: 0, sleep_disturbance: 0, energy: 0 }
  result.value = null
}

async function calculate() {
  if (!selectedTool.value) return
  
  loading.value = true
  try {
    const toolId = selectedTool.value.id
    let endpoint = `/v1/scoring/${toolId}`
    let data: any = {}

    if (toolId === 'hypertension') {
      data = {
        sbp: hypertensionForm.value.sbp,
        dbp: hypertensionForm.value.dbp,
        age: hypertensionForm.value.age,
        has_diabetes: hypertensionForm.value.riskFactors.includes('has_diabetes'),
        dyslipidemia: hypertensionForm.value.riskFactors.includes('dyslipidemia'),
        smoking: hypertensionForm.value.riskFactors.includes('smoking'),
        has_chd: hypertensionForm.value.clinicalConditions.includes('has_chd'),
        has_stroke: hypertensionForm.value.clinicalConditions.includes('has_stroke'),
        has_ckd: hypertensionForm.value.clinicalConditions.includes('has_ckd'),
      }
    } else if (toolId === 'diabetes') {
      data = {
        fasting_glucose: diabetesForm.value.fasting_glucose,
        hba1c: diabetesForm.value.hba1c,
        age: diabetesForm.value.age,
        disease_duration_years: diabetesForm.value.disease_duration_years,
        has_hypertension: diabetesForm.value.complications.includes('has_hypertension'),
        has_retinopathy: diabetesForm.value.complications.includes('has_retinopathy'),
        has_nephropathy: diabetesForm.value.complications.includes('has_nephropathy'),
        has_neuropathy: diabetesForm.value.complications.includes('has_neuropathy'),
      }
    } else if (toolId === 'cat') {
      data = catForm.value
    }

    const response = await request.post(endpoint, data)
    result.value = response
    ElMessage.success('评分完成')
  } catch (error: any) {
    // 错误已由 request.ts 拦截器统一提示
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.scoring-tools {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-card {
  margin-bottom: 20px;
}

.tool-card {
  text-align: center;
  padding: 20px;
  cursor: pointer;
  transition: all 0.3s;
  margin-bottom: 15px;
}

.tool-card:hover {
  transform: translateY(-5px);
}

.tool-card.active {
  border-color: #409eff;
  background: #ecf5ff;
}

.tool-icon {
  font-size: 32px;
  margin-bottom: 10px;
}

.tool-name {
  font-weight: bold;
  margin-bottom: 5px;
}

.tool-desc {
  font-size: 12px;
  color: #909399;
}

.form-card, .result-card {
  margin-top: 20px;
}

.action-bar {
  text-align: center;
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #ebeef5;
}

.recommendations {
  margin: 0;
  padding-left: 20px;
}

.recommendations li {
  margin: 5px 0;
}

.cat-details {
  margin-top: 20px;
}
</style>
