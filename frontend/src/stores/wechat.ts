import { defineStore } from 'pinia'
import { ref } from 'vue'
import type { WechatBinding, WechatQuery } from '@/types/wechat'
import { wechatApi } from '@/api/wechat'

export const useWechatStore = defineStore('wechat', () => {
  const bindings = ref<WechatBinding[]>([])
  const loading = ref(false)
  const total = ref(0)

  async function fetchBindings(params?: WechatQuery) {
    loading.value = true
    try {
      const res = await wechatApi.getList(params)
      bindings.value = res.items || []
      total.value = res.total || 0
    } finally {
      loading.value = false
    }
  }

  async function getById(id: string) {
    loading.value = true
    try {
      return await wechatApi.getById(id)
    } finally {
      loading.value = false
    }
  }

  async function sendNotification(id: string, msg: string) {
    await wechatApi.sendNotification(id, { message: msg })
    await fetchBindings()
  }

  async function unbindWechat(id: string) {
    await wechatApi.unbind(id)
    await fetchBindings()
  }

  async function deleteRecord(id: string) {
    await wechatApi.delete(id)
    await fetchBindings()
  }

  async function activateBinding(id: string) {
    await wechatApi.update(id, { is_active: true })
    await fetchBindings()
  }

  async function deactivateBinding(id: string) {
    await wechatApi.update(id, { is_active: false })
    await fetchBindings()
  }

  async function enableNotification(id: string) {
    await wechatApi.update(id, { notification_enabled: true })
    await fetchBindings()
  }

  async function disableNotification(id: string) {
    await wechatApi.update(id, { notification_enabled: false })
    await fetchBindings()
  }

  return {
    bindings, loading, total, fetchBindings,
    getById, sendNotification, unbindWechat, deleteRecord,
    activateBinding, deactivateBinding, enableNotification, disableNotification,
  }
})
