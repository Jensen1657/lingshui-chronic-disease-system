/**
 * 主动弹窗预警 — 轮询未读高危告警
 * 每30秒查询一次，新告警弹出桌面级通知
 */
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import request from '@/api/request'

interface AlertItem {
  alert_id: string
  alert_title: string
  alert_content: string
  alert_level: string
  patient_name?: string
  created_at: string
}

export function useAlertPolling() {
  const unreadCriticalCount = ref(0)
  const latestAlerts = ref<AlertItem[]>([])
  const showPopup = ref(false)
  const popupAlert = ref<AlertItem | null>(null)
  let timer: ReturnType<typeof setInterval> | null = null
  let lastAlertIds = new Set<string>()
  const router = useRouter()

  async function checkAlerts() {
    try {
      const res = await request.get<{ items: AlertItem[]; total: number }>(
        '/v1/alerts',
        { params: { status: 'unresolved', alert_level: 'CRITICAL,HIGH', page_size: 50 } }
      )
      const items = res.data.items || []
      const newIds = new Set(items.map((a: AlertItem) => a.alert_id))

      // 检测新告警
      const newAlerts = items.filter((a: AlertItem) => !lastAlertIds.has(a.alert_id))

      unreadCriticalCount.value = items.length

      if (newAlerts.length > 0 && lastAlertIds.size > 0) {
        // 有问题新告警
        const critical = newAlerts.find((a: AlertItem) => a.alert_level === 'CRITICAL')
        popupAlert.value = critical || newAlerts[0]
        showPopup.value = true
        // 5秒后自动消失
        setTimeout(() => {
          showPopup.value = false
        }, 8000)

        // 浏览器桌面通知
        if (Notification.permission === 'granted') {
          const title = popupAlert.value.alert_title || '⚠️ 高危预警'
          new Notification(title, {
            body: `${popupAlert.value.patient_name || '患者'} - ${popupAlert.value.alert_content?.substring(0, 60) || ''}`,
            icon: '/favicon.ico',
            tag: popupAlert.value.alert_id,
          })
        }
      }

      lastAlertIds = newIds
      latestAlerts.value = items.slice(0, 5)
    } catch {
      // 静默失败，避免阻塞
    }
  }

  function requestNotificationPermission() {
    if ('Notification' in window && Notification.permission === 'default') {
      Notification.requestPermission()
    }
  }

  function goToAlerts() {
    showPopup.value = false
    router.push('/alerts')
  }

  function dismissPopup() {
    showPopup.value = false
  }

  onMounted(() => {
    requestNotificationPermission()
    checkAlerts() // 首次立即检查
    timer = setInterval(checkAlerts, 30000) // 每30秒轮询
  })

  onUnmounted(() => {
    if (timer) clearInterval(timer)
  })

  return {
    unreadCriticalCount,
    latestAlerts,
    showPopup,
    popupAlert,
    goToAlerts,
    dismissPopup,
    checkAlerts,
  }
}
