<template>
  <el-dialog
    :model-value="props.visible"
    @update:model-value="emit('update:visible', $event)"
    :title="isEdit ? '编辑随访提醒' : '新增随访提醒'"
    width="700px"
    @close="handleClose"
  >
    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-width="130px"
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
                :key="patient.patient_id"
                :label="patient.name_enc"
                :value="patient.patient_id"
              />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="慢病类型" prop="disease_code">
            <el-select v-model="form.disease_code" placeholder="请选择慢病类型" clearable>
              <el-option label="高血压" value="HYPERTENSION" />
              <el-option label="糖尿病" value="DIABETES" />
              <el-option label="冠心病" value="CHD" />
              <el-option label="脑卒中" value="STROKE" />
              <el-option label="慢阻肺" value="COPD" />
              <el-option label="慢性肾脏病" value="CKD" />
            </el-select>
          </el-form-item>
        </el-col>
      </el-row>

      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="计划类型" prop="plan_type">
            <el-select v-model="form.plan_type" placeholder="请选择计划类型">
              <el-option label="随访" value="FOLLOWUP" />
              <el-option label="评估" value="ASSESSMENT" />
              <el-option label="检查" value="EXAM" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="计划日期" prop="plan_date">
            <el-date-picker
              v-model="form.plan_date"
              type="date"
              placeholder="请选择计划日期"
              style="width: 100%"
              format="YYYY-MM-DD"
              value-format="YYYY-MM-DD"
            />
          </el-form-item>
        </el-col>
      </el-row>

      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="通知渠道" prop="channel">
            <el-select v-model="form.channel" placeholder="请选择通知渠道">
              <el-option label="短信" value="SMS" />
              <el-option label="微信" value="WECHAT" />
              <el-option label="App推送" value="APP_PUSH" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="状态" prop="status">
            <el-select v-model="form.status" placeholder="请选择状态">
              <el-option label="待发送" value="PENDING" />
              <el-option label="已发送" value="SENT" />
              <el-option label="发送失败" value="FAILED" />
            </el-select>
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
import { useReminderStore } from '@/stores/reminder'
import { usePatientStore } from '@/stores/patient'
import { ElMessage } from 'element-plus'
import type { ReminderRecord, ReminderCreate, ReminderUpdate } from '@/types/reminder'
import type { Patient } from '@/types/patient'
import type { FormInstance, FormRules } from 'element-plus'

const props = defineProps<{
  visible: boolean
  reminder?: ReminderRecord | null
}>()

const emit = defineEmits<{
  'update:visible': [value: boolean]
  success: []
}>()

const reminderStore = useReminderStore()
const patientStore = usePatientStore()

const formRef = ref<FormInstance>()
const loading = ref(false)
const patientLoading = ref(false)
const patientOptions = ref<Patient[]>([])

const isEdit = computed(() => !!props.reminder)

const form = reactive<ReminderCreate | ReminderUpdate>({
  patient_id: '',
  disease_code: '',
  plan_date: '',
  plan_type: 'FOLLOWUP',
  channel: 'WECHAT',
  status: 'PENDING',
})

const rules = reactive<FormRules>({
  patient_id: [{ required: true, message: '请选择患者', trigger: 'change' }],
  plan_type: [{ required: true, message: '请选择计划类型', trigger: 'change' }],
  plan_date: [{ required: true, message: '请选择计划日期', trigger: 'change' }],
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

watch(() => props.reminder, (val) => {
  if (val) {
    Object.assign(form, {
      patient_id: val.patient_id,
      disease_code: val.disease_code || '',
      plan_date: val.plan_date,
      plan_type: val.plan_type,
      channel: val.channel || 'WECHAT',
      status: val.status,
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

const resetForm = () => {
  Object.assign(form, {
    patient_id: '',
    disease_code: '',
    plan_date: '',
    plan_type: 'FOLLOWUP',
    channel: 'WECHAT',
    status: 'PENDING',
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

    if (isEdit.value && props.reminder) {
      await reminderStore.updateReminder(props.reminder.reminder_id, form as ReminderUpdate)
      ElMessage.success('更新成功')
    } else {
      await reminderStore.createReminder(form as ReminderCreate)
      ElMessage.success('创建成功')
    }

    emit('success')
    handleClose()
  } catch (error) {
    if (error !== false) {
      ElMessage.error('操作失败')
    }
  } finally {
    loading.value = false
  }
}
</script>
