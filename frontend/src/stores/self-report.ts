import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { SelfReport, SelfReportQuery } from '@/types/self-report'
import { selfReportApi } from '@/api/self-report'

export const useSelfReportStore = defineStore('self-report', () => {
  const records = ref<SelfReport[]>([])
  const loading = ref(false)
  const total = ref(0)

  async function fetchRecords(params?: SelfReportQuery) {
    loading.value = true
    try {
      const res = await selfReportApi.getList(params)
      records.value = res.items || []
      total.value = res.total || 0
    } finally {
      loading.value = false
    }
  }

  return { records, loading, total, fetchRecords }
})
