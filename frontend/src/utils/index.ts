import { UserRole, RolePermissions, type Permission } from '@/types'

// Token管理
export const tokenUtils = {
  getToken(): string | null {
    return localStorage.getItem('token')
  },

  setToken(token: string): void {
    localStorage.setItem('token', token)
  },

  removeToken(): void {
    localStorage.removeItem('token')
  }
}

// 用户信息管理
export const userUtils = {
  getUser() {
    const userStr = localStorage.getItem('user')
    return userStr ? JSON.parse(userStr) : null
  },

  setUser(user: any): void {
    localStorage.setItem('user', JSON.stringify(user))
  },

  removeUser(): void {
    localStorage.removeItem('user')
  }
}

// 权限判断
export const permissionUtils = {
  hasPermission(code: string): boolean {
    const user = userUtils.getUser()
    if (!user) return false
    
    // 管理员拥有所有权限
    if (user.role === UserRole.ADMIN) return true
    
    const permissions = RolePermissions[user.role as UserRole] || []
    return permissions.some(p => p.code === code)
  },

  hasAnyPermission(codes: string[]): boolean {
    return codes.some(code => permissionUtils.hasPermission(code))
  },

  getRolePermissions(role: UserRole): Permission[] {
    return RolePermissions[role] || []
  }
}

// 格式化工具
export const formatUtils = {
  formatDate(date: string | Date, format: string = 'YYYY-MM-DD'): string {
    if (!date) return ''
    const d = new Date(date)
    const year = d.getFullYear()
    const month = String(d.getMonth() + 1).padStart(2, '0')
    const day = String(d.getDate()).padStart(2, '0')
    const hour = String(d.getHours()).padStart(2, '0')
    const minute = String(d.getMinutes()).padStart(2, '0')
    const second = String(d.getSeconds()).padStart(2, '0')
    
    return format
      .replace('YYYY', String(year))
      .replace('MM', month)
      .replace('DD', day)
      .replace('HH', hour)
      .replace('mm', minute)
      .replace('ss', second)
  },

  formatNumber(num: number, decimals: number = 2): string {
    if (num === null || num === undefined) return '-'
    return num.toFixed(decimals)
  },

  formatBP(systolic: number, diastolic: number): string {
    if (!systolic || !diastolic) return '-'
    return `${systolic}/${diastolic} mmHg`
  },

  formatBMI(bmi: number): string {
    if (!bmi) return '-'
    const value = bmi.toFixed(1)
    let category = ''
    if (bmi < 18.5) category = '偏瘦'
    else if (bmi < 24) category = '正常'
    else if (bmi < 28) category = '超重'
    else category = '肥胖'
    return `${value} (${category})`
  }
}

// 数据导出
export const exportUtils = {
  exportToExcel(data: any[], filename: string, headers?: string[]): void {
    // 简单的CSV导出
    if (!data.length) return
    
    const headers_ = headers || Object.keys(data[0])
    const csvContent = [
      headers_.join(','),
      ...data.map(row => headers_.map(h => row[h]).join(','))
    ].join('\n')
    
    const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.download = `${filename}_${formatUtils.formatDate(new Date(), 'YYYYMMDD')}.csv`
    link.click()
  },

  exportToPDF(content: string, filename: string): void {
    // 可以使用浏览器的打印功能
    const printContent = window.open('', '_blank')
    if (printContent) {
      printContent.document.write(content)
      printContent.document.close()
      printContent.print()
    }
  }
}

// 计算工具
export const calcUtils = {
  calculateBMI(weight: number, height: number): number | null {
    if (!weight || !height) return null
    const heightM = height / 100
    return weight / (heightM * heightM)
  },

  calculateNextFollowUpDate(lastDate: string, riskLevel: string): string {
    const date = new Date(lastDate)
    let interval: number
    
    if (riskLevel === 'high') interval = 28      // 高危每月一次
    else if (riskLevel === 'medium') interval = 56  // 中危每两月一次
    else interval = 84                       // 常规每三个月一次
    
    date.setDate(date.getDate() + interval)
    return formatUtils.formatDate(date)
  },

  evaluateRiskLevel(score: number): { level: string; color: string } {
    if (score >= 20) return { level: '高危', color: '#f56c6c' }
    if (score >= 10) return { level: '中危', color: '#e6a23c' }
    return { level: '低危', color: '#67c23a' }
  }
}

// 表单验证
export const validateUtils = {
  isValidIdCard(idCard: string): boolean {
    const reg = /(^\d{15}$)|(^\d{18}$)|(^\d{17}(\d|X|x)$)/
    return reg.test(idCard)
  },

  isValidPhone(phone: string): boolean {
    const reg = /^1[3-9]\d{9}$/
    return reg.test(phone)
  },

  isValidBP(systolic: number, diastolic: number): boolean {
    return systolic >= 60 && systolic <= 250 && diastolic >= 30 && diastolic <= 150 && systolic > diastolic
  }
}

//血压参考值
export const bpReference = {
  normal: { systolic: [90, 120], diastolic: [60, 80] },
  normalHigh: { systolic: [120, 140], diastolic: [80, 90] },
  hypertension: { systolic: [140, 999], diastolic: [90, 999] }
}

// 血糖参考值（mmol/L）
export const bloodSugarReference = {
  normal: { fasting: [3.9, 6.1], postprandial: [3.9, 7.8] },
  impairedFasting: { fasting: [6.1, 7.0], postprandial: [3.9, 7.8] },
  impairedGlucose: { fasting: [3.9, 6.1], postprandial: [7.8, 11.1] },
  diabetes: { fasting: [7.0, 999], postprandial: [11.1, 999] }
}

// 疾病名称格式化
export function formatDiseaseList(diseases: string[]): string {
  if (!diseases || diseases.length === 0) return ''
  
  const diseaseNames: Record<string, string> = {
    'HYPERTENSION': '高血压',
    'DIABETES': '糖尿病',
    'CORONARY_HEART_DISEASE': '冠心病',
    'STROKE': '脑卒中',
    'COPD': '慢阻肺',
    'CKD': '慢性肾脏病'
  }
  
  return diseases.map(d => diseaseNames[d] || d).join(', ')
}

// 风险等级颜色
export function getRiskLevelColor(level: string): string {
  const colors: Record<string, string> = {
    'LOW': 'success',
    'MEDIUM': 'warning',
    'HIGH': 'danger',
    'VERY_HIGH': 'danger'
  }
  return colors[level] || 'info'
}

// 计算年龄
export function calculateAge(birthDate: string): number {
  if (!birthDate) return 0
  const today = new Date()
  const birth = new Date(birthDate)
  let age = today.getFullYear() - birth.getFullYear()
  const monthDiff = today.getMonth() - birth.getMonth()
  if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birth.getDate())) {
    age--
  }
  return age
}