<template>
  <div class="assessment-form">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>{{ isEdit ? '编辑评估' : '新建年度评估' }}</span>
          <el-button @click="$router.push('/assessments')">返回列表</el-button>
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
            <el-form-item label="评估年份" prop="assessment_year">
              <el-date-picker v-model="form.assessment_year" type="year" value-format="YYYY" style="width: 100%" placeholder="选择年份" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="评估类型" prop="assessment_type">
              <el-select v-model="form.assessment_type" style="width: 100%">
                <el-option label="常规" value="常规" />
                <el-option label="专项" value="专项" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="风险等级" prop="risk_level">
              <el-select v-model="form.risk_level" style="width: 100%">
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
              <el-select v-model="form.control_status" style="width: 100%">
                <el-option label="达标" value="达标" />
                <el-option label="未达标" value="未达标" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="综合评分" prop="score">
              <el-input-number v-model="form.score" :min="0" :max="100" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-divider content-position="left">评估结论</el-divider>

        <el-form-item label="评估结论" prop="conclusion">
          <el-input v-model="form.conclusion" type="textarea" :rows="4" placeholder="请输入评估结论及建议" />
        </el-form-item>

        <el-form-item label="备注">
          <el-input v-model="form.notes" type="textarea" :rows="3" placeholder="其他备注信息" />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleSubmit" :loading="submitting">
            {{ isEdit ? '保存修改' : '创建评估' }}
          </el-button>
          <el-button @click="$router.push('/assessments')">取消</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { assessmentApi } from '@/api/assessment'
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
  assessment_year: new Date().getFullYear().toString(),
  assessment_type: '常规',
  risk_level: 'MEDIUM',
  control_status: '未达标',
  score: undefined as number | undefined,
  conclusion: '',
  notes: '',
})

const rules: FormRules = {
  patient_id: [{ required: true, message: '请选择患者', trigger: 'change' }],
  assessment_year: [{ required: true, message: '请选择评估年份', trigger: 'change' }],
  assessment_type: [{ required: true, message: '请选择评估类型', trigger: 'change' }],
  risk_level: [{ required: true, message: '请选择风险等级', trigger: 'change' }],
  control_status: [{ required: true, message: '请选择控制状态', trigger: 'change' }],
  conclusion: [{ required: true, message: '请输入评估结论', trigger: 'blur' }],
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
      const data = await assessmentApi.getById(route.params.id as string)
      Object.assign(form, {
        patient_id: data.patient_id || '',
        assessment_year: data.assessment_year || '',
        assessment_type: data.assessment_type || '常规',
        risk_level: data.risk_level || 'MEDIUM',
        control_status: data.control_status || '未达标',
        score: data.score,
        conclusion: data.conclusion || '',
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
    const payload: Record<string, any> = {}
    for (const [k, v] of Object.entries(form)) {
      if (v !== '' && v !== null && v !== undefined) payload[k] = v
    }
    if (isEdit.value) {
      await assessmentApi.update(route.params.id as string, payload)
      ElMessage.success('修改成功')
    } else {
      await assessmentApi.create(payload)
      ElMessage.success('创建成功')
    }
    router.push('/assessments')
  } catch (e: any) {
    const msg = e?.response?.data?.detail || e?.message || '操作失败'
    // 错误已由 request.ts 拦截器统一提示
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.assessment-form { padding: 20px; }
.card-header { display: flex; justify-content: space-between; align-items: center; }
</style>