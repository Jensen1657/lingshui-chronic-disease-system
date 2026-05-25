// 随访提醒类型定义（与后端 ReminderResponse 保持一致）
// 后端字段: reminder_id, patient_id, disease_code, plan_date, plan_type, channel, status, is_sent, sent_at, created_at

export interface ReminderRecord {
  reminder_id: string
  patient_id: string
  disease_code?: string
  plan_date: string
  plan_type: string  // FOLLOWUP | ASSESSMENT | EXAM
  channel?: string   // SMS | WECHAT | APP_PUSH
  status: string     // PENDING | SENT | FAILED
  is_sent: boolean
  sent_at?: string
  created_at: string
}

export interface ReminderCreate {
  patient_id: string
  disease_code?: string
  plan_date: string
  plan_type: string
  channel?: string
  status?: string
}

export interface ReminderUpdate {
  plan_date?: string
  plan_type?: string
  channel?: string
  status?: string
  is_sent?: boolean
  sent_at?: string
}

export interface ReminderQuery {
  patient_id?: string
  disease_code?: string
  plan_type?: string
  channel?: string
  status?: string
  is_sent?: boolean
  page?: number
  page_size?: number
}
