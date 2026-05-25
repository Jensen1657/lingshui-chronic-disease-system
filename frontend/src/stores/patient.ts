import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Patient, PatientQuery } from '@/types/patient'
import { patientApi } from '@/api/patient'

export const usePatientStore = defineStore('patient', () => {
  const patients = ref<Patient[]>([])
  const loading = ref(false)
  const total = ref(0)
  const currentPatient = ref<Patient | null>(null)

  async function fetchPatients(params?: PatientQuery) {
    loading.value = true
    try {
      const res = await patientApi.getList(params)
      patients.value = res.items || []
      total.value = res.total || 0
    } finally {
      loading.value = false
    }
  }

  async function fetchPatient(id: string) {
    loading.value = true
    try {
      const res: any = await patientApi.getById(id)
      currentPatient.value = res
      return res
    } finally {
      loading.value = false
    }
  }

  async function deletePatient(id: string) {
    await patientApi.delete(id)
  }

  return { patients, loading, total, currentPatient, fetchPatients, fetchPatient, deletePatient }
})
