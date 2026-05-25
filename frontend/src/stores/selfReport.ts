import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { selfReportApi } from '@/api/self-report'

type SelfReportRecord = any
type SelfReportQuery = any

export const useSelfReportStore = defineStore('selfReport', () => {
  const records = ref<SelfReportRecord[]>([])
  const currentRecord = ref<SelfReportRecord | null>(null)
  const loading = ref(false)
  const total = ref(0)
  const page = ref(1)
  const pageSize = ref(20)

  const recordCount = computed(() => records.value.length)

  async function fetchRecords(params?: SelfReportQuery) {
    loading.value = true
    try {
      const response = await selfReportApi.getList(params)
      records.value = response.items || []
      total.value = response.total || 0
      page.value = response.page || 1
      pageSize.value = response.page_size || 20
    } catch (error) {
      console.error('Failed to fetch self-report records:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  async function fetchRecord(id: string) {
    loading.value = true
    try {
      const response = await selfReportApi.getById(id)
      currentRecord.value = response
      return response
    } catch (error) {
      console.error('Failed to fetch self-report record:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  async function createRecord(data: any) {
    loading.value = true
    try {
      const response = await selfReportApi.create(data)
      await fetchRecords({ page: page.value, page_size: pageSize.value })
      return response
    } catch (error) {
      console.error('Failed to create self-report record:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  async function updateRecord(id: string, data: any) {
    loading.value = true
    try {
      const response = await selfReportApi.update(id, data)
      await fetchRecords({ page: page.value, page_size: pageSize.value })
      return response
    } catch (error) {
      console.error('Failed to update self-report record:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  async function deleteRecord(id: string) {
    loading.value = true
    try {
      await selfReportApi.delete(id)
      await fetchRecords({ page: page.value, page_size: pageSize.value })
    } catch (error) {
      console.error('Failed to delete self-report record:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  async function approveRecord(id: string) {
    loading.value = true
    try {
      const response = await selfReportApi.update(id, { status: 'approved' })
      await fetchRecords({ page: page.value, page_size: pageSize.value })
      return response
    } catch (error) {
      console.error('Failed to approve self-report:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  async function rejectRecord(id: string, reason: string) {
    loading.value = true
    try {
      const response = await selfReportApi.update(id, { status: 'rejected', reject_reason: reason })
      await fetchRecords({ page: page.value, page_size: pageSize.value })
      return response
    } catch (error) {
      console.error('Failed to reject self-report:', error)
      throw error
    } finally {
      loading.value = false
    }
  }

  function resetState() {
    records.value = []
    currentRecord.value = null
    loading.value = false
    total.value = 0
    page.value = 1
    pageSize.value = 20
  }

  return {
    records,
    currentRecord,
    loading,
    total,
    page,
    pageSize,
    recordCount,
    fetchRecords,
    fetchRecord,
    createRecord,
    updateRecord,
    deleteRecord,
    approveRecord,
    rejectRecord,
    resetState
  }
})
