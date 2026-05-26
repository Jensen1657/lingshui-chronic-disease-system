<template>
  <el-dialog :model-value="modelValue" @update:model-value="$emit('update:modelValue', $event)" :title="isEdit ? '编辑随访' : '新增随访'" width="650px">
    <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="患者ID" prop="patient_id">
            <el-input v-model="form.patient_id" placeholder="请输入患者ID" :disabled="isEdit" />
          </el-form-item>
        </el-col>
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
      </el-row>

      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="随访日期" prop="followup_date">
            <el-date-picker v-model="form.followup_date" type="date" placeholder="选择日期" style="width: 100%" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="随访医生" prop="performed_by">
            <el-input v-model="form.performed_by" placeholder="请输入随访医生" />
          </el-form-item>
        </el-col>
      </el-row>

      <el-row :gutter="20">
        <el-col :span="8">
          <el-form-item label="收缩压" prop="bp_systolic">
            <el-input v-model.number="form.bp_systolic" placeholder="mmHg">
              <template #append>mmHg</template>
            </el-input>
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="舒张压" prop="bp_diastolic">
            <el-input v-model.number="form.bp_diastolic" placeholder="mmHg">
              <template #append>mmHg</template>
            </el-input>
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="空腹血糖" prop="fbg">
            <el-input v-model.number="form.fbg" placeholder="mmol/L">
              <template #append>mmol/L</template>
            </el-input>
          </el-form-item>
        </el-col>
      </el-row>

      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="体重" prop="weight">
            <el-input v-model.number="form.weight" placeholder="kg">
              <template #append>kg</template>
            </el-input>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="是否控制">
            <el-radio-group v-model="form.is_controlled">
              <el-radio :value="true">已控制</el-radio>
              <el-radio :value="false">未控制</el-radio>
            </el-radio-group>
          </el-form-item>
        </el-col>
      </el-row>

      <el-form-item label="医嘱建议">
        <el-input v-model="form.doctor_advice" type="textarea" :rows="3" placeholder="请输入医嘱建议" />
      </el-form-item>

      <el-form-item label="下次随访日期">
        <el-date-picker v-model="form.next_followup_date" type="date" placeholder="选择日期" style="width: 100%" />
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
import { followupApi } from '@/api/followup'

interface FollowupRecord {
  followup_id?: string
  patient_id: string
  disease_code: string
  followup_date: string
  bp_systolic?: number
  bp_diastolic?: number
  fbg?: number
  weight?: number
  is_controlled: boolean
  doctor_advice?: string
  performed_by?: string
  next_followup_date?: string
}

const props = defineProps<{
  modelValue: boolean
  record: FollowupRecord | null
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'success': []
}>()

const formRef = ref()
const loading = ref(false)

const isEdit = computed(() => !!props.record?.followup_id)

const form = reactive<Omit<FollowupRecord, 'followup_id'>>({
  patient_id: '',
  disease_code: '',
  followup_date: '',
  bp_systolic: undefined,
  bp_diastolic: undefined,
  fbg: undefined,
  weight: undefined,
  is_controlled: true,
  doctor_advice: '',
  performed_by: '',
  next_followup_date: ''
})

const rules = {
  patient_id: [{ required: true, message: '请输入患者ID', trigger: 'blur' }],
  disease_code: [{ required: true, message: '请选择慢病类型', trigger: 'change' }],
  followup_date: [{ required: true, message: '请选择随访日期', trigger: 'change' }],
  performed_by: [{ required: true, message: '请输入随访医生', trigger: 'blur' }]
}

watch(() => props.record, (val) => {
  if (val) {
    Object.assign(form, {
      patient_id: val.patient_id || '',
      disease_code: val.disease_code || '',
      followup_date: val.followup_date || '',
      bp_systolic: val.bp_systolic ?? undefined,
      bp_diastolic: val.bp_diastolic ?? undefined,
      fbg: val.fbg ?? undefined,
      weight: val.weight ?? undefined,
      is_controlled: val.is_controlled ?? true,
      doctor_advice: val.doctor_advice || '',
      performed_by: val.performed_by || '',
      next_followup_date: val.next_followup_date || ''
    })
  } else {
    Object.assign(form, {
      patient_id: '',
      disease_code: '',
      followup_date: '',
      bp_systolic: undefined,
      bp_diastolic: undefined,
      fbg: undefined,
      weight: undefined,
      is_controlled: true,
      doctor_advice: '',
      performed_by: '',
      next_followup_date: ''
    })
  }
}, { immediate: true })

async function handleSubmit() {
  try {
    await formRef.value.validate()
    loading.value = true

    if (isEdit.value) {
      await followupApi.update(props.record!.followup_id!, form)
      ElMessage.success('修改成功')
    } else {
      await followupApi.create(form)
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