import request from './request';

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: {
    username: string;
    real_name: string;
    role: string;
  };
}

export interface UserInfo {
  user_id?: string;
  username: string;
  real_name: string;
  role: string;
  org_code?: string;
  phone?: string;
  email?: string;
  is_active: boolean;
  created_at?: string;
}

/**
 * 用户登录
 */
export async function login(data: LoginRequest): Promise<LoginResponse> {
  return await request.post<LoginResponse>('/v1/auth/login', data);
}

/**
 * 获取当前用户信息
 */
export async function getCurrentUser(): Promise<UserInfo> {
  return await request.get<UserInfo>('/v1/auth/me');
}

/**
 * 退出登录
 */
export async function logout(): Promise<void> {
  await request.post('/v1/auth/logout');
}

/**
 * 刷新 Token
 */
export async function refreshToken(): Promise<LoginResponse> {
  return await request.post<LoginResponse>('/v1/auth/refresh');
}
