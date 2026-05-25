export interface Alert {
  alert_id: string
  patient_id?: string
  org_code?: string
  alert_type: string        // BP_HIGH/BP_LOW/BG_HIGH/MISS_FU等
  alert_level: string       // LOW/MEDIUM/HIGH/CRITICAL
  alert_title: string
  alert_content: string
  
  // 处理状态
  is_handled: boolean
  handled_by?: string
  handled_at?: string
  handle_note?: string
  
  created_at: string
}

export interface AlertQuery {
  patient_id?: string
  org_code?: string
  alert_type?: string
  alert_level?: string
  is_handled?: boolean
  start_date?: string
  end_date?: string
  page?: number
  page_size?: number
}
