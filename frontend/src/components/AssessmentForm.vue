<template>
  <el-dialog :model-value="modelValue" @update:model-value="$emit('update:modelValue', $event)" :title="isEdit ? '编辑评估' : '新增评估'" width="650px">
    <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="患者ID" prop="patient_id">
            <el-input v-model="form.patient_id" placeholder="请输入患者ID" :disabled="isEdit" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="评估年份" prop="assessment_year">
            <el-date-picker v-model="form.assessment_year" type="year" placeholder="选择年份" style="width: 100%" />
          </el-form-item>
        </el-col>
      </el-row>

      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="慢病类型" prop="disease_code">
            <el-select v-model="form.disease_code" placeholder="请选择慢病类型" style="width: 100%">
              <el-option label="高血压" value="HYPERTENSION" />
              <el-option label="糖尿病" value="DIABETES" />
              <el-option label="冠心病" value="CORONARY_HEART_DISEASE" />
              <el-option label="脑卒中" value="STROKE" />
              <el-option label="慢阻肺" value="COPD" />
              <el-option label="慢性肾病" value="CKD" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="风险等级" prop="risk_level">
            <el-select v-model="form.risk_level" placeholder="请选择风险等级" style="width: 100%">
              <el-option label="低风险" value="LOW" />
              <el-option label="中风险" value="MEDIUM" />
              <el-option label="高风险" value="HIGH" />
              <el-option label="极高风险" value="VERY_HIGH" />
            </el-select>
          </el-form-item>
        </el-col>
      </el-row>

      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="控制状态" prop="control_status">
            <el-select v-model="form.control_status" placeholder="请选择控制状态" style="width: 100%">
              <el-option label="良好" value="GOOD" />
              <el-option label="一般" value="FAIR" />
              <el-option label="差" value="POOR" />
            </el-select>
          </el-form-item>
        </el-col>
      </el-row>

      <el-form-item label="并发症">
        <el-checkbox-group v-model="form.complications">
          <el-checkbox value="RENAL">肾病</el-checkbox>
          <el-checkbox value="RETINOPATHY">视网膜病变</el-checkbox>
          <el-checkbox value="NEUROPATHY">神经病变</el-checkbox>
          <el-checkbox value="CARDIOVASCULAR">心血管疾病</el-checkbox>
          <el-checkbox value="CEREBROVASCULAR">脑血管疾病</el-checkbox>
          <el-checkbox value="DIABETIC_FOOT">糖尿病足</el-checkbox>
        </el-checkbox-group>
      </el-form-item>

      <el-form-item label="治疗方案">
        <el-input v-model="form.treatment_plan" type="textarea" :rows="3" placeholder="请输入治疗方案" />
      </el-form-item>

      <el-form-item label="医嘱建议">
        <el-input v-model="form.doctor_advice" type="textarea" :rows="3" placeholder="请输入医嘱建议" />
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="$emit('update:modelValue', false)">取消</el-button>
      <el-button type="primary" :loading="loading" @click="handleSubmit">确定</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { reactive, ref, watch, computed } from 'vue'
import { assessmentApi } from '@/api/assessment'

interface AssessmentRecord {
  assessment_id?: string
  patient_id: string
  assessment_year: string
  disease_code: string
  risk_level?: string
  control_status?: string
  complications: string[]
  treatment_plan?: string
  doctor_advice?: string
}

const props = defineProps<{
  modelValue: boolean
  record: AssessmentRecord | null
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'success': []
}>()

const formRef = ref()
const loading = ref(false)

const isEdit = computed(() => !!props.record?.assessment_id)

const form = reactive<Omit<AssessmentRecord, 'assessment_id'>>({
  patient_id: '',
  assessment_year: new Date().getFullYear().toString(),
  disease_code: '',
  risk_level: 'LOW',
  control_status: 'GOOD',
  complications: [],
  treatment_plan: '',
  doctor_advice: ''
})

const rules = {
  patient_id: [{ required: true, message: '请输入患者ID', trigger: 'blur' }],
  assessment_year: [{ required: true, message: '请选择评估年份', trigger: 'change' }],
  disease_code: [{ required: true, message: '请选择慢病类型', trigger: 'change' }],
  risk_level: [{ required: true, message: '请选择风险等级', trigger: 'change' }],
  control_status: [{ required: true, message: '请选择控制状态', trigger: 'change' }]
}

watch(() => props.record, (val) => {
  if (val) {
    Object.assign(form, {
      patient_id: val.patient_id || '',
      assessment_year: val.assessment_year || new Date().getFullYear().toString(),
      disease_code: val.disease_code || '',
      risk_level: val.risk_level || 'LOW',
      control_status: val.control_status || 'GOOD',
      complications: val.complications || [],
      treatment_plan: val.treatment_plan || '',
      doctor_advice: val.doctor_advice || ''
    })
  } else {
    Object.assign(form, {
      patient_id: '',
      assessment_year: new Date().getFullYear().toString(),
      disease_code: '',
      risk_level: 'LOW',
      control_status: 'GOOD',
      complications: [],
      treatment_plan: '',
      doctor_advice: ''
    })
  }
}, { immediate: true })

async function handleSubmit() {
  try {
    await formRef.value.validate()
    loading.value = true

    if (isEdit.value) {
      await assessmentApi.update(props.record!.assessment_id!, form)
      ElMessage.success('修改成功')
    } else {
      await assessmentApi.create(form)
      ElMessage.success('创建成功')
    }

    emit('success')
    emit('update:modelValue', false)
  } catch (error: any) {
    if (error !== false) {
      // 错误已由 request.ts 拦截器统一提示
    }
  } finally {
    loading.value = false
  }
}
</script>