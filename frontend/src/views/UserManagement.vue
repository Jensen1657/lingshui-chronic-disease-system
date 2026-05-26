import TableSkeleton from "@/components/TableSkeleton.vue"
<template>
  <div class="user-management">
    <div class="page-header">
      <h2>用户管理</h2>
      <el-button type="primary" @click="showCreateDialog">
        <el-icon><Plus /></el-icon> 新建账户
      </el-button>
    </div>

    <!-- 搜索筛选 -->
    <div class="search-bar">
      <el-input v-model="keyword" placeholder="搜索用户名/姓名" clearable style="width:200px" @keyup.enter="loadData" />
      <el-select v-model="filterRole" placeholder="账户类型" clearable style="width:150px" @change="loadData">
        <el-option label="管理员" value="ADMIN" />
        <el-option label="医生" value="DOCTOR" />
      </el-select>
      <el-select v-model="filterOrg" placeholder="所属机构" clearable filterable style="width:220px" @change="loadData">
        <el-option v-for="o in orgList" :key="o.org_code" :label="o.org_name" :value="o.org_code" />
      </el-select>
      <el-select v-model="filterStatus" placeholder="状态" clearable style="width:120px" @change="loadData">
        <el-option label="启用" :value="true" />
        <el-option label="禁用" :value="false" />
      </el-select>
      <el-button type="primary" @click="loadData">查询</el-button>
      <el-button @click="resetFilter">重置</el-button>
    </div>

    <!-- 用户列表 -->
      <el-table :data="users" v-loading="loading" stripe border style="width:100%">
      <el-table-column prop="username" label="用户名" width="120" />
      <el-table-column prop="real_name" label="姓名" width="100" />
      <el-table-column prop="org_name" label="所属机构" min-width="180" />
      <el-table-column prop="org_level" label="机构层级" width="140" align="center">
        <template #default="{row}">
          <el-tag :type="getLevelTagType(row.org_level)" size="small">{{ row.org_level }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="role_name" label="账户类型" width="110" align="center">
        <template #default="{row}">
          <el-tag :type="row.role_code === 'ADMIN' ? 'danger' : 'primary'" size="small">{{ row.role_name }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="is_active" label="状态" width="80" align="center">
        <template #default="{row}">
          <el-tag :type="row.is_active ? 'success' : 'danger'" size="small">{{ row.is_active ? '启用' : '禁用' }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="last_login_at" label="最后登录" width="170" />
      <el-table-column label="操作" width="260" fixed="right">
        <template #default="{row}">
          <el-button size="small" type="primary" link @click="showEditDialog(row)">编辑</el-button>
          <el-button size="small" :type="row.is_active ? 'warning' : 'success'" link @click="toggleStatus(row)">
            {{ row.is_active ? '禁用' : '启用' }}
          </el-button>
          <el-button size="small" type="warning" link @click="resetPwd(row)">重置密码</el-button>
          <el-button size="small" type="danger" link @click="deleteUser(row)" :disabled="row.username === currentUser">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 分页 -->
    <div class="pagination-wrapper">
      <el-pagination
        v-model:current-page="page"
        v-model:page-size="pageSize"
        :total="total"
        :page-sizes="[10,20,50]"
        layout="total,sizes,prev,pager,next"
        @size-change="loadData"
        @current-change="loadData"
      />
    </div>

    <!-- 新建/编辑对话框 -->
    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑用户' : '新建账户'" width="550px" destroy-on-close>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" :disabled="isEdit" placeholder="默认使用手机号码作为用户名" />
        </el-form-item>
        <el-form-item v-if="!isEdit" label="密码" prop="password">
          <el-input v-model="form.password" type="password" show-password placeholder="至少6位" />
        </el-form-item>
        <el-form-item label="姓名" prop="real_name">
          <el-input v-model="form.real_name" placeholder="真实姓名" />
        </el-form-item>
        <el-form-item label="账户类型" prop="role_code">
          <el-select v-model="form.role_code" :disabled="isEdit && form.role_code === 'ADMIN'" style="width:100%">
            <el-option v-if="isEdit && form.role_code === 'ADMIN'" label="管理员 (ADMIN)" value="ADMIN" />
            <el-option label="医生 (DOCTOR)" value="DOCTOR" />
          </el-select>
          <div class="form-tip" v-if="!isEdit">ℹ️ 医生账户只能查看/操作本机构数据</div>
        </el-form-item>
        <el-form-item label="所属机构" prop="org_code">
          <el-cascader
            v-model="form.org_code"
            :options="orgTreeOptions"
            :props="{value:'org_code',label:'org_name',children:'children',checkStrictly:true,emitPath:false}"
            filterable
            clearable
            placeholder="选择机构"
            style="width:100%"
          />
        </el-form-item>
        <el-form-item label="手机号">
          <el-input v-model="form.phone_enc" placeholder="输入手机号（将自动作为用户名）" @input="onPhoneInput" />
        </el-form-item>
        <el-form-item label="状态">
          <el-switch v-model="form.is_active" active-text="启用" inactive-text="禁用" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>

    <!-- 重置密码对话框 -->
    <el-dialog v-model="pwdDialogVisible" title="重置密码" width="400px">
      <el-form label-width="80px">
        <el-form-item label="新密码">
          <el-input v-model="newPassword" type="password" show-password placeholder="输入新密码（至少6位）" />
        </el-form-item>
        <el-form-item label="确认密码">
          <el-input v-model="confirmPassword" type="password" show-password placeholder="再次输入新密码" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="pwdDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="pwdSubmitting" @click="handleResetPwd">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { Plus } from '@element-plus/icons-vue'
import request from '@/api/request'

const loading = ref(false)
const submitting = ref(false)
const pwdSubmitting = ref(false)
const dialogVisible = ref(false)
const pwdDialogVisible = ref(false)
const isEdit = ref(false)
const users = ref<any[]>([])
const orgList = ref<any[]>([])
const orgTreeOptions = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)

const keyword = ref('')
const filterRole = ref('')
const filterOrg = ref('')
const filterStatus = ref<any>(null)

const currentUser = computed(() => {
  const u = localStorage.getItem('user')
  try { return JSON.parse(u)?.username || '' } catch { return '' }
})

const formRef = ref()
const form = reactive({
  username: '',
  password: '',
  real_name: '',
  role_code: 'DOCTOR',
  org_code: '',
  phone_enc: '',
  is_active: true,
})
const editUserId = ref('')
const newPassword = ref('')
const confirmPassword = ref('')

const rules = {
  username: [{ required: true, message: '请输入手机号作为用户名', trigger: 'blur' }, { pattern: /^1\d{10}$/, message: '请输入正确的11位手机号码', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }, { min:6, max:100, message: '6-100个字符', trigger: 'blur' }],
  real_name: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
  role_code: [{ required: true, message: '请选择账户类型', trigger: 'change' }],
  org_code: [{ required: true, message: '请选择所属机构', trigger: 'change' }],
}

function getLevelTagType(level: string) {
  const map: Record<string, string> = {'省级': 'info', '市县级': '', '乡镇卫生院/社区卫生服务中心': 'warning', '村卫生室': 'success'}
  return map[level] || ''
}

async function loadOrgs() {
  try {
    const res = await request.get('/v1/admin/orgs')
    orgList.value = res.flat || []
    orgTreeOptions.value = res.tree || []
  } catch(e) { console.error('加载机构失败', e) }
}

async function loadData() {
  loading.value = true
  try {
    const params: any = { page: page.value, page_size: pageSize.value }
    if (keyword.value) params.keyword = keyword.value
    if (filterRole.value) params.role_code = filterRole.value
    if (filterOrg.value) params.org_code = filterOrg.value
    if (filterStatus.value !== null && filterStatus.value !== '') params.is_active = filterStatus.value
    
    const res = await request.get('/v1/admin/users', { params })
    users.value = res.items || []
    total.value = res.total || 0
  } catch(e: any) {
    // 错误已由 request.ts 拦截器统一提示
  } finally {
    loading.value = false
  }
}

function resetFilter() {
  keyword.value = ''
  filterRole.value = ''
  filterOrg.value = ''
  filterStatus.value = null
  page.value = 1
  loadData()
}

function showCreateDialog() {
  isEdit.value = false
  Object.assign(form, { username:'', password:'', real_name:'', role_code:'DOCTOR', org_code:'', phone_enc:'', is_active:true })
  dialogVisible.value = true
}

function onPhoneInput(val: string) {
  // 新建时手机号自动同步为用户名
  if (!isEdit.value && !form.username) {
    form.username = val
  }
}

function showEditDialog(row: any) {
  isEdit.value = true
  editUserId.value = row.user_id
  Object.assign(form, {
    username: row.username,
    password: '',
    real_name: row.real_name,
    role_code: row.role_code,
    org_code: row.org_code,
    phone_enc: '',
    is_active: row.is_active,
  })
  dialogVisible.value = true
}

async function handleSubmit() {
  try {
    await formRef.value?.validate()
  } catch { return }
  
  submitting.value = true
  try {
    if (isEdit.value) {
      const data: any = { ...form }
      delete data.username
      delete data.password
      await request.put(`/v1/admin/users/${editUserId.value}`, data)
      ElMessage.success('更新成功')
    } else {
      await request.post('/v1/admin/users', form)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    loadData()
  } catch(e: any) {
    // 错误已由 request.ts 拦截器统一提示
  } finally {
    submitting.value = false
  }
}

async function toggleStatus(row: any) {
  const action = row.is_active ? '禁用' : '启用'
  try {
    await ElMessageBox.confirm(`确定要${action}用户 "${row.real_name}" 吗？`, '确认', { type: 'warning' })
    await request.patch(`/v1/admin/users/${row.user_id}/toggle-status`)
    ElMessage.success(`已${action}`)
    loadData()
  } catch(e: any) {
    if (e !== 'cancel') {
      // 错误已由 request.ts 拦截器统一提示
    }
  }
}

function resetPwd(row: any) {
  newPassword.value = ''
  confirmPassword.value = ''
  editUserId.value = row.user_id
  pwdDialogVisible.value = true
}

async function handleResetPwd() {
  if (!newPassword.value || newPassword.value.length < 6) {
    ElMessage.warning('请输入至少6位密码')
    return
  }
  if (newPassword.value !== confirmPassword.value) {
    ElMessage.error('两次密码不一致')
    return
  }
  pwdSubmitting.value = true
  try {
    await request.put(`/v1/admin/users/${editUserId.value}/reset-password`, null, {
      params: { new_password: newPassword.value }
    })
    ElMessage.success('密码重置成功')
    pwdDialogVisible.value = false
  } catch(e: any) {
    // 错误已由 request.ts 拦截器统一提示
  } finally {
    pwdSubmitting.value = false
  }
}

async function deleteUser(row: any) {
  try {
    await ElMessageBox.confirm(`确定要删除用户 "${row.real_name}" 吗？删除后该账户将被禁用。`, '确认删除', { type: 'error' })
    await request.delete(`/v1/admin/users/${row.user_id}`)
    ElMessage.success('已删除')
    loadData()
  } catch(e: any) {
    if (e !== 'cancel') {
      // 错误已由 request.ts 拦截器统一提示
    }
  }
}

onMounted(() => {
  loadOrgs()
  loadData()
})
</script>

<style scoped>
.user-management { padding: 0; }

.user-management :deep(.el-card) {
  border-radius: 14px !important;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0;
  font-size: 22px;
  font-weight: 700;
  color: var(--text-primary);
}

.search-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

.form-tip {
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 4px;
  line-height: 1.4;
}

/* 表格行 hover 效果 */
.user-management :deep(.el-table) {
  border-radius: 10px !important;
}

.user-management :deep(.el-dialog) {
  border-radius: 16px !important;
}
</style>
