<template>
  <el-dialog :model-value="modelValue" @update:model-value="$emit('update:modelValue', $event)" :title="isEdit ? '编辑转诊' : '新增转诊'" width="600px">
    <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="患者ID" prop="patient_id">
            <el-input v-model="form.patient_id" placeholder="请输入患者ID" :disabled="isEdit" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="转诊类型" prop="referral_type">
            <el-select v-model="form.referral_type" placeholder="请选择转诊类型" style="width: 100%">
              <el-option label="上转" value="UP" />
              <el-option label="下转" value="DOWN" />
            </el-select>
          </el-form-item>
        </el-col>
      </el-row>

      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="转出机构" prop="from_org_code">
            <el-input v-model="form.from_org_code" placeholder="请输入转出机构编码" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="转入机构" prop="to_org_code">
            <el-input v-model="form.to_org_code" placeholder="请输入转入机构编码" />
          </el-form-item>
        </el-col>
      </el-row>

      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="转诊日期" prop="referral_date">
            <el-date-picker v-model="form.referral_date" type="date" placeholder="选择日期" style="width: 100%" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="状态">
            <el-select v-model="form.status" placeholder="请选择状态" style="width: 100%">
              <el-option label="待处理" value="PENDING" />
              <el-option label="已完成" value="COMPLETED" />
              <el-option label="已取消" value="CANCELLED" />
            </el-select>
          </el-form-item>
        </el-col>
      </el-row>

      <el-form-item label="诊断" prop="diagnosis">
        <el-input v-model="form.diagnosis" type="textarea" :rows="2" placeholder="请输入诊断" />
      </el-form-item>

      <el-form-item label="转诊原因" prop="reason">
        <el-input v-model="form.reason" type="textarea" :rows="3" placeholder="请输入转诊原因" />
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
import { referralApi } from '@/api/referral'

interface ReferralRecord {
  referral_id?: string
  patient_id: string
  referral_type: string
  from_org_code: string
  to_org_code: string
  referral_date: string
  diagnosis?: string
  reason?: string
  status?: string
}

const props = defineProps<{
  modelValue: boolean
  record: ReferralRecord | null
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'success': []
}>()

const formRef = ref()
const loading = ref(false)

const isEdit = computed(() => !!props.record?.referral_id)

const form = reactive<Omit<ReferralRecord, 'referral_id'>>({
  patient_id: '',
  referral_type: '',
  from_org_code: '',
  to_org_code: '',
  referral_date: '',
  diagnosis: '',
  reason: '',
  status: 'PENDING'
})

const rules = {
  patient_id: [{ required: true, message: '请输入患者ID', trigger: 'blur' }],
  referral_type: [{ required: true, message: '请选择转诊类型', trigger: 'change' }],
  from_org_code: [{ required: true, message: '请输入转出机构编码', trigger: 'blur' }],
  to_org_code: [{ required: true, message: '请输入转入机构编码', trigger: 'blur' }],
  referral_date: [{ required: true, message: '请选择转诊日期', trigger: 'change' }],
  reason: [{ required: true, message: '请输入转诊原因', trigger: 'blur' }]
}

watch(() => props.record, (val) => {
  if (val) {
    Object.assign(form, {
      patient_id: val.patient_id || '',
      referral_type: val.referral_type || '',
      from_org_code: val.from_org_code || '',
      to_org_code: val.to_org_code || '',
      referral_date: val.referral_date || '',
      diagnosis: val.diagnosis || '',
      reason: val.reason || '',
      status: val.status || 'PENDING'
    })
  } else {
    Object.assign(form, {
      patient_id: '',
      referral_type: '',
      from_org_code: '',
      to_org_code: '',
      referral_date: '',
      diagnosis: '',
      reason: '',
      status: 'PENDING'
    })
  }
}, { immediate: true })

async function handleSubmit() {
  try {
    await formRef.value.validate()
    loading.value = true

    if (isEdit.value) {
      await referralApi.update(props.record!.referral_id!, form)
      ElMessage.success('修改成功')
    } else {
      await referralApi.create(form)
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