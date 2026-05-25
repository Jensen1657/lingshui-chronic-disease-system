<template>
  <!-- 登录页不显示布局 -->
  <div v-if="isLoginPage" class="login-page-wrapper">
    <router-view />
  </div>
  <el-container v-else class="layout-container">
    <!-- 侧边栏 -->
    <el-aside :width="isCollapse ? '64px' : '240px'" class="sidebar">
      <div class="logo" @click="$router.push('/')">
        <div class="logo-icon">🏥</div>
        <transition name="fade">
          <div v-if="!isCollapse" class="logo-text">
            <h2>慢病管理系统</h2>
            <p>陵水县人民医院</p>
          </div>
        </transition>
      </div>
      <el-menu
        :default-active="activeMenu"
        :collapse="isCollapse"
        router
        background-color="transparent"
        text-color="rgba(255,255,255,0.65)"
        active-text-color="#FFFFFF"
        class="sidebar-menu"
      >
        <el-menu-item index="/">
          <span>📊 首页仪表盘</span>
        </el-menu-item>
        
        <el-menu-item v-if="canAccess(['ADMIN', 'DOCTOR', 'NURSE'])" index="/patients">
          <span>👥 患者管理</span>
        </el-menu-item>
        
        <el-menu-item v-if="canAccess(['ADMIN', 'DOCTOR', 'NURSE'])" index="/followups">
          <span>📋 随访记录</span>
        </el-menu-item>
        
        <el-menu-item v-if="canAccess(['ADMIN', 'DOCTOR'])" index="/referrals">
          <span>🔄 双向转诊</span>
        </el-menu-item>
        
        <el-menu-item v-if="canAccess(['ADMIN', 'DOCTOR'])" index="/assessments">
          <span>📝 年度评估</span>
        </el-menu-item>
        
        <el-menu-item index="/alerts">
          <span>🔔 预警中心</span>
        </el-menu-item>
        
        <el-sub-menu v-if="canAccess(['ADMIN', 'DOCTOR', 'NURSE'])" index="tcm">
          <template #title><span>🌿 中医管理</span></template>
          <el-menu-item index="/tcm">中医档案</el-menu-item>
        </el-sub-menu>
        
        <el-sub-menu v-if="canAccess(['ADMIN', 'DOCTOR'])" index="emergency">
          <template #title><span>🚑 急救联动</span></template>
          <el-menu-item index="/emergency">急救记录</el-menu-item>
        </el-sub-menu>
        
        <el-menu-item v-if="canAccess(['ADMIN', 'DOCTOR', 'NURSE'])" index="/self-reports">
          <span>📱 患者自报</span>
        </el-menu-item>
        
        <el-menu-item v-if="canAccess(['ADMIN', 'DOCTOR', 'NURSE'])" index="/reminders">
          <span>⏰ 随访提醒</span>
        </el-menu-item>
        
        <el-menu-item v-if="canAccess(['ADMIN', 'NURSE'])" index="/wechat">
          <span>💬 微信绑定</span>
        </el-menu-item>
        
        <el-menu-item v-if="canAccess(['ADMIN', 'DOCTOR'])" index="/county-township">
          <span>🏥 县乡协同</span>
        </el-menu-item>
        
        <el-menu-item v-if="canAccess(['ADMIN', 'DOCTOR'])" index="/scoring-tools">
          <span>⭐ 评分工具</span>
        </el-menu-item>
        
        <el-menu-item v-if="canAccess(['ADMIN', 'DOCTOR'])" index="/quality-control">
          <span>✅ 质量控制</span>
        </el-menu-item>
        
        <el-menu-item v-if="canAccess(['ADMIN'])" index="/users/manage">
          <span>👤 用户管理</span>
        </el-menu-item>
        
        <el-menu-item v-if="canAccess(['ADMIN'])" index="/audit-logs">
          <span>📜 操作审计</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <!-- 主内容区 -->
    <el-container>
      <el-header class="header">
        <div class="header-left">
          <button class="collapse-btn" @click="isCollapse = !isCollapse">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
              <line x1="3" y1="6" x2="21" y2="6"/>
              <line x1="3" y1="12" x2="21" y2="12"/>
              <line x1="3" y1="18" x2="21" y2="18"/>
            </svg>
          </button>
          <span class="breadcrumb">{{ currentPageTitle }}</span>
        </div>
        <GlobalSearch />
        <div class="header-right">
          <div class="user-info">
            <div class="user-avatar">{{ userName.charAt(0) }}</div>
            <div class="user-detail">
              <span class="user-name">{{ userName }}</span>
              <span class="role-badge" :class="'role-' + userRole.toLowerCase()">{{ roleLabel }}</span>
            </div>
          </div>
          <button class="logout-btn" @click="handleLogout" title="退出登录">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
              <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/>
              <polyline points="16 17 21 12 16 7"/>
              <line x1="21" y1="12" x2="9" y2="12"/>
            </svg>
          </button>
        </div>
      </el-header>
      <el-main class="main-content">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import GlobalSearch from '@/components/GlobalSearch.vue'

type UserRole = 'ADMIN' | 'DOCTOR' | 'NURSE' | 'VIEWER'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()
const isCollapse = ref(false)

const isLoginPage = computed(() => route.path === '/login')
const activeMenu = computed(() => route.path)
const userName = computed(() => userStore.realName || '用户')
const userRole = computed(() => userStore.userRole as UserRole)

// 页面标题映射
const pageTitles: Record<string, string> = {
  '/': '首页仪表盘',
  '/patients': '患者管理',
  '/followups': '随访记录',
  '/referrals': '双向转诊',
  '/assessments': '年度评估',
  '/alerts': '预警中心',
  '/tcm': '中医管理',
  '/emergency': '急救联动',
  '/self-reports': '患者自报',
  '/reminders': '随访提醒',
  '/wechat': '微信绑定',
  '/county-township': '县乡协同',
  '/scoring-tools': '评分工具',
  '/quality-control': '质量控制',
  '/users/manage': '用户管理',
  '/audit-logs': '操作审计',
}

const currentPageTitle = computed(() => pageTitles[route.path] || '慢病管理系统')

// 角色显示标签
const roleLabel = computed(() => {
  const labels: Record<UserRole, string> = {
    'ADMIN': '管理员',
    'DOCTOR': '医生',
    'NURSE': '护士',
    'VIEWER': '访客'
  }
  return labels[userRole.value] || '用户'
})

// 初始化用户状态
onMounted(() => {
  userStore.initFromStorage()
})

// 检查是否有权限访问
function canAccess(allowedRoles: UserRole[]): boolean {
  if (userRole.value === 'ADMIN') return true
  return allowedRoles.includes(userRole.value)
}

async function handleLogout() {
  await userStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.layout-container {
  height: 100vh;
}

/* ============ 侧边栏 ============ */
.sidebar {
  background: var(--bg-sidebar);
  transition: width 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  overflow-x: hidden;
  overflow-y: auto;
  border-right: none;
}

.sidebar::-webkit-scrollbar {
  width: 4px;
}

.sidebar::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.15);
  border-radius: 2px;
}

.logo {
  height: 68px;
  display: flex;
  align-items: center;
  padding: 0 16px;
  gap: 12px;
  cursor: pointer;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  overflow: hidden;
  white-space: nowrap;
}

.logo-icon {
  font-size: 28px;
  flex-shrink: 0;
  filter: drop-shadow(0 2px 4px rgba(0,0,0,0.2));
}

.logo-text h2 {
  margin: 0;
  font-size: 15px;
  font-weight: 700;
  color: #FFFFFF;
  letter-spacing: 0.5px;
}

.logo-text p {
  margin: 2px 0 0;
  font-size: 11px;
  color: rgba(255, 255, 255, 0.45);
  letter-spacing: 0.3px;
}

.sidebar-menu {
  border-right: none !important;
  padding: 8px;
}

.sidebar-menu .el-menu-item,
.sidebar-menu .el-sub-menu :deep(.el-sub-menu__title) {
  border-radius: 8px !important;
  margin: 2px 0 !important;
  height: 44px !important;
  line-height: 44px !important;
  font-size: 14px !important;
  transition: all 0.2s ease !important;
}

.sidebar-menu .el-menu-item:hover,
.sidebar-menu .el-sub-menu :deep(.el-sub-menu__title:hover) {
  background: rgba(255, 255, 255, 0.08) !important;
}

.sidebar-menu .el-menu-item.is-active {
  background: var(--primary) !important;
  color: #FFFFFF !important;
  font-weight: 600 !important;
  box-shadow: 0 4px 12px rgba(46, 107, 230, 0.4);
}

.sidebar-menu .el-sub-menu .el-menu-item {
  padding-left: 52px !important;
  font-size: 13px !important;
}

/* 折叠态 */
.sidebar-menu.el-menu--collapse .el-menu-item {
  padding: 0 !important;
  text-align: center;
}

/* ============ 顶部栏 ============ */
.header {
  background: #FFFFFF;
  border-bottom: 1px solid var(--border-color);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  height: 60px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.03);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.collapse-btn {
  background: none;
  border: none;
  cursor: pointer;
  padding: 6px;
  border-radius: 6px;
  color: var(--text-secondary);
  transition: all 0.2s;
  display: flex;
  align-items: center;
}

.collapse-btn:hover {
  background: var(--bg-hover);
  color: var(--text-primary);
}

.breadcrumb {
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.user-avatar {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: linear-gradient(135deg, var(--primary), var(--primary-light));
  color: #FFFFFF;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 15px;
  font-weight: 700;
}

.user-detail {
  display: flex;
  flex-direction: column;
  line-height: 1.3;
}

.user-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.role-badge {
  font-size: 11px;
  font-weight: 600;
  padding: 1px 8px;
  border-radius: 4px;
  display: inline-block;
  width: fit-content;
}

.role-badge.role-admin {
  background: #FFF3E0;
  color: #E65100;
}

.role-badge.role-doctor {
  background: #E8F0FE;
  color: var(--primary);
}

.role-badge.role-nurse {
  background: #E8F5E9;
  color: #2E7D32;
}

.role-badge.role-viewer {
  background: #F5F5F5;
  color: #616161;
}

.logout-btn {
  background: none;
  border: 1px solid var(--border-color);
  cursor: pointer;
  padding: 8px;
  border-radius: 8px;
  color: var(--text-secondary);
  transition: all 0.2s;
  display: flex;
  align-items: center;
}

.logout-btn:hover {
  background: #FFF0F0;
  border-color: #FFCDD2;
  color: var(--danger);
}

/* ============ 主内容区 ============ */
.main-content {
  background: var(--bg-page);
  padding: 24px;
  overflow-y: auto;
}

.login-page-wrapper {
  min-height: 100vh;
}

/* ============ 过渡动画 ============ */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
