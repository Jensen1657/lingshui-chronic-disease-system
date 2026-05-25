import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { Assessment, AssessmentQuery } from '@/types/assessment'
import { assessmentApi } from '@/api/assessment'

export const useAssessmentStore = defineStore('assessment', () => {
  const records = ref<Assessment[]>([])
  const loading = ref(false)
  const total = ref(0)

  async function fetchRecords(params?: AssessmentQuery) {
    loading.value = true
    try {
      const res = await assessmentApi.getList(params)
      records.value = res.items || []
      total.value = res.total || 0
    } finally {
      loading.value = false
    }
  }

  async function getById(id: string) {
    loading.value = true
    try {
      return await assessmentApi.getById(id)
    } finally {
      loading.value = false
    }
  }

  async function deleteAssessment(id: string) {
    await assessmentApi.delete(id)
  }

  return { records, loading, total, fetchRecords, getById, deleteAssessment }
})