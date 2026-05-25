import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { TcmRecord, TcmQuery, TcmCreate, TcmUpdate } from '@/types/tcm'
import { tcmApi } from '@/api/tcm'

export const useTcmStore = defineStore('tcm', () => {
  const records = ref<TcmRecord[]>([])
  const loading = ref(false)
  const total = ref(0)

  async function fetchRecords(params?: TcmQuery) {
    loading.value = true
    try {
      const res = await tcmApi.getList(params)
      records.value = res.items || []
      total.value = res.total || 0
    } finally {
      loading.value = false
    }
  }

  async function getById(id: string) {
    loading.value = true
    try {
      return await tcmApi.getById(id)
    } finally {
      loading.value = false
    }
  }

  async function createRecord(data: TcmCreate) {
    await tcmApi.create(data)
    await fetchRecords()
  }

  async function deleteRecord(id: string) {
    await tcmApi.delete(id)
    await fetchRecords()
  }

  async function updateRecord(id: string, data: TcmUpdate) {
    await tcmApi.update(id, data)
    await fetchRecords()
  }

  async function completeRecord(id: string, data: TcmUpdate) {
    await tcmApi.update(id, data)
    await fetchRecords()
  }

  async function assessConstitution(id: string) {
    // 调用后端体质辨识接口
    await tcmApi.update(id, { reassess: true })
  }

  return {
    records, loading, total, fetchRecords,
    getById, createRecord, deleteRecord, updateRecord, completeRecord, assessConstitution,
  }
})