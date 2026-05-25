import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { ReferralRecord, ReferralQuery } from '@/types/referral'
import { referralApi } from '@/api/referral'

export const useReferralStore = defineStore('referral', () => {
  const records = ref<ReferralRecord[]>([])
  const loading = ref(false)
  const total = ref(0)

  async function fetchRecords(params?: ReferralQuery) {
    loading.value = true
    try {
      const res = await referralApi.getList(params)
      records.value = res.items || []
      total.value = res.total || 0
    } finally {
      loading.value = false
    }
  }

  async function getById(id: string) {
    loading.value = true
    try {
      return await referralApi.getById(id)
    } finally {
      loading.value = false
    }
  }

  async function approveRecord(id: string) {
    await referralApi.update(id, { status: 'approved' })
  }

  async function rejectRecord(id: string, _reason: string) {
    await referralApi.update(id, { status: 'rejected' })
  }

  async function completeRecord(id: string) {
    await referralApi.update(id, { status: 'completed' })
  }

  return { records, loading, total, fetchRecords, getById, approveRecord, rejectRecord, completeRecord }
})