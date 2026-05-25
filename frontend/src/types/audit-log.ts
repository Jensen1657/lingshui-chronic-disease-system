// 审计日志类型（对应后端 API）
export interface AuditLog {
  log_id: string;
  timestamp: string;
  user_id: string;
  username: string;
  user_role?: string;
  action: string;
  resource: string;
  resource_id?: string;
  ip_address?: string;
  request_method?: string;
  request_path?: string;
  response_status?: number;
  details?: any;
  is_sensitive: string;
  session_id?: string;
}

export interface AuditLogQuery {
  skip?: number;
  limit?: number;
  user_id?: string;
  action?: string;
  resource?: string;
  is_sensitive?: string;
  start_date?: string;
  end_date?: string;
}

export interface AuditStats {
  totalLogs: number;
  todayLogs: number;
  sensitiveOperations: number;
  activeUsers: number;
}
