<template>
  <div class="wechat-form">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>{{ isEdit ? '编辑微信绑定' : '新建微信绑定记录' }}</span>
          <el-button @click="$router.push('/wechat')">返回列表</el-button>
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
            <el-form-item label="关注状态" prop="subscribe_status">
              <el-select v-model="form.subscribe_status" style="width: 100%">
                <el-option label="已关注" value="已关注" />
                <el-option label="未关注" value="未关注" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-divider content-position="left">微信信息</el-divider>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="OpenID" prop="openid">
              <el-input v-model="form.openid" placeholder="请输入OpenID" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="昵称">
              <el-input v-model="form.nickname" placeholder="请输入微信昵称" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="绑定日期" prop="bind_date">
              <el-date-picker v-model="form.bind_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" placeholder="选择日期" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="备注">
          <el-input v-model="form.notes" type="textarea" :rows="3" placeholder="其他备注信息" />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleSubmit" :loading="submitting">
            {{ isEdit ? '保存修改' : '创建绑定' }}
          </el-button>
          <el-button @click="$router.push('/wechat')">取消</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { wechatApi } from '@/api/wechat'
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
  openid: '',
  nickname: '',
  subscribe_status: '已关注',
  bind_date: new Date().toISOString().slice(0, 10),
  notes: '',
})

const rules: FormRules = {
  patient_id: [{ required: true, message: '请选择患者', trigger: 'change' }],
  subscribe_status: [{ required: true, message: '请选择关注状态', trigger: 'change' }],
  openid: [{ required: true, message: '请输入OpenID', trigger: 'blur' }],
  bind_date: [{ required: true, message: '请选择绑定日期', trigger: 'change' }],
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
      const data = await wechatApi.getById(route.params.id as string)
      Object.assign(form, {
        patient_id: data.patient_id || '',
        openid: data.openid || '',
        nickname: data.nickname || '',
        subscribe_status: data.subscribe_status || '已关注',
        bind_date: data.bind_date || '',
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
      await wechatApi.update(route.params.id as string, form)
      ElMessage.success('修改成功')
    } else {
      await wechatApi.create(form)
      ElMessage.success('创建成功')
    }
    router.push('/wechat')
  } catch (e: any) {
    const msg = e?.response?.data?.detail || e?.message || '操作失败'
    // 错误已由 request.ts 拦截器统一提示
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.wechat-form { padding: 20px; }
.card-header { display: flex; justify-content: space-between; align-items: center; }
</style>