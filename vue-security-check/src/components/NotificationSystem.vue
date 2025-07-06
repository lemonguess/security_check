<script setup lang="ts">
import { ref, reactive } from 'vue'

interface Notification {
  id: number
  message: string
  type: 'info' | 'success' | 'warning' | 'error'
  visible: boolean
}

const notifications = reactive<Notification[]>([])
let notificationId = 0

const showNotification = (message: string, type: 'info' | 'success' | 'warning' | 'error' = 'info') => {
  const notification: Notification = {
    id: ++notificationId,
    message,
    type,
    visible: true
  }
  
  notifications.push(notification)
  
  setTimeout(() => {
    removeNotification(notification.id)
  }, 3000)
}

const removeNotification = (id: number) => {
  const index = notifications.findIndex(n => n.id === id)
  if (index > -1) {
    notifications[index].visible = false
    setTimeout(() => {
      notifications.splice(index, 1)
    }, 300)
  }
}

// 暴露方法给全局使用
window.showNotification = showNotification
</script>

<template>
  <div class="notification-container">
    <transition-group name="notification" tag="div">
      <div
        v-for="notification in notifications"
        :key="notification.id"
        :class="['notification', notification.type, { visible: notification.visible }]"
        @click="removeNotification(notification.id)"
      >
        {{ notification.message }}
      </div>
    </transition-group>
  </div>
</template>

<style scoped>
.notification-container {
  position: fixed;
  top: 20px;
  right: 20px;
  z-index: 9999;
  pointer-events: none;
}

.notification {
  padding: 12px 20px;
  margin-bottom: 10px;
  border-radius: 8px;
  color: white;
  font-weight: 500;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  cursor: pointer;
  pointer-events: auto;
  opacity: 0;
  transform: translateX(100%);
  transition: all 0.3s ease;
  max-width: 300px;
  word-wrap: break-word;
}

.notification.visible {
  opacity: 1;
  transform: translateX(0);
}

.notification.info {
  background: #17a2b8;
}

.notification.success {
  background: #28a745;
}

.notification.warning {
  background: #ffc107;
  color: #212529;
}

.notification.error {
  background: #dc3545;
}

.notification:hover {
  opacity: 0.9;
}

/* 过渡动画 */
.notification-enter-active,
.notification-leave-active {
  transition: all 0.3s ease;
}

.notification-enter-from {
  opacity: 0;
  transform: translateX(100%);
}

.notification-leave-to {
  opacity: 0;
  transform: translateX(100%);
}
</style>