<template>
  <div class="app-layout">
    <!-- 顶部导航 -->
    <div class="layout-header">
      <div class="header-left">
        <h1 class="logo">陵水县人民医院慢病管理系统</h1>
      </div>
      <div class="header-right">
        <el-tag v-if="userStore.orgName" size="small" type="info" style="margin-right:12px">{{ userStore.orgName }}</el-tag>
        <el-tag :type="userStore.roleCode === 'ADMIN' ? 'danger' : 'primary'" size="small" style="margin-right:12px">
          {{ userStore.roleCode === 'ADMIN' ? '管理员' : '医生' }}
        </el-tag>
        <el-dropdown @command="handleCommand">
          <span class="user-info">
            <el-icon><User /></el-icon>
            <span class="username">{{ userStore.realName }}</span>
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="logout">退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>
    
    <!-- 侧边栏 -->
    <div class="layout-container">
      <aside class="sidebar">
        <el-menu
          :default-active="activeMenu"
          router
          class="sidebar-menu"
          background-color="#304156"
          text-color="#bfcbd9"
          active-text-color="#409eff"
        >
          <el-menu-item index="/dashboard">
            <el-icon><HomeFilled /></el-icon>
            <span>工作台</span>
          </el-menu-item>

          <el-menu-item index="/patients">
            <el-icon><User /></el-icon>
            <span>患者管理</span>
          </el-menu-item>

          <el-menu-item index="/followups">
            <el-icon><Document /></el-icon>
            <span>随访记录</span>
          </el-menu-item>

          <el-sub-menu index="referral-group">
            <template #title>
              <el-icon><Position /></el-icon>
              <span>双向转诊</span>
            </template>
            <el-menu-item index="/referrals">转诊列表</el-menu-item>
            <el-menu-item index="/county-township">县乡协同</el-menu-item>
          </el-sub-menu>

          <el-sub-menu index="assessment-group" v-if="showAssessmentMenu">
            <template #title>
              <el-icon><DataAnalysis /></el-icon>
              <span>评估与质控</span>
            </template>
            <el-menu-item index="/assessments">年度评估</el-menu-item>
            <el-menu-item index="/scoring-tools">评分工具</el-menu-item>
            <el-menu-item index="/quality-control">质量控制</el-menu-item>
          </el-sub-menu>

          <el-sub-menu index="alert-group">
            <template #title>
              <el-icon><Bell /></el-icon>
              <span>预警与急救</span>
            </template>
            <el-menu-item index="/alerts">预警中心</el-menu-item>
            <el-menu-item index="/emergency">急救联动</el-menu-item>
          </el-sub-menu>

          <el-sub-menu index="tcm-group">
            <template #title>
              <el-icon><FirstAidKit /></el-icon>
              <span>特色功能</span>
            </template>
            <el-menu-item index="/tcm">中医管理</el-menu-item>
            <el-menu-item index="/self-reports">患者自报</el-menu-item>
            <el-menu-item index="/reminders">随访提醒</el-menu-item>
            <el-menu-item index="/wechat">微信绑定</el-menu-item>
          </el-sub-menu>

          <el-menu-item index="/users/manage">
            <el-icon><Setting /></el-icon>
            <span>用户管理</span>
          </el-menu-item>

          <el-menu-item index="/audit-logs">
            <el-icon><Tickets /></el-icon>
            <span>操作审计</span>
          </el-menu-item>
        </el-menu>
      </aside>
      
      <!-- 主内容区 -->
      <main class="main-content">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import {
  HomeFilled, User, Position, Bell, DataAnalysis,
  Document, FirstAidKit, Setting, Tickets
} from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

const activeMenu = computed(() => route.path)
const isAdmin = computed(() => userStore.roleCode === 'ADMIN')
const showAssessmentMenu = computed(() => {
  const role = userStore.roleCode
  return role === 'ADMIN' || role === 'DOCTOR'
})

async function handleCommand(command: string) {
  if (command === 'logout') {
    try {
      await ElMessageBox.confirm('确定要退出登录吗？', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      })
      userStore.logout()
      router.push('/login')
    } catch {}
  }
}
</script>

<style scoped>
.app-layout {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.layout-header {
  height: 60px;
  background: linear-gradient(135deg, #1976d2 0%, #2196f3 100%);
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.header-left .logo {
  color: #fff;
  font-size: 20px;
  font-weight: 600;
  margin: 0;
}

.header-right .user-info {
  color: #fff;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
}

.username {
  font-weight: 500;
}

.layout-container {
  display: flex;
  flex: 1;
}

.sidebar {
  width: 220px;
  background: #304156;
  overflow-y: auto;
}

.sidebar-menu {
  border-right: none;
}

.sidebar-menu .el-menu-item {
  height: 50px;
  line-height: 50px;
}

.main-content {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  background: #f5f7fa;
}
</style>
