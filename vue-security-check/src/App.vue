<script setup lang="ts">
import { ref, provide } from 'vue'
// 确保AppHeader组件存在于正确的路径下
import AppHeader from '@/components/AppHeader.vue'
import StatsPanel from './components/StatsPanel.vue'
import TabNavigation from './components/TabNavigation.vue'
import ScrapingTab from './components/ScrapingTab.vue'
import AuditTab from './components/AuditTab.vue'
import NotificationSystem from './components/NotificationSystem.vue'

const activeTab = ref('scraping')
const notificationSystemRef = ref()

const switchTab = (tab: string) => {
  activeTab.value = tab
}

const showNotification = (message: string, type: string = 'info') => {
  if (notificationSystemRef.value) {
    notificationSystemRef.value.showNotification(message, type)
  }
}

// 提供全局通知函数
provide('showNotification', showNotification)

// 设置全局通知函数
if (typeof window !== 'undefined') {
  (window as any).showNotification = showNotification
}
</script>

<template>
  <div class="container">
    <AppHeader />
    <StatsPanel />
    <TabNavigation :active-tab="activeTab" @switch-tab="switchTab" />
    
    <ScrapingTab v-if="activeTab === 'scraping'" @switch-to-audit="switchTab('audit')" />
    <AuditTab v-if="activeTab === 'audit'" />
    
    <NotificationSystem ref="notificationSystemRef" />
  </div>
</template>

<style>
/* 全局样式重置 */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  min-height: 100vh;
  padding: 20px;
}

/* 主容器样式 */
.container {
  max-width: 1200px;
  margin: 0 auto;
  background: white;
  border-radius: 15px;
  box-shadow: 0 20px 40px rgba(0,0,0,0.1);
  overflow: hidden;
}


</style>
