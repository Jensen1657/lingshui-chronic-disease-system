<template>
  <div class="audit-log-view">
    <el-card class="header-card" shadow="never">
      <div class="header">
        <h2>📋 操作审计日志</h2>
        <div class="header-actions">
          <el-button type="primary" size="small" @click="handleExport">导出日志</el-button>
          <el-button type="success" size="small" @click="loadData">刷新</el-button>
        </div>
      </div>
    </el-card>

    <!-- 统计卡片 -->
    <el-row :gutter="20" style="margin-bottom: 20px;">
      <el-col :span="6">
        <el-card shadow="hover">
          <el-statistic title="总日志数" :value="stats.totalLogs" />
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <el-statistic title="今日日志" :value="stats.todayLogs" />
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <el-statistic title="敏感操作" :value="stats.sensitiveOperations" />
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <el-statistic title="活跃用户" :value="stats.activeUsers" />
        </el-card>
      </el-col>
    </el-row>

    <!-- 过滤条件 -->
    <el-card class="filter-card" shadow="hover">
      <el-form :inline="true" :model="query" class="filter-form">
        <el-form-item label="用户">
          <el-input v-model="query.user_id" placeholder="用户ID" clearable />
        </el-form-item>
        <el-form-item label="操作类型">
          <el-select v-model="query.action" placeholder="全部" clearable>
            <el-option label="全部" value="" />
            <el-option label="新增" value="POST" />
            <el-option label="更新" value="PUT" />
            <el-option label="删除" value="DELETE" />
          </el-select>
        </el-form-item>
        <el-form-item label="资源类型">
          <el-select v-model="query.resource" placeholder="全部" clearable>
            <el-option label="全部" value="" />
            <el-option label="患者" value="patient" />
            <el-option label="随访" value="followup" />
            <el-option label="转诊" value="referral" />
            <el-option label="评估" value="assessment" />
            <el-option label="预警" value="alert" />
          </el-select>
        </el-form-item>
        <el-form-item label="敏感操作">
          <el-select v-model="query.is_sensitive" placeholder="全部" clearable>
            <el-option label="全部" value="" />
            <el-option label="是" value="Y" />
            <el-option label="否" value="N" />
          </el-select>
        </el-form-item>
        <el-form-item label="开始日期">
          <el-date-picker v-model="query.start_date" type="date" value-format="YYYY-MM-DD" placeholder="开始" style="width: 140px;" />
        </el-form-item>
        <el-form-item label="结束日期">
          <el-date-picker v-model="query.end_date" type="date" value-format="YYYY-MM-DD" placeholder="结束" style="width: 140px;" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="resetQuery">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 日志表格 -->
    <el-card class="table-card" shadow="hover">
      <el-table :data="logs" border stripe v-loading="loading" style="width: 100%">
        <el-table-column prop="timestamp" label="时间" width="180" sortable />
        <el-table-column prop="username" label="用户" width="120" />
        <el-table-column prop="action" label="操作" width="100">
          <template #default="{ row }">
            <el-tag :type="getActionType(row.action)" size="small">{{ getActionText(row.action) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="resource" label="资源" width="120" />
        <el-table-column prop="resource_id" label="资源ID" width="150" />
        <el-table-column prop="ip_address" label="IP地址" width="150" />
        <el-table-column prop="request_method" label="方法" width="80" />
        <el-table-column prop="response_status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.response_status === 'success' ? 'success' : 'danger'">
              {{ row.response_status || 'N/A' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="is_sensitive" label="敏感" width="80">
          <template #default="{ row }">
            <el-tag :type="row.isSensitive === 'Y' ? 'danger' : 'info'">
              {{ row.isSensitive === 'Y' ? '是' : '否' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="viewDetail(row)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="query.limit"
          :total="total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>

    <!-- 详情对话框 -->
    <el-dialog v-model="detailVisible" title="操作详情" width="800px">
      <el-descriptions :column="2" border v-if="selectedLog">
        <el-descriptions-item label="日志ID">{{ selectedLog.log_id }}</el-descriptions-item>
        <el-descriptions-item label="时间">{{ selectedLog.timestamp }}</el-descriptions-item>
        <el-descriptions-item label="用户">{{ selectedLog.username }}</el-descriptions-item>
        <el-descriptions-item label="角色">{{ selectedLog.user_role || 'N/A' }}</el-descriptions-item>
        <el-descriptions-item label="操作">{{ getActionText(selectedLog.action) }}</el-descriptions-item>
        <el-descriptions-item label="资源">{{ selectedLog.resource }}</el-descriptions-item>
        <el-descriptions-item label="资源ID">{{ selectedLog.resource_id || 'N/A' }}</el-descriptions-item>
        <el-descriptions-item label="IP地址">{{ selectedLog.ip_address || 'N/A' }}</el-descriptions-item>
        <el-descriptions-item label="请求方法">{{ selectedLog.request_method || 'N/A' }}</el-descriptions-item>
        <el-descriptions-item label="请求路径">{{ selectedLog.request_path || 'N/A' }}</el-descriptions-item>
        <el-descriptions-item label="响应状态">{{ selectedLog.response_status || 'N/A' }}</el-descriptions-item>
        <el-descriptions-item label="敏感操作">
          <el-tag :type="selectedLog.isSensitive === 'Y' ? 'danger' : 'info'">
            {{ selectedLog.isSensitive === 'Y' ? '是' : '否' }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="会话ID">{{ selectedLog.session_id || 'N/A' }}</el-descriptions-item>
        <el-descriptions-item label="详细信息" :span="2">
          <pre>{{ JSON.stringify(selectedLog.details, null, 2) }}</pre>
        </el-descriptions-item>
      </el-descriptions>
      <template #footer>
        <el-button @click="detailVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { getAuditLogs, getAuditStats } from '@/api/audit-log'
import type { AuditLog, AuditStats, AuditLogQuery } from '@/types/audit-log'
import request from '@/api/request'

const logs = ref<AuditLog[]>([])
const stats = ref<AuditStats>({
  totalLogs: 0,
  todayLogs: 0,
  sensitiveOperations: 0,
  activeUsers: 0,
})
const loading = ref(false)
const total = ref(0)

const query = reactive<AuditLogQuery>({
  skip: 0,
  limit: 20,
  user_id: '',
  action: '',
  resource: '',
  is_sensitive: '',
  start_date: '',
  end_date: '',
})

const currentPage = computed({
  get: () => Math.floor(query.skip / query.limit) + 1,
  set: (val: number) => { query.skip = (val - 1) * query.limit },
})

const detailVisible = ref(false)
const selectedLog = ref<AuditLog | null>(null)

const loadData = async () => {
  loading.value = true
  try {
    const [logsRes, statsRes] = await Promise.all([
      getAuditLogs(query),
      getAuditStats(),
    ])
    logs.value = logsRes.items
    total.value = logsRes.total
    stats.value = statsRes
  } catch (error) {
    // 错误已由 request.ts 拦截器统一提示
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  query.skip = 0
  loadData()
}

const resetQuery = () => {
  query.user_id = ''
  query.action = ''
  query.resource = ''
  query.is_sensitive = ''
  query.start_date = ''
  query.end_date = ''
  query.skip = 0
  loadData()
}

const handleSizeChange = (val: number) => {
  query.limit = val
  query.skip = 0
  loadData()
}

const handlePageChange = (val: number) => {
  query.skip = (val - 1) * query.limit
  loadData()
}

const viewDetail = (row: AuditLog) => {
  selectedLog.value = row
  detailVisible.value = true
}

const handleExport = async () => {
  if (!query.start_date || !query.end_date) {
    ElMessage.warning('请先选择导出的日期范围')
    return
  }
  try {
    loading.value = true
    const res = await request.get('/v1/audit-logs/logs/export', {
      params: {
        start_date: query.start_date,
        end_date: query.end_date,
      },
    })
    // 下载 CSV 文件
    const BOM = '\uFEFF'
    const blob = new Blob([BOM + res.reportText], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.download = `audit_log_${query.start_date}_${query.end_date}.csv`
    link.click()
    URL.revokeObjectURL(link.href)
    ElMessage.success(`成功导出 ${res.totalRecords} 条日志`)
  } catch (error) {
    // 错误已由 request.ts 拦截器统一提示
  } finally {
    loading.value = false
  }
}

const getActionType = (action: string) => {
  const map: Record<string, string> = {
    'POST': 'success',
    'GET': 'info',
    'PUT': 'warning',
    'DELETE': 'danger',
    'PATCH': 'warning',
  }
  return map[action] || 'info'
}

const getActionText = (action: string) => {
  const map: Record<string, string> = {
    'POST': '新增',
    'GET': '查询',
    'PUT': '更新',
    'DELETE': '删除',
    'PATCH': '修改',
  }
  return map[action] || action || '-'
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.audit-log-view {
  padding: 20px;
}

.header-card {
  margin-bottom: 20px;
  background: linear-gradient(135rgg, #667eea 0%, #764ba2 100%);
  color: white;
}

.header-card h2 {
  color: white;
  margin: 0;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.filter-card {
  margin-bottom: 20px;
}

.filter-form {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.table-card {
  margin-bottom: 20px;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>
