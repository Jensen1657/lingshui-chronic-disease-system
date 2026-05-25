<template>
  <el-dialog :model-value="modelValue" @update:model-value="$emit('update:modelValue', $event)" :title="isEdit ? '编辑患者' : '新增患者'" width="600px">
    <el-form :model="form" :rules="rules" ref="formRef" label-width="120px">
      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="姓名" prop="name">
            <el-input v-model="form.name" placeholder="请输入姓名" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="性别" prop="gender">
            <el-radio-group v-model="form.gender">
              <el-radio value="M">男</el-radio>
              <el-radio value="F">女</el-radio>
              <el-radio value="O">其他</el-radio>
            </el-radio-group>
          </el-form-item>
        </el-col>
      </el-row>

      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="出生日期" prop="birth_date">
            <el-date-picker v-model="form.birth_date" type="date" placeholder="选择日期" style="width: 100%" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="联系电话" prop="phone">
            <el-input v-model="form.phone" placeholder="请输入电话" />
          </el-form-item>
        </el-col>
      </el-row>

      <el-row :gutter="20">
        <el-col :span="24">
          <el-form-item label="身份证号" prop="id_card">
            <el-input v-model="form.id_card" placeholder="请输入身份证号" />
          </el-form-item>
        </el-col>
      </el-row>

      <el-form-item label="地址">
        <el-input v-model="form.address" type="textarea" :rows="2" placeholder="请输入地址" />
      </el-form-item>

      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="村编码">
            <el-input v-model="form.village_code" placeholder="如：460123103" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="管理机构编码">
            <el-input v-model="form.manage_org_code" placeholder="如：46012301" />
          </el-form-item>
        </el-col>
      </el-row>

      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="慢病类型" prop="disease_list">
            <el-select v-model="form.disease_list" multiple placeholder="请选择慢病类型" style="width: 100%">
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
          <el-form-item label="风险等级">
            <el-select v-model="form.risk_level" placeholder="请选择风险等级" style="width: 100%">
              <el-option label="低风险" value="LOW" />
              <el-option label="中风险" value="MEDIUM" />
              <el-option label="高风险" value="HIGH" />
              <el-option label="极高风险" value="VERY_HIGH" />
            </el-select>
          </el-form-item>
        </el-col>
      </el-row>
    </el-form>

    <template #footer>
      <el-button @click="$emit('update:modelValue', false)">取消</el-button>
      <el-button type="primary" :loading="loading" @click="handleSubmit">确定</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { reactive, ref, watch, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { patientApi } from '@/api/patient'
import type { Patient } from '@/types/patient'

const props = defineProps<{
  modelValue: boolean
  patient: Patient | null
}>()

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'success': []
}>()

const formRef = ref()
const loading = ref(false)

const isEdit = computed(() => !!props.patient?.patient_id)

const form = reactive({
  name: '',
  gender: 'M',
  birth_date: '',
  phone: '',
  id_card: '',
  address: '',
  village_code: '460123103',
  manage_org_code: '46012301',
  disease_list: [] as string[],
  risk_level: 'LOW'
})

const rules = {
  name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  gender: [{ required: true, message: '请选择性别', trigger: 'change' }],
  birth_date: [{ required: true, message: '请选择出生日期', trigger: 'change' }],
  phone: [{ required: true, message: '请输入联系电话', trigger: 'blur' }],
  id_card: [{ required: true, message: '请输入身份证号', trigger: 'blur' }],
  disease_list: [{ required: true, message: '请选择慢病类型', trigger: 'change', type: 'array' }]
}

// 监听 patient 变化，填充表单
watch(() => props.patient, (val) => {
  if (val) {
    Object.assign(form, {
      name: val.name_enc || '',
      gender: val.gender || 'M',
      birth_date: val.birth_date || '',
      phone: '',
      id_card: '',
      address: val.address || '',
      village_code: val.village_code || '460123103',
      manage_org_code: val.manage_org_code || '46012301',
      disease_list: val.disease_list || [],
      risk_level: val.risk_level || 'LOW'
    })
  } else {
    // 重置表单
    Object.assign(form, {
      name: '',
      gender: 'M',
      birth_date: '',
      phone: '',
      id_card: '',
      address: '',
      village_code: '460123103',
      manage_org_code: '46012301',
      disease_list: [],
      risk_level: 'LOW'
    })
  }
}, { immediate: true })

async function handleSubmit() {
  try {
    await formRef.value.validate()
    
    loading.value = true
    
    const submitData = { ...form }
    
    if (isEdit.value) {
      await patientApi.update(props.patient!.patient_id, submitData)
      ElMessage.success('修改成功')
    } else {
      await patientApi.create(submitData)
      ElMessage.success('创建成功')
    }
    
    emit('success')
    emit('update:modelValue', false)
  } catch (error: any) {
    if (error !== false) {
      ElMessage.error(isEdit.value ? '修改失败' : '创建失败')
    }
  } finally {
    loading.value = false
  }
}
</script>
