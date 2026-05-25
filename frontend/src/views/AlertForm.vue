<template>
  <div class="alert-form">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>{{ isEdit ? '编辑预警' : '新建预警记录' }}</span>
          <el-button @click="$router.push('/alerts')">返回列表</el-button>
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
            <el-form-item label="预警类型" prop="alert_type">
              <el-select v-model="form.alert_type" style="width: 100%">
                <el-option label="血压异常" value="血压异常" />
                <el-option label="血糖异常" value="血糖异常" />
                <el-option label="漏服药" value="漏服药" />
                <el-option label="未随访" value="未随访" />
                <el-option label="指标超标" value="指标超标" />
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
                <el-option label="已处理" value="RESOLVED" />
                <el-option label="已忽略" value="DISMISSED" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-divider content-position="left">预警详情</el-divider>

        <el-form-item label="预警信息" prop="alert_message">
          <el-input v-model="form.alert_message" type="textarea" :rows="4" placeholder="请输入预警详情内容" />
        </el-form-item>

        <el-form-item label="备注">
          <el-input v-model="form.notes" type="textarea" :rows="3" placeholder="其他备注信息" />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleSubmit" :loading="submitting">
            {{ isEdit ? '保存修改' : '创建预警' }}
          </el-button>
          <el-button @click="$router.push('/alerts')">取消</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { alertApi } from '@/api/alert'
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
  alert_type: '',
  severity: '中',
  alert_message: '',
  status: 'ACTIVE',
  notes: '',
})

const rules: FormRules = {
  patient_id: [{ required: true, message: '请选择患者', trigger: 'change' }],
  alert_type: [{ required: true, message: '请选择预警类型', trigger: 'change' }],
  severity: [{ required: true, message: '请选择严重程度', trigger: 'change' }],
  alert_message: [{ required: true, message: '请输入预警信息', trigger: 'blur' }],
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
      const data = await alertApi.getById(route.params.id as string)
      Object.assign(form, {
        patient_id: data.patient_id || '',
        alert_type: data.alert_type || '',
        severity: data.severity || '中',
        alert_message: data.alert_message || '',
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
      await alertApi.update(route.params.id as string, form)
      ElMessage.success('修改成功')
    } else {
      await alertApi.create(form)
      ElMessage.success('创建成功')
    }
    router.push('/alerts')
  } catch (e: any) {
    const msg = e?.response?.data?.detail || e?.message || '操作失败'
    ElMessage.error(msg)
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.alert-form { padding: 20px; }
.card-header { display: flex; justify-content: space-between; align-items: center; }
</style>