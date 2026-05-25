// 用户相关类型定义

// 用户角色枚举
export enum UserRole {
  VILLAGE_DOCTOR = 'village_doctor',        // 村卫生室医生
  TOWN_DOCTOR = 'town_doctor',               // 乡镇卫生院医生
  COUNTY_DOCTOR = 'county_doctor',           // 县级医院医生
  ADMIN = 'admin'                            // 管理中心管理员
}

// 用户信息
export interface User {
  id: string
  username: string
  name: string
  role: UserRole
  orgId: string
  orgName: string
  phone?: string
  avatar?: string
}

// 登录请求
export interface LoginRequest {
  username: string
  password: string
}

// 登录响应
export interface LoginResponse {
  token: string
  user: User
  expiresIn: number
}

// Token信息
export interface TokenInfo {
  accessToken: string
  refreshToken?: string
  expiresIn: number
  expiresAt: number
}
