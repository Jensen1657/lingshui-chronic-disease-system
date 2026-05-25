import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { EmergencyRecord, EmergencyQuery, EmergencyCreate, EmergencyUpdate } from '@/types/emergency'
import { emergencyApi } from '@/api/emergency'

export const useEmergencyStore = defineStore('emergency', () => {
  const records = ref<EmergencyRecord[]>([])
  const loading = ref(false)
  const total = ref(0)

  async function fetchRecords(params?: EmergencyQuery) {
    loading.value = true
    try {
      const res = await emergencyApi.getList(params)
      records.value = res.items || []
      total.value = res.total || 0
    } finally {
      loading.value = false
    }
  }

  async function getById(id: string) {
    loading.value = true
    try {
      const res = await emergencyApi.getById(id)
      return res
    } finally {
      loading.value = false
    }
  }

  async function createRecord(data: EmergencyCreate) {
    loading.value = true
    try {
      await emergencyApi.create(data)
      await fetchRecords()
    } finally {
      loading.value = false
    }
  }

  async function updateRecord(id: string, data: EmergencyUpdate) {
    loading.value = true
    try {
      await emergencyApi.update(id, data)
      await fetchRecords()
    } finally {
      loading.value = false
    }
  }

  async function deleteRecord(id: string) {
    loading.value = true
    try {
      await emergencyApi.delete(id)
      await fetchRecords()
    } finally {
      loading.value = false
    }
  }

  async function processRecord(id: string, data: any) {
    await emergencyApi.processRecord(id, data)
    await fetchRecords()
  }

  async function completeRecord(id: string, data: any) {
    await emergencyApi.completeRecord(id, data)
    await fetchRecords()
  }

  async function cancelRecord(id: string, reason?: string) {
    await emergencyApi.cancelRecord(id, reason)
    await fetchRecords()
  }

  async function activateEmergency(patientId: string, data: EmergencyCreate) {
    await emergencyApi.create({ ...data, patient_id: patientId })
    await fetchRecords()
  }

  return {
    records,
    loading,
    total,
    fetchRecords,
    getById,
    createRecord,
    updateRecord,
    deleteRecord,
    processRecord,
    completeRecord,
    cancelRecord,
    activateEmergency,
  }
})
