export interface ReferralRecord {
  referral_id: string
  patient_id: string
  disease_code?: string
  referral_type: string
  
  // 申请信息
  apply_org_code: string
  apply_doctor?: string
  apply_at: string
  referral_reason?: string
  
  // 接收信息
  receive_org_code?: string
  receive_doctor?: string
  receive_at?: string
  
  // 资格校验
  is_eligible?: boolean
  match_criteria?: any
  reject_reason?: string
  
  // 状态
  status: string
  timeout_alert_sent: boolean
  completed_at?: string
  
  // 随访关联
  post_referral_fu_id?: string
  down_plan?: any
  
  created_at: string
  updated_at: string
}

export interface ReferralQuery {
  patient_id?: string
  referral_type?: string
  status?: string
  page?: number
  page_size?: number
}
