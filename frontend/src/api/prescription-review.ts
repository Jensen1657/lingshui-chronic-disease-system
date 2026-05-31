import request from './request';

export interface RxReview {
  review_id: string;
  medication_id: string;
  patient_id: string;
  patient_name: string;
  review_type: string;
  original_dosage: string;
  original_frequency: string;
  original_drug: string;
  suggested_dosage: string;
  suggested_frequency: string;
  suggested_drug: string;
  review_reason: string;
  review_result: string;
  reviewed_by: string;
  reviewer_name: string;
  reviewer_org: string;
  prescribed_by: string;
  prescriber_name: string;
  is_applied: boolean;
  applied_at: string;
  reviewed_at: string;
  notes: string;
}

export interface RxReviewCreate {
  medication_id: string;
  patient_id: string;
  review_type?: string;
  suggested_dosage?: string;
  suggested_frequency?: string;
  suggested_drug?: string;
  review_reason?: string;
  review_result: string;
  prescribed_by?: string;
  notes?: string;
}

export interface RxReviewStats {
  total_reviews: number;
  approved: number;
  adjusted: number;
  rejected: number;
  applied_count: number;
  adoption_rate: number;
}

export interface AIRecommendation {
  type: string;           // ADD / WARNING
  disease_code?: string;
  drug_class?: string;
  suggested_drugs?: string[];
  reason?: string;
  confidence?: number;
  evidence_level?: string;
  severity?: string;     // HIGH / MEDIUM / LOW
  message?: string;
}

export interface AIRecommendationResult {
  patient_id: string;
  current_medications: any[];
  recommendations: AIRecommendation[];
  warnings: AIRecommendation[];
  summary: string;
  total_warnings: number;
  total_recommendations: number;
}

export interface ManualAssessRequest {
  patient_id: string;
  drug_name: string;
  dosage: string;
  frequency: string;
  duration?: string;
  review_reason?: string;
  notes?: string;
}

export const rxReviewApi = {
  list: (params: { page?: number; page_size?: number; patient_id?: string; review_result?: string; is_applied?: boolean }) =>
    request.get<{ items: RxReview[]; total: number; page: number; page_size: number }>('/prescription-reviews', { params }),

  create: (data: RxReviewCreate) => request.post('/prescription-reviews', data),

  apply: (reviewId: string) => request.put(`/prescription-reviews/${reviewId}/apply`),

  stats: (orgCode?: string) => request.get<RxReviewStats>('/prescription-reviews/stats', { params: { org_code: orgCode } }),

  aiRecommend: (patientId: string) =>
    request.post<AIRecommendationResult>('/prescription-reviews/ai/recommend', undefined, { params: { patient_id: patientId } }),

  manualAssess: (data: ManualAssessRequest) =>
    request.post('/prescription-reviews/manual/assess', data),

  sendWechat: (reviewId: string) =>
    request.post(`/prescription-reviews/${reviewId}/send-wechat`),
};