export interface SelfReport {
  id: string
  patient_id: string
  patient_name: string
  report_type: string
  content: string
  images: string[]
  created_at: string
}

export interface SelfReportQuery {
  patient_id?: string
  report_type?: string
  page?: number
  page_size?: number
}
