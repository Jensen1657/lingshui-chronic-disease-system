import request from './request';

export interface RiskAssessment {
  assessment_id: string;
  patient_id: string;
  patient_name: string;
  risk_score: number;
  risk_level: string;
  risk_factors: string[];
  manage_level: string;
  assigned_org: string;
  bp_assessment: string;
  bg_assessment: string;
  compliance_assessment: string;
  followup_frequency: string;
  need_up_referral: boolean;
  assessed_at: string;
  valid_until: string;
}

export interface RiskAssessmentCreate {
  patient_id: string;
  risk_score: number;
  risk_level: string;
  risk_factors?: string[];
  manage_level: string;
  assigned_org?: string;
  assigned_doctor?: string;
  bp_assessment?: string;
  bg_assessment?: string;
  compliance_assessment?: string;
  followup_frequency?: string;
  need_up_referral?: boolean;
  assessment_note?: string;
}

export interface RiskDashboard {
  total_patients: number;
  risk_distribution: Record<string, number>;
  unassessed_rate: number;
  high_risk_count: number;
  high_risk_rate: number;
  status: string;
  message: string;
}

export const riskApi = {
  getByPatient: (patientId: string) =>
    request.get<RiskAssessment & { has_assessment: boolean }>(`/risk-assessment/patient/${patientId}`),

  create: (data: RiskAssessmentCreate) =>
    request.post('/risk-assessment', data),

  batch: (patientIds: string[], autoStratify = true) =>
    request.post('/risk-assessment/batch', { patient_ids: patientIds, auto_stratify: autoStratify }),

  list: (params: { page?: number; page_size?: number; risk_level?: string; manage_level?: string; assigned_org?: string }) =>
    request.get<{ items: RiskAssessment[]; total: number; page: number; page_size: number }>('/risk-assessment/list', { params }),

  dashboard: (orgCode?: string) =>
    request.get<RiskDashboard>('/risk-assessment/dashboard', { params: { org_code: orgCode } }),
};