import TableSkeleton from "@/components/TableSkeleton.vue"
<template>
  <div class="tcm-list">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>中医管理列表</span>
          <el-button type="primary" @click="handleCreate">新增中医记录</el-button>
        </div>
      </template>

      <!-- 搜索表单 -->
      <el-form :model="searchForm" inline>
        <el-form-item label="患者ID">
          <el-input v-model="searchForm.patient_id" placeholder="请输入患者ID" clearable />
        </el-form-item>
        <el-form-item label="证型">
          <el-select v-model="searchForm.syndrome_type" placeholder="请选择证型" clearable>
            <el-option label="气虚质" value="qi_deficiency" />
            <el-option label="阳虚质" value="yang_deficiency" />
            <el-option label="阴虚质" value="yin_deficiency" />
            <el-option label="血瘀质" value="blood_stasis" />
            <el-option label="痰湿质" value="phlegm_dampness" />
            <el-option label="湿热质" value="damp_heat" />
            <el-option label="气郁质" value="qi_stagnation" />
            <el-option label="血虚质" value="blood_deficiency" />
          </el-select>
        </el-form-item>
        <el-form-item label="中医病名">
          <el-select v-model="searchForm.tcm_disease" placeholder="请选择中医病名" clearable>
            <el-option label="消渴" value="xiao_ke" />
            <el-option label="眩晕" value="xuan_yun" />
            <el-option label="胸痹" value="xiong_bi" />
            <el-option label="中风" value="zhong_feng" />
            <el-option label="肺胀" value="fei_zhang" />
            <el-option label="水肿" value="shui_zhong" />
          </el-select>
        </el-form-item>
        <el-form-item label="就诊医生">
          <el-input v-model="searchForm.visit_doctor" placeholder="请输入就诊医生" clearable />
        </el-form-item>
        <el-form-item label="完成状态">
          <el-select v-model="searchForm.is_completed" placeholder="请选择状态" clearable>
            <el-option label="已完成" :value="true" />
            <el-option label="未完成" :value="false" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">搜索</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>

      <!-- 中医管理表格 -->
      <TableSkeleton v-if="loading" :rows="8" />
        <el-table v-else :data="tcmStore.records" v-loading="tcmStore.loading" style="width: 100%">
        <el-table-column prop="patient_id" label="患者ID" width="100" />
        <el-table-column prop="patient_name" label="患者姓名" width="100">
          <template #default="{ row }">
            {{ row.patient_name || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="org_name" label="所属机构" width="140">
          <template #default="{ row }">
            {{ row.org_name || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="syndrome_type" label="证型" width="120">
          <template #default="{ row }">
            <el-tag>{{ row.syndrome_type || '-' }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="tcm_disease" label="中医病名" width="100">
          <template #default="{ row }">
            {{ row.tcm_disease || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="record_date" label="就诊日期" width="120" />
        <el-table-column prop="recorded_by" label="就诊医生" width="100" />
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="handleView(row)">查看</el-button>
            <el-button type="warning" size="small" @click="handleEdit(row)" :disabled="row.is_completed">编辑</el-button>
            <el-button type="success" size="small" @click="handleComplete(row)">完成</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.page_size"
          :page-sizes="[10, 20, 50, 100]"
          :total="tcmStore.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- 新增/编辑对话框 -->
    <TcmForm
      v-model:visible="dialogVisible"
      :record="currentRecord"
      @success="handleSuccess"
    />

    <!-- 完成对话框 -->
    <el-dialog v-model="completeDialogVisible" title="完成中医诊疗" width="500px">
      <el-form :model="completeForm" label-width="100px">
        <el-form-item label="疗效评价">
          <el-input
            v-model="completeForm.efficacy_evaluation"
            type="textarea"
            :rows="3"
            placeholder="请输入疗效评价"
          />
        </el-form-item>
        <el-form-item label="下次就诊日期">
          <el-date-picker
            v-model="completeForm.next_visit_date"
            type="date"
            placeholder="请选择下次就诊日期"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="completeDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleCompleteSubmit" :loading="completeLoading">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useTcmStore } from '@/stores/tcm'
import TcmForm from '@/components/TcmForm.vue'
import type { TcmRecord } from '@/types/tcm'

const tcmStore = useTcmStore()

const dialogVisible = ref(false)
const currentRecord = ref<TcmRecord | null>(null)

const completeDialogVisible = ref(false)
const completeLoading = ref(false)
const completeForm = reactive({
  efficacy_evaluation: '',
  next_visit_date: ''
})
const currentCompleteId = ref('')

const searchForm = reactive({
  patient_id: '',
  syndrome_type: '',
  disease_code: '',
  visit_doctor: '',
  is_completed: undefined as boolean | undefined
})

const pagination = reactive({
  page: 1,
  page_size: 20
})

const handleCreate = () => {
  currentRecord.value = null
  dialogVisible.value = true
}

const handleView = (row: TcmRecord) => {
  currentRecord.value = row
  dialogVisible.value = true
}

const handleEdit = (row: TcmRecord) => {
  currentRecord.value = row
  dialogVisible.value = true
}

const handleComplete = (row: TcmRecord) => {
  currentCompleteId.value = row.id
  completeForm.efficacy_evaluation = ''
  completeForm.next_visit_date = ''
  completeDialogVisible.value = true
}

const handleCompleteSubmit = async () => {
  try {
    completeLoading.value = true
    await tcmStore.completeRecord(currentCompleteId.value, {
      efficacy_evaluation: completeForm.efficacy_evaluation,
      next_visit_date: completeForm.next_visit_date
    })
    ElMessage.success('中医诊疗已完成')
    completeDialogVisible.value = false
    loadData()
  } catch (error) {
    // 错误已由 request.ts 拦截器统一提示
  } finally {
    completeLoading.value = false
  }
}

const handleSearch = () => {
  pagination.page = 1
  loadData()
}

const handleReset = () => {
  searchForm.patient_id = ''
  searchForm.syndrome_type = ''
  searchForm.disease_code = ''
  searchForm.visit_doctor = ''
  searchForm.is_completed = undefined
  pagination.page = 1
  loadData()
}

const handleSizeChange = (val: number) => {
  pagination.page_size = val
  loadData()
}

const handleCurrentChange = (val: number) => {
  pagination.page = val
  loadData()
}

const handleSuccess = () => {
  dialogVisible.value = false
  loadData()
}

const loadData = async () => {
  const params: any = {
    page: pagination.page,
    page_size: pagination.page_size
  }

  if (searchForm.patient_id) params.patient_id = searchForm.patient_id
  if (searchForm.syndrome_type) params.syndrome_type = searchForm.syndrome_type
  if (searchForm.disease_code) params.disease_code = searchForm.disease_code
  if (searchForm.visit_doctor) params.visit_doctor = searchForm.visit_doctor

  await tcmStore.fetchRecords(params)
}

const getSyndromeTypeText = (type: string) => {
  const map: Record<string, string> = {
    'qi_deficiency': '气虚质',
    'yang_deficiency': '阳虚质',
    'yin_deficiency': '阴虚质',
    'blood_stasis': '血瘀质',
    'phlegm_dampness': '痰湿质',
    'damp_heat': '湿热质',
    'qi_stagnation': '气郁质',
    'blood_deficiency': '血虚质'
  }
  return map[type] || type
}

const getTcmDiseaseText = (disease: string) => {
  const map: Record<string, string> = {
    'xiao_ke': '消渴',
    'xuan_yun': '眩晕',
    'xiong_bi': '胸痹',
    'zhong_feng': '中风',
    'fei_zhang': '肺胀',
    'shui_zhong': '水肿'
  }
  return map[disease] || disease
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.tcm-list {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.pagination-container {
  margin-top: 20px;
  text-align: right;
}
</style>
