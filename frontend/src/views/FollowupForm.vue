<template>
  <div class="followup-form">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>{{ isEdit ? '编辑随访' : '新建随访记录' }}</span>
          <el-button @click="$router.push('/followups')">返回列表</el-button>
        </div>
      </template>

      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="130px"
        style="max-width: 800px; margin: 0 auto;"
      >
        <el-divider content-position="left">基本信息</el-divider>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="患者" prop="patient_id">
              <el-select
                v-model="form.patient_id"
                filterable
                remote
                reserve-keyword
                placeholder="搜索患者姓名/ID"
                :remote-method="searchPatients"
                :loading="patientLoading"
                style="width: 100%"
              >
                <el-option
                  v-for="p in patientOptions"
                  :key="p.patient_id"
                  :label="`${p.name} (${p.patient_id})`"
                  :value="p.patient_id"
                />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="随访日期" prop="followup_date">
              <el-date-picker v-model="form.followup_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="随访方式" prop="followup_type">
              <el-select v-model="form.followup_type" style="width: 100%">
                <el-option label="门诊" value="门诊" />
                <el-option label="电话" value="电话" />
                <el-option label="家庭访视" value="家庭访视" />
                <el-option label="视频" value="视频" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="随访医生">
              <el-input v-model="form.doctor_name" placeholder="医生姓名" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-divider content-position="left">体征数据</el-divider>

        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="收缩压(mmHg)">
              <el-input-number v-model="form.bp_systolic" :min="60" :max="260" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="舒张压(mmHg)">
              <el-input-number v-model="form.bp_diastolic" :min="30" :max="160" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="心率(次/分)">
              <el-input-number v-model="form.heart_rate" :min="30" :max="200" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="空腹血糖(mmol/L)">
              <el-input-number v-model="form.fbg" :min="1" :max="30" :precision="1" step="0.1" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="餐后血糖(mmol/L)">
              <el-input-number v-model="form.pbg" :min="1" :max="40" :precision="1" step="0.1" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="身高(cm)">
              <el-input-number v-model="form.height" :min="50" :max="220" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="体重(kg)">
              <el-input-number v-model="form.weight" :min="10" :max="200" :precision="1" step="0.1" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-divider content-position="left">用药与评估</el-divider>

        <el-form-item label="用药依从性">
          <el-radio-group v-model="form.medication_adherence">
            <el-radio label="良好" />
            <el-radio label="一般" />
            <el-radio label="差" />
          </el-radio-group>
        </el-form-item>

        <el-form-item label="当前用药">
          <el-input v-model="form.medications" type="textarea" :rows="2" placeholder="当前服用药物，如：氨氯地平5mg qd" />
        </el-form-item>

        <el-form-item label="症状描述">
          <el-input v-model="form.symptoms" type="textarea" :rows="2" placeholder="主要症状描述" />
        </el-form-item>

        <el-form-item label="健康指导">
          <el-input v-model="form.health_guidance" type="textarea" :rows="3" placeholder="本次健康指导意见" />
        </el-form-item>

        <el-form-item label="下次随访计划">
          <el-date-picker v-model="form.next_followup_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
        </el-form-item>

        <el-form-item label="备注">
          <el-input v-model="form.notes" type="textarea" :rows="2" placeholder="其他备注" />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleSubmit" :loading="submitting">
            {{ isEdit ? '保存修改' : '创建随访' }}
          </el-button>
          <el-button @click="$router.push('/followups')">取消</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { followupApi } from '@/api/followup'
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
  followup_date: new Date().toISOString().slice(0, 10),
  followup_type: '门诊',
  doctor_name: '',
  bp_systolic: undefined as number | undefined,
  bp_diastolic: undefined as number | undefined,
  heart_rate: undefined as number | undefined,
  fbg: undefined as number | undefined,
  pbg: undefined as number | undefined,
  height: undefined as number | undefined,
  weight: undefined as number | undefined,
  medication_adherence: '良好',
  medications: '',
  symptoms: '',
  health_guidance: '',
  next_followup_date: '',
  notes: '',
})

const rules: FormRules = {
  patient_id: [{ required: true, message: '请选择患者', trigger: 'change' }],
  followup_date: [{ required: true, message: '请选择随访日期', trigger: 'change' }],
  followup_type: [{ required: true, message: '请选择随访方式', trigger: 'change' }],
}

// 搜索患者
const searchPatients = async (query: string) => {
  if (!query || query.length < 1) return
  patientLoading.value = true
  try {
    const res = await patientApi.getList({ page: 1, page_size: 10, keyword: query })
    patientOptions.value = (res.items || []).map((p: any) => ({
      patient_id: p.patient_id,
      name: p.name,
    }))
  } catch {
    patientOptions.value = []
  } finally {
    patientLoading.value = false
  }
}

// 编辑模式加载
onMounted(async () => {
  if (isEdit.value && route.params.id) {
    try {
      const data = await followupApi.getById(route.params.id as string)
      Object.assign(form, {
        patient_id: data.patient_id || '',
        followup_date: data.followup_date || '',
        followup_type: data.followup_type || '门诊',
        doctor_name: data.doctor_name || '',
        bp_systolic: data.bp_systolic,
        bp_diastolic: data.bp_diastolic,
        heart_rate: data.heart_rate,
        fbg: data.fbg,
        pbg: data.pbg,
        height: data.height,
        weight: data.weight,
        medication_adherence: data.medication_adherence || '良好',
        medications: data.medications || '',
        symptoms: data.symptoms || '',
        health_guidance: data.health_guidance || '',
        next_followup_date: data.next_followup_date || '',
        notes: data.notes || '',
      })
      // 加载患者名称到选项
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
    // 清理空值
    const payload: Record<string, any> = {}
    for (const [k, v] of Object.entries(form)) {
      if (v !== '' && v !== null && v !== undefined) {
        payload[k] = v
      }
    }

    if (isEdit.value) {
      await followupApi.update(route.params.id as string, payload)
      ElMessage.success('修改成功')
    } else {
      await followupApi.create(payload)
      ElMessage.success('创建成功')
    }
    router.push('/followups')
  } catch (e: any) {
    const msg = e?.response?.data?.detail || e?.message || '操作失败'
    ElMessage.error(msg)
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.followup-form {
  padding: 20px;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
