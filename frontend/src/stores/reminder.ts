import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { ReminderRecord, ReminderQuery, ReminderCreate, ReminderUpdate } from '@/types/reminder'
import { reminderApi } from '@/api/reminder'

export const useReminderStore = defineStore('reminder', () => {
  const records = ref<ReminderRecord[]>([])
  const loading = ref(false)
  const total = ref(0)

  async function fetchRecords(params?: ReminderQuery) {
    loading.value = true
    try {
      const res = await reminderApi.getList(params)
      records.value = res.items || []
      total.value = res.total || 0
    } finally {
      loading.value = false
    }
  }

  async function getById(id: string) {
    loading.value = true
    try {
      return await reminderApi.getById(id)
    } finally {
      loading.value = false
    }
  }

  async function createReminder(data: ReminderCreate) {
    loading.value = true
    try {
      await reminderApi.create(data)
      await fetchRecords()
    } finally {
      loading.value = false
    }
  }

  async function updateReminder(id: string, data: ReminderUpdate) {
    loading.value = true
    try {
      await reminderApi.update(id, data)
      await fetchRecords()
    } finally {
      loading.value = false
    }
  }

  async function markAsSent(id: string) {
    await reminderApi.update(id, { is_sent: true })
    await fetchRecords()
  }

  async function markAsCompleted(id: string) {
    await reminderApi.update(id, { status: 'COMPLETED' })
    await fetchRecords()
  }

  return {
    records,
    loading,
    total,
    fetchRecords,
    getById,
    createReminder,
    updateReminder,
    markAsSent,
    markAsCompleted,
  }
})
