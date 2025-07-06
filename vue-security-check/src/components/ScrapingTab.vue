<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import ColumnTypeSelector from './ColumnTypeSelector.vue'
import ContentList from './ContentList.vue'
import ProgressModal from './ProgressModal.vue'

// 定义emit
const emit = defineEmits<{
  switchToAudit: []
}>()

const selectedColumnType = ref('')
const isScrapingInProgress = ref(false)
const showModal = ref(false)
const testResults = ref(null)
const contentList = ref([])
const showContentContainer = ref(false)

const modalData = reactive({
  title: '🚀 正在抓取内容',
  progress: 0,
  status: '准备开始抓取...',
  results: null,
  showCloseBtn: false
})

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

const canStartScraping = computed(() => {
  return selectedColumnType.value && !isScrapingInProgress.value
})

const handleColumnTypeSelect = (type: string) => {
  if (isScrapingInProgress.value) {
    window.showNotification('抓取进行中，无法更改选择', 'warning')
    return
  }
  selectedColumnType.value = type
}

const startScraping = async () => {
  if (!selectedColumnType.value) {
    window.showNotification('请先选择栏目类型', 'warning')
    return
  }
  
  if (isScrapingInProgress.value) {
    window.showNotification('抓取正在进行中', 'warning')
    return
  }
  
  isScrapingInProgress.value = true
  showModal.value = true
  
  // 重置模态框数据
  modalData.title = '🚀 正在抓取内容'
  modalData.progress = 0
  modalData.status = '准备开始抓取...'
  modalData.results = null
  modalData.showCloseBtn = false
  
  try {
    console.log('开始抓取，栏目类型:', selectedColumnType.value)
    
    // 模拟进度更新
    const progressSteps = [
      { progress: 10, message: '正在连接服务器...', delay: 1000 },
      { progress: 25, message: '正在分析网站结构...', delay: 2000 },
      { progress: 40, message: '正在提取内容...', delay: 2000 },
      { progress: 60, message: '正在处理媒体文件...', delay: 1500 },
      { progress: 80, message: '正在保存数据...', delay: 1000 },
      { progress: 100, message: '抓取完成！', delay: 500 }
    ]
    
    // 开始API请求
    const apiPromise = performScraping()
    
    // 同时进行进度动画
    for (const step of progressSteps) {
      await new Promise(resolve => setTimeout(resolve, step.delay))
      modalData.progress = step.progress
      modalData.status = step.message
    }
    
    // 等待API完成
    const result = await apiPromise
    
    if (result.success) {
      modalData.title = '✅ 抓取完成'
      modalData.status = '数据抓取成功完成！'
      modalData.results = result.data
      modalData.showCloseBtn = true
      
      // 显示结果
      if (result.data && result.data.content_list) {
        contentList.value = result.data.content_list
        showContentContainer.value = true
      }
      
      window.showNotification('抓取完成！', 'success')
      
      // 3秒后自动切换到内容审核标签
      setTimeout(() => {
        closeModal()
        emit('switchToAudit')
      }, 3000)
    } else {
      throw new Error(result.message || '抓取失败')
    }
    
  } catch (error) {
    console.error('抓取失败:', error)
    const errorMessage = error instanceof Error ? error.message : '未知错误'
    modalData.title = '❌ 抓取失败'
    modalData.status = `抓取失败: ${errorMessage}`
    modalData.showCloseBtn = true
    window.showNotification(`抓取失败: ${errorMessage}`, 'error')
  } finally {
    isScrapingInProgress.value = false
  }
}

const performScraping = async () => {
  const API_BASE = `${window.location.protocol}//${window.location.hostname}:6188`
  const response = await fetch(`${API_BASE}/api/v1/scrape`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      column_type: selectedColumnType.value
    })
  })
  
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${response.statusText}`)
  }
  
  const result = await response.json()
  return result
}



const closeModal = () => {
  showModal.value = false
}

const startCountdownAndRedirect = () => {
  // 3秒后自动跳转到审核页面
  setTimeout(() => {
    closeModal()
    // 触发父组件切换到审核页面
    // 这里需要通过事件或者状态管理来实现
  }, 3000)
}
</script>

<template>
  <div class="tab-content">
    <!-- 栏目类型选择区域 -->
    <ColumnTypeSelector
      :column-types="columnTypes"
      :selected-type="selectedColumnType"
      :disabled="isScrapingInProgress"
      @select="handleColumnTypeSelect"
    />
    
    <div class="scrape-controls">
      <div class="selected-type">
        <span>已选择: </span>
        <span class="selected-type-text">
          {{ selectedColumnType || '请选择栏目类型' }}
        </span>
      </div>
      <button 
        class="btn btn-success" 
        :disabled="!canStartScraping"
        @click="startScraping"
      >
        🚀 开始抓取
      </button>
    </div>
    
    <!-- 测试结果显示 -->
    <div v-if="testResults" class="test-results">
      <!-- 测试结果内容 -->
    </div>
    
    <!-- 抓取内容列表 -->
    <ContentList 
      v-if="showContentContainer"
      :content-list="contentList"
      type="scraping"
    />
    
    <!-- 进度模态框 -->
    <ProgressModal
      v-if="showModal"
      :title="modalData.title"
      :progress="modalData.progress"
      :status="modalData.status"
      :results="modalData.results"
      :show-close-btn="modalData.showCloseBtn"
      @close="closeModal"
      @countdown-redirect="startCountdownAndRedirect"
    />
  </div>
</template>

<style scoped>
.tab-content {
  padding: 30px;
}

.scrape-controls {
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

.btn-success {
  background: #28a745;
  color: white;
}

.btn-success:hover:not(:disabled) {
  background: #218838;
  transform: translateY(-2px);
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none !important;
}

.test-results {
  margin-top: 20px;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
}
</style>