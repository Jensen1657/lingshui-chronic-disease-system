<template>
  <el-dialog
    :model-value="props.visible"
    @update:model-value="emit('update:visible', $event)"
    :title="isEdit ? '编辑中医记录' : '新增中医记录'"
    width="900px"
    @close="handleClose"
  >
    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-width="120px"
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
                :key="patient.id"
                :label="`${patient.name} (${patient.patient_no})`"
                :value="patient.id"
              />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="就诊日期" prop="visit_date">
            <el-date-picker
              v-model="form.visit_date"
              type="date"
              placeholder="请选择就诊日期"
              style="width: 100%"
            />
          </el-form-item>
        </el-col>
      </el-row>

      <el-form-item label="就诊医生" prop="visit_doctor">
        <el-input v-model="form.visit_doctor" placeholder="请输入就诊医生" />
      </el-form-item>

      <el-divider content-position="left">辨证信息</el-divider>

      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="证型" prop="syndrome_type">
            <el-select v-model="form.syndrome_type" placeholder="请选择证型">
              <el-option label="气虚质" value="qi_deficiency" />
              <el-option label="阳虚质" value="yang_deficiency" />
              <el-option label="阴虚质" value="yin_deficiency" />
              <el-option label="血瘀质" value="blood_stasis" />
              <el-option label="痰湿质" value="phlegm_dampness" />
              <el-option label="湿热质" value="damp_heat" />
              <el-option label="气郁质" value="qi_stagnation" />
              <el-option label="血虚质" value="blood_deficiency" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="中医病名" prop="tcm_disease">
            <el-select v-model="form.tcm_disease" placeholder="请选择中医病名">
              <el-option label="消渴" value="xiao_ke" />
              <el-option label="眩晕" value="xuan_yun" />
              <el-option label="胸痹" value="xiong_bi" />
              <el-option label="中风" value="zhong_feng" />
              <el-option label="肺胀" value="fei_zhang" />
              <el-option label="水肿" value="shui_zhong" />
            </el-select>
          </el-form-item>
        </el-col>
      </el-row>

      <el-form-item label="证名" prop="syndrome_name">
        <el-input v-model="form.syndrome_name" placeholder="请输入证名" />
      </el-form-item>

      <el-form-item label="辨证分析" prop="syndrome_differentiation">
        <el-input
          v-model="form.syndrome_differentiation"
          type="textarea"
          :rows="3"
          placeholder="请输入辨证分析"
        />
      </el-form-item>

      <el-divider content-position="left">四诊信息</el-divider>

      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="望诊" prop="inspection">
            <el-input
              v-model="form.inspection"
              type="textarea"
              :rows="2"
              placeholder="请输入望诊信息"
            />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="闻诊" prop="auscultation">
            <el-input
              v-model="form.auscultation"
              type="textarea"
              :rows="2"
              placeholder="请输入闻诊信息"
            />
          </el-form-item>
        </el-col>
      </el-row>

      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="问诊" prop="interrogation">
            <el-input
              v-model="form.interrogation"
              type="textarea"
              :rows="2"
              placeholder="请输入问诊信息"
            />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="切诊" prop="palpation">
            <el-input
              v-model="form.palpation"
              type="textarea"
              :rows="2"
              placeholder="请输入切诊信息"
            />
          </el-form-item>
        </el-col>
      </el-row>

      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="舌质" prop="tongue_body">
            <el-input v-model="form.tongue_body" placeholder="请输入舌质" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="舌苔" prop="tongue_coating">
            <el-input v-model="form.tongue_coating" placeholder="请输入舌苔" />
          </el-form-item>
        </el-col>
      </el-row>

      <el-form-item label="脉象" prop="pulse">
        <el-input v-model="form.pulse" placeholder="请输入脉象" />
      </el-form-item>

      <el-divider content-position="left">中医治疗</el-divider>

      <el-form-item label="治法" prop="treatment_method">
        <el-input
          v-model="form.treatment_method"
          type="textarea"
          :rows="2"
          placeholder="请输入治法"
        />
      </el-form-item>

      <el-form-item label="方药" prop="prescription">
        <el-input
          v-model="form.prescription"
          type="textarea"
          :rows="3"
          placeholder="请输入方药"
        />
      </el-form-item>

      <el-form-item label="中药饮片" prop="herbs">
        <el-input
          v-model="form.herbs"
          type="textarea"
          :rows="2"
          placeholder="请输入中药饮片"
        />
      </el-form-item>

      <el-form-item label="中成药" prop="patent_medicine">
        <el-input
          v-model="form.patent_medicine"
          type="textarea"
          :rows="2"
          placeholder="请输入中成药"
        />
      </el-form-item>

      <el-divider content-position="left">其他疗法</el-divider>

      <el-row :gutter="20">
        <el-col :span="8">
          <el-form-item label="针灸" prop="acupuncture">
            <el-input
              v-model="form.acupuncture"
              type="textarea"
              :rows="2"
              placeholder="请输入针灸方案"
            />
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="艾灸" prop="moxibustion">
            <el-input
              v-model="form.moxibustion"
              type="textarea"
              :rows="2"
              placeholder="请输入艾灸方案"
            />
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="推拿" prop="tuina">
            <el-input
              v-model="form.tuina"
              type="textarea"
              :rows="2"
              placeholder="请输入推拿方案"
            />
          </el-form-item>
        </el-col>
      </el-row>

      <el-form-item label="其他疗法" prop="other_therapy">
        <el-input
          v-model="form.other_therapy"
          type="textarea"
          :rows="2"
          placeholder="请输入其他疗法"
        />
      </el-form-item>

      <el-divider content-position="left">养生指导</el-divider>

      <el-form-item label="饮食调理" prop="diet_therapy">
        <el-input
          v-model="form.diet_therapy"
          type="textarea"
          :rows="2"
          placeholder="请输入饮食调理建议"
        />
      </el-form-item>

      <el-form-item label="运动调理" prop="exercise_therapy">
        <el-input
          v-model="form.exercise_therapy"
          type="textarea"
          :rows="2"
          placeholder="请输入运动调理建议"
        />
      </el-form-item>

      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="情志调理" prop="emotion_therapy">
            <el-input
              v-model="form.emotion_therapy"
              type="textarea"
              :rows="2"
              placeholder="请输入情志调理建议"
            />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="起居指导" prop="lifestyle_guidance">
            <el-input
              v-model="form.lifestyle_guidance"
              type="textarea"
              :rows="2"
              placeholder="请输入起居指导建议"
            />
          </el-form-item>
        </el-col>
      </el-row>

      <el-divider content-position="left">疗效评估</el-divider>

      <el-form-item label="疗效评价" prop="efficacy_evaluation">
        <el-input
          v-model="form.efficacy_evaluation"
          type="textarea"
          :rows="3"
          placeholder="请输入疗效评价"
        />
      </el-form-item>

      <el-form-item label="下次就诊日期" prop="next_visit_date">
        <el-date-picker
          v-model="form.next_visit_date"
          type="date"
          placeholder="请选择下次就诊日期"
          style="width: 200px"
        />
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
import { useTcmStore } from '@/stores/tcm'
import { usePatientStore } from '@/stores/patient'
import { ElMessage } from 'element-plus'
import type { TcmRecord, TcmCreate, TcmUpdate } from '@/types/tcm'
import type { Patient } from '@/types/patient'
import type { FormInstance, FormRules } from 'element-plus'

const props = defineProps<{
  visible: boolean
  record?: TcmRecord | null
}>()

const emit = defineEmits<{
  'update:visible': [value: boolean]
  success: []
}>()

const tcmStore = useTcmStore()
const patientStore = usePatientStore()

const formRef = ref<FormInstance>()
const loading = ref(false)
const patientLoading = ref(false)
const patientOptions = ref<Patient[]>([])

const isEdit = computed(() => !!props.record)

const form = reactive<TcmCreate | TcmUpdate>({
  patient_id: '',
  visit_date: '',
  visit_doctor: '',
  syndrome_type: '',
  syndrome_name: '',
  tcm_disease: '',
  syndrome_differentiation: '',
  inspection: '',
  auscultation: '',
  interrogation: '',
  palpation: '',
  tongue_body: '',
  tongue_coating: '',
  pulse: '',
  treatment_method: '',
  prescription: '',
  herbs: '',
  patent_medicine: '',
  acupuncture: '',
  moxibustion: '',
  tuina: '',
  other_therapy: '',
  diet_therapy: '',
  exercise_therapy: '',
  emotion_therapy: '',
  lifestyle_guidance: '',
  efficacy_evaluation: '',
  next_visit_date: ''
})

const rules = reactive<FormRules>({
  patient_id: [{ required: true, message: '请选择患者', trigger: 'change' }],
  visit_date: [{ required: true, message: '请选择就诊日期', trigger: 'change' }],
  syndrome_type: [{ required: true, message: '请选择证型', trigger: 'change' }]
})

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

const resetForm = () => {
  Object.assign(form, {
    patient_id: '',
    visit_date: '',
    visit_doctor: '',
    syndrome_type: '',
    syndrome_name: '',
    tcm_disease: '',
    syndrome_differentiation: '',
    inspection: '',
    auscultation: '',
    interrogation: '',
    palpation: '',
    tongue_body: '',
    tongue_coating: '',
    pulse: '',
    treatment_method: '',
    prescription: '',
    herbs: '',
    patent_medicine: '',
    acupuncture: '',
    moxibustion: '',
    tuina: '',
    other_therapy: '',
    diet_therapy: '',
    exercise_therapy: '',
    emotion_therapy: '',
    lifestyle_guidance: '',
    efficacy_evaluation: '',
    next_visit_date: ''
  })
  patientOptions.value = []
}

watch(() => props.record, (val) => {
  if (val) {
    Object.assign(form, {
      patient_id: val.patient_id,
      visit_date: val.visit_date,
      visit_doctor: val.visit_doctor || '',
      syndrome_type: val.syndrome_type || '',
      syndrome_name: val.syndrome_name || '',
      tcm_disease: val.tcm_disease || '',
      syndrome_differentiation: val.syndrome_differentiation || '',
      inspection: val.inspection || '',
      auscultation: val.auscultation || '',
      interrogation: val.interrogation || '',
      palpation: val.palpation || '',
      tongue_body: val.tongue_body || '',
      tongue_coating: val.tongue_coating || '',
      pulse: val.pulse || '',
      treatment_method: val.treatment_method || '',
      prescription: val.prescription || '',
      herbs: val.herbs || '',
      patent_medicine: val.patent_medicine || '',
      acupuncture: val.acupuncture || '',
      moxibustion: val.moxibustion || '',
      tuina: val.tuina || '',
      other_therapy: val.other_therapy || '',
      diet_therapy: val.diet_therapy || '',
      exercise_therapy: val.exercise_therapy || '',
      emotion_therapy: val.emotion_therapy || '',
      lifestyle_guidance: val.lifestyle_guidance || '',
      efficacy_evaluation: val.efficacy_evaluation || '',
      next_visit_date: val.next_visit_date || ''
    })

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

const handleClose = () => {
  emit('update:visible', false)
  resetForm()
}

const handleSubmit = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
    loading.value = true

    if (isEdit.value && props.record) {
      await tcmStore.updateRecord(props.record.tcm_id!, form as TcmUpdate)
      ElMessage.success('更新成功')
    } else {
      await tcmStore.createRecord(form as TcmCreate)
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
