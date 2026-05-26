<template>
  <el-dialog 
    :model-value="visible" 
    @update:model-value="$emit('update:visible', $event)" 
    :title="isEdit ? '编辑预警' : '新建预警'" 
    width="700px"
  >
    <el-form :model="form" :rules="rules" ref="formRef" label-width="120px">
      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="患者" prop="patient_id">
            <el-select 
              v-model="form.patient_id" 
              filterable 
              placeholder="请选择患者"
              style="width: 100%"
              :disabled="isEdit"
            >
              <el-option 
                v-for="patient in patients" 
                :key="patient.patient_id" 
                :label="`${patient.name} (${patient.patient_id})`" 
                :value="patient.patient_id" 
              />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="预警类型" prop="alert_type">
            <el-select v-model="form.alert_type" placeholder="请选择预警类型" style="width: 100%">
              <el-option label="血压异常" value="BP_ABNORMAL" />
              <el-option label="血糖异常" value="GLUCOSE_ABNORMAL" />
              <el-option label="心率异常" value="HR_ABNORMAL" />
              <el-option label="体重异常" value="WEIGHT_ABNORMAL" />
              <el-option label="用药提醒" value="MEDICATION_REMINDER" />
              <el-option label="随访提醒" value="FOLLOWUP_REMINDER" />
              <el-option label="转诊提醒" value="REFERRAL_REMINDER" />
              <el-option label="其他" value="OTHER" />
            </el-select>
          </el-form-item>
        </el-col>
      </el-row>

      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="预警级别" prop="alert_level">
            <el-select v-model="form.alert_level" placeholder="请选择预警级别" style="width: 100%">
              <el-option label="🔴 紧急" value="URGENT" />
              <el-option label="🟠 重要" value="IMPORTANT" />
              <el-option label="🟡 一般" value="NORMAL" />
              <el-option label="🟢 提示" value="INFO" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="预警来源" prop="source">
            <el-select v-model="form.source" placeholder="请选择预警来源" style="width: 100%">
              <el-option label="系统自动" value="SYSTEM" />
              <el-option label="医生创建" value="DOCTOR" />
              <el-option label="患者自报" value="PATIENT" />
              <el-option label="设备监测" value="DEVICE" />
            </el-select>
          </el-form-item>
        </el-col>
      </el-row>

      <el-form-item label="预警标题" prop="title">
        <el-input v-model="form.title" placeholder="请输入预警标题" maxlength="100" show-word-limit />
      </el-form-item>

      <el-form-item label="预警内容" prop="content">
        <el-input 
          v-model="form.content" 
          type="textarea" 
          :rows="4" 
          placeholder="请输入预警详细内容"
          maxlength="500"
          show-word-limit
        />
      </el-form-item>

      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="触发指标">
            <el-input v-model="form.trigger_value" placeholder="如：血压 180/110 mmHg" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="阈值范围">
            <el-input v-model="form.threshold" placeholder="如：收缩压 ≥ 180" />
          </el-form-item>
        </el-col>
      </el-row>

      <el-form-item label="处理建议">
        <el-input 
          v-model="form.suggestion" 
          type="textarea" 
          :rows="3" 
          placeholder="请输入处理建议"
          maxlength="300"
        />
      </el-form-item>

      <el-form-item label="附件">
        <el-upload
          action="#"
          :auto-upload="false"
          :limit="3"
        >
          <el-button size="small" type="primary">点击上传</el-button>
          <template #tip>
            <div class="el-upload__tip">支持 jpg/png/pdf 文件，不超过 5MB</div>
          </template>
        </el-upload>
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="$emit('update:visible', false)">取消</el-button>
      <el-button type="primary" @click="handleSubmit" :loading="loading">
        {{ isEdit ? '保存' : '创建' }}
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { reactive, ref, computed, watch, onMounted } from 'vue'
import type { FormInstance, FormRules } from 'element-plus'
import { patientApi } from '@/api/patient'

const props = defineProps<{ 
  visible: boolean
  record: any 
}>()

const emit = defineEmits(['update:visible', 'success'])

const formRef = ref<FormInstance>()
const loading = ref(false)
const patients = ref<any[]>([])

const isEdit = computed(() => !!props.record?.alert_id)

const form = reactive({
  patient_id: '',
  alert_type: '',
  alert_level: '',
  source: 'SYSTEM',
  title: '',
  content: '',
  trigger_value: '',
  threshold: '',
  suggestion: ''
})

const rules: FormRules = {
  patient_id: [
    { required: true, message: '请选择患者', trigger: 'change' }
  ],
  alert_type: [
    { required: true, message: '请选择预警类型', trigger: 'change' }
  ],
  alert_level: [
    { required: true, message: '请选择预警级别', trigger: 'change' }
  ],
  title: [
    { required: true, message: '请输入预警标题', trigger: 'blur' },
    { min: 5, max: 100, message: '标题长度在 5 到 100 个字符', trigger: 'blur' }
  ],
  content: [
    { required: true, message: '请输入预警内容', trigger: 'blur' }
  ]
}

// 加载患者列表
async function loadPatients() {
  try {
    const res = await patientApi.getList({ page: 1, page_size: 1000 })
    patients.value = res.items || []
  } catch (error) {
    console.error('加载患者列表失败:', error)
  }
}

// 监听 record 变化，填充表单
watch(() => props.record, (val) => {
  if (val) {
    Object.assign(form, {
      patient_id: val.patient_id || '',
      alert_type: val.alert_type || '',
      alert_level: val.alert_level || '',
      source: val.source || 'SYSTEM',
      title: val.title || '',
      content: val.content || val.message || '',
      trigger_value: val.trigger_value || '',
      threshold: val.threshold || '',
      suggestion: val.suggestion || ''
    })
  } else {
    // 重置表单
    formRef.value?.resetFields()
  }
}, { immediate: true })

// 监听 visible 变化，加载患者列表
watch(() => props.visible, (val) => {
  if (val && patients.value.length === 0) {
    loadPatients()
  }
})

async function handleSubmit() {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    
    loading.value = true
    try {
      // 这里应该调用 API 创建/更新预警
      // await alertApi.create(form)
      ElMessage.success(isEdit.value ? '预警已更新' : '预警已创建')
      emit('success')
      emit('update:visible', false)
    } catch (error) {
      // 错误已由 request.ts 拦截器统一提示
    } finally {
      loading.value = false
    }
  })
}

onMounted(() => {
  loadPatients()
})
</script>

<style scoped>
.el-select {
  width: 100%;
}

.el-upload__tip {
  font-size: 12px;
  color: #909399;
  margin-top: 5px;
}
</style>
