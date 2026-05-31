import request from './request';
import type { PageParams } from './index';

export interface MedicationItem {
  medication_id: string;
  patient_id: string;
  patient_name: string;
  disease_code: string;
  drug_name: string;
  drug_class: string;
  specification: string;
  dosage: string;
  frequency: string;
  route: string;
  start_date: string;
  end_date: string | null;
  is_long_term: boolean;
  is_active: boolean;
  prescribed_org: string;
  adherence_status: string;
  side_effects: string | null;
  notes: string | null;
  adjust_reason: string | null;
  is_ai_recommended: boolean;
  created_at: string;
}

export interface MedicationCreate {
  patient_id: string;
  disease_code: string;
  drug_name: string;
  drug_class?: string;
  specification?: string;
  dosage: string;
  frequency: string;
  route?: string;
  start_date: string;
  end_date?: string;
  is_long_term?: boolean;
  prescribed_org?: string;
  notes?: string;
}

export const medicationApi = {
  list: (params: PageParams & { patient_id?: string; disease_code?: string; is_active?: boolean; drug_name?: string }) =>
    request.get<{ items: MedicationItem[]; total: number; page: number; page_size: number }>('/medications', { params }),

  getByPatient: (patientId: string, activeOnly = false) =>
    request.get(`/medications/patient/${patientId}`, { params: { active_only: activeOnly } }),

  create: (data: MedicationCreate) =>
    request.post('/medications', data),

  update: (id: string, data: Record<string, unknown>) =>
    request.put(`/medications/${id}`, data),

  adherenceStats: (orgCode?: string) =>
    request.get('/medications/adherence/stats', { params: { org_code: orgCode } }),
};
