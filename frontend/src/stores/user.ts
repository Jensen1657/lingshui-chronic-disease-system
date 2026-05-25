import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import * as authApi from '@/api/auth'

export interface User {
  user_id?: string
  username: string
  real_name: string
  role: string
  role_code?: string
  org_code?: string
  org_name?: string
  phone?: string
  email?: string
}

export const useUserStore = defineStore('user', () => {
  const user = ref<User | null>(null)
  const token = ref<string | null>(null)
  const loading = ref(false)

  // 计算属性
  const isLoggedIn = computed(() => !!token.value && !!user.value)
  const userRole = computed(() => user.value?.role_code || user.value?.role || '')
  const roleCode = computed(() => user.value?.role_code || user.value?.role || '')
  const realName = computed(() => user.value?.real_name || '')
  const username = computed(() => user.value?.username || '')
  const orgName = computed(() => user.value?.org_name || '')
  const isAdmin = computed(() => {
    const r = user.value?.role_code || user.value?.role || ''
    return r === 'ADMIN'
  })
  const isDoctor = computed(() => {
    const r = user.value?.role_code || user.value?.role || ''
    return r === 'DOCTOR'
  })
  const isNurse = computed(() => user.value?.role === 'NURSE')

  /**
   * 用户登录
   */
  async function login(username: string, password: string) {
    loading.value = true
    try {
      const res = await authApi.login({ username, password })
      
      // 保存 token 和用户信息（适配后端实际返回字段）
      token.value = res.access_token
      user.value = {
        username: res.user.username,
        real_name: res.user.real_name,
        role: res.user.role,
        role_code: res.user.role,
      }
      
      // 持久化到 localStorage
      localStorage.setItem('token', res.access_token)
      localStorage.setItem('refresh_token', res.refresh_token)
      localStorage.setItem('user', JSON.stringify(user.value))
      
      return res
    } finally {
      loading.value = false
    }
  }

  /**
   * 获取当前用户信息
   */
  async function fetchCurrentUser() {
    if (!token.value) return null
    
    try {
      const res = await authApi.getCurrentUser()
      user.value = res
      localStorage.setItem('user', JSON.stringify(res))
      return res
    } catch (error) {
      // 获取失败，清除状态
      logout()
      return null
    }
  }

  /**
   * 退出登录
   */
  async function logout() {
    try {
      // 调用后端退出接口
      await authApi.logout()
    } catch (error) {
      // 忽略退出接口错误
    } finally {
      // 清除状态
      token.value = null
      user.value = null
      localStorage.removeItem('token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('user')
    }
  }

  /**
   * 刷新 Token
   */
  async function refreshToken() {
    const savedRefreshToken = localStorage.getItem('refresh_token')
    if (!savedRefreshToken) {
      throw new Error('No refresh token')
    }
    
    try {
      const res = await authApi.refreshToken()
      token.value = res.access_token
      localStorage.setItem('token', res.access_token)
      return res
    } catch (error) {
      // 刷新失败，退出登录
      logout()
      throw error
    }
  }

  /**
   * 从 localStorage 恢复状态
   */
  function initFromStorage() {
    const savedToken = localStorage.getItem('token')
    const savedUser = localStorage.getItem('user')
    
    if (savedToken) {
      token.value = savedToken
    }
    
    if (savedUser) {
      try {
        user.value = JSON.parse(savedUser)
      } catch (error) {
        user.value = null
      }
    }
  }

  /**
   * 检查权限
   */
  function hasPermission(requiredRole: string | string[]): boolean {
    if (!user.value) return false
    
    const currentRole = user.value.role
    
    // 管理员拥有所有权限
    if (currentRole === 'ADMIN') return true
    
    if (Array.isArray(requiredRole)) {
      return requiredRole.includes(currentRole)
    }
    
    return currentRole === requiredRole
  }

  return {
    // 状态
    user,
    token,
    loading,
    
    // 计算属性
    isLoggedIn,
    userRole,
    roleCode,
    realName,
    username,
    orgName,
    isAdmin,
    isDoctor,
    isNurse,
    
    // 方法
    login,
    logout,
    fetchCurrentUser,
    refreshToken,
    initFromStorage,
    hasPermission
  }
})
