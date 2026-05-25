export interface FollowupRecord {
  followup_id: string
  patient_id: string
  disease_code: string
  followup_type: string
  followup_date: string
  followup_no: number
  
  // 生理指标
  bp_systolic?: number
  bp_diastolic?: number
  fbg?: string
  pbg?: string
  hba1c?: string
  ldl_c?: string
  hdl_c?: string
  tc?: string
  tg?: string
  weight?: string
  bmi?: string
  heart_rate?: number
  
  // 随访信息
  medication_adherence?: string
  is_controlled: boolean
  symptoms?: string
  signs?: string
  medication_changed?: boolean
  medication_note?: string
  next_followup_date?: string
  
  // 审计信息
  performed_by: string
  org_code: string
  is_audited: boolean
  audited_by?: string
  audited_at?: string
  audit_note?: string
  
  created_at: string
  updated_at: string
}

export interface FollowupQuery {
  patient_id?: string
  disease_code?: string
  followup_type?: string
  start_date?: string
  end_date?: string
  performed_by?: string
  org_code?: string
  is_controlled?: boolean
  is_audited?: boolean
  page?: number
  page_size?: number
}
