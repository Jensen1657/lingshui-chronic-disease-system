// 急救联动类型定义（与后端 EmergencyAlertResponse 保持一致）
// 后端字段: alert_id, patient_id, alert_type, patient_history, medications, allergies,
//           vital_signs, target_org, target_dept, estimated_arrival, trigger_by, trigger_at, status, created_at

export interface EmergencyRecord {
  alert_id: string
  patient_id: string
  alert_type: string        // CHEST_PAIN | STROKE | HYPERTENSIVE_CRISIS | HYPOGLYCEMIA | HYPERGLYCEMIA | RESPIRATORY_FAILURE | OTHER
  patient_history?: string
  medications?: string
  allergies?: string
  vital_signs?: {
    consciousness?: string
    blood_pressure?: string
    heart_rate?: number
    respiratory_rate?: number
    body_temperature?: number
    spo2?: number
  }
  target_org?: string
  target_dept?: string
  estimated_arrival?: string
  trigger_by?: string
  trigger_at?: string
  status: string            // ACTIVATED | PROCESSING | COMPLETED | CANCELLED
  response_time?: string
  created_at: string
}

export interface EmergencyQuery {
  patient_id?: string
  alert_type?: string
  status?: string
  trigger_by?: string
  page?: number
  page_size?: number
}

export interface EmergencyCreate {
  patient_id: string
  alert_type: string
  patient_history?: string
  medications?: string
  allergies?: string
  vital_signs?: {
    consciousness?: string
    blood_pressure?: string
    heart_rate?: number
    respiratory_rate?: number
    body_temperature?: number
    spo2?: number
  }
  target_org?: string
  target_dept?: string
  estimated_arrival?: string
  trigger_by?: string
}

export interface EmergencyUpdate {
  patient_history?: string
  medications?: string
  allergies?: string
  vital_signs?: {
    consciousness?: string
    blood_pressure?: string
    heart_rate?: number
    respiratory_rate?: number
    body_temperature?: number
    spo2?: number
  }
  target_org?: string
  target_dept?: string
  estimated_arrival?: string
  status?: string
}
