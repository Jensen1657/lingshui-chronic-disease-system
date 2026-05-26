<template>
  <div class="emergency-form">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>{{ isEdit ? '编辑急救记录' : '新建急救联动记录' }}</span>
          <el-button @click="$router.push('/emergency')">返回列表</el-button>
        </div>
      </template>

      <el-form ref="formRef" :model="form" :rules="rules" label-width="130px" style="max-width: 800px; margin: 0 auto;">
        <el-divider content-position="left">基本信息</el-divider>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="患者" prop="patient_id">
              <el-select v-model="form.patient_id" filterable remote reserve-keyword placeholder="搜索患者姓名/ID" :remote-method="searchPatients" :loading="patientLoading" style="width: 100%">
                <el-option v-for="p in patientOptions" :key="p.patient_id" :label="`${p.name} (${p.patient_id})`" :value="p.patient_id" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="急救类型" prop="emergency_type">
              <el-select v-model="form.emergency_type" style="width: 100%">
                <el-option label="心梗" value="心梗" />
                <el-option label="卒中" value="卒中" />
                <el-option label="外伤" value="外伤" />
                <el-option label="中毒" value="中毒" />
                <el-option label="休克" value="休克" />
                <el-option label="其他" value="其他" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="严重程度" prop="severity">
              <el-select v-model="form.severity" style="width: 100%">
                <el-option label="高" value="高" />
                <el-option label="中" value="中" />
                <el-option label="低" value="低" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="当前状态">
              <el-select v-model="form.status" style="width: 100%">
                <el-option label="活跃" value="ACTIVE" />
                <el-option label="处理中" value="HANDLING" />
                <el-option label="已完成" value="COMPLETED" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-divider content-position="left">急救信息</el-divider>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="事发地点" prop="location">
              <el-input v-model="form.location" placeholder="请输入事发地点" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="联系电话" prop="contact_phone">
              <el-input v-model="form.contact_phone" placeholder="请输入联系电话" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="处理人" prop="handler_name">
              <el-input v-model="form.handler_name" placeholder="请输入处理人姓名" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="处理时间" prop="handle_time">
              <el-date-picker v-model="form.handle_time" type="datetime" value-format="YYYY-MM-DD HH:mm:ss" style="width: 100%" placeholder="选择时间" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="备注">
          <el-input v-model="form.notes" type="textarea" :rows="4" placeholder="其他备注信息" />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleSubmit" :loading="submitting">
            {{ isEdit ? '保存修改' : '创建急救记录' }}
          </el-button>
          <el-button @click="$router.push('/emergency')">取消</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { emergencyApi } from '@/api/emergency'
import { patientApi } from '@/api/patient'
import type { FormInstance, FormRules } from 'element-plus'

const route = useRoute()
const router = useRouter()
const formRef = ref<FormInstance>()
const submitting = ref(false)
const patientLoading = ref(false)
const patientOptions = ref<any[]>([])

const isEdit = computed(() => !!route.params.id)

const form = reactive({
  patient_id: '',
  emergency_type: '',
  severity: '高',
  location: '',
  contact_phone: '',
  handler_name: '',
  handle_time: '',
  status: 'ACTIVE',
  notes: '',
})

const rules: FormRules = {
  patient_id: [{ required: true, message: '请选择患者', trigger: 'change' }],
  emergency_type: [{ required: true, message: '请选择急救类型', trigger: 'change' }],
  severity: [{ required: true, message: '请选择严重程度', trigger: 'change' }],
  location: [{ required: true, message: '请输入事发地点', trigger: 'blur' }],
  contact_phone: [{ required: true, message: '请输入联系电话', trigger: 'blur' }],
  handler_name: [{ required: true, message: '请输入处理人姓名', trigger: 'blur' }],
  handle_time: [{ required: true, message: '请选择处理时间', trigger: 'change' }],
}

const searchPatients = async (query: string) => {
  if (!query || query.length < 1) return
  patientLoading.value = true
  try {
    const res = await patientApi.getList({ page: 1, page_size: 10, keyword: query })
    patientOptions.value = (res.items || []).map((p: any) => ({ patient_id: p.patient_id, name: p.name }))
  } catch {
    patientOptions.value = []
  } finally {
    patientLoading.value = false
  }
}

onMounted(async () => {
  if (isEdit.value && route.params.id) {
    try {
      const data = await emergencyApi.getById(route.params.id as string)
      Object.assign(form, {
        patient_id: data.patient_id || '',
        emergency_type: data.emergency_type || '',
        severity: data.severity || '高',
        location: data.location || '',
        contact_phone: data.contact_phone || '',
        handler_name: data.handler_name || '',
        handle_time: data.handle_time || '',
        status: data.status || 'ACTIVE',
        notes: data.notes || '',
      })
      if (data.patient_id) {
        try {
          const p = await patientApi.getById(data.patient_id)
          patientOptions.value = [{ patient_id: p.patient_id, name: p.name }]
        } catch {}
      }
    } catch {
      ElMessage.error('加载数据失败')
    }
  }
})

const handleSubmit = async () => {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  submitting.value = true
  try {
    if (isEdit.value) {
      await emergencyApi.update(route.params.id as string, form)
      ElMessage.success('修改成功')
    } else {
      await emergencyApi.create(form)
      ElMessage.success('创建成功')
    }
    router.push('/emergency')
  } catch (e: any) {
    const msg = e?.response?.data?.detail || e?.message || '操作失败'
    // 错误已由 request.ts 拦截器统一提示
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.emergency-form { padding: 20px; }
.card-header { display: flex; justify-content: space-between; align-items: center; }
</style>