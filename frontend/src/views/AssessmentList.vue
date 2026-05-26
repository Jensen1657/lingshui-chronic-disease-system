import TableSkeleton from "@/components/TableSkeleton.vue"
<template>
  <div class="assessment-list">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>年度评估列表</span>
          <el-button type="primary" @click="handleCreate">新增评估</el-button>
        </div>
      </template>

      <!-- 搜索表单 -->
      <el-form :model="searchForm" inline>
        <el-form-item label="患者编号">
          <el-input v-model="searchForm.patient_id" placeholder="请输入患者编号" clearable />
        </el-form-item>
        <el-form-item label="慢病类型">
          <el-select v-model="searchForm.disease_code" placeholder="请选择慢病类型" clearable>
            <el-option label="高血压" value="HYPERTENSION" />
            <el-option label="糖尿病" value="DIABETES" />
            <el-option label="冠心病" value="CORONARY_HEART_DISEASE" />
            <el-option label="脑卒中" value="STROKE" />
            <el-option label="慢阻肺" value="COPD" />
            <el-option label="慢性肾病" value="CKD" />
          </el-select>
        </el-form-item>
        <el-form-item label="评估年度">
          <el-date-picker
            v-model="searchForm.assessment_year"
            type="year"
            placeholder="选择年度"
            value-format="YYYY"
          />
        </el-form-item>
        <el-form-item label="眼底检查">
          <el-select v-model="searchForm.eye_exam_done" placeholder="请选择" clearable>
            <el-option label="已检查" :value="true" />
            <el-option label="未检查" :value="false" />
          </el-select>
        </el-form-item>
        <el-form-item label="足部检查">
          <el-select v-model="searchForm.foot_exam_done" placeholder="请选择" clearable>
            <el-option label="已检查" :value="true" />
            <el-option label="未检查" :value="false" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">搜索</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>

      <!-- 评估表格 -->
      <TableSkeleton v-if="loading" :rows="8" />
        <el-table v-else :data="assessmentStore.records" v-loading="assessmentStore.loading" style="width: 100%">
        <el-table-column prop="assessment_id" label="评估编号" width="140" />
        <el-table-column prop="patient_name" label="患者姓名" width="100" />
        <el-table-column prop="org_name" label="所属机构" width="140" />
        <el-table-column prop="patient_id" label="患者编号" width="100" />
        <el-table-column prop="disease_code" label="慢病类型" width="100">
          <template #default="{ row }">
            <el-tag size="small">{{ diseaseLabel(row.disease_code) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="assessment_year" label="评估年度" width="100" />
        <el-table-column label="血压控制率" width="100">
          <template #default="{ row }">
            <span v-if="row.bp_controlled_rate">{{ row.bp_controlled_rate }}%</span>
            <span v-else>-</span>
          </template>
        </el-table-column>

        <el-table-column label="检查项目" width="120">
          <template #default="{ row }">
            <el-tag v-if="row.eye_exam_done" type="success" size="small" style="margin-right:4px">眼底</el-tag>
            <el-tag v-if="row.foot_exam_done" type="success" size="small" style="margin-right:4px">足部</el-tag>
            <el-tag v-if="row.echo_done" type="success" size="small">心超</el-tag>
            <span v-if="!row.eye_exam_done && !row.foot_exam_done && !row.echo_done">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="assessed_by" label="评估医生" width="100">
          <template #default="{ row }">
            {{ row.assessed_by || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="160">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="handleView(row)">查看</el-button>
            <el-button type="warning" size="small" @click="handleEdit(row)">编辑</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.page_size"
          :page-sizes="[10, 20, 50, 100]"
          :total="assessmentStore.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAssessmentStore } from '@/stores/assessment'
import type { Assessment } from '@/types/assessment'

const router = useRouter()
const assessmentStore = useAssessmentStore()

const searchForm = reactive({
  patient_id: '',
  disease_code: '',
  assessment_year: '',
  eye_exam_done: '' as boolean | '',
  foot_exam_done: '' as boolean | ''
})

const pagination = reactive({
  page: 1,
  page_size: 20
})

const handleCreate = () => {
  router.push('/assessments/create')
}

const handleView = (row: Assessment) => {
  router.push(`/assessments/${row.assessment_id}`)
}

const handleEdit = (row: Assessment) => {
  router.push(`/assessments/${row.assessment_id}/edit`)
}

const handleSearch = () => {
  pagination.page = 1
  loadData()
}

const handleReset = () => {
  Object.assign(searchForm, {
    patient_id: '',
    disease_code: '',
    assessment_year: '',
    eye_exam_done: '',
    foot_exam_done: ''
  })
  pagination.page = 1
  loadData()
}

const handleSizeChange = (size: number) => {
  pagination.page_size = size
  loadData()
}

const handleCurrentChange = (page: number) => {
  pagination.page = page
  loadData()
}

const loadData = async () => {
  const params: any = {
    page: pagination.page,
    page_size: pagination.page_size
  }

  if (searchForm.patient_id) params.patient_id = searchForm.patient_id
  if (searchForm.disease_code) params.disease_code = searchForm.disease_code
  if (searchForm.assessment_year) params.assessment_year = parseInt(searchForm.assessment_year)
  if (searchForm.eye_exam_done !== '') params.eye_exam_done = searchForm.eye_exam_done
  if (searchForm.foot_exam_done !== '') params.foot_exam_done = searchForm.foot_exam_done

  await assessmentStore.fetchRecords(params)
}

function diseaseLabel(disease: string) {
  const map: Record<string, string> = {
    'HYPERTENSION': '高血压',
    'DIABETES': '糖尿病',
    'CORONARY': '冠心病',
    'CORONARY_HEART_DISEASE': '冠心病',
    'I10': '高血压',
    'E11': '糖尿病',
    'I20': '冠心病',
    'STROKE': '脑卒中',
    'COPD': '慢阻肺',
    'CKD': '慢性肾病'
  }
  return map[disease] || disease || '-'
}

function formatDateTime(dateStr: string) {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.assessment-list {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>
