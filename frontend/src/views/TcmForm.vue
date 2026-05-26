<template>
  <div class="tcm-form">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>{{ isEdit ? '编辑中医档案' : '新建中医管理档案' }}</span>
          <el-button @click="$router.push('/tcm')">返回列表</el-button>
        </div>
      </template>

      <el-form ref="formRef" :model="form" :rules="rules" label-width="130px" style="max-width: 900px; margin: 0 auto;">
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
            <el-form-item label="体质类型" prop="constitution_type">
              <el-select v-model="form.constitution_type" style="width: 100%" placeholder="请选择">
                <el-option label="平和质" value="平和质" />
                <el-option label="气虚质" value="气虚质" />
                <el-option label="阳虚质" value="阳虚质" />
                <el-option label="阴虚质" value="阴虚质" />
                <el-option label="痰湿质" value="痰湿质" />
                <el-option label="湿热质" value="湿热质" />
                <el-option label="血瘀质" value="血瘀质" />
                <el-option label="气郁质" value="气郁质" />
                <el-option label="特禀质" value="特禀质" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-divider content-position="left">四诊信息</el-divider>

        <el-form-item label="四诊信息" prop="symptoms">
          <el-input v-model="form.symptoms" type="textarea" :rows="3" placeholder="望、闻、问、切四诊信息，如：面色苍白，舌淡胖有齿痕，脉沉细..." />
        </el-form-item>

        <el-divider content-position="left">辨证论治</el-divider>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="辨证" prop="diagnosis">
              <el-input v-model="form.diagnosis" placeholder="请输入辨证结果" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="治法" prop="treatment">
              <el-input v-model="form.treatment" placeholder="请输入治疗法则" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="方药" prop="prescription">
          <el-input v-model="form.prescription" type="textarea" :rows="3" placeholder="请输入方药组成及用法，如：党参15g 黄芪30g 白术10g..." />
        </el-form-item>

        <el-divider content-position="left">调养建议</el-divider>

        <el-form-item label="调养建议" prop="advice">
          <el-input v-model="form.advice" type="textarea" :rows="4" placeholder="饮食、起居、情志等方面的调养建议" />
        </el-form-item>

        <el-form-item label="备注">
          <el-input v-model="form.notes" type="textarea" :rows="3" placeholder="其他备注信息" />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleSubmit" :loading="submitting">
            {{ isEdit ? '保存修改' : '创建中医档案' }}
          </el-button>
          <el-button @click="$router.push('/tcm')">取消</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { tcmApi } from '@/api/tcm'
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
  constitution_type: '',
  symptoms: '',
  diagnosis: '',
  treatment: '',
  prescription: '',
  advice: '',
  notes: '',
})

const rules: FormRules = {
  patient_id: [{ required: true, message: '请选择患者', trigger: 'change' }],
  constitution_type: [{ required: true, message: '请选择体质类型', trigger: 'change' }],
  symptoms: [{ required: true, message: '请输入四诊信息', trigger: 'blur' }],
  diagnosis: [{ required: true, message: '请输入辨证', trigger: 'blur' }],
  treatment: [{ required: true, message: '请输入治法', trigger: 'blur' }],
  prescription: [{ required: true, message: '请输入方药', trigger: 'blur' }],
  advice: [{ required: true, message: '请输入调养建议', trigger: 'blur' }],
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
      const data = await tcmApi.getById(route.params.id as string)
      Object.assign(form, {
        patient_id: data.patient_id || '',
        constitution_type: data.constitution_type || '',
        symptoms: data.symptoms || '',
        diagnosis: data.diagnosis || '',
        treatment: data.treatment || '',
        prescription: data.prescription || '',
        advice: data.advice || '',
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
      await tcmApi.update(route.params.id as string, form)
      ElMessage.success('修改成功')
    } else {
      await tcmApi.create(form)
      ElMessage.success('创建成功')
    }
    router.push('/tcm')
  } catch (e: any) {
    const msg = e?.response?.data?.detail || e?.message || '操作失败'
    // 错误已由 request.ts 拦截器统一提示
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.tcm-form { padding: 20px; }
.card-header { display: flex; justify-content: space-between; align-items: center; }
</style>