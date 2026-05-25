import request from './request'

// 审计日志类型
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

// 获取审计日志列表
export const getAuditLogs = async (params: AuditLogQuery = {}): Promise<{items: AuditLog[]; total: number}> => {
  const response = await request.get('/v1/audit-logs/logs', { params }) as any;
  return {
    items: response.items || [],
    total: response.total || 0,
  };
};

// 获取审计统计
export const getAuditStats = async (): Promise<AuditStats> => {
  try {
    const logsRes = await request.get('/v1/audit-logs/logs', { params: { page_size: 1 } }) as any;
    const total = logsRes.total || 0;
    
    // 尝试获取今日统计
    const todayRes = await request.get('/v1/audit-logs/logs', {
      params: {
        page_size: 100,
        start_date: new Date().toISOString().slice(0, 10),
      }
    }) as any;
    const todayLogs = todayRes.total || 0;

    // 敏感操作统计
    const sensitiveRes = await request.get('/v1/audit-logs/logs', {
      params: { page_size: 100, is_sensitive: 'Y' }
    }) as any;
    const sensitiveOps = sensitiveRes.total || 0;

    return {
      totalLogs: total,
      todayLogs,
      sensitiveOperations: sensitiveOps,
      activeUsers: 8, // 后续可从用户表获取
    };
  } catch {
    return {
      totalLogs: 0,
      todayLogs: 0,
      sensitiveOperations: 0,
      activeUsers: 0,
    };
  }
};
