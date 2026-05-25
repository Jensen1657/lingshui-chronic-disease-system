import TableSkeleton from "@/components/TableSkeleton.vue"
<template>
  <div class="wechat-list">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>微信绑定列表</span>
          <el-button type="primary" @click="handleBind">绑定微信</el-button>
        </div>
      </template>

      <!-- 搜索表单 -->
      <el-form :model="searchForm" inline>
        <el-form-item label="患者ID">
          <el-input v-model="searchForm.patient_id" placeholder="请输入患者ID" clearable />
        </el-form-item>
        <el-form-item label="绑定状态">
          <el-select v-model="searchForm.is_active" placeholder="请选择状态" clearable>
            <el-option label="已绑定" :value="true" />
            <el-option label="未绑定" :value="false" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">搜索</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>

      <!-- 微信绑定表格 -->
      <TableSkeleton v-if="loading" :rows="8" />
        <el-table v-else :data="wechatStore.bindings" v-loading="wechatStore.loading" style="width: 100%">
        <el-table-column prop="patient_id" label="患者ID" width="100" />
        <el-table-column prop="nickname" label="微信昵称" width="120" />
        <el-table-column prop="avatar_url" label="头像" width="80">
          <template #default="{ row }">
            <el-avatar v-if="row.avatar_url" :src="row.avatar_url" :size="40" />
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="is_active" label="绑定状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'">
              {{ row.is_active ? '已绑定' : '未绑定' }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="250" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="handleView(row)">查看</el-button>
            <el-button
              v-if="!row.is_active"
              type="success"
              size="small"
              @click="handleActivate(row)"
            >激活</el-button>
            <el-button
              v-if="row.is_active"
              type="warning"
              size="small"
              @click="handleDeactivate(row)"
            >停用</el-button>
            <el-button type="danger" size="small" @click="handleUnbind(row)">解绑</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.page_size"
          :page-sizes="[10, 20, 50, 100]"
          :total="wechatStore.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- 绑定对话框 -->
    <WechatForm
      v-model:visible="dialogVisible"
      :binding="currentBinding"
      @success="handleSuccess"
    />

  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useWechatStore } from '@/stores/wechat'
import { ElMessage, ElMessageBox } from 'element-plus'
import WechatForm from '@/components/WechatForm.vue'
import type { WechatBinding } from '@/types/wechat'

const wechatStore = useWechatStore()

const dialogVisible = ref(false)
const currentBinding = ref<WechatBinding | null>(null)


const searchForm = reactive({
  patient_id: '',
  is_active: ''
})

const pagination = reactive({
  page: 1,
  page_size: 20
})

const handleBind = () => {
  currentBinding.value = null
  dialogVisible.value = true
}

const handleView = (row: WechatBinding) => {
  console.log('View Wechat binding:', row.id)
}

const handleActivate = async (row: WechatBinding) => {
  try {
    await wechatStore.activateBinding(row.id)
    ElMessage.success('激活成功')
    loadData()
  } catch (error) {
    ElMessage.error('激活失败')
  }
}

const handleDeactivate = async (row: WechatBinding) => {
  try {
    await wechatStore.deactivateBinding(row.id)
    ElMessage.success('停用成功')
    loadData()
  } catch (error) {
    ElMessage.error('停用失败')
  }
}

const handleUnbind = async (row: WechatBinding) => {
  try {
    await ElMessageBox.confirm('确定要解绑此患者的微信吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await wechatStore.unbindWechat(row.id)
    ElMessage.success('解绑成功')
    loadData()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('解绑失败')
    }
  }
}

const handleSearch = () => {
  pagination.page = 1
  loadData()
}

const handleReset = () => {
  searchForm.patient_id = ''
  searchForm.is_active = ''
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
  if (searchForm.is_active !== '') params.is_active = searchForm.is_active

  await wechatStore.fetchBindings(params)
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.wechat-list {
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
