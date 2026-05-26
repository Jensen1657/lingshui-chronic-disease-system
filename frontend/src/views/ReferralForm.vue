<template>
  <div class="referral-form">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>{{ isEdit ? '编辑转诊' : '新建转诊记录' }}</span>
          <el-button @click="$router.push('/referrals')">返回列表</el-button>
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
            <el-form-item label="转诊类型" prop="referral_type">
              <el-select v-model="form.referral_type" style="width: 100%">
                <el-option label="上转" value="上转" />
                <el-option label="下转" value="下转" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="转出机构" prop="source_org">
              <el-input v-model="form.source_org" placeholder="请输入转出机构" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="转入机构" prop="target_org">
              <el-input v-model="form.target_org" placeholder="请输入转入机构" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="紧急程度" prop="urgency">
              <el-select v-model="form.urgency" style="width: 100%">
                <el-option label="普通" value="普通" />
                <el-option label="紧急" value="紧急" />
                <el-option label="危重" value="危重" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="当前状态">
              <el-select v-model="form.status" style="width: 100%">
                <el-option label="待处理" value="PENDING" />
                <el-option label="已完成" value="COMPLETED" />
                <el-option label="已取消" value="CANCELLED" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-divider content-position="left">转诊信息</el-divider>

        <el-form-item label="诊断" prop="diagnosis">
          <el-input v-model="form.diagnosis" placeholder="请输入诊断信息" />
        </el-form-item>

        <el-form-item label="转诊原因" prop="referral_reason">
          <el-input v-model="form.referral_reason" type="textarea" :rows="4" placeholder="请输入转诊原因" />
        </el-form-item>

        <el-form-item label="备注">
          <el-input v-model="form.notes" type="textarea" :rows="3" placeholder="其他备注信息" />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleSubmit" :loading="submitting">
            {{ isEdit ? '保存修改' : '创建转诊' }}
          </el-button>
          <el-button @click="$router.push('/referrals')">取消</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { referralApi } from '@/api/referral'
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
  referral_type: '上转',
  source_org: '',
  target_org: '',
  referral_reason: '',
  diagnosis: '',
  urgency: '普通',
  status: 'PENDING',
  notes: '',
})

const rules: FormRules = {
  patient_id: [{ required: true, message: '请选择患者', trigger: 'change' }],
  referral_type: [{ required: true, message: '请选择转诊类型', trigger: 'change' }],
  source_org: [{ required: true, message: '请输入转出机构', trigger: 'blur' }],
  target_org: [{ required: true, message: '请输入转入机构', trigger: 'blur' }],
  urgency: [{ required: true, message: '请选择紧急程度', trigger: 'change' }],
  diagnosis: [{ required: true, message: '请输入诊断', trigger: 'blur' }],
  referral_reason: [{ required: true, message: '请输入转诊原因', trigger: 'blur' }],
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
      const data = await referralApi.getById(route.params.id as string)
      Object.assign(form, {
        patient_id: data.patient_id || '',
        referral_type: data.referral_type || '上转',
        source_org: data.source_org || '',
        target_org: data.target_org || '',
        referral_reason: data.referral_reason || '',
        diagnosis: data.diagnosis || '',
        urgency: data.urgency || '普通',
        status: data.status || 'PENDING',
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
      await referralApi.update(route.params.id as string, form)
      ElMessage.success('修改成功')
    } else {
      await referralApi.create(form)
      ElMessage.success('创建成功')
    }
    router.push('/referrals')
  } catch (e: any) {
    const msg = e?.response?.data?.detail || e?.message || '操作失败'
    // 错误已由 request.ts 拦截器统一提示
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.referral-form { padding: 20px; }
.card-header { display: flex; justify-content: space-between; align-items: center; }
</style>