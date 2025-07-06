<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import ColumnTypeSelector from './ColumnTypeSelector.vue'
import ContentList from './ContentList.vue'

interface ContentItem {
  id: string
  title: string
  content: string
  url: string
  publish_time: string
  created_at: string
  column_type: string
  status: string
  audit_status: string
  images: string[]
  videos: string[]
  audios: string[]
}

const selectedColumnType = ref('')
const contentList = ref<ContentItem[]>([])
const currentPage = ref(1)
const totalPages = ref(1)
const isLoading = ref(false)

const columnTypes = [
  {
    type: '时政要闻',
    icon: '📰',
    title: '时政要闻',
    desc: '政治新闻和时事要闻'
  },
  {
    type: '行业热点',
    icon: '🔥',
    title: '行业热点',
    desc: '行业动态和热点资讯'
  },
  {
    type: '川烟动态',
    icon: '🏢',
    title: '川烟动态',
    desc: '公司内部动态信息'
  },
  {
    type: '媒体报道',
    icon: '📺',
    title: '媒体报道',
    desc: '媒体相关报道内容'
  }
]

const canLoadContent = computed(() => {
  return selectedColumnType.value && !isLoading.value
})

const showContentContainer = computed(() => {
  return selectedColumnType.value && contentList.value.length > 0
})

const handleColumnTypeSelect = (type: string) => {
  selectedColumnType.value = type
  // 选择栏目类型后自动加载内容
  loadAuditContent(1)
}

const loadAuditContent = async (page = 1) => {
  if (!selectedColumnType.value) {
    window.showNotification('请先选择栏目类型', 'warning')
    return
  }
  
  isLoading.value = true
  
  try {
    const API_BASE = `${window.location.protocol}//${window.location.hostname}:6188`
    const response = await fetch(
      `${API_BASE}/api/v1/content/list?column_type=${selectedColumnType.value}&page=${page}&page_size=10`
    )
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`)
    }
    
    const result = await response.json()
    
    if (result.success) {
      contentList.value = result.data.items || []
      totalPages.value = Math.ceil((result.data.total || 0) / 10)
      currentPage.value = result.data.page || 1
      
      window.showNotification('内容加载成功', 'success')
    } else {
      throw new Error(result.message || '加载失败')
    }
    
  } catch (error) {
    console.error('加载内容审核数据失败:', error)
    const errorMessage = error instanceof Error ? error.message : '未知错误'
    window.showNotification(`加载失败: ${errorMessage}`, 'error')
  } finally {
    isLoading.value = false
  }
}



const handlePageChange = (page: number) => {
  if (page !== currentPage.value && !isLoading.value) {
    loadAuditContent(page)
  }
}


</script>

<template>
  <div class="tab-content">
    <!-- 栏目类型选择区域 -->
    <ColumnTypeSelector
      :column-types="columnTypes"
      :selected-type="selectedColumnType"
      :title="'📋 选择审核栏目类型'"
      @select="handleColumnTypeSelect"
    />
    
    <div class="audit-controls">
      <div class="selected-type">
        <span>已选择: </span>
        <span class="selected-type-text">
          {{ selectedColumnType || '请选择栏目类型' }}
        </span>
      </div>
      <div v-if="isLoading" class="loading-indicator">
        <span>⏳ 加载中...</span>
      </div>
    </div>
    
    <!-- 审核内容容器 -->
    <div v-if="showContentContainer" class="audit-content-container">

      
      <ContentList 
        :content-list="contentList"
        :current-page="currentPage"
        :total-pages="totalPages"
        :is-loading="isLoading"
        type="audit"
        @page-change="handlePageChange"
      />
    </div>
  </div>
</template>

<style scoped>
.tab-content {
  padding: 30px;
}

.audit-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 20px;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
}

.selected-type {
  font-size: 16px;
  font-weight: 500;
}

.selected-type-text {
  color: #c41e3a;
  font-weight: 600;
}

.audit-content-container {
  margin-top: 30px;
}





.btn {
  padding: 12px 25px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  text-decoration: none;
  display: inline-block;
  text-align: center;
}

.btn-sm {
  padding: 8px 16px;
  font-size: 12px;
}

.btn-primary {
  background: #c41e3a;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #8b1538;
  transform: translateY(-2px);
}

.btn-success {
  background: #28a745;
  color: white;
}

.btn-success:hover:not(:disabled) {
  background: #218838;
  transform: translateY(-2px);
}

.btn-danger {
  background: #dc3545;
  color: white;
}

.btn-danger:hover:not(:disabled) {
  background: #c82333;
  transform: translateY(-2px);
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none !important;
}

.loading-indicator {
  display: flex;
  align-items: center;
  color: #666;
  font-size: 14px;
}

.loading-indicator span {
  margin-left: 5px;
}
</style>