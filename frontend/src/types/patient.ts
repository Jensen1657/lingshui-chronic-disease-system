export interface Patient {
  patient_id: string
  name_enc: string
  gender: string
  age: number
  phone_enc: string
  id_card_enc?: string
  id_card_hash?: string
  address?: string
  village_code?: string
  manage_org_code?: string
  disease_list: string[]
  risk_level: string
  birth_date: string
  is_active: boolean
  empi_status: string
  created_at: string
  updated_at: string
}

export interface PatientQuery {
  skip?: number
  limit?: number
  page?: number
  page_size?: number
  name?: string
  patient_id?: string
  village_code?: string
  manage_org_code?: string
  disease_code?: string
  risk_level?: string
  is_active?: boolean
  min_age?: number
  max_age?: number
}

export interface CreatePatient {
  name_enc: string
  gender: string
  birth_date: string
  phone_enc: string
  id_card_enc: string
  id_card_hash: string
  address?: string
  village_code?: string
  manage_org_code?: string
  disease_list: string[]
  risk_level?: string
}
