<template>
  <el-dialog
    :model-value="props.visible"
    @update:model-value="emit('update:visible', $event)"
    :title="isEdit ? '编辑微信绑定' : '绑定微信'"
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
          <el-form-item label="微信OpenID" prop="wechat_openid">
            <el-input v-model="form.wechat_openid" placeholder="请输入微信OpenID" />
          </el-form-item>
        </el-col>
      </el-row>

      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="微信UnionID" prop="wechat_unionid">
            <el-input v-model="form.wechat_unionid" placeholder="请输入微信UnionID" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="微信昵称" prop="wechat_nickname">
            <el-input v-model="form.wechat_nickname" placeholder="请输入微信昵称" />
          </el-form-item>
        </el-col>
      </el-row>

      <el-form-item label="微信头像" prop="wechat_avatar">
        <el-input v-model="form.wechat_avatar" placeholder="请输入微信头像URL" />
      </el-form-item>

      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="激活状态" prop="is_active">
            <el-switch v-model="form.is_active" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="通知启用" prop="notification_enabled">
            <el-switch v-model="form.notification_enabled" />
          </el-form-item>
        </el-col>
      </el-row>
    </el-form>

    <template #footer>
      <el-button @click="handleClose">取消</el-button>
      <el-button type="primary" @click="handleSubmit" :loading="loading">
        {{ isEdit ? '更新' : '绑定' }}
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue'
import { useWechatStore } from '@/stores/wechat'
import { usePatientStore } from '@/stores/patient'
import type { WechatBinding, WechatBindingCreate, WechatBindingUpdate } from '@/types/wechat'
import type { Patient } from '@/types/patient'
import type { FormInstance, FormRules } from 'element-plus'

const props = defineProps<{
  visible: boolean
  binding?: WechatBinding | null
}>()

const emit = defineEmits<{
  'update:visible': [value: boolean]
  success: []
}>()

const wechatStore = useWechatStore()
const patientStore = usePatientStore()

const formRef = ref<FormInstance>()
const loading = ref(false)
const patientLoading = ref(false)
const patientOptions = ref<Patient[]>([])

const isEdit = computed(() => !!props.binding)

const form = reactive<WechatBindingCreate | WechatBindingUpdate>({
  patient_id: '',
  wechat_openid: '',
  wechat_unionid: '',
  wechat_nickname: '',
  wechat_avatar: '',
  is_active: true,
  notification_enabled: true
})

const rules = reactive<FormRules>({
  patient_id: [{ required: true, message: '请选择患者', trigger: 'change' }],
  wechat_openid: [{ required: true, message: '请输入微信OpenID', trigger: 'blur' }]
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

watch(() => props.binding, (val) => {
  if (val) {
    Object.assign(form, {
      patient_id: val.patient_id,
      wechat_openid: val.wechat_openid || '',
      wechat_unionid: val.wechat_unionid || '',
      wechat_nickname: val.wechat_nickname || '',
      wechat_avatar: val.wechat_avatar || '',
      is_active: val.is_active,
      notification_enabled: val.notification_enabled
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

const resetForm = () => {
  Object.assign(form, {
    patient_id: '',
    wechat_openid: '',
    wechat_unionid: '',
    wechat_nickname: '',
    wechat_avatar: '',
    is_active: true,
    notification_enabled: true
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

    if (isEdit.value && props.binding) {
      await wechatStore.updateBinding(props.binding.id, form as WechatBindingUpdate)
      ElMessage.success('更新成功')
    } else {
      await wechatStore.bindWechat(form as WechatBindingCreate)
      ElMessage.success('绑定成功')
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
