<template>
  <div class="reminder-form">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>{{ isEdit ? '编辑提醒' : '新建随访提醒' }}</span>
          <el-button @click="$router.push('/reminders')">返回列表</el-button>
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
            <el-form-item label="提醒类型" prop="reminder_type">
              <el-select v-model="form.reminder_type" style="width: 100%">
                <el-option label="随访" value="随访" />
                <el-option label="复诊" value="复诊" />
                <el-option label="取药" value="取药" />
                <el-option label="检查" value="检查" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="提醒日期" prop="reminder_date">
              <el-date-picker v-model="form.reminder_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" placeholder="选择日期" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="通知渠道" prop="channel">
              <el-select v-model="form.channel" style="width: 100%">
                <el-option label="短信" value="短信" />
                <el-option label="微信" value="微信" />
                <el-option label="电话" value="电话" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="当前状态">
              <el-select v-model="form.status" style="width: 100%">
                <el-option label="待发送" value="PENDING" />
                <el-option label="已发送" value="SENT" />
                <el-option label="已完成" value="COMPLETED" />
                <el-option label="已取消" value="CANCELLED" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-divider content-position="left">提醒内容</el-divider>

        <el-form-item label="提醒内容" prop="content">
          <el-input v-model="form.content" type="textarea" :rows="4" placeholder="请输入提醒内容" />
        </el-form-item>

        <el-form-item label="备注">
          <el-input v-model="form.notes" type="textarea" :rows="3" placeholder="其他备注信息" />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleSubmit" :loading="submitting">
            {{ isEdit ? '保存修改' : '创建提醒' }}
          </el-button>
          <el-button @click="$router.push('/reminders')">取消</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { reminderApi } from '@/api/reminder'
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
  reminder_type: '随访',
  reminder_date: '',
  content: '',
  status: 'PENDING',
  channel: '短信',
  notes: '',
})

const rules: FormRules = {
  patient_id: [{ required: true, message: '请选择患者', trigger: 'change' }],
  reminder_type: [{ required: true, message: '请选择提醒类型', trigger: 'change' }],
  reminder_date: [{ required: true, message: '请选择提醒日期', trigger: 'change' }],
  channel: [{ required: true, message: '请选择通知渠道', trigger: 'change' }],
  content: [{ required: true, message: '请输入提醒内容', trigger: 'blur' }],
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
      const data = await reminderApi.getById(route.params.id as string)
      Object.assign(form, {
        patient_id: data.patient_id || '',
        reminder_type: data.reminder_type || '随访',
        reminder_date: data.reminder_date || '',
        content: data.content || '',
        status: data.status || 'PENDING',
        channel: data.channel || '短信',
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
      await reminderApi.update(route.params.id as string, form)
      ElMessage.success('修改成功')
    } else {
      await reminderApi.create(form)
      ElMessage.success('创建成功')
    }
    router.push('/reminders')
  } catch (e: any) {
    const msg = e?.response?.data?.detail || e?.message || '操作失败'
    // 错误已由 request.ts 拦截器统一提示
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.reminder-form { padding: 20px; }
.card-header { display: flex; justify-content: space-between; align-items: center; }
</style>