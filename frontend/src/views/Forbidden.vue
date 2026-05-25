<template>
  <div class="forbidden-container">
    <div class="forbidden-content">
      <div class="error-code">403</div>
      <div class="error-icon">🔒</div>
      <h1 class="error-title">权限不足</h1>
      <p class="error-message">
        抱歉，您没有权限访问此页面。请联系管理员获取相应权限。
      </p>
      <div class="error-actions">
        <el-button type="primary" @click="goHome">返回首页</el-button>
        <el-button @click="goBack">返回上一页</el-button>
      </div>
      <div class="error-info" v-if="userInfo">
        <el-divider />
        <p><strong>当前用户：</strong>{{ userInfo.username }}</p>
        <p><strong>角色：</strong>{{ roleLabel }}</p>
        <p><strong>需要角色：</strong>{{ requiredRolesText }}</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const userInfo = computed(() => userStore.user)
const userRole = computed(() => userStore.userRole)

const roleLabels: Record<string, string> = {
  ADMIN: '管理员',
  DOCTOR: '医生',
  NURSE: '护士',
  VIEWER: '访客'
}

const roleLabel = computed(() => roleLabels[userRole.value] || userRole.value)

const requiredRolesText = computed(() => {
  const roles = route.query.roles as string
  if (roles) {
    return roles.split(',').map(r => roleLabels[r] || r).join('、')
  }
  return '未知'
})

const goHome = () => {
  router.push('/')
}

const goBack = () => {
  router.back()
}
</script>

<style scoped>
.forbidden-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.forbidden-content {
  background: white;
  border-radius: 16px;
  padding: 60px 80px;
  text-align: center;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  max-width: 600px;
  width: 100%;
}

.error-code {
  font-size: 120px;
  font-weight: bold;
  color: #f56c6c;
  line-height: 1;
  margin-bottom: 20px;
  text-shadow: 4px 4px 0 rgba(245, 108, 108, 0.2);
}

.error-icon {
  font-size: 60px;
  margin-bottom: 20px;
}

.error-title {
  font-size: 28px;
  color: #303133;
  margin-bottom: 16px;
  font-weight: 600;
}

.error-message {
  font-size: 16px;
  color: #606266;
  margin-bottom: 32px;
  line-height: 1.6;
}

.error-actions {
  display: flex;
  gap: 16px;
  justify-content: center;
}

.error-info {
  margin-top: 32px;
  text-align: left;
  color: #909399;
  font-size: 14px;
}

.error-info p {
  margin: 8px 0;
}

.error-info strong {
  color: #606266;
}

@media (max-width: 600px) {
  .forbidden-content {
    padding: 40px 30px;
  }

  .error-code {
    font-size: 80px;
  }

  .error-title {
    font-size: 24px;
  }

  .error-actions {
    flex-direction: column;
  }
}
</style>
