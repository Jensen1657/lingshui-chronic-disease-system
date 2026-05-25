export interface Assessment {
  assessment_id: string
  patient_id: string
  disease_code: string
  assessment_year: number
  
  // 控制率指标
  bp_controlled_rate?: number      // 血压控制率
  bg_controlled_rate?: number      // 血糖控制率
  lipid_controlled_rate?: number   // 血脂控制率
  followup_completion_rate?: number // 随访完成率
  
  // 检查项目
  eye_exam_done?: boolean          // 眼底检查
  foot_exam_done?: boolean         // 足部检查
  echo_done?: boolean              // 心脏超声
  
  // 报告
  report_content?: string
  report_url?: string
  
  assessed_by?: string
  assessed_at?: string
  created_at: string
}

export interface AssessmentQuery {
  patient_id?: string
  disease_code?: string
  assessment_year?: number
  eye_exam_done?: boolean
  foot_exam_done?: boolean
  page?: number
  page_size?: number
}
