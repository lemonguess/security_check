<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import ColumnTypeSelector from './ColumnTypeSelector.vue'
import ContentList from './ContentList.vue'

interface Props {
  checkType?: 'text' | 'image' | 'audio' | 'video' | 'audit'
}

const props = withDefaults(defineProps<Props>(), {
  checkType: 'audit'
})

const activeSubTab = ref('audit') // 新增：子标签状态

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

// 前置校对相关状态
const textContent = ref('')
const selectedFiles = ref<FileList | null>(null)
const isAuditing = ref(false)
interface AuditResult {
  final_decision: string
  final_score: number
  processing_time: number
  risk_reasons: string[]
  violated_categories: string[]
  ai_result: {
    decision: string
    score: number
    risk_level: string
    confidence_score: number
  }
  rule_result: {
    decision: string
    score: number
    risk_level: string
    sensitive_matches: number
  }
}

const auditResult = ref<AuditResult | null>(null)
const showAuditModal = ref(false)

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

// 子标签切换
const switchSubTab = (tab: string) => {
  activeSubTab.value = tab
}

// 文件选择处理
const handleFileSelect = (event: Event) => {
  const target = event.target as HTMLInputElement
  selectedFiles.value = target.files
}

// 前置校对审核 - 文字
const performTextAudit = async () => {
  if (!textContent.value.trim()) {
    window.showNotification('请输入要审核的文本内容', 'warning')
    return
  }
  
  isAuditing.value = true
  showAuditModal.value = true
  auditResult.value = null
  
  try {
    const API_BASE = `${window.location.protocol}//${window.location.hostname}:6188`
    const response = await fetch(`${API_BASE}/api/v1/moderation/text`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        content: textContent.value,
        timeout: 30.0
      })
    })
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`)
    }
    
    const result = await response.json()
    
    if (result.success) {
      auditResult.value = result.data
      window.showNotification('文字审核完成', 'success')
    } else {
      throw new Error(result.message || '审核失败')
    }
    
  } catch (error) {
    console.error('文字审核失败:', error)
    const errorMessage = error instanceof Error ? error.message : '未知错误'
    window.showNotification(`审核失败: ${errorMessage}`, 'error')
  } finally {
    isAuditing.value = false
  }
}

// 前置校对审核 - 图片
const performImageAudit = async () => {
  if (!selectedFiles.value || selectedFiles.value.length === 0) {
    window.showNotification('请选择要审核的图片文件', 'warning')
    return
  }
  
  isAuditing.value = true
  showAuditModal.value = true
  auditResult.value = null
  
  try {
    const formData = new FormData()
    for (let i = 0; i < selectedFiles.value.length; i++) {
      formData.append('images', selectedFiles.value[i])
    }
    
    const API_BASE = `${window.location.protocol}//${window.location.hostname}:6188`
    const response = await fetch(`${API_BASE}/api/v1/check/images`, {
      method: 'POST',
      body: formData
    })
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`)
    }
    
    const result = await response.json()
    
    if (result.success) {
      auditResult.value = result.data
      window.showNotification('图片审核完成', 'success')
    } else {
      throw new Error(result.message || '审核失败')
    }
    
  } catch (error) {
    console.error('图片审核失败:', error)
    const errorMessage = error instanceof Error ? error.message : '未知错误'
    window.showNotification(`审核失败: ${errorMessage}`, 'error')
  } finally {
    isAuditing.value = false
  }
}

// 前置校对审核 - 音频
const performAudioAudit = async () => {
  if (!selectedFiles.value || selectedFiles.value.length === 0) {
    window.showNotification('请选择要审核的音频文件', 'warning')
    return
  }
  
  isAuditing.value = true
  showAuditModal.value = true
  auditResult.value = null
  
  try {
    const formData = new FormData()
    for (let i = 0; i < selectedFiles.value.length; i++) {
      formData.append('audios', selectedFiles.value[i])
    }
    
    const API_BASE = `${window.location.protocol}//${window.location.hostname}:6188`
    const response = await fetch(`${API_BASE}/api/v1/check/audios`, {
      method: 'POST',
      body: formData
    })
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`)
    }
    
    const result = await response.json()
    
    if (result.success) {
      auditResult.value = result.data
      window.showNotification('音频审核完成', 'success')
    } else {
      throw new Error(result.message || '审核失败')
    }
    
  } catch (error) {
    console.error('音频审核失败:', error)
    const errorMessage = error instanceof Error ? error.message : '未知错误'
    window.showNotification(`审核失败: ${errorMessage}`, 'error')
  } finally {
    isAuditing.value = false
  }
}

// 前置校对审核 - 视频
const performVideoAudit = async () => {
  if (!selectedFiles.value || selectedFiles.value.length === 0) {
    window.showNotification('请选择要审核的视频文件', 'warning')
    return
  }
  
  isAuditing.value = true
  showAuditModal.value = true
  auditResult.value = null
  
  try {
    const formData = new FormData()
    for (let i = 0; i < selectedFiles.value.length; i++) {
      formData.append('videos', selectedFiles.value[i])
    }
    
    const API_BASE = `${window.location.protocol}//${window.location.hostname}:6188`
    const response = await fetch(`${API_BASE}/api/v1/check/videos`, {
      method: 'POST',
      body: formData
    })
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`)
    }
    
    const result = await response.json()
    
    if (result.success) {
      auditResult.value = result.data
      window.showNotification('视频审核完成', 'success')
    } else {
      throw new Error(result.message || '审核失败')
    }
    
  } catch (error) {
    console.error('视频审核失败:', error)
    const errorMessage = error instanceof Error ? error.message : '未知错误'
    window.showNotification(`审核失败: ${errorMessage}`, 'error')
  } finally {
    isAuditing.value = false
  }
}

// 关闭审核结果弹窗
const closeAuditModal = () => {
  showAuditModal.value = false
  auditResult.value = null
}

// 获取风险等级的显示样式
const getRiskLevelClass = (riskLevel: string) => {
  switch (riskLevel) {
    case 'SAFE': return 'risk-safe'
    case 'SUSPICIOUS': return 'risk-suspicious'
    case 'RISKY': return 'risk-risky'
    default: return 'risk-unknown'
  }
}

// 获取风险等级的中文显示
const getRiskLevelText = (riskLevel: string) => {
  switch (riskLevel) {
    case 'SAFE': return '安全'
    case 'SUSPICIOUS': return '可疑'
    case 'RISKY': return '风险'
    default: return '未知'
  }
}


</script>

<template>
  <div class="tab-content">
    <!-- 事前合规校对 - 文字校对 -->
    <div v-if="checkType === 'text'" class="text-check-content">
      <div class="check-container">
        <h3 class="check-title">📝 文字校对</h3>
        <p class="check-desc">输入文本内容进行实时审核检测</p>
        
        <div class="text-input-section">
          <label for="textContent" class="input-label">文本内容：</label>
          <textarea
            id="textContent"
            v-model="textContent"
            class="text-input"
            placeholder="请输入要审核的文本内容..."
            rows="8"
            :disabled="isAuditing"
          ></textarea>
        </div>
        
        <div class="action-section">
          <button 
            class="audit-btn"
            @click="performTextAudit"
            :disabled="isAuditing || !textContent.trim()"
          >
            <span v-if="isAuditing">⏳ 审核中...</span>
            <span v-else>🔍 开始审核</span>
          </button>
        </div>
      </div>
    </div>
    
    <!-- 事前合规校对 - 图片校对 -->
    <div v-else-if="checkType === 'image'" class="image-check-content">
      <div class="check-container">
        <h3 class="check-title">🖼️ 图片校对</h3>
        <p class="check-desc">上传图片文件进行审核检测</p>
        
        <div class="file-input-section">
          <label for="imageFiles" class="input-label">选择图片：</label>
          <input
            id="imageFiles"
            type="file"
            multiple
            accept="image/*"
            @change="handleFileSelect"
            class="file-input"
            :disabled="isAuditing"
          >
          <div v-if="selectedFiles && selectedFiles.length > 0" class="file-list">
            <p>已选择 {{ selectedFiles.length }} 个文件：</p>
            <ul>
              <li v-for="(file, index) in Array.from(selectedFiles)" :key="index">
                {{ file.name }} ({{ (file.size / 1024 / 1024).toFixed(2) }}MB)
              </li>
            </ul>
          </div>
        </div>
        
        <div class="action-section">
          <button 
            class="audit-btn"
            @click="performImageAudit"
            :disabled="isAuditing || !selectedFiles || selectedFiles.length === 0"
          >
            <span v-if="isAuditing">⏳ 审核中...</span>
            <span v-else>🔍 开始审核</span>
          </button>
        </div>
      </div>
    </div>
    
    <!-- 事前合规校对 - 音频校对 -->
    <div v-else-if="checkType === 'audio'" class="audio-check-content">
      <div class="check-container">
        <h3 class="check-title">🎵 音频校对</h3>
        <p class="check-desc">上传音频文件进行审核检测</p>
        
        <div class="file-input-section">
          <label for="audioFiles" class="input-label">选择音频：</label>
          <input
            id="audioFiles"
            type="file"
            multiple
            accept="audio/*"
            @change="handleFileSelect"
            class="file-input"
            :disabled="isAuditing"
          >
          <div v-if="selectedFiles && selectedFiles.length > 0" class="file-list">
            <p>已选择 {{ selectedFiles.length }} 个文件：</p>
            <ul>
              <li v-for="(file, index) in Array.from(selectedFiles)" :key="index">
                {{ file.name }} ({{ (file.size / 1024 / 1024).toFixed(2) }}MB)
              </li>
            </ul>
          </div>
        </div>
        
        <div class="action-section">
          <button 
            class="audit-btn"
            @click="performAudioAudit"
            :disabled="isAuditing || !selectedFiles || selectedFiles.length === 0"
          >
            <span v-if="isAuditing">⏳ 审核中...</span>
            <span v-else>🔍 开始审核</span>
          </button>
        </div>
      </div>
    </div>
    
    <!-- 事前合规校对 - 视频校对 -->
    <div v-else-if="checkType === 'video'" class="video-check-content">
      <div class="check-container">
        <h3 class="check-title">🎬 视频校对</h3>
        <p class="check-desc">上传视频文件进行审核检测</p>
        
        <div class="file-input-section">
          <label for="videoFiles" class="input-label">选择视频：</label>
          <input
            id="videoFiles"
            type="file"
            multiple
            accept="video/*"
            @change="handleFileSelect"
            class="file-input"
            :disabled="isAuditing"
          >
          <div v-if="selectedFiles && selectedFiles.length > 0" class="file-list">
            <p>已选择 {{ selectedFiles.length }} 个文件：</p>
            <ul>
              <li v-for="(file, index) in Array.from(selectedFiles)" :key="index">
                {{ file.name }} ({{ (file.size / 1024 / 1024).toFixed(2) }}MB)
              </li>
            </ul>
          </div>
        </div>
        
        <div class="action-section">
          <button 
            class="audit-btn"
            @click="performVideoAudit"
            :disabled="isAuditing || !selectedFiles || selectedFiles.length === 0"
          >
            <span v-if="isAuditing">⏳ 审核中...</span>
            <span v-else>🔍 开始审核</span>
          </button>
        </div>
      </div>
    </div>
    
    <!-- 事后合规监测 - 内容审核 -->
    <div v-else-if="checkType === 'audit'" class="audit-tab-content">
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
    
    <!-- 审核结果弹窗 -->
    <div v-if="showAuditModal" class="modal-overlay" @click="closeAuditModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>📊 审核结果</h3>
          <button class="close-btn" @click="closeAuditModal">×</button>
        </div>
        
        <div class="modal-body">
          <div v-if="isAuditing" class="loading-section">
            <div class="loading-spinner"></div>
            <p>正在审核内容，请稍候...</p>
          </div>
          
          <div v-else-if="auditResult" class="result-section">
            <div class="result-summary">
              <div class="risk-level">
                <span class="label">风险等级：</span>
                <span :class="['risk-badge', getRiskLevelClass(auditResult.final_decision)]">
                  {{ getRiskLevelText(auditResult.final_decision) }}
                </span>
              </div>
              <div class="risk-score">
                <span class="label">风险评分：</span>
                <span class="score">{{ (auditResult.final_score * 100).toFixed(1) }}%</span>
              </div>
              <div class="processing-time">
                <span class="label">处理时间：</span>
                <span class="time">{{ auditResult.processing_time.toFixed(2) }}秒</span>
              </div>
            </div>
            
            <div v-if="auditResult.risk_reasons && auditResult.risk_reasons.length > 0" class="risk-reasons">
              <h4>风险原因：</h4>
              <ul>
                <li v-for="reason in auditResult.risk_reasons" :key="reason">{{ reason }}</li>
              </ul>
            </div>
            
            <div v-if="auditResult.violated_categories && auditResult.violated_categories.length > 0" class="violated-categories">
              <h4>违规分类：</h4>
              <div class="category-tags">
                <span v-for="category in auditResult.violated_categories" :key="category" class="category-tag">
                  {{ category }}
                </span>
              </div>
            </div>
            
            <div class="engine-results">
              <div v-if="auditResult.ai_result" class="engine-result">
                <h4>🤖 AI检测结果：</h4>
                <p>风险等级: {{ getRiskLevelText(auditResult.ai_result.risk_level) }}</p>
                <p>置信度: {{ (auditResult.ai_result.confidence_score * 100).toFixed(1) }}%</p>
              </div>
              
              <div v-if="auditResult.rule_result" class="engine-result">
                <h4>📋 规则检测结果：</h4>
                <p>风险等级: {{ getRiskLevelText(auditResult.rule_result.risk_level) }}</p>
                <p>敏感词匹配: {{ auditResult.rule_result.sensitive_matches }}个</p>
              </div>
            </div>
          </div>
        </div>
        
        <div class="modal-footer">
          <button class="close-modal-btn" @click="closeAuditModal">关闭</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.tab-content {
  padding: 30px;
}

/* 子标签导航样式 */
.sub-tab-navigation {
  display: flex;
  gap: 10px;
  margin-bottom: 30px;
  border-bottom: 2px solid #e9ecef;
  padding-bottom: 10px;
}

.sub-tab-btn {
  padding: 12px 24px;
  border: none;
  background: #f8f9fa;
  color: #6c757d;
  border-radius: 8px 8px 0 0;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.sub-tab-btn:hover {
  background: #e9ecef;
  color: #495057;
}

.sub-tab-btn.active {
  background: #c41e3a;
  color: white;
  box-shadow: 0 2px 4px rgba(196, 30, 58, 0.2);
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
  color: #000000;
}

.selected-type-text {
  color: #c41e3a;
  font-weight: 600;
}

.audit-content-container {
  margin-top: 30px;
}

/* 校对容器通用样式 */
.check-container {
  max-width: 800px;
  margin: 0 auto;
  padding: 30px;
  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.check-title {
  font-size: 24px;
  font-weight: 700;
  color: #2c3e50;
  margin-bottom: 10px;
  text-align: center;
}

.check-desc {
  font-size: 16px;
  color: #6c757d;
  text-align: center;
  margin-bottom: 30px;
}

/* 文件上传样式 */
.file-input-section {
  margin-bottom: 25px;
}

.file-input {
  width: 100%;
  padding: 12px;
  border: 2px dashed #dee2e6;
  border-radius: 8px;
  background: #f8f9fa;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.file-input:hover {
  border-color: #007bff;
  background: #e3f2fd;
}

.file-input:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.file-list {
  margin-top: 15px;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #dee2e6;
}

.file-list p {
  margin: 0 0 10px 0;
  font-weight: 600;
  color: #495057;
}

.file-list ul {
  margin: 0;
  padding-left: 20px;
}

.file-list li {
  margin-bottom: 5px;
  color: #6c757d;
  font-size: 14px;
}

.text-input-section {
  margin-bottom: 30px;
}

.input-label {
  display: block;
  font-size: 16px;
  font-weight: 600;
  color: #2c3e50;
  margin-bottom: 10px;
}

.text-input {
  width: 100%;
  padding: 15px;
  border: 2px solid #e9ecef;
  border-radius: 8px;
  font-size: 14px;
  line-height: 1.5;
  resize: vertical;
  transition: border-color 0.3s ease;
}

.text-input:focus {
  outline: none;
  border-color: #c41e3a;
  box-shadow: 0 0 0 3px rgba(196, 30, 58, 0.1);
}

.text-input:disabled {
  background-color: #f8f9fa;
  cursor: not-allowed;
}

.action-section {
  text-align: center;
}

.audit-btn {
  padding: 15px 40px;
  background: linear-gradient(135deg, #c41e3a, #a91b2e);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 6px rgba(196, 30, 58, 0.2);
}

.audit-btn:hover:not(:disabled) {
  background: linear-gradient(135deg, #a91b2e, #8b1426);
  transform: translateY(-2px);
  box-shadow: 0 6px 12px rgba(196, 30, 58, 0.3);
}

.audit-btn:disabled {
  background: #6c757d;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}

/* 弹窗样式 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 12px;
  max-width: 600px;
  width: 90%;
  max-height: 80vh;
  overflow-y: auto;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 30px;
  border-bottom: 1px solid #e9ecef;
}

.modal-header h3 {
  margin: 0;
  font-size: 20px;
  font-weight: 700;
  color: #2c3e50;
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #6c757d;
  padding: 0;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.close-btn:hover {
  color: #c41e3a;
}

.modal-body {
  padding: 30px;
}

.loading-section {
  text-align: center;
  padding: 40px 20px;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #c41e3a;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 20px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.result-section {
  space-y: 20px;
}

.result-summary {
  background: #f8f9fa;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 20px;
}

.result-summary > div {
  margin-bottom: 10px;
  display: flex;
  align-items: center;
}

.result-summary > div:last-child {
  margin-bottom: 0;
}

.label {
  font-weight: 600;
  margin-right: 10px;
  min-width: 80px;
  color: #000000;
}

.risk-badge {
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
}

.risk-safe {
  background: #d4edda;
  color: #155724;
}

.risk-suspicious {
  background: #fff3cd;
  color: #856404;
}

.risk-risky {
  background: #f8d7da;
  color: #721c24;
}

.risk-unknown {
  background: #e2e3e5;
  color: #383d41;
}

.score {
  font-weight: 600;
  color: #c41e3a;
}

.time {
  font-weight: 600;
  color: #28a745;
}

.risk-reasons, .violated-categories, .engine-results {
  margin-bottom: 20px;
}

.risk-reasons h4, .violated-categories h4, .engine-result h4 {
  margin: 0 0 10px 0;
  font-size: 16px;
  font-weight: 600;
  color: #2c3e50;
}

.risk-reasons ul {
  margin: 0;
  padding-left: 20px;
}

.risk-reasons li {
  margin-bottom: 5px;
  color: #6c757d;
}

.category-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.category-tag {
  background: #e9ecef;
  color: #495057;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.engine-results {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.engine-result {
  background: #f8f9fa;
  padding: 15px;
  border-radius: 8px;
}

.engine-result p {
  margin: 5px 0;
  font-size: 14px;
  color: #6c757d;
}

.modal-footer {
  padding: 20px 30px;
  border-top: 1px solid #e9ecef;
  text-align: right;
}

.close-modal-btn {
  padding: 10px 20px;
  background: #6c757d;
  color: white;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: background-color 0.3s ease;
}

.close-modal-btn:hover {
  background: #5a6268;
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