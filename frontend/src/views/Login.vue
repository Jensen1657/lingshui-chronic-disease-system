<template>
  <div class="login-container">
    <div class="login-bg">
      <div class="bg-circle c1"></div>
      <div class="bg-circle c2"></div>
      <div class="bg-circle c3"></div>
    </div>
    <div class="login-card">
      <div class="login-header">
        <div class="login-icon">🏥</div>
        <h2>慢病管理系统</h2>
        <p>陵水县人民医院</p>
      </div>

      <el-form ref="formRef" :model="form" :rules="rules" label-width="0" class="login-form">
        <el-form-item prop="username">
          <el-input
            v-model="form.username"
            placeholder="请输入用户名"
            size="large"
            clearable
            prefix-icon="User"
          />
        </el-form-item>

        <el-form-item prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="请输入密码"
            size="large"
            show-password
            prefix-icon="Lock"
            @keyup.enter="handleLogin"
          />
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            size="large"
            :loading="userStore.loading"
            class="login-btn"
            @click="handleLogin"
          >
            {{ userStore.loading ? '登录中...' : '登 录' }}
          </el-button>
        </el-form-item>
      </el-form>

      <div class="login-footer">
        <span>测试账号: admin / admin123</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

// 页面加载时自动清除旧缓存（解决浏览器缓存问题）
onMounted(() => {
  const t = route.query._t
  if (t) {
    // 清除所有 localStorage 数据
    localStorage.clear()
    console.log('[Login] 已清除缓存，版本:', t)
  }
})
const formRef = ref()

const form = reactive({
  username: '',
  password: ''
})

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度至少6位', trigger: 'blur' }
  ]
}

const handleLogin = async () => {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  try {
    await userStore.login(form.username, form.password)
    ElMessage.success('登录成功')
    
    // 跳转到首页（根路径）
    router.push('/')
  } catch (error: any) {
    console.error('登录失败:', error)
    ElMessage.error(error.response?.data?.detail || '登录失败，请检查用户名和密码')
  }
}
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #0F172A 0%, #1E3A5F 50%, #2E6BE6 100%);
  position: relative;
  overflow: hidden;
}

/* 背景装饰圆 */
.login-bg {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.bg-circle {
  position: absolute;
  border-radius: 50%;
  opacity: 0.08;
}

.c1 {
  width: 600px;
  height: 600px;
  background: #FFFFFF;
  top: -200px;
  right: -100px;
  animation: float 20s ease-in-out infinite;
}

.c2 {
  width: 400px;
  height: 400px;
  background: #409EFF;
  bottom: -150px;
  left: -100px;
  animation: float 15s ease-in-out infinite reverse;
}

.c3 {
  width: 200px;
  height: 200px;
  background: #67C23A;
  top: 40%;
  left: 15%;
  animation: float 12s ease-in-out infinite;
}

@keyframes float {
  0%, 100% { transform: translate(0, 0); }
  50% { transform: translate(30px, -30px); }
}

/* 登录卡片 */
.login-card {
  width: 420px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-radius: 20px;
  padding: 48px 40px 36px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3), 0 0 0 1px rgba(255, 255, 255, 0.1);
  position: relative;
  z-index: 1;
}

.login-header {
  text-align: center;
  margin-bottom: 36px;
}

.login-icon {
  font-size: 48px;
  margin-bottom: 16px;
  filter: drop-shadow(0 4px 8px rgba(0,0,0,0.1));
}

.login-header h2 {
  margin: 0 0 6px;
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: 1px;
}

.login-header p {
  margin: 0;
  font-size: 14px;
  color: var(--text-secondary);
  letter-spacing: 0.5px;
}

.login-form {
  margin-top: 8px;
}

.login-form :deep(.el-input__wrapper) {
  height: 48px;
  border-radius: 12px;
  padding: 0 16px;
  box-shadow: 0 0 0 1px #E5E5EA inset !important;
  transition: all 0.2s ease;
}

.login-form :deep(.el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px var(--primary-light) inset !important;
}

.login-form :deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 2px var(--primary) inset !important;
}

.login-form :deep(.el-input__inner) {
  font-size: 15px;
}

.login-form :deep(.el-form-item) {
  margin-bottom: 22px;
}

.login-btn {
  width: 100%;
  height: 48px !important;
  font-size: 16px !important;
  font-weight: 600 !important;
  border-radius: 12px !important;
  background: linear-gradient(135deg, var(--primary), var(--primary-light)) !important;
  border: none !important;
  letter-spacing: 2px;
  transition: all 0.3s ease !important;
}

.login-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(46, 107, 230, 0.4) !important;
}

.login-btn:active {
  transform: translateY(0);
}

.login-footer {
  text-align: center;
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px solid var(--border-color);
}

.login-footer span {
  font-size: 13px;
  color: var(--text-secondary);
}

/* 响应式 */
@media (max-width: 480px) {
  .login-card {
    width: 90%;
    padding: 32px 24px 28px;
  }
}
</style>
