import request from './request';

export interface EduTemplate {
  template_id: string;
  title: string;
  category: string;
  disease_code: string;
  risk_level: string;
  content_text: string;
  content_rich: string;
  media_urls: string[];
  tags: string[];
  usage_count: number;
  is_active: boolean;
  created_at: string;
}

export interface EduTemplateCreate {
  title: string;
  category: string;
  disease_code?: string;
  risk_level?: string;
  content_text: string;
  content_rich?: string;
  media_urls?: string[];
  tags?: string[];
}

export interface SendRecord {
  record_id: string;
  patient_id: string;
  template_id: string;
  sent_channel: string;
  sent_at: string;
  is_read: boolean;
  read_at: string;
  patient_feedback: string;
}

export interface HealthEduStats {
  total_sends: number;
  channel_stats: Record<string, number>;
  read_rate: number;
  read_count: number;
  feedback_rate: number;
  feedback_count: number;
  monthly_trend: { month: string; count: number }[];
  top_templates: { template_id: string; title: string; category: string; usage_count: number }[];
  category_stats: { category: string; template_count: number; usage_count: number }[];
}

export const healthEduApi = {
  templates: {
    list: (params: { page?: number; page_size?: number; category?: string; disease_code?: string; keyword?: string }) =>
      request.get<{ items: EduTemplate[]; total: number; page: number; page_size: number }>('/health-education/templates', { params }),
    get: (id: string) => request.get<EduTemplate>(`/health-education/templates/${id}`),
    create: (data: EduTemplateCreate) => request.post('/health-education/templates', data),
    update: (id: string, data: Partial<EduTemplateCreate>) => request.put(`/health-education/templates/${id}`, data),
  },
  send: {
    one: (data: { patient_id: string; template_id: string; sent_channel?: string }) =>
      request.post('/health-education/send', data),
    batch: (data: { patient_ids: string[]; template_id: string; sent_channel?: string }) =>
      request.post('/health-education/send/batch', data),
  },
  records: (params: { page?: number; page_size?: number; patient_id?: string; template_id?: string; is_read?: boolean }) =>
    request.get<{ items: SendRecord[]; total: number }>('/health-education/records', { params }),
  stats: () => request.get<HealthEduStats>('/health-education/stats'),
  categories: () => request.get<{ categories: { code: string; name: string }[] }>('/health-education/categories'),
};