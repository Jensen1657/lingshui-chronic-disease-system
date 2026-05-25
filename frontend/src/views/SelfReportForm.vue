<template>
  <div class="self-report-form">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>{{ isEdit ? '编辑自报' : '新建患者自报' }}</span>
          <el-button @click="$router.push('/self-reports')">返回列表</el-button>
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
            <el-form-item label="上报类型" prop="report_type">
              <el-select v-model="form.report_type" style="width: 100%">
                <el-option label="血压" value="血压" />
                <el-option label="血糖" value="血糖" />
                <el-option label="症状" value="症状" />
                <el-option label="用药" value="用药" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="上报数值" prop="report_value">
              <el-input v-model="form.report_value" placeholder="请输入上报数值或内容" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="上报日期" prop="report_date">
              <el-date-picker v-model="form.report_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" placeholder="选择日期" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-divider content-position="left">补充信息</el-divider>

        <el-form-item label="备注">
          <el-input v-model="form.notes" type="textarea" :rows="4" placeholder="其他补充说明" />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleSubmit" :loading="submitting">
            {{ isEdit ? '保存修改' : '创建自报' }}
          </el-button>
          <el-button @click="$router.push('/self-reports')">取消</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { selfReportApi } from '@/api/self-report'
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
  report_type: '血压',
  report_value: '',
  report_date: new Date().toISOString().slice(0, 10),
  notes: '',
})

const rules: FormRules = {
  patient_id: [{ required: true, message: '请选择患者', trigger: 'change' }],
  report_type: [{ required: true, message: '请选择上报类型', trigger: 'change' }],
  report_value: [{ required: true, message: '请输入上报数值', trigger: 'blur' }],
  report_date: [{ required: true, message: '请选择上报日期', trigger: 'change' }],
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
      const data = await selfReportApi.getById(route.params.id as string)
      Object.assign(form, {
        patient_id: data.patient_id || '',
        report_type: data.report_type || '血压',
        report_value: data.report_value || '',
        report_date: data.report_date || '',
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
      await selfReportApi.update(route.params.id as string, form)
      ElMessage.success('修改成功')
    } else {
      await selfReportApi.create(form)
      ElMessage.success('创建成功')
    }
    router.push('/self-reports')
  } catch (e: any) {
    const msg = e?.response?.data?.detail || e?.message || '操作失败'
    ElMessage.error(msg)
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.self-report-form { padding: 20px; }
.card-header { display: flex; justify-content: space-between; align-items: center; }
</style>