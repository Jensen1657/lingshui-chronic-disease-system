import { createRouter, createWebHistory } from 'vue-router'

/**
 * 角色定义
 */
export type UserRole = 'ADMIN' | 'DOCTOR' | 'NURSE' | 'VIEWER'

/**
 * 路由元信息类型
 */
declare module 'vue-router' {
  interface RouteMeta {
    title?: string
    requiresAuth?: boolean
    roles?: UserRole[] // 允许访问的角色列表，undefined 表示所有角色都可访问
  }
}

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'Login',
      component: () => import('@/views/Login.vue'),
      meta: { title: '登录' }
    },
    {
      path: '/forbidden',
      name: 'Forbidden',
      component: () => import('@/views/Forbidden.vue'),
      meta: { title: '权限不足' }
    },
    {
      path: '/',
      name: 'Dashboard',
      component: () => import('@/views/Dashboard.vue'),
      meta: { title: '首页仪表盘', requiresAuth: true }
    },
    {
      path: '/patients',
      name: 'Patients',
      component: () => import('@/views/PatientList.vue'),
      meta: { title: '患者管理', requiresAuth: true, roles: ['ADMIN', 'DOCTOR', 'NURSE'] }
    },
    {
      path: '/patients/create',
      name: 'PatientCreate',
      component: () => import('@/views/PatientForm.vue'),
      meta: { title: '新建患者', requiresAuth: true, roles: ['ADMIN', 'DOCTOR', 'NURSE'] }
    },
    {
      path: '/patients/:id',
      name: 'PatientDetail',
      component: () => import('@/views/PatientDetail.vue'),
      meta: { title: '患者详情', requiresAuth: true, roles: ['ADMIN', 'DOCTOR', 'NURSE'] }
    },
    {
      path: '/patients/:id/edit',
      name: 'PatientEdit',
      component: () => import('@/views/PatientForm.vue'),
      meta: { title: '编辑患者', requiresAuth: true, roles: ['ADMIN', 'DOCTOR', 'NURSE'] }
    },
    {
      path: '/followups',
      name: 'Followups',
      component: () => import('@/views/FollowupList.vue'),
      meta: { title: '随访记录', requiresAuth: true, roles: ['ADMIN', 'DOCTOR', 'NURSE'] }
    },
    {
      path: '/followups/create',
      name: 'FollowupCreate',
      component: () => import('@/views/FollowupForm.vue'),
      meta: { title: '新建随访', requiresAuth: true, roles: ['ADMIN', 'DOCTOR', 'NURSE'] }
    },
    {
      path: '/followups/:id',
      name: 'FollowupDetail',
      component: () => import('@/views/FollowupDetail.vue'),
      meta: { title: '随访详情', requiresAuth: true, roles: ['ADMIN', 'DOCTOR', 'NURSE'] }
    },
    {
      path: '/followups/:id/edit',
      name: 'FollowupEdit',
      component: () => import('@/views/FollowupForm.vue'),
      meta: { title: '编辑随访', requiresAuth: true, roles: ['ADMIN', 'DOCTOR', 'NURSE'] }
    },
    {
      path: '/referrals',
      name: 'Referrals',
      component: () => import('@/views/ReferralList.vue'),
      meta: { title: '双向转诊', requiresAuth: true, roles: ['ADMIN', 'DOCTOR'] }
    },
    {
      path: '/referrals/create',
      name: 'ReferralCreate',
      component: () => import('@/views/ReferralForm.vue'),
      meta: { title: '新建转诊', requiresAuth: true, roles: ['ADMIN', 'DOCTOR'] }
    },
    {
      path: '/referrals/:id',
      name: 'ReferralDetail',
      component: () => import('@/views/ReferralDetail.vue'),
      meta: { title: '转诊详情', requiresAuth: true, roles: ['ADMIN', 'DOCTOR'] }
    },
    {
      path: '/referrals/:id/edit',
      name: 'ReferralEdit',
      component: () => import('@/views/ReferralForm.vue'),
      meta: { title: '编辑转诊', requiresAuth: true, roles: ['ADMIN', 'DOCTOR'] }
    },
    {
      path: '/assessments',
      name: 'Assessments',
      component: () => import('@/views/AssessmentList.vue'),
      meta: { title: '年度评估', requiresAuth: true, roles: ['ADMIN', 'DOCTOR'] }
    },
    {
      path: '/assessments/create',
      name: 'AssessmentCreate',
      component: () => import('@/views/AssessmentForm.vue'),
      meta: { title: '新建评估', requiresAuth: true, roles: ['ADMIN', 'DOCTOR'] }
    },
    {
      path: '/assessments/:id',
      name: 'AssessmentDetail',
      component: () => import('@/views/AssessmentDetail.vue'),
      meta: { title: '评估详情', requiresAuth: true, roles: ['ADMIN', 'DOCTOR'] }
    },
    {
      path: '/assessments/:id/edit',
      name: 'AssessmentEdit',
      component: () => import('@/views/AssessmentForm.vue'),
      meta: { title: '编辑评估', requiresAuth: true, roles: ['ADMIN', 'DOCTOR'] }
    },
    {
      path: '/alerts',
      name: 'Alerts',
      component: () => import('@/views/AlertList.vue'),
      meta: { title: '预警中心', requiresAuth: true }
    },
    {
      path: '/alerts/create',
      name: 'AlertCreate',
      component: () => import('@/views/AlertForm.vue'),
      meta: { title: '新建预警', requiresAuth: true }
    },
    {
      path: '/alerts/:id',
      name: 'AlertDetail',
      component: () => import('@/views/AlertDetail.vue'),
      meta: { title: '预警详情', requiresAuth: true }
    },
    {
      path: '/alerts/:id/edit',
      name: 'AlertEdit',
      component: () => import('@/views/AlertForm.vue'),
      meta: { title: '编辑预警', requiresAuth: true }
    },
    {
      path: '/tcm',
      name: 'Tcm',
      component: () => import('@/views/TcmList.vue'),
      meta: { title: '中医管理', requiresAuth: true, roles: ['ADMIN', 'DOCTOR', 'NURSE'] }
    },
    {
      path: '/tcm/create',
      name: 'TcmCreate',
      component: () => import('@/views/TcmForm.vue'),
      meta: { title: '新建中医档案', requiresAuth: true, roles: ['ADMIN', 'DOCTOR', 'NURSE'] }
    },
    {
      path: '/tcm/:id',
      name: 'TcmDetail',
      component: () => import('@/views/TcmDetail.vue'),
      meta: { title: '中医详情', requiresAuth: true, roles: ['ADMIN', 'DOCTOR', 'NURSE'] }
    },
    {
      path: '/tcm/:id/edit',
      name: 'TcmEdit',
      component: () => import('@/views/TcmForm.vue'),
      meta: { title: '编辑中医档案', requiresAuth: true, roles: ['ADMIN', 'DOCTOR', 'NURSE'] }
    },
    {
      path: '/emergency',
      name: 'Emergency',
      component: () => import('@/views/EmergencyList.vue'),
      meta: { title: '急救联动', requiresAuth: true, roles: ['ADMIN', 'DOCTOR'] }
    },
    {
      path: '/emergency/create',
      name: 'EmergencyCreate',
      component: () => import('@/views/EmergencyForm.vue'),
      meta: { title: '新建急救记录', requiresAuth: true, roles: ['ADMIN', 'DOCTOR'] }
    },
    {
      path: '/emergency/:id',
      name: 'EmergencyDetail',
      component: () => import('@/views/EmergencyDetail.vue'),
      meta: { title: '急救详情', requiresAuth: true, roles: ['ADMIN', 'DOCTOR'] }
    },
    {
      path: '/emergency/:id/edit',
      name: 'EmergencyEdit',
      component: () => import('@/views/EmergencyForm.vue'),
      meta: { title: '编辑急救记录', requiresAuth: true, roles: ['ADMIN', 'DOCTOR'] }
    },
    {
      path: '/self-reports',
      name: 'SelfReports',
      component: () => import('@/views/SelfReportList.vue'),
      meta: { title: '患者自报', requiresAuth: true, roles: ['ADMIN', 'DOCTOR', 'NURSE'] }
    },
    {
      path: '/self-reports/create',
      name: 'SelfReportCreate',
      component: () => import('@/views/SelfReportForm.vue'),
      meta: { title: '新建自报', requiresAuth: true, roles: ['ADMIN', 'DOCTOR', 'NURSE'] }
    },
    {
      path: '/self-reports/:id',
      name: 'SelfReportDetail',
      component: () => import('@/views/SelfReportDetail.vue'),
      meta: { title: '自报详情', requiresAuth: true, roles: ['ADMIN', 'DOCTOR', 'NURSE'] }
    },
    {
      path: '/self-reports/:id/edit',
      name: 'SelfReportEdit',
      component: () => import('@/views/SelfReportForm.vue'),
      meta: { title: '编辑自报', requiresAuth: true, roles: ['ADMIN', 'DOCTOR', 'NURSE'] }
    },
    {
      path: '/reminders',
      name: 'Reminders',
      component: () => import('@/views/ReminderList.vue'),
      meta: { title: '随访提醒', requiresAuth: true, roles: ['ADMIN', 'DOCTOR', 'NURSE'] }
    },
    {
      path: '/reminders/create',
      name: 'ReminderCreate',
      component: () => import('@/views/ReminderForm.vue'),
      meta: { title: '新建提醒', requiresAuth: true, roles: ['ADMIN', 'DOCTOR', 'NURSE'] }
    },
    {
      path: '/reminders/:id',
      name: 'ReminderDetail',
      component: () => import('@/views/ReminderDetail.vue'),
      meta: { title: '提醒详情', requiresAuth: true, roles: ['ADMIN', 'DOCTOR', 'NURSE'] }
    },
    {
      path: '/reminders/:id/edit',
      name: 'ReminderEdit',
      component: () => import('@/views/ReminderForm.vue'),
      meta: { title: '编辑提醒', requiresAuth: true, roles: ['ADMIN', 'DOCTOR', 'NURSE'] }
    },
    {
      path: '/wechat',
      name: 'Wechat',
      component: () => import('@/views/WechatList.vue'),
      meta: { title: '微信绑定', requiresAuth: true, roles: ['ADMIN', 'NURSE'] }
    },
    {
      path: '/wechat/create',
      name: 'WechatCreate',
      component: () => import('@/views/WechatForm.vue'),
      meta: { title: '新建微信绑定', requiresAuth: true, roles: ['ADMIN', 'NURSE'] }
    },
    {
      path: '/wechat/:id',
      name: 'WechatDetail',
      component: () => import('@/views/WechatDetail.vue'),
      meta: { title: '微信详情', requiresAuth: true, roles: ['ADMIN', 'NURSE'] }
    },
    {
      path: '/wechat/:id/edit',
      name: 'WechatEdit',
      component: () => import('@/views/WechatForm.vue'),
      meta: { title: '编辑微信绑定', requiresAuth: true, roles: ['ADMIN', 'NURSE'] }
    },
    {
      path: '/county-township',
      name: 'CountyTownship',
      component: () => import('@/views/CountyTownshipView.vue'),
      meta: { title: '县乡协同', requiresAuth: true, roles: ['ADMIN', 'DOCTOR'] }
    },
    {
      path: '/users/manage',
      name: 'UserManage',
      component: () => import('@/views/UserManagement.vue'),
      meta: { title: '用户管理', requiresAuth: true, roles: ['ADMIN'] }
    },
    {
      path: '/audit-logs',
      name: 'AuditLogs',
      component: () => import('@/views/AuditLogView.vue'),
      meta: { title: '操作审计', requiresAuth: true, roles: ['ADMIN'] }
    },
    {
      path: '/scoring-tools',
      name: 'ScoringTools',
      component: () => import('@/views/ScoringTools.vue'),
      meta: { title: '评分工具', requiresAuth: true, roles: ['ADMIN', 'DOCTOR'] }
    },
    {
      path: '/quality-control',
      name: 'QualityControl',
      component: () => import('@/views/QualityControl.vue'),
      meta: { title: '质量控制', requiresAuth: true, roles: ['ADMIN', 'DOCTOR'] }
    }
  ]
})

router.beforeEach((to, _from, next) => {
  // 设置页面标题
  document.title = (to.meta.title as string) || '慢性病管理系统'

  // 登录页不需要验证
  if (to.path === '/login') {
    // 如果已登录，直接跳转首页
    const token = localStorage.getItem('token')
    if (token && !isTokenExpired(token)) {
      next('/')
      return
    }
    next()
    return
  }

  // 需要认证的页面
  if (to.meta.requiresAuth) {
    const token = localStorage.getItem('token')
    const userStr = localStorage.getItem('user')
    
    // 未登录
    if (!token) {
      next('/login')
      return
    }
    
    // Token 已过期
    if (isTokenExpired(token)) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      next('/login')
      return
    }
    
    // 角色权限检查
    const requiredRoles = to.meta.roles
    if (requiredRoles && requiredRoles.length > 0) {
      let userRole: UserRole | null = null
      
      if (userStr) {
        try {
          const user = JSON.parse(userStr)
          userRole = user.role_code || user.role || null
        } catch (e) {
          console.error('解析用户信息失败:', e)
        }
      }
      
      // 用户角色不在允许列表中
      if (!userRole || !requiredRoles.includes(userRole)) {
        // 无权限，跳转到 403 页面
        console.warn(`权限不足: 需要 ${requiredRoles.join('/')} 角色，当前角色: ${userRole}`)
        next(`/forbidden?roles=${requiredRoles.join(',')}`)
        return
      }
    }
  }
  
  next()
})

/**
 * 检查 JWT Token 是否过期
 */
function isTokenExpired(token: string): boolean {
  try {
    // JWT 格式: header.payload.signature
    const parts = token.split('.')
    if (parts.length !== 3) {
      return true
    }
    
    // 解码 payload
    const payload = JSON.parse(atob(parts[1]))
    
    // 检查 exp 字段（过期时间戳，秒）
    if (!payload.exp) {
      return false // 没有 exp 字段，认为不过期
    }
    
    // 当前时间（秒）
    const now = Math.floor(Date.now() / 1000)
    
    // 过期时间早于当前时间 = 已过期
    return payload.exp < now
  } catch (e) {
    // 解析失败，认为已过期
    return true
  }
}

/**
 * 检查用户是否有权限访问指定路由
 */
export function hasRoutePermission(role: UserRole, requiredRoles?: UserRole[]): boolean {
  if (!requiredRoles || requiredRoles.length === 0) {
    return true
  }
  return requiredRoles.includes(role)
}

export default router
