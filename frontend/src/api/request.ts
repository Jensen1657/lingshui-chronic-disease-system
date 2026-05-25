import axios, { AxiosInstance, AxiosResponse, InternalAxiosRequestConfig } from 'axios';
import { ElMessage } from 'element-plus';

const request: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Token 刷新状态
let isRefreshing = false;
let refreshSubscribers: Array<(token: string) => void> = [];

// 订阅 token 刷新
function subscribeTokenRefresh(cb: (token: string) => void) {
  refreshSubscribers.push(cb);
}

// 通知所有订阅者
function onRefreshed(token: string) {
  refreshSubscribers.forEach(cb => cb(token));
  refreshSubscribers = [];
}

// 刷新 token
async function refreshAccessToken(): Promise<string | null> {
  const refreshToken = localStorage.getItem('refresh_token');
  if (!refreshToken) {
    return null;
  }
  
  try {
    const response = await axios.post(
      `${import.meta.env.VITE_API_BASE_URL || '/api'}/v1/auth/refresh`,
      {},
      {
        headers: {
          'Authorization': `Bearer ${refreshToken}`,
          'Content-Type': 'application/json'
        }
      }
    );
    const newToken = response.data.access_token;
    localStorage.setItem('token', newToken);
    return newToken;
  } catch (error) {
    // 刷新失败，清除所有 token
    localStorage.removeItem('token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    return null;
  }
}

// 请求拦截器
request.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器
request.interceptors.response.use(
  (response: AxiosResponse) => {
    // 后端直接返回数据，不需要额外处理
    return response.data;
  },
  async (error) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };
    
    // 处理 HTTP 错误
    if (error.response) {
      const status = error.response.status;

      if (status === 401) {
        // 如果是登录请求失败，直接提示
        if (originalRequest.url?.includes('/auth/login')) {
          ElMessage.error('用户名或密码错误');
        }
        
        // 尝试刷新 token（非登录请求）
        if (!originalRequest.url?.includes('/auth/login') && !originalRequest._retry) {
          originalRequest._retry = true;
          
          if (isRefreshing) {
            return new Promise((resolve) => {
              subscribeTokenRefresh((token: string) => {
                originalRequest.headers.Authorization = `Bearer ${token}`;
                resolve(request(originalRequest));
              });
            });
          }
          
          isRefreshing = true;
          const newToken = await refreshAccessToken();
          isRefreshing = false;
          
          if (newToken) {
            originalRequest.headers.Authorization = `Bearer ${newToken}`;
            onRefreshed(newToken);
            return request(originalRequest);
          }
        }
        
        // Token 过期或刷新失败
        localStorage.removeItem('token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user');
        ElMessage.error('登录已过期，请重新登录');
        if (window.location.pathname !== '/login') {
          window.location.href = '/login';
        }
      }
      // 其他错误（403/404/422/5xx）由各页面 catch 自行处理，避免双重提示
    }
    return Promise.reject(error);
  }
);

// 拦截器已提取 response.data，重写类型让调用方直接拿到 data
type RequestInstance = {
  get<T = any>(url: string, config?: any): Promise<T>
  post<T = any>(url: string, data?: any, config?: any): Promise<T>
  put<T = any>(url: string, data?: any, config?: any): Promise<T>
  delete<T = any>(url: string, config?: any): Promise<T>
}

export default request as unknown as RequestInstance;
