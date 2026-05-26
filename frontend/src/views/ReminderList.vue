import TableSkeleton from "@/components/TableSkeleton.vue"
<template>
  <div class="reminder-list">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>随访提醒列表</span>
          <el-button type="primary" @click="handleCreate">新增提醒</el-button>
        </div>
      </template>

      <!-- 搜索表单 -->
      <el-form :model="searchForm" inline>
        <el-form-item label="患者ID">
          <el-input v-model="searchForm.patient_id" placeholder="请输入患者ID" clearable />
        </el-form-item>
        <el-form-item label="提醒类型">
          <el-select v-model="searchForm.plan_type" placeholder="请选择提醒类型" clearable>
            <el-option label="用药提醒" value="MEDICATION" />
            <el-option label="随访提醒" value="followup" />
            <el-option label="评估提醒" value="assessment" />
            <el-option label="生活方式" value="lifestyle" />
            <el-option label="自定义" value="custom" />
          </el-select>
        </el-form-item>
        <el-form-item label="激活状态">
          <el-select v-model="searchForm.status" placeholder="请选择状态" clearable>
            <el-option label="待发送" value="PENDING" />
            <el-option label="已发送" value="SENT" />
            <el-option label="发送失败" value="FAILED" />
          </el-select>
        </el-form-item>
        <el-form-item label="发送状态">
          <el-select v-model="searchForm.is_sent" placeholder="请选择发送状态" clearable>
            <el-option label="已发送" :value="true" />
            <el-option label="未发送" :value="false" />
          </el-select>
        </el-form-item>
        <el-form-item label="提醒时间">
          <el-date-picker
            v-model="searchForm.date_range"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">搜索</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>

      <!-- 提醒表格 -->
      <TableSkeleton v-if="loading" :rows="8" />
        <el-table v-else :data="reminderStore.reminders" v-loading="reminderStore.loading" style="width: 100%">
        <el-table-column prop="patient_id" label="患者ID" width="100" />
        <el-table-column prop="plan_type" label="提醒类型" width="100">
          <template #default="{ row }">
            <el-tag>{{ getReminderTypeText(row.plan_type) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="report_content" label="提醒内容" width="250" show-overflow-tooltip />
        <el-table-column prop="plan_date" label="提醒时间" width="120" />
        <el-table-column prop="status" label="激活状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.status === 'SENT' ? 'success' : 'info'">
              {{ row.status === 'SENT' ? '已激活' : '未激活' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="is_sent" label="发送状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_sent ? 'success' : 'warning'">
              {{ row.is_sent ? '已发送' : '未发送' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="sent_at" label="发送时间" width="120" />
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="handleView(row)">查看</el-button>
            <el-button type="warning" size="small" @click="handleEdit(row)" :disabled="row.is_sent">编辑</el-button>
            <el-button v-if="!row.is_sent" type="success" size="small" @click="handleSend(row)">发送</el-button>
            <el-button type="danger" size="small" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.page_size"
          :page-sizes="[10, 20, 50, 100]"
          :total="reminderStore.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- 新增/编辑对话框 -->
    <ReminderForm
      v-model:visible="dialogVisible"
      :reminder="currentReminder"
      @success="handleSuccess"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useReminderStore } from '@/stores/reminder'
import ReminderForm from '@/components/ReminderForm.vue'
import type { ReminderRecord } from '@/types/reminder'

const reminderStore = useReminderStore()

const dialogVisible = ref(false)
const currentReminder = ref<ReminderRecord | null>(null)

const searchForm = reactive({
  patient_id: '',
  plan_type: '',
  status: '',
  is_sent: '',
  date_range: []
})

const pagination = reactive({
  page: 1,
  page_size: 20
})

const handleCreate = () => {
  currentReminder.value = null
  dialogVisible.value = true
}

const handleView = (row: ReminderRecord) => {
  console.log('View reminder:', row.id)
}

const handleEdit = (row: ReminderRecord) => {
  currentReminder.value = row
  dialogVisible.value = true
}

const handleSend = async (row: ReminderRecord) => {
  try {
    await ElMessageBox.confirm('确定要发送此提醒吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await reminderStore.sendReminder(row.id)
    ElMessage.success('提醒已发送')
    loadData()
  } catch (error) {
    if (error !== 'cancel') {
      // 错误已由 request.ts 拦截器统一提示
    }
  }
}

const handleDelete = async (row: ReminderRecord) => {
  try {
    await ElMessageBox.confirm('确定要删除此提醒吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await reminderStore.deleteReminder(row.id)
    ElMessage.success('删除成功')
    loadData()
  } catch (error) {
    if (error !== 'cancel') {
      // 错误已由 request.ts 拦截器统一提示
    }
  }
}

const handleSearch = () => {
  pagination.page = 1
  loadData()
}

const handleReset = () => {
  searchForm.patient_id = ''
  searchForm.plan_type = ''
  searchForm.status = ''
  searchForm.is_sent = ''
  searchForm.date_range = []
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
  if (searchForm.plan_type) params.plan_type = searchForm.plan_type
  if (searchForm.status) params.status = searchForm.status
  if (searchForm.is_sent !== '') params.is_sent = searchForm.is_sent
  if (searchForm.date_range && searchForm.date_range.length === 2) {
    params.start_time = searchForm.date_range[0]
    params.end_time = searchForm.date_range[1]
  }

  await reminderStore.fetchReminders(params)
}

const getReminderTypeText = (type: string) => {
  const map: Record<string, string> = {
    'medication': '用药提醒', 'MEDICATION': '用药提醒',
    'followup': '随访提醒', 'FOLLOWUP': '随访提醒',
    'assessment': '评估提醒', 'ASSESSMENT': '评估提醒',
    'lifestyle': '生活方式', 'LIFESTYLE': '生活方式',
    'custom': '自定义', 'CUSTOM': '自定义'
  }
  return map[type] || type
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.reminder-list {
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