import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { FollowupRecord, FollowupQuery } from '@/types/followup'
import { followupApi } from '@/api/followup'

export const useFollowupStore = defineStore('followup', () => {
  const records = ref<FollowupRecord[]>([])
  const loading = ref(false)
  const total = ref(0)

  async function fetchRecords(params?: FollowupQuery) {
    loading.value = true
    try {
      const res = await followupApi.getList(params)
      console.log('Followup API response:', res)
      records.value = res.items || []
      total.value = res.total || 0
      console.log('Records set:', records.value.length, 'Total set:', total.value)
    } catch (err) {
      console.error('Followup API error:', err)
      records.value = []
      total.value = 0
    } finally {
      loading.value = false
    }
  }

  async function getById(id: string) {
    loading.value = true
    try {
      return await followupApi.getById(id)
    } finally {
      loading.value = false
    }
  }

  return { records, loading, total, fetchRecords, getById }
})