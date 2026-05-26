<template>
  <el-dialog
    :model-value="props.visible"
    @update:model-value="emit('update:visible', $event)"
    :title="isEdit ? '编辑急救联动' : '新增急救联动'"
    width="900px"
    @close="handleClose"
  >
    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-width="130px"
    >
      <el-divider content-position="left">基本信息</el-divider>

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
                :key="patient.patient_id"
                :label="patient.name_enc"
                :value="patient.patient_id"
              />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="急救类型" prop="alert_type">
            <el-select v-model="form.alert_type" placeholder="请选择急救类型">
              <el-option label="胸痛" value="CHEST_PAIN" />
              <el-option label="脑卒中" value="STROKE" />
              <el-option label="高血压危象" value="HYPERTENSIVE_CRISIS" />
              <el-option label="低血糖" value="HYPOGLYCEMIA" />
              <el-option label="高血糖" value="HYPERGLYCEMIA" />
              <el-option label="呼吸衰竭" value="RESPIRATORY_FAILURE" />
              <el-option label="其他" value="OTHER" />
            </el-select>
          </el-form-item>
        </el-col>
      </el-row>

      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="触发人" prop="trigger_by">
            <el-input v-model="form.trigger_by" placeholder="请输入触发人" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="预计到达时间" prop="estimated_arrival">
            <el-date-picker
              v-model="form.estimated_arrival"
              type="datetime"
              placeholder="请选择预计到达时间"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>
      </el-row>

      <el-divider content-position="left">患者信息</el-divider>

      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="既往病史" prop="patient_history">
            <el-input
              v-model="form.patient_history"
              type="textarea"
              :rows="2"
              placeholder="请输入既往病史"
            />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="用药情况" prop="medications">
            <el-input
              v-model="form.medications"
              type="textarea"
              :rows="2"
              placeholder="请输入当前用药情况"
            />
          </el-form-item>
        </el-col>
      </el-row>

      <el-form-item label="过敏史" prop="allergies">
        <el-input
          v-model="form.allergies"
          placeholder='请输入过敏史（若无请填"无"）'
        />
      </el-form-item>

      <el-divider content-position="left">生命体征</el-divider>

      <el-row :gutter="20">
        <el-col :span="8">
          <el-form-item label="意识状态" prop="vital_signs.consciousness">
            <el-input v-model="form.vital_signs!.consciousness" placeholder="如：清醒、嗜睡、昏迷" />
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="血压(mmHg)" prop="vital_signs.blood_pressure">
            <el-input v-model="form.vital_signs!.blood_pressure" placeholder="如：120/80" />
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="心率(次/分)" prop="vital_signs.heart_rate">
            <el-input-number
              v-model="form.vital_signs!.heart_rate"
              :min="0"
              :max="300"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>
      </el-row>

      <el-row :gutter="20">
        <el-col :span="8">
          <el-form-item label="呼吸频率" prop="vital_signs.respiratory_rate">
            <el-input-number
              v-model="form.vital_signs!.respiratory_rate"
              :min="0"
              :max="100"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="体温(℃)" prop="vital_signs.body_temperature">
            <el-input-number
              v-model="form.vital_signs!.body_temperature"
              :precision="1"
              :step="0.1"
              :min="30"
              :max="50"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="血氧饱和度(%)" prop="vital_signs.spo2">
            <el-input-number
              v-model="form.vital_signs!.spo2"
              :min="0"
              :max="100"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>
      </el-row>

      <el-divider content-position="left">转诊信息</el-divider>

      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="目标机构" prop="target_org">
            <el-input v-model="form.target_org" placeholder="请输入目标医院" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="目标科室" prop="target_dept">
            <el-input v-model="form.target_dept" placeholder="请输入目标科室" />
          </el-form-item>
        </el-col>
      </el-row>
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
import { useEmergencyStore } from '@/stores/emergency'
import { usePatientStore } from '@/stores/patient'
import type { EmergencyRecord, EmergencyCreate, EmergencyUpdate } from '@/types/emergency'
import type { Patient } from '@/types/patient'
import type { FormInstance, FormRules } from 'element-plus'

const props = defineProps<{
  visible: boolean
  record?: EmergencyRecord | null
}>()

const emit = defineEmits<{
  'update:visible': [value: boolean]
  success: []
}>()

const emergencyStore = useEmergencyStore()
const patientStore = usePatientStore()

const formRef = ref<FormInstance>()
const loading = ref(false)
const patientLoading = ref(false)
const patientOptions = ref<Patient[]>([])

const isEdit = computed(() => !!props.record)

const form = reactive<EmergencyCreate | EmergencyUpdate>({
  patient_id: '',
  alert_type: '',
  patient_history: '',
  medications: '',
  allergies: '',
  vital_signs: {
    consciousness: '',
    blood_pressure: '',
    heart_rate: undefined,
    respiratory_rate: undefined,
    body_temperature: undefined,
    spo2: undefined,
  },
  target_org: '',
  target_dept: '',
  estimated_arrival: '',
  trigger_by: '',
})

const rules = reactive<FormRules>({
  patient_id: [{ required: true, message: '请选择患者', trigger: 'change' }],
  alert_type: [{ required: true, message: '请选择急救类型', trigger: 'change' }],
})

const searchPatients = async (query: string) => {
  if (!query) {
    patientOptions.value = []
    return
  }
  try {
    patientLoading.value = true
    await patientStore.fetchPatients({ page: 1, page_size: 20 })
    patientOptions.value = patientStore.patients.filter(p =>
      p.name_enc && p.name_enc.includes(query)
    )
  } catch (error) {
    console.error('搜索患者失败:', error)
  } finally {
    patientLoading.value = false
  }
}

const resetForm = () => {
  Object.assign(form, {
    patient_id: '',
    alert_type: '',
    patient_history: '',
    medications: '',
    allergies: '',
    vital_signs: {
      consciousness: '',
      blood_pressure: '',
      heart_rate: undefined,
      respiratory_rate: undefined,
      body_temperature: undefined,
      spo2: undefined,
    },
    target_org: '',
    target_dept: '',
    estimated_arrival: '',
    trigger_by: '',
  })
  patientOptions.value = []
}

const handleClose = () => {
  emit('update:visible', false)
  resetForm()
}

watch(() => props.record, (val) => {
  if (val) {
    Object.assign(form, {
      patient_id: val.patient_id,
      alert_type: val.alert_type,
      patient_history: val.patient_history || '',
      medications: val.medications || '',
      allergies: val.allergies || '',
      vital_signs: {
        consciousness: val.vital_signs?.consciousness || '',
        blood_pressure: val.vital_signs?.blood_pressure || '',
        heart_rate: val.vital_signs?.heart_rate,
        respiratory_rate: val.vital_signs?.respiratory_rate,
        body_temperature: val.vital_signs?.body_temperature,
        spo2: val.vital_signs?.spo2,
      },
      target_org: val.target_org || '',
      target_dept: val.target_dept || '',
      estimated_arrival: val.estimated_arrival || '',
      trigger_by: val.trigger_by || '',
    })
    if (val.patient_id) {
      patientOptions.value = [{
        patient_id: val.patient_id,
        name_enc: val.patient_id,
        gender: '',
        birth_date: '',
        age: 0,
        phone_enc: '',
        address: '',
        village_code: '',
        disease_list: [],
        risk_level: '',
        is_active: true,
        empi_status: '',
        manage_org_code: '',
        id_card_enc: '',
        id_card_hash: '',
        created_at: '',
        updated_at: '',
      }]
    }
  } else {
    resetForm()
  }
}, { immediate: true })

const handleSubmit = async () => {
  if (!formRef.value) return
  try {
    await formRef.value.validate()
    loading.value = true

    const submitData = {
      ...form,
      vital_signs: form.vital_signs,
    }

    if (isEdit.value && props.record) {
      await emergencyStore.updateRecord(props.record.alert_id, submitData as EmergencyUpdate)
      ElMessage.success('更新成功')
    } else {
      await emergencyStore.createRecord(submitData as EmergencyCreate)
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
