<script setup lang="ts">
import { ref, provide } from 'vue'
import AppHeader from '@/components/AppHeader.vue'
import StatsPanel from './components/StatsPanel.vue'
import ScrapingTab from './components/ScrapingTab.vue'
import AuditTab from './components/AuditTab.vue'
import VocabularyTab from './components/VocabularyTab.vue'
import NotificationSystem from './components/NotificationSystem.vue'

const activeMainTab = ref('compliance-dashboard') // 激活默认合格检测看板
const activeSubTab = ref('time-dashboard') // 激活默认二级菜单
const notificationSystemRef = ref()

// 定义主导航项和二级菜单
const navItems = ref([
  { 
    id: 'compliance-dashboard', 
    label: '合格检测看板', 
    icon: '📊',
    children: [
      { id: 'time-dashboard', label: '全时段看板', icon: '⏰' },
      { id: 'platform-dashboard', label: '全平台看板', icon: '🌐' }
    ]
  },
  { 
    id: 'pre-compliance', 
    label: '事前合规校对', 
    icon: '✏️',
    children: [
      { id: 'text-check', label: '文字校对', icon: '📝' },
      { id: 'image-check', label: '图片校对', icon: '🖼️' },
      { id: 'audio-check', label: '音频校对', icon: '🎵' },
      { id: 'video-check', label: '视频校对', icon: '🎬' }
    ]
  },
  { 
    id: 'post-compliance', 
    label: '事后合规监测', 
    icon: '🔍',
    children: [
      { id: 'content-audit', label: '内容审核', icon: '📋' }
    ]
  },
  { 
    id: 'compliance-update', 
    label: '更新合规监测', 
    icon: '🔄',
    children: [
      { id: 'data-scraping', label: '数据抓取', icon: '🚀' }
    ]
  },
  { 
    id: 'system-management', 
    label: '系统管理', 
    icon: '⚙️',
    children: [
      { id: 'vocabulary-management', label: '词库管理', icon: '📚' }
    ]
  }
])

const switchMainTab = (tab: string) => {
  activeMainTab.value = tab
  // 切换到一级菜单时，默认选择第一个二级菜单
  const selectedNav = navItems.value.find(item => item.id === tab)
  if (selectedNav && selectedNav.children && selectedNav.children.length > 0) {
    activeSubTab.value = selectedNav.children[0].id
  }
}

const switchSubTab = (tab: string) => {
  activeSubTab.value = tab
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
    
    <!-- 主要布局容器 -->
    <div class="main-layout">
      <!-- 左侧导航区域 -->
      <div class="global-left-sidebar">
        <div class="sidebar-nav">
          <div v-for="item in navItems" :key="item.id" class="nav-group">
            <!-- 一级菜单 -->
            <div 
              class="nav-item main-nav"
              :class="{ active: activeMainTab === item.id }"
              @click="switchMainTab(item.id)"
            >
              <span class="nav-icon">{{ item.icon }}</span>
              <span class="nav-label">{{ item.label }}</span>
            </div>
            
            <!-- 二级菜单 -->
            <div v-if="activeMainTab === item.id && item.children" class="sub-nav">
              <div 
                v-for="child in item.children" 
                :key="child.id"
                class="nav-item sub-nav-item"
                :class="{ active: activeSubTab === child.id }"
                @click="switchSubTab(child.id)"
              >
                <span class="nav-icon">{{ child.icon }}</span>
                <span class="nav-label">{{ child.label }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 右侧内容区域 -->
      <div class="main-content">
        <!-- 合格检测看板 -->
        <div v-if="activeMainTab === 'compliance-dashboard'" class="dashboard-container">
          <!-- 全时段看板 -->
          <div v-if="activeSubTab === 'time-dashboard'" class="time-dashboard">
            <StatsPanel dashboard-type="time" />
          </div>
          <!-- 全平台看板 -->
          <div v-if="activeSubTab === 'platform-dashboard'" class="platform-dashboard">
            <StatsPanel dashboard-type="platform" />
          </div>
        </div>
        
        <!-- 事前合规校对 -->
        <div v-if="activeMainTab === 'pre-compliance'" class="pre-compliance-container">
          <!-- 文字校对 -->
          <div v-if="activeSubTab === 'text-check'" class="text-check">
            <AuditTab check-type="text" />
          </div>
          <!-- 图片校对 -->
          <div v-if="activeSubTab === 'image-check'" class="image-check">
            <AuditTab check-type="image" />
          </div>
          <!-- 音频校对 -->
          <div v-if="activeSubTab === 'audio-check'" class="audio-check">
            <AuditTab check-type="audio" />
          </div>
          <!-- 视频校对 -->
          <div v-if="activeSubTab === 'video-check'" class="video-check">
            <AuditTab check-type="video" />
          </div>
        </div>
        
        <!-- 事后合规监测 -->
        <div v-if="activeMainTab === 'post-compliance'" class="post-compliance-container">
          <!-- 内容审核 -->
          <div v-if="activeSubTab === 'content-audit'" class="content-audit">
            <AuditTab check-type="audit" />
          </div>
        </div>
        
        <!-- 更新合规监测 -->
        <div v-if="activeMainTab === 'compliance-update'" class="compliance-update-container">
          <!-- 数据抓取 -->
          <div v-if="activeSubTab === 'data-scraping'" class="data-scraping">
            <ScrapingTab 
              @switch-to-audit="() => { switchMainTab('post-compliance'); switchSubTab('content-audit'); }" 
            />
          </div>
        </div>
        
        <!-- 系统管理 -->
        <div v-if="activeMainTab === 'system-management'" class="system-management-container">
          <!-- 词库管理 -->
          <div v-if="activeSubTab === 'vocabulary-management'" class="vocabulary-management">
            <VocabularyTab />
          </div>
        </div>
        
        <NotificationSystem ref="notificationSystemRef" />
      </div>
    </div>
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
  max-width: 1400px;
  margin: 0 auto;
  background: white;
  border-radius: 15px;
  box-shadow: 0 20px 40px rgba(0,0,0,0.1);
  overflow: hidden;
}

/* 主要布局样式 */
.main-layout {
  display: flex;
  min-height: 80vh;
}

.global-left-sidebar {
  width: 250px;
  background: #2c3e50;
  color: white;
}

.main-content {
  flex: 1;
  padding: 20px;
  background: #f8f9fa;
  display: flex;
  flex-direction: column;
}

.dashboard-container,
.scraping-container,
.audit-container,
.system-management-container {
  flex: 1;
  display: flex;
  flex-direction: column;
}

/* 内容抓取和审核页面样式 */
.scraping-container,
.audit-container,
.system-management-container {
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  overflow: hidden;
}

/* 侧边导航样式 */
.sidebar-nav {
  padding: 20px 0;
}

.nav-group {
  margin-bottom: 4px;
}

.nav-item {
  display: flex;
  align-items: center;
  padding: 15px 25px;
  cursor: pointer;
  transition: all 0.3s ease;
  border-left: 4px solid transparent;
}

.nav-item:hover {
  background: rgba(255, 255, 255, 0.1);
}

.nav-item.active {
  background: rgba(255, 255, 255, 0.15);
  border-left: 4px solid #42b983;
}

.main-nav {
  font-weight: 600;
}

.main-nav.active {
  background: rgba(255, 255, 255, 0.2);
  border-left: 4px solid #42b983;
}

.sub-nav {
  margin-left: 20px;
  border-left: 2px solid rgba(255, 255, 255, 0.2);
  padding-left: 10px;
}

.sub-nav-item {
  padding: 10px 20px;
  font-size: 0.95em;
  color: rgba(255, 255, 255, 0.8);
}

.sub-nav-item:hover {
  background: rgba(255, 255, 255, 0.08);
  color: rgba(255, 255, 255, 0.95);
}

.sub-nav-item.active {
  background: rgba(255, 255, 255, 0.12);
  color: white;
  border-left: 3px solid #42b983;
  font-weight: 500;
}

.nav-icon {
  font-size: 1.5em;
  margin-right: 15px;
  width: 30px;
  text-align: center;
}

.nav-label {
  font-size: 1.1em;
  font-weight: 500;
}

/* 响应式设计 */
@media (max-width: 992px) {
  .main-layout {
    flex-direction: column;
  }
  
  .global-left-sidebar {
    width: 100%;
  }
  
  .sidebar-nav {
    display: flex;
    overflow-x: auto;
    padding: 0;
  }
  
  .nav-item {
    flex-direction: column;
    padding: 15px;
    min-width: 120px;
    text-align: center;
    border-left: none;
    border-bottom: 4px solid transparent;
  }
  
  .nav-item.active {
    border-left: none;
    border-bottom: 4px solid #42b983;
  }
  
  .nav-icon {
    margin-right: 0;
    margin-bottom: 8px;
  }
}

@media (max-width: 768px) {
  .container {
    padding: 10px;
  }
  
  .main-content {
    padding: 15px;
  }
  
  .nav-item {
    padding: 10px;
    min-width: 100px;
  }
  
  .nav-icon {
    font-size: 1.3em;
  }
  
  .nav-label {
    font-size: 0.9em;
  }
  
  .dashboard-container,
  .audit-container,
  .system-management-container {
    padding: 10px;
  }
}
</style>