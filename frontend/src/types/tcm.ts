// 中医管理类型定义（与后端 TcmResponse 保持一致）
// 后端字段: tcm_id, patient_id, disease_code, record_date, syndrome_type,
//           syndrome_name, syndrome_differentiation, tcm_disease,
//           inspection, auscultation, interrogation, palpation,
//           tongue_body, tongue_coating, tongue_coat, pulse, pulse_status,
//           treatment_method, prescription, tcm_prescription, herbs, tcm_herbs, patent_medicine,
//           acupuncture, moxibustion, tuina, other_therapy, therapy_type, therapy_note,
//           diet_therapy, exercise_therapy, emotion_therapy, lifestyle_guidance,
//           efficacy_evaluation, next_visit_date, visit_date, visit_doctor,
//           recorded_by, created_at

export interface TcmRecord {
  tcm_id: string
  patient_id: string
  disease_code?: string
  record_date: string
  syndrome_type?: string
  syndrome_name?: string
  syndrome_differentiation?: string
  tcm_disease?: string
  inspection?: string
  auscultation?: string
  interrogation?: string
  palpation?: string
  tongue_body?: string
  tongue_coating?: string
  tongue_coat?: string
  pulse?: string
  pulse_status?: string
  treatment_method?: string
  prescription?: string
  tcm_prescription?: string
  herbs?: string
  tcm_herbs?: Array<Record<string, any>>
  patent_medicine?: string
  acupuncture?: string
  moxibustion?: string
  tuina?: string
  other_therapy?: string
  therapy_type?: string[]
  therapy_note?: string
  diet_therapy?: string
  exercise_therapy?: string
  emotion_therapy?: string
  lifestyle_guidance?: string
  efficacy_evaluation?: string
  next_visit_date?: string
  visit_date?: string
  visit_doctor?: string
  recorded_by?: string
  created_at: string
}

export interface TcmCreate {
  patient_id: string
  disease_code?: string
  record_date?: string
  syndrome_type?: string
  syndrome_name?: string
  syndrome_differentiation?: string
  tcm_disease?: string
  inspection?: string
  auscultation?: string
  interrogation?: string
  palpation?: string
  tongue_body?: string
  tongue_coating?: string
  tongue_coat?: string
  pulse?: string
  pulse_status?: string
  treatment_method?: string
  prescription?: string
  tcm_prescription?: string
  herbs?: string
  tcm_herbs?: Array<Record<string, any>>
  patent_medicine?: string
  acupuncture?: string
  moxibustion?: string
  tuina?: string
  other_therapy?: string
  therapy_type?: string[]
  therapy_note?: string
  diet_therapy?: string
  exercise_therapy?: string
  emotion_therapy?: string
  lifestyle_guidance?: string
  efficacy_evaluation?: string
  next_visit_date?: string
  visit_date?: string
  visit_doctor?: string
  recorded_by?: string
}

export interface TcmUpdate {
  disease_code?: string
  record_date?: string
  syndrome_type?: string
  syndrome_name?: string
  syndrome_differentiation?: string
  tcm_disease?: string
  inspection?: string
  auscultation?: string
  interrogation?: string
  palpation?: string
  tongue_body?: string
  tongue_coating?: string
  tongue_coat?: string
  pulse?: string
  pulse_status?: string
  treatment_method?: string
  prescription?: string
  tcm_prescription?: string
  herbs?: string
  tcm_herbs?: Array<Record<string, any>>
  patent_medicine?: string
  acupuncture?: string
  moxibustion?: string
  tuina?: string
  other_therapy?: string
  therapy_type?: string[]
  therapy_note?: string
  diet_therapy?: string
  exercise_therapy?: string
  emotion_therapy?: string
  lifestyle_guidance?: string
  efficacy_evaluation?: string
  next_visit_date?: string
  visit_date?: string
  visit_doctor?: string
  recorded_by?: string
}

export interface TcmQuery {
  patient_id?: string
  disease_code?: string
  syndrome_type?: string
  start_date?: string
  end_date?: string
  recorded_by?: string
  page?: number
  page_size?: number
}
