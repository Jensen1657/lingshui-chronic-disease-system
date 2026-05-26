<template>
  <el-dialog
    :model-value="props.visible"
    @update:model-value="emit('update:visible', $event)"
    :title="isEdit ? '编辑自报数据' : '新增自报数据'"
    width="700px"
    @close="handleClose"
  >
    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-width="120px"
    >
      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="患者" prop="patient_id">
            <el-select
              v-model="form.patient_id"
              placeholder="请选择患者"
              filterable
              remote
              :remote-method="searchPatients"
              :loading="patientLoading"
              style="width: 100%"
            >
              <el-option
                v-for="patient in patientOptions"
                :key="patient.id"
                :label="`${patient.name} (${patient.patient_no})`"
                :value="patient.id"
              />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="数据类型" prop="report_type">
            <el-select v-model="form.report_type" placeholder="请选择数据类型" @change="handleTypeChange">
              <el-option label="血压" value="blood_pressure" />
              <el-option label="血糖" value="blood_sugar" />
              <el-option label="体重" value="weight" />
              <el-option label="心率" value="heart_rate" />
              <el-option label="步数" value="steps" />
              <el-option label="睡眠" value="sleep" />
              <el-option label="症状" value="symptom" />
              <el-option label="用药" value="medication" />
              <el-option label="其他" value="other" />
            </el-select>
          </el-form-item>
        </el-col>
      </el-row>

      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="上报日期" prop="report_date">
            <el-date-picker
              v-model="form.report_date"
              type="datetime"
              placeholder="请选择上报日期"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="数据来源" prop="data_source">
            <el-select v-model="form.data_source" placeholder="请选择数据来源">
              <el-option label="手动录入" value="manual" />
              <el-option label="设备同步" value="device" />
              <el-option label="微信上报" value="wechat" />
            </el-select>
          </el-form-item>
        </el-col>
      </el-row>

      <!-- 动态字段：血压 -->
      <template v-if="form.report_type === 'blood_pressure'">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="收缩压(mmHg)" prop="systolic">
              <el-input-number
                v-model="form.systolic"
                :min="0"
                :max="300"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="舒张压(mmHg)" prop="diastolic">
              <el-input-number
                v-model="form.diastolic"
                :min="0"
                :max="200"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
        </el-row>
      </template>

      <!-- 动态字段：血糖 -->
      <template v-if="form.report_type === 'blood_sugar'">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="血糖值(mmol/L)" prop="blood_sugar_value">
              <el-input-number
                v-model="form.blood_sugar_value"
                :precision="1"
                :step="0.1"
                :min="0"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="测量时间" prop="measurement_time">
              <el-select v-model="form.measurement_time" placeholder="请选择测量时间">
                <el-option label="空腹" value="fasting" />
                <el-option label="早餐后" value="after_breakfast" />
                <el-option label="午餐后" value="after_lunch" />
                <el-option label="晚餐后" value="after_dinner" />
                <el-option label="睡前" value="before_sleep" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
      </template>

      <!-- 动态字段：体重 -->
      <template v-if="form.report_type === 'weight'">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="体重(kg)" prop="weight_value">
              <el-input-number
                v-model="form.weight_value"
                :precision="1"
                :step="0.1"
                :min="0"
                :max="500"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="BMI" prop="bmi_value">
              <el-input-number
                v-model="form.bmi_value"
                :precision="1"
                :step="0.1"
                :min="0"
                :max="100"
                style="width: 100%"
                disabled
              />
            </el-form-item>
          </el-col>
        </el-row>
      </template>

      <!-- 动态字段：心率 -->
      <template v-if="form.report_type === 'heart_rate'">
        <el-form-item label="心率(次/分)" prop="heart_rate_value">
          <el-input-number
            v-model="form.heart_rate_value"
            :min="0"
            :max="300"
            style="width: 200px"
          />
        </el-form-item>
      </template>

      <!-- 动态字段：步数 -->
      <template v-if="form.report_type === 'steps'">
        <el-form-item label="步数" prop="steps_value">
          <el-input-number
            v-model="form.steps_value"
            :min="0"
            :max="100000"
            style="width: 200px"
          />
        </el-form-item>
      </template>

      <!-- 动态字段：睡眠 -->
      <template v-if="form.report_type === 'sleep'">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="睡眠时长(小时)" prop="sleep_duration">
              <el-input-number
                v-model="form.sleep_duration"
                :precision="1"
                :step="0.5"
                :min="0"
                :max="24"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="睡眠质量" prop="sleep_quality">
              <el-select v-model="form.sleep_quality" placeholder="请选择睡眠质量">
                <el-option label="好" value="good" />
                <el-option label="一般" value="fair" />
                <el-option label="差" value="poor" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
      </template>

      <!-- 动态字段：症状 -->
      <template v-if="form.report_type === 'symptom'">
        <el-form-item label="症状描述" prop="symptom_desc">
          <el-input
            v-model="form.symptom_desc"
            type="textarea"
            :rows="3"
            placeholder="请输入症状描述"
          />
        </el-form-item>
      </template>

      <!-- 动态字段：用药 -->
      <template v-if="form.report_type === 'medication'">
        <el-form-item label="用药情况" prop="medication_desc">
          <el-input
            v-model="form.medication_desc"
            type="textarea"
            :rows="3"
            placeholder="请输入用药情况"
          />
        </el-form-item>
      </template>

      <!-- 通用字段：备注 -->
      <el-form-item label="备注" prop="remark">
        <el-input
          v-model="form.remark"
          type="textarea"
          :rows="2"
          placeholder="请输入备注"
        />
      </el-form-item>

      <!-- 设备ID（可选） -->
      <el-form-item v-if="form.data_source === 'device'" label="设备ID" prop="device_id">
        <el-input v-model="form.device_id" placeholder="请输入设备ID" />
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="handleClose">取消</el-button>
      <el-button type="primary" @click="handleSubmit" :loading="loading">
        {{ isEdit ? '更新' : '创建' }}
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue'
import { useSelfReportStore } from '@/stores/selfReport'
import { usePatientStore } from '@/stores/patient'
import type { SelfReportRecord, SelfReportCreate, SelfReportUpdate } from '@/types/self-report'
import type { Patient } from '@/types/patient'
import type { FormInstance, FormRules } from 'element-plus'

const props = defineProps<{
  visible: boolean
  report?: SelfReportRecord | null
}>()

const emit = defineEmits<{
  'update:visible': [value: boolean]
  success: []
}>()

const selfReportStore = useSelfReportStore()
const patientStore = usePatientStore()

const formRef = ref<FormInstance>()
const loading = ref(false)
const patientLoading = ref(false)
const patientOptions = ref<Patient[]>([])

const isEdit = computed(() => !!props.report)

const form = reactive<SelfReportCreate | SelfReportUpdate>({
  patient_id: '',
  report_type: '',
  report_date: '',
  data_source: 'manual',
  device_id: '',
  remark: '',
  // 动态字段
  systolic: undefined,
  diastolic: undefined,
  blood_sugar_value: undefined,
  measurement_time: '',
  weight_value: undefined,
  bmi_value: undefined,
  heart_rate_value: undefined,
  steps_value: undefined,
  sleep_duration: undefined,
  sleep_quality: '',
  symptom_desc: '',
  medication_desc: ''
})

const rules = reactive<FormRules>({
  patient_id: [{ required: true, message: '请选择患者', trigger: 'change' }],
  report_type: [{ required: true, message: '请选择数据类型', trigger: 'change' }],
  report_date: [{ required: true, message: '请选择上报日期', trigger: 'change' }]
})

const handleTypeChange = () => {
  // 切换类型时清空动态字段
  form.systolic = undefined
  form.diastolic = undefined
  form.blood_sugar_value = undefined
  form.measurement_time = ''
  form.weight_value = undefined
  form.bmi_value = undefined
  form.heart_rate_value = undefined
  form.steps_value = undefined
  form.sleep_duration = undefined
  form.sleep_quality = ''
  form.symptom_desc = ''
  form.medication_desc = ''
}

const searchPatients = async (query: string) => {
  if (!query) {
    patientOptions.value = []
    return
  }

  try {
    patientLoading.value = true
    await patientStore.fetchPatients({ name: query, page: 1, page_size: 10 })
    patientOptions.value = patientStore.patients
  } catch (error) {
    console.error('Failed to search patients:', error)
  } finally {
    patientLoading.value = false
  }
}

watch(() => props.report, (val) => {
  if (val) {
    Object.assign(form, {
      patient_id: val.patient_id,
      report_type: val.report_type,
      report_date: val.report_date,
      data_source: val.data_source || 'manual',
      device_id: val.device_id || '',
      remark: val.remark || ''
    })

    // 根据数据类型填充动态字段
    if (val.report_data) {
      const reportData = typeof val.report_data === 'string' ? JSON.parse(val.report_data) : val.report_data
      if (form.report_type === 'blood_pressure') {
        form.systolic = reportData.systolic
        form.diastolic = reportData.diastolic
      } else if (form.report_type === 'blood_sugar') {
        form.blood_sugar_value = reportData.blood_sugar_value
        form.measurement_time = reportData.measurement_time
      } else if (form.report_type === 'weight') {
        form.weight_value = reportData.weight_value
        form.bmi_value = reportData.bmi_value
      } else if (form.report_type === 'heart_rate') {
        form.heart_rate_value = reportData.heart_rate_value
      } else if (form.report_type === 'steps') {
        form.steps_value = reportData.steps_value
      } else if (form.report_type === 'sleep') {
        form.sleep_duration = reportData.sleep_duration
        form.sleep_quality = reportData.sleep_quality
      } else if (form.report_type === 'symptom') {
        form.symptom_desc = reportData.symptom_desc
      } else if (form.report_type === 'medication') {
        form.medication_desc = reportData.medication_desc
      }
    }

    // 将当前患者添加到选项中
    if (val.patient_id && val.patient_name) {
      patientOptions.value = [{
        id: val.patient_id,
        name: val.patient_name,
        patient_no: val.patient_no || '',
        id_card: '',
        gender: '',
        birth_date: '',
        is_archived: false,
        created_at: '',
        updated_at: ''
      } as Patient]
    }
  } else {
    resetForm()
  }
}, { immediate: true })

const resetForm = () => {
  Object.assign(form, {
    patient_id: '',
    report_type: '',
    report_date: '',
    data_source: 'manual',
    device_id: '',
    remark: '',
    systolic: undefined,
    diastolic: undefined,
    blood_sugar_value: undefined,
    measurement_time: '',
    weight_value: undefined,
    bmi_value: undefined,
    heart_rate_value: undefined,
    steps_value: undefined,
    sleep_duration: undefined,
    sleep_quality: '',
    symptom_desc: '',
    medication_desc: ''
  })
  patientOptions.value = []
}

const handleClose = () => {
  emit('update:visible', false)
  resetForm()
}

const handleSubmit = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
    loading.value = true

    // 构建report_data
    const reportData: any = {}
    if (form.report_type === 'blood_pressure') {
      reportData.systolic = form.systolic
      reportData.diastolic = form.diastolic
    } else if (form.report_type === 'blood_sugar') {
      reportData.blood_sugar_value = form.blood_sugar_value
      reportData.measurement_time = form.measurement_time
    } else if (form.report_type === 'weight') {
      reportData.weight_value = form.weight_value
      reportData.bmi_value = form.bmi_value
    } else if (form.report_type === 'heart_rate') {
      reportData.heart_rate_value = form.heart_rate_value
    } else if (form.report_type === 'steps') {
      reportData.steps_value = form.steps_value
    } else if (form.report_type === 'sleep') {
      reportData.sleep_duration = form.sleep_duration
      reportData.sleep_quality = form.sleep_quality
    } else if (form.report_type === 'symptom') {
      reportData.symptom_desc = form.symptom_desc
    } else if (form.report_type === 'medication') {
      reportData.medication_desc = form.medication_desc
    }

    const submitData = {
      ...form,
      report_data: JSON.stringify(reportData)
    }

    if (isEdit.value && props.report) {
      await selfReportStore.updateReport(props.report.id, submitData as SelfReportUpdate)
      ElMessage.success('更新成功')
    } else {
      await selfReportStore.createReport(submitData as SelfReportCreate)
      ElMessage.success('创建成功')
    }

    emit('success')
    handleClose()
  } catch (error) {
    if (error !== false) {
      // 错误已由 request.ts 拦截器统一提示
    }
  } finally {
    loading.value = false
  }
}
</script>
