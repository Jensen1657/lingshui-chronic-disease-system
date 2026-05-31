<template>
  <Teleport to="body">
    <Transition name="alert-popup">
      <div v-if="show" class="alert-notification-popup" @click="onClick">
        <div class="alert-popup-header" :class="'level-' + (alert?.alert_level?.toLowerCase() || 'high')">
          <span class="alert-popup-icon">{{ alert?.alert_level === 'CRITICAL' ? '🚨' : '⚠️' }}</span>
          <span class="alert-popup-title">{{ alert?.alert_title || '高危预警' }}</span>
          <button class="alert-popup-close" @click.stop="$emit('dismiss')">✕</button>
        </div>
        <div class="alert-popup-body">
          <p v-if="alert?.patient_name" class="alert-patient">👤 {{ alert.patient_name }}</p>
          <p class="alert-content">{{ alert?.alert_content }}</p>
          <p class="alert-time">🕐 {{ formatTime(alert?.created_at) }}</p>
        </div>
        <div class="alert-popup-footer">
          <span class="alert-hint">点击查看详情 →</span>
          <span class="alert-count" v-if="count > 0">共 {{ count }} 条待处理预警</span>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup lang="ts">
interface AlertItem {
  alert_id: string
  alert_title: string
  alert_content: string
  alert_level: string
  patient_name?: string
  created_at: string
}

defineProps<{
  show: boolean
  alert: AlertItem | null
  count: number
}>()

const emit = defineEmits<{
  dismiss: []
  click: []
}>()

function onClick() {
  emit('click')
}

function formatTime(dateStr?: string) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return d.toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}
</script>

<style scoped>
.alert-notification-popup {
  position: fixed;
  top: 20px;
  right: 20px;
  width: 380px;
  max-width: 90vw;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.18), 0 2px 8px rgba(0, 0, 0, 0.1);
  z-index: 9999;
  cursor: pointer;
  overflow: hidden;
  animation: slideIn 0.4s cubic-bezier(0.16, 1, 0.3, 1);
}
@keyframes slideIn {
  from { transform: translateX(120%); opacity: 0; }
  to { transform: translateX(0); opacity: 1; }
}

.alert-popup-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 16px;
  color: #fff;
  font-weight: 600;
}
.alert-popup-header.level-critical {
  background: linear-gradient(135deg, #ff4d4f, #ff7875);
}
.alert-popup-header.level-high {
  background: linear-gradient(135deg, #fa8c16, #ffc069);
}

.alert-popup-icon { font-size: 20px; }
.alert-popup-title { flex: 1; font-size: 15px; }
.alert-popup-close {
  background: rgba(255,255,255,0.25);
  border: none;
  color: #fff;
  width: 24px;
  height: 24px;
  border-radius: 50%;
  cursor: pointer;
  font-size: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.alert-popup-close:hover { background: rgba(255,255,255,0.4); }

.alert-popup-body {
  padding: 14px 16px;
  border-bottom: 1px solid #f0f0f0;
}
.alert-patient { margin: 0 0 6px; font-weight: 600; color: #333; }
.alert-content { margin: 0 0 8px; color: #555; font-size: 13px; line-height: 1.5; }
.alert-time { margin: 0; color: #999; font-size: 12px; }

.alert-popup-footer {
  padding: 10px 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #fafafa;
}
.alert-hint { color: var(--primary, #409EFF); font-size: 13px; font-weight: 500; }
.alert-count { color: #999; font-size: 12px; }

/* Transition */
.alert-popup-enter-active { animation: slideIn 0.4s cubic-bezier(0.16, 1, 0.3, 1); }
.alert-popup-leave-active { animation: slideOut 0.3s ease-in; }
@keyframes slideOut {
  from { transform: translateX(0); opacity: 1; }
  to { transform: translateX(120%); opacity: 0; }
}
</style>