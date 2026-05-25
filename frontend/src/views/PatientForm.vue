<template>
  <div class="patient-form">
    <el-card shadow="never">
      <template #header>
        <div class="card-header">
          <span>{{ isEdit ? '编辑患者' : '新建患者' }}</span>
          <el-button @click="$router.push('/patients')">返回列表</el-button>
        </div>
      </template>

      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="120px"
        style="max-width: 800px; margin: 0 auto;"
      >
        <el-divider content-position="left">基本信息</el-divider>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="姓名" prop="name">
              <el-input v-model="form.name" placeholder="请输入姓名" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="性别" prop="gender">
              <el-select v-model="form.gender" placeholder="请选择" style="width: 100%">
                <el-option label="男" value="男" />
                <el-option label="女" value="女" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="出生日期" prop="date_of_birth">
              <el-date-picker v-model="form.date_of_birth" type="date" placeholder="选择日期" value-format="YYYY-MM-DD" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="身份证号" prop="id_card">
              <el-input v-model="form.id_card" placeholder="请输入身份证号" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="手机号" prop="phone">
              <el-input v-model="form.phone" placeholder="请输入手机号" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="民族">
              <el-select v-model="form.ethnicity" placeholder="请选择" filterable allow-create style="width: 100%">
                <el-option label="汉族" value="汉族" />
                <el-option label="黎族" value="黎族" />
                <el-option label="苗族" value="苗族" />
                <el-option label="回族" value="回族" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-divider content-position="left">地址信息</el-divider>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="乡镇/区域">
              <el-select v-model="form.township_code" placeholder="请选择" style="width: 100%">
                <el-option label="椰林镇" value="460123100" />
                <el-option label="光坡镇" value="460123101" />
                <el-option label="三才镇" value="460123102" />
                <el-option label="英州镇" value="460123103" />
                <el-option label="隆广镇" value="460123104" />
                <el-option label="本号镇" value="460123105" />
                <el-option label="新村镇" value="460123106" />
                <el-option label="黎安镇" value="460123107" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="村/社区">
              <el-input v-model="form.village_name" placeholder="请输入村名" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="详细地址">
          <el-input v-model="form.address" type="textarea" :rows="2" placeholder="详细地址" />
        </el-form-item>

        <el-divider content-position="left">慢病信息</el-divider>

        <el-row :gutter="20">
          <el-col :span="24">
            <el-form-item label="慢病类型" prop="disease_list">
              <el-checkbox-group v-model="form.disease_list">
                <el-checkbox label="HYPERTENSION">高血压</el-checkbox>
                <el-checkbox label="DIABETES">糖尿病</el-checkbox>
                <el-checkbox label="CHD">冠心病</el-checkbox>
                <el-checkbox label="STROKE">脑卒中</el-checkbox>
                <el-checkbox label="COPD">慢阻肺</el-checkbox>
                <el-checkbox label="CKD">慢性肾脏病</el-checkbox>
              </el-checkbox-group>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="风险等级">
              <el-select v-model="form.risk_level" placeholder="自动评估" style="width: 100%">
                <el-option label="低风险" value="LOW" />
                <el-option label="中风险" value="MEDIUM" />
                <el-option label="高风险" value="HIGH" />
                <el-option label="极高风险" value="VERY_HIGH" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="建档日期">
              <el-date-picker v-model="form.filing_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="备注">
          <el-input v-model="form.notes" type="textarea" :rows="3" placeholder="备注信息" />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleSubmit" :loading="submitting">
            {{ isEdit ? '保存修改' : '创建患者' }}
          </el-button>
          <el-button @click="$router.push('/patients')">取消</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { patientApi } from '@/api/patient'
import type { FormInstance, FormRules } from 'element-plus'

const route = useRoute()
const router = useRouter()
const formRef = ref<FormInstance>()
const submitting = ref(false)

const isEdit = computed(() => !!route.params.id)

const form = reactive({
  name: '',
  gender: '',
  date_of_birth: '',
  id_card: '',
  phone: '',
  ethnicity: '汉族',
  township_code: '',
  village_name: '',
  address: '',
  disease_list: [] as string[],
  risk_level: 'MEDIUM',
  filing_date: new Date().toISOString().slice(0, 10),
  notes: '',
})

const rules: FormRules = {
  name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  gender: [{ required: true, message: '请选择性别', trigger: 'change' }],
  phone: [
    { pattern: /^1[3-9]\d{9}$/, message: '手机号格式不正确', trigger: 'blur' }
  ],
}

// 编辑模式：加载现有数据
onMounted(async () => {
  if (isEdit.value && route.params.id) {
    try {
      const data = await patientApi.getById(route.params.id as string)
      Object.assign(form, {
        name: data.name || '',
        gender: data.gender || '',
        date_of_birth: data.date_of_birth || '',
        id_card: '', // 不回显身份证
        phone: data.phone || '',
        ethnicity: data.ethnicity || '汉族',
        township_code: data.township_code || '',
        village_name: data.village_name || '',
        address: data.address || '',
        disease_list: data.disease_list ? (typeof data.disease_list === 'string' ? data.disease_list.split(',') : data.disease_list) : [],
        risk_level: data.risk_level || 'MEDIUM',
        filing_date: data.filing_date || '',
        notes: data.notes || '',
      })
    } catch (e: any) {
      ElMessage.error('加载患者数据失败')
    }
  }
})

const handleSubmit = async () => {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  submitting.value = true
  try {
    const payload = {
      ...form,
      disease_list: Array.isArray(form.disease_list) ? form.disease_list.join(',') : form.disease_list,
    }

    if (isEdit.value) {
      await patientApi.update(route.params.id as string, payload)
      ElMessage.success('修改成功')
    } else {
      await patientApi.create(payload)
      ElMessage.success('创建成功')
    }
    router.push('/patients')
  } catch (e: any) {
    const msg = e?.response?.data?.detail || e?.message || '操作失败'
    ElMessage.error(msg)
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.patient-form {
  padding: 20px;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
