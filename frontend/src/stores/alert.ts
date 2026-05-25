import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Alert, AlertQuery } from '@/types/alert'
import { alertApi } from '@/api/alert'

export const useAlertStore = defineStore('alert', () => {
  const records = ref<Alert[]>([])
  const loading = ref(false)
  const total = ref(0)

  async function fetchRecords(params?: AlertQuery) {
    loading.value = true
    try {
      const res = await alertApi.getList(params)
      records.value = res.items || []
      total.value = res.total || 0
    } finally {
      loading.value = false
    }
  }

  async function getById(id: string) {
    loading.value = true
    try {
      return await alertApi.getById(id)
    } finally {
      loading.value = false
    }
  }

  async function markAsRead(id: string) {
    await alertApi.update(id, { is_handled: true })
  }

  async function updateRecord(id: string, data: any) {
    await alertApi.update(id, data)
  }

  return { records, loading, total, fetchRecords, getById, markAsRead, updateRecord }
})