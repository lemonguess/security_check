<script setup lang="ts">
import { ref, computed, reactive, watch } from 'vue'

interface ContentItem {
  id: string
  title: string
  content: string
  url?: string
  publish_time?: string
  created_at?: string
  column_type: string
  status: string
  audit_status?: string
  images?: string[]
  videos?: string[]
  audios?: string[]
}

interface Props {
  contentList: ContentItem[]
  type: 'scraping' | 'audit'
  currentPage?: number
  totalPages?: number
  isLoading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  currentPage: 1,
  totalPages: 1,
  isLoading: false
})

const emit = defineEmits<{
  pageChange: [page: number]
}>()

const selectedContent = reactive(new Set<string>())
const localCurrentPage = ref(1)
const pageSize = ref(10)
const showProgress = ref(false)
const progressData = reactive({
  current: 0,
  total: 0,
  message: '准备中...'
})

// 报告预览相关状态
const showReportModal = ref(false)
const currentReportContentId = ref<number | null>(null)
const reportHtml = ref<string>('')
const reportLoading = ref(false)
const reportError = ref<string>('')

// 使用服务器端分页时，直接显示传入的内容
// 使用客户端分页时，进行本地分页
const isServerPagination = computed(() => props.currentPage !== undefined && props.totalPages !== undefined)

const totalRecords = computed(() => props.contentList.length)
const totalPages = computed(() => {
  return isServerPagination.value ? props.totalPages! : Math.ceil(totalRecords.value / pageSize.value)
})

const currentPage = computed(() => {
  return isServerPagination.value ? props.currentPage! : localCurrentPage.value
})

const paginatedContent = computed(() => {
  if (isServerPagination.value) {
    // 服务器端分页：直接返回传入的内容
    return props.contentList
  } else {
    // 客户端分页：进行本地分页
    const start = (localCurrentPage.value - 1) * pageSize.value
    const end = start + pageSize.value
    return props.contentList.slice(start, end)
  }
})

const selectedCount = computed(() => selectedContent.size)

const toggleSelection = (contentId: string) => {
  if (selectedContent.has(contentId)) {
    selectedContent.delete(contentId)
  } else {
    selectedContent.add(contentId)
  }
}

const toggleSelectAll = () => {
  if (selectedContent.size === paginatedContent.value.length) {
    selectedContent.clear()
  } else {
    selectedContent.clear()
    paginatedContent.value.forEach(item => {
      selectedContent.add(item.id)
    })
  }
}

const changePage = (direction: number) => {
  const newPage = currentPage.value + direction
  if (newPage >= 1 && newPage <= totalPages.value) {
    if (isServerPagination.value) {
      // 服务器端分页：发出事件
      emit('pageChange', newPage)
    } else {
      // 客户端分页：更新本地页码
      localCurrentPage.value = newPage
    }
  }
}

const auditSingleItem = async (contentId: string) => {
  try {
    const item = props.contentList.find(item => item.id === contentId)
    if (!item) return
    
    await auditItem(item)
  } catch (error) {
    console.error('审核失败:', error)
  }
}

const auditItem = async (item: ContentItem) => {
  try {
    // 立即更新状态为审核中
    item.audit_status = 'reviewing'
    
    const API_BASE = `${window.location.protocol}//${window.location.hostname}:6188`
    const response = await fetch(`${API_BASE}/api/v1/moderation/single`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        content: item.title,
        content_id: String(item.id),
        content_type: "text",
        priority: 0,
        timeout: 30.0
      })
    })
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`)
    }
    
    const result = await response.json()
    console.log('审核任务提交成功:', result)
    
    // 显示提交成功通知
    window.showNotification('审核任务已提交，正在处理中...', 'info')
    
    // 开始轮询任务状态
    if (result.task_id) {
      pollTaskStatus(result.task_id, item)
    }
  } catch (error) {
    console.error('提交审核失败:', error)
    // 恢复状态
    item.audit_status = 'pending'
    const errorMessage = error instanceof Error ? error.message : '未知错误'
    window.showNotification(`提交审核失败: ${errorMessage}`, 'error')
  }
}

// 轮询任务状态
const pollTaskStatus = async (taskId: string, item: ContentItem) => {
  const maxAttempts = 30 // 最多轮询30次
  let attempts = 0
  
  const poll = async () => {
    try {
      attempts++
      
      const API_BASE = `${window.location.protocol}//${window.location.hostname}:6188`
      const response = await fetch(`${API_BASE}/api/v1/moderation/task/${taskId}`)
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const taskStatus = await response.json()
      console.log('任务状态:', taskStatus)
      
      if (taskStatus.status === 'completed') {
        // 任务完成，更新内容状态
        await updateContentStatus(item)
        window.showNotification('审核完成', 'success')
        return
      } else if (taskStatus.status === 'failed') {
        // 任务失败
        item.audit_status = 'pending'
        window.showNotification(`审核失败: ${taskStatus.message}`, 'error')
        return
      } else if (attempts >= maxAttempts) {
        // 超时
        item.audit_status = 'pending'
        window.showNotification('审核超时，请重试', 'warning')
        return
      }
      
      // 继续轮询
      setTimeout(poll, 2000) // 2秒后再次查询
    } catch (error) {
      console.error('查询任务状态失败:', error)
      if (attempts >= maxAttempts) {
        item.audit_status = 'pending'
        window.showNotification('查询审核状态失败', 'error')
      } else {
        setTimeout(poll, 2000) // 出错后继续重试
      }
    }
  }
  
  // 开始轮询
  setTimeout(poll, 1000) // 1秒后开始第一次查询
}

// 更新内容状态
const updateContentStatus = async (item: ContentItem) => {
  try {
    const API_BASE = `${window.location.protocol}//${window.location.hostname}:6188`
    const response = await fetch(`${API_BASE}/api/v1/moderation/content/${item.id}/status`)
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }
    
    const statusData = await response.json()
    item.audit_status = statusData.audit_status
    console.log('内容状态已更新:', statusData)
  } catch (error) {
    console.error('更新内容状态失败:', error)
    // 默认设置为已完成
    item.audit_status = 'completed'
  }
}

const auditSelectedItems = async () => {
  if (selectedContent.size === 0) {
    window.showNotification('请先选择要审核的内容', 'warning')
    return
  }
  
  const selectedIds = Array.from(selectedContent)
  showProgress.value = true
  progressData.current = 0
  progressData.total = selectedIds.length
  progressData.message = '正在批量审核...'
  
  try {
    for (let i = 0; i < selectedIds.length; i++) {
      await auditSingleItem(selectedIds[i])
      progressData.current = i + 1
      progressData.message = `正在审核 (${i + 1}/${selectedIds.length})`
    }
    
    window.showNotification('批量审核完成', 'success')
    selectedContent.clear()
  } catch (error) {
    console.error('批量审核失败:', error)
    const errorMessage = error instanceof Error ? error.message : '未知错误'
    window.showNotification(`批量审核失败: ${errorMessage}`, 'error')
  } finally {
    showProgress.value = false
  }
}

const auditAllContent = async () => {
  if (props.contentList.length === 0) {
    window.showNotification('没有可审核的内容', 'warning')
    return
  }
  
  const confirmResult = confirm(`确定要审核所有 ${props.contentList.length} 条内容吗？`)
  if (!confirmResult) return
  
  showProgress.value = true
  progressData.current = 0
  progressData.total = props.contentList.length
  progressData.message = '正在批量审核...'
  
  try {
    for (let i = 0; i < props.contentList.length; i++) {
      await auditSingleItem(props.contentList[i].id)
      progressData.current = i + 1
      progressData.message = `正在审核 (${i + 1}/${props.contentList.length})`
    }
    
    window.showNotification('批量审核完成', 'success')
  } catch (error) {
    console.error('批量审核失败:', error)
    window.showNotification('批量审核失败', 'error')
  } finally {
    showProgress.value = false
  }
}



const getStatusClass = (status: string) => {
  switch (status) {
    case 'approved': return 'status-completed'
    case 'completed': return 'status-completed'
    case 'reviewing': return 'status-reviewing'
    case 'rejected': return 'status-failed'
    case 'failed': return 'status-failed'
    default: return 'status-pending'
  }
}

const getStatusText = (status: string) => {
  switch (status) {
    case 'approved': return '审核通过'
    case 'completed': return '已完成'
    case 'reviewing': return '审核中'
    case 'rejected': return '审核拒绝'
    case 'failed': return '失败'
    default: return '待审核'
  }
}

const getAuditButtonText = (status: string) => {
  switch (status) {
    case 'approved': return '已通过'
    case 'completed': return '重新审核'
    case 'reviewing': return '审核中...'
    case 'rejected': return '重新审核'
    case 'failed': return '重新审核'
    default: return '审核'
  }
}

// 重新审核功能
const reAuditItem = async (item: ContentItem) => {
  try {
    // 直接进入审核中状态
    item.audit_status = 'reviewing'
    
    const API_BASE = `${window.location.protocol}//${window.location.hostname}:6188`
    const response = await fetch(`${API_BASE}/api/v1/moderation/single`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        content: item.title,
        content_id: String(item.id),
        content_type: "text",
        priority: 0,
        timeout: 30.0,
        regenerate_report: true  // 标记为重新生成报告
      })
    })
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`)
    }
    
    const result = await response.json()
    console.log('重新审核任务提交成功:', result)
    
    // 显示提交成功通知
    window.showNotification('重新审核任务已提交，正在处理中...', 'info')
    
    // 开始轮询任务状态
    if (result.task_id) {
      pollTaskStatus(result.task_id, item)
    }
  } catch (error) {
    console.error('重新审核失败:', error)
    // 恢复原状态
    item.audit_status = 'approved'
    const errorMessage = error instanceof Error ? error.message : '未知错误'
    window.showNotification(`重新审核失败: ${errorMessage}`, 'error')
  }
}

// 监听内容变化，当内容更新时重新计算分页
watch(() => props.contentList, async () => {
  if (props.currentPage !== undefined) {
    // 服务端分页模式，直接使用传入的内容
    return
  }
  // 客户端分页模式，重置到第一页
  localCurrentPage.value = 1
  
  // 更新内容的审核状态
  await updateAllContentStatus()
}, { immediate: true })

// 更新所有内容的审核状态
const updateAllContentStatus = async () => {
  if (!props.contentList || props.contentList.length === 0) return
  
  try {
    const API_BASE = `${window.location.protocol}//${window.location.hostname}:6188`
    
    // 批量查询内容状态
    for (const item of props.contentList) {
      try {
        const response = await fetch(`${API_BASE}/api/v1/moderation/content/${item.id}/status`)
        if (response.ok) {
          const statusData = await response.json()
          item.audit_status = statusData.audit_status
        }
      } catch (error) {
        console.warn(`获取内容 ${item.id} 状态失败:`, error)
        // 保持原有状态或设置为默认状态
        if (!item.audit_status) {
          item.audit_status = 'pending'
        }
      }
    }
  } catch (error) {
     console.error('批量更新内容状态失败:', error)
   }
 }

// 查看审核报告
const viewAuditReport = async (contentId: string) => {
  try {
    currentReportContentId.value = parseInt(contentId)
    showReportModal.value = true
    reportLoading.value = true
    reportError.value = ''
    reportHtml.value = ''
    
    const API_BASE = `${window.location.protocol}//${window.location.hostname}:6188`
    const response = await fetch(`${API_BASE}/api/v1/moderation/content/${contentId}/audit`)
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`)
    }
    
    const result = await response.json()
    if (result.success && result.data.result) {
      reportHtml.value = result.data.result
    } else {
      reportError.value = '暂无审核报告'
    }
  } catch (error) {
    console.error('获取审核报告失败:', error)
    reportError.value = error instanceof Error ? error.message : '获取报告失败'
  } finally {
    reportLoading.value = false
  }
}

// 关闭报告模态框
const closeReportModal = () => {
  showReportModal.value = false
  currentReportContentId.value = null
  reportHtml.value = ''
  reportError.value = ''
}

// 下载报告
 const downloadReport = (format: string = 'pdf') => {
   if (currentReportContentId.value) {
     const API_BASE = `${window.location.protocol}//${window.location.hostname}:6188`
     const downloadUrl = `${API_BASE}/api/v1/moderation/content/${currentReportContentId.value}/audit/download?format=${format}`
     window.open(downloadUrl, '_blank')
   }
 }
</script>

<template>
  <div class="content-container">
    <h3>📄 {{ type === 'scraping' ? '抓取内容列表' : '内容列表' }}</h3>
    
    <!-- 批量操作 -->
    <div class="batch-operations">
      <label v-if="type === 'audit'">
        <input 
          type="checkbox" 
          :checked="selectedContent.size === paginatedContent.length && paginatedContent.length > 0"
          @change="toggleSelectAll"
        >
        <span>全选</span>
      </label>
      <span>已选择: {{ selectedCount }} 项</span>
      <button class="btn btn-primary" @click="auditAllContent">审核全部</button>
      <button class="btn btn-warning" @click="auditSelectedItems">审核选中</button>

    </div>
    
    <!-- 进度条 -->
    <div v-if="showProgress" class="progress-container">
      <div class="progress-bar">
        <div 
          class="progress-fill" 
          :style="{ width: `${(progressData.current / progressData.total) * 100}%` }"
        ></div>
      </div>
      <div class="progress-text">
        {{ progressData.message }} ({{ progressData.current }}/{{ progressData.total }})
      </div>
    </div>
    
    <!-- 内容列表 -->
    <div class="content-list">
      <div 
        v-for="item in paginatedContent" 
        :key="item.id"
        class="content-item"
      >
        <div class="content-checkbox">
          <input 
            type="checkbox" 
            :checked="selectedContent.has(item.id)"
            @change="toggleSelection(item.id)"
          >
        </div>
        
        <div class="content-main">
          <div class="content-header">
            <span class="column-type">[{{ item.column_type }}]</span>
            <span :class="['status', getStatusClass(item.audit_status || item.status)]">
              {{ getStatusText(item.audit_status || item.status) }}
            </span>
            <a 
              v-if="item.url" 
              :href="item.url" 
              target="_blank" 
              class="content-title-link"
            >
              {{ item.title }}
            </a>
            <span v-else class="content-title">{{ item.title }}</span>
          </div>
          
          <div v-if="item.publish_time" class="content-meta">
            🕒 发布时间: {{ new Date(item.publish_time).toLocaleString() }}
          </div>
          
          <div v-if="item.created_at" class="content-meta">
            📅 创建时间: {{ new Date(item.created_at).toLocaleString() }}
          </div>
          
          <div v-if="item.content" class="content-preview">
            📝 {{ item.content.substring(0, 100) }}{{ item.content.length > 100 ? '...' : '' }}
          </div>
          
          <!-- 媒体文件信息 -->
          <div v-if="item.images?.length || item.videos?.length" class="media-info">
            <span v-if="item.images?.length">🖼️ 图片: {{ item.images.length }} 个</span>
            <span v-if="item.videos?.length">🎥 视频: {{ item.videos.length }} 个</span>
          </div>
        </div>
        
        <div class="content-actions">
          <button 
            class="btn btn-primary btn-sm"
            :class="{ 
              'approved-btn': item.audit_status === 'approved'
            }"
            :disabled="item.audit_status === 'reviewing'"
            @click="item.audit_status === 'approved' ? reAuditItem(item) : auditSingleItem(item.id)"
          >
            <span class="btn-text" v-if="item.audit_status === 'approved'">已通过</span>
            <span v-else>{{ getAuditButtonText(item.audit_status || item.status) }}</span>
            <span class="btn-hover-text" v-if="item.audit_status === 'approved'">重新审核</span>
          </button>
          <button 
            v-if="item.audit_status === 'approved' || item.audit_status === 'rejected'"
            class="btn btn-info btn-sm"
            @click="viewAuditReport(item.id)"
            style="margin-left: 8px;"
          >
            查看报告
          </button>
        </div>
      </div>
    </div>
    
    <!-- 分页控件 -->
    <div class="pagination-controls">
      <div class="pagination-info">
        <span v-if="isServerPagination">
          第 {{ currentPage }} 页，共 {{ totalPages }} 页
        </span>
        <span v-else>
          第 {{ currentPage }} 页，共 {{ totalRecords }} 条记录
        </span>
      </div>
      <div class="pagination-buttons">
        <button 
          class="btn btn-secondary" 
          :disabled="currentPage <= 1"
          @click="changePage(-1)"
        >
          上一页
        </button>
        <span>第 {{ currentPage }} 页</span>
        <button 
          class="btn btn-secondary" 
          :disabled="currentPage >= totalPages"
          @click="changePage(1)"
        >
          下一页
        </button>
      </div>
    </div>
    
    <!-- 审核报告预览模态框 -->
    <div v-if="showReportModal" class="modal-overlay" @click="closeReportModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>审核报告 - 内容ID: {{ currentReportContentId }}</h3>
          <button class="close-btn" @click="closeReportModal">×</button>
        </div>
        <div class="modal-body">
          <div v-if="reportLoading" class="loading-indicator">
            正在加载报告...
          </div>
          <div v-else-if="reportError" class="error-message">
            {{ reportError }}
          </div>
          <iframe 
            v-else-if="reportHtml"
            :srcdoc="reportHtml"
            class="report-iframe"
            frameborder="0"
          ></iframe>
          <div v-else class="no-report">
            暂无审核报告
          </div>
        </div>
        <div class="modal-footer">
           <button class="btn btn-secondary" @click="closeReportModal">关闭</button>
           <div v-if="reportHtml" class="download-buttons">
             <button 
               class="btn btn-primary" 
               @click="downloadReport('pdf')"
             >
               下载PDF
             </button>
             <button 
               class="btn btn-outline-primary" 
               @click="downloadReport('html')"
               style="margin-left: 8px;"
             >
               下载HTML
             </button>
           </div>
         </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.content-container {
  margin-top: 30px;
}

.content-container h3 {
  margin-bottom: 20px;
  color: #333;
}

.batch-operations {
  color: #000000;
  display: flex;
  align-items: center;
  gap: 15px;
  margin-bottom: 20px;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 8px;
}

.batch-operations label {
  display: flex;
  align-items: center;
  gap: 5px;
  font-weight: 500;
}

.progress-container {
  margin-bottom: 20px;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 8px;
}

.progress-bar {
  width: 100%;
  height: 8px;
  background: #e9ecef;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 10px;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(135deg, #c41e3a 0%, #8b1538 100%);
  border-radius: 4px;
  transition: width 0.3s ease;
}

.progress-text {
  text-align: center;
  color: #666;
  font-size: 14px;
}

.content-list {
  border: 1px solid #e9ecef;
  border-radius: 8px;
  overflow: hidden;
}

.content-item {
  display: flex;
  align-items: center;
  padding: 15px;
  border-bottom: 1px solid #e9ecef;
  transition: background-color 0.2s ease;
}

.content-item:hover {
  background-color: #f8f9fa;
}

.content-item:last-child {
  border-bottom: none;
}

.content-checkbox {
  margin-right: 15px;
}

.content-main {
  flex: 1;
}

.content-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
  flex-wrap: wrap;
}

.column-type {
  background: #f0f0f0;
  padding: 2px 6px;
  border-radius: 3px;
  font-size: 12px;
  color: #666;
}

.status {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: bold;
}

.status-pending {
  background: #fff3cd;
  color: #856404;
}

.status-reviewing {
  background: #cce5ff;
  color: #0066cc;
}

.status-completed {
  background: #d4edda;
  color: #155724;
  border: 1px solid #c3e6cb;
}

.status-reviewing {
  background: #fff3cd;
  color: #856404;
  border: 1px solid #ffeaa7;
  animation: pulse 2s infinite;
}

.status-failed {
  background: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
}

.status-pending {
  background: #e2e3e5;
  color: #383d41;
  border: 1px solid #d1d3d4;
}

@keyframes pulse {
  0% { opacity: 1; }
  50% { opacity: 0.7; }
  100% { opacity: 1; }
}

.content-title-link {
  color: #c41e3a;
  text-decoration: none;
  font-weight: bold;
}

.content-title-link:hover {
  text-decoration: underline;
}

.content-title {
  font-weight: bold;
}

.content-meta {
  font-size: 12px;
  color: #999;
  margin-bottom: 5px;
}

.content-preview {
  font-size: 12px;
  color: #666;
  margin-bottom: 5px;
}

.media-info {
  font-size: 12px;
  color: #666;
  display: flex;
  gap: 15px;
}

.content-actions {
  margin-left: 15px;
}

.btn {
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-sm {
  padding: 5px 10px;
  font-size: 12px;
}

.btn-primary {
  background: #c41e3a;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: linear-gradient(135deg, #a91b2e 0%, #7a1230 100%);
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(201, 30, 58, 0.3);
}

/* 已通过按钮的特殊样式 */
.approved-btn {
  position: relative;
  overflow: hidden;
  transition: width 0.3s ease;
}

.approved-btn .btn-text {
  transition: opacity 0.3s ease;
  white-space: nowrap;
}

.approved-btn .btn-hover-text {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  opacity: 0;
  transition: opacity 0.3s ease;
  pointer-events: none;
  white-space: nowrap;
}

.approved-btn:hover {
  width: auto;
  min-width: 80px;
  transform: translateY(-1px);
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.approved-btn:hover .btn-text {
  opacity: 0;
}

.approved-btn:hover .btn-hover-text {
  opacity: 1;
}



.btn-warning {
  background: #ffc107;
  color: #212529;
}

.btn-warning:hover:not(:disabled) {
  background: #e0a800;
}

.btn-success {
  background: #28a745;
  color: white;
}

.btn-success:hover:not(:disabled) {
  background: #218838;
}

.btn-secondary {
  background: #6c757d;
  color: white;
}

.btn-secondary:hover:not(:disabled) {
  background: #5a6268;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* 模态框样式 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 8px;
  width: 90%;
  max-width: 1200px;
  height: 80%;
  max-height: 800px;
  display: flex;
  flex-direction: column;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
}

.modal-header {
  padding: 20px;
  border-bottom: 1px solid #eee;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-header h3 {
  margin: 0;
  color: #333;
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #666;
  padding: 0;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.close-btn:hover {
  color: #333;
}

.modal-body {
  flex: 1;
  padding: 20px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.report-iframe {
  width: 100%;
  height: 100%;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.loading-indicator {
  text-align: center;
  padding: 40px;
  color: #666;
}

.error-message {
  text-align: center;
  padding: 40px;
  color: #d32f2f;
  background-color: #ffebee;
  border-radius: 4px;
}

.no-report {
  text-align: center;
  padding: 40px;
  color: #666;
  background-color: #f5f5f5;
  border-radius: 4px;
}

.modal-footer {
  padding: 20px;
  border-top: 1px solid #eee;
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.btn-info {
  background-color: #17a2b8;
  color: white;
  border: 1px solid #17a2b8;
}

.btn-info:hover {
   background-color: #138496;
   border-color: #117a8b;
 }
 
 .download-buttons {
   display: flex;
   align-items: center;
 }
 
 .btn-outline-primary {
   background-color: transparent;
   color: #007bff;
   border: 1px solid #007bff;
 }
 
 .btn-outline-primary:hover {
   background-color: #007bff;
   color: white;
 }

.pagination-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 20px;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 8px;
}

.pagination-buttons {
  display: flex;
  align-items: center;
  gap: 15px;
}

.pagination-info {
  color: #666;
  font-size: 14px;
}
</style>