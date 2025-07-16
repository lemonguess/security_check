<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'

interface ViolationWord {
  id?: number
  wrong_input: string
  correct_input: string
  violation_score: number
  is_active: boolean
  created_at?: string
  updated_at?: string
}

interface VocabularyResponse {
  items: ViolationWord[]
  total: number
  page: number
  page_size: number
  total_pages: number
}

const vocabularyList = ref<ViolationWord[]>([])
const loading = ref(false)
const showModal = ref(false)
const editingItem = ref<ViolationWord | null>(null)
const searchKeyword = ref('')
const currentPage = ref(1)
const pageSize = ref(10)
const total = ref(0)

// 表单数据
const formData = ref<ViolationWord>({
  wrong_input: '',
  correct_input: '',
  violation_score: 1,
  is_active: true
})

// 表单验证错误
const formErrors = ref<Record<string, string>>({})

// 获取词库列表
const fetchVocabulary = async () => {
  loading.value = true
  try {
    const params = new URLSearchParams({
      page: currentPage.value.toString(),
      size: pageSize.value.toString(),
      ...(searchKeyword.value && { search: searchKeyword.value })
    })
    
    const response = await fetch(`http://localhost:6188/api/v1/vocabulary/words?${params}`)
    
    if (response.ok) {
      const result: VocabularyResponse = await response.json()
      vocabularyList.value = result.items
      total.value = result.total
    } else {
      const errorData = await response.json()
      console.error('获取词库失败:', errorData.detail)
    }
  } catch (error) {
    console.error('获取词库失败:', error)
  } finally {
    loading.value = false
  }
}

// 搜索
const handleSearch = () => {
  currentPage.value = 1
  fetchVocabulary()
}

// 分页
const handlePageChange = (page: number) => {
  currentPage.value = page
  fetchVocabulary()
}

// 打开新增/编辑模态框
const openModal = (item?: ViolationWord) => {
  editingItem.value = item || null
  if (item) {
    formData.value = { ...item }
  } else {
    formData.value = {
      wrong_input: '',
      correct_input: '',
      violation_score: 1,
      is_active: true
    }
  }
  formErrors.value = {}
  showModal.value = true
}

// 关闭模态框
const closeModal = () => {
  showModal.value = false
  editingItem.value = null
  formData.value = {
    wrong_input: '',
    correct_input: '',
    violation_score: 1,
    is_active: true
  }
  formErrors.value = {}
}

// 表单验证
const validateForm = (): boolean => {
  formErrors.value = {}
  
  if (!formData.value.wrong_input.trim()) {
    formErrors.value.wrong_input = '错误输入不能为空'
  }
  
  if (!formData.value.correct_input.trim()) {
    formErrors.value.correct_input = '正确输入不能为空'
  }
  
  if (formData.value.violation_score < 1 || formData.value.violation_score > 100) {
    formErrors.value.violation_score = '违规分数必须在1-100之间'
  }
  
  return Object.keys(formErrors.value).length === 0
}

// 保存词库项
const saveVocabulary = async () => {
  if (!validateForm()) {
    return
  }
  
  loading.value = true
  try {
    const url = editingItem.value 
      ? `http://localhost:6188/api/v1/vocabulary/words/${editingItem.value.id}`
      : 'http://localhost:6188/api/v1/vocabulary/words'
    
    const method = editingItem.value ? 'PUT' : 'POST'
    
    const response = await fetch(url, {
      method,
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(formData.value)
    })
    
    if (response.ok) {
      const result = await response.json()
      closeModal()
      fetchVocabulary()
      // 显示成功通知
      if (typeof window !== 'undefined' && (window as any).showNotification) {
        (window as any).showNotification(
          editingItem.value ? '词库更新成功' : '词库添加成功', 
          'success'
        )
      }
    } else {
      const errorData = await response.json()
      console.error('保存失败:', errorData.detail)
      if (typeof window !== 'undefined' && (window as any).showNotification) {
        (window as any).showNotification(errorData.detail || '保存失败', 'error')
      }
    }
  } catch (error) {
    console.error('保存失败:', error)
    if (typeof window !== 'undefined' && (window as any).showNotification) {
      (window as any).showNotification('保存失败', 'error')
    }
  } finally {
    loading.value = false
  }
}

// 删除词库项
const deleteVocabulary = async (id: number) => {
  if (!confirm('确定要删除这个词库项吗？')) {
    return
  }
  
  loading.value = true
  try {
    const response = await fetch(`http://localhost:6188/api/v1/vocabulary/words/${id}`, {
      method: 'DELETE'
    })
    
    if (response.ok) {
      const result = await response.json()
      fetchVocabulary()
      if (typeof window !== 'undefined' && (window as any).showNotification) {
        (window as any).showNotification('删除成功', 'success')
      }
    } else {
      const errorData = await response.json()
      console.error('删除失败:', errorData.detail)
      if (typeof window !== 'undefined' && (window as any).showNotification) {
        (window as any).showNotification(errorData.detail || '删除失败', 'error')
      }
    }
  } catch (error) {
    console.error('删除失败:', error)
    if (typeof window !== 'undefined' && (window as any).showNotification) {
      (window as any).showNotification('删除失败', 'error')
    }
  } finally {
    loading.value = false
  }
}

// 切换启用状态
const toggleActive = async (item: ViolationWord) => {
  const updatedItem = { ...item, is_active: !item.is_active }
  
  loading.value = true
  try {
    const response = await fetch(`http://localhost:6188/api/v1/vocabulary/words/${item.id}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(updatedItem)
    })
    
    if (response.ok) {
      const result = await response.json()
      fetchVocabulary()
      if (typeof window !== 'undefined' && (window as any).showNotification) {
        (window as any).showNotification(
          updatedItem.is_active ? '已启用' : '已禁用', 
          'success'
        )
      }
    } else {
      const errorData = await response.json()
      console.error('更新失败:', errorData.detail)
      if (typeof window !== 'undefined' && (window as any).showNotification) {
        (window as any).showNotification(errorData.detail || '更新失败', 'error')
      }
    }
  } catch (error) {
    console.error('更新失败:', error)
    if (typeof window !== 'undefined' && (window as any).showNotification) {
      (window as any).showNotification('更新失败', 'error')
    }
  } finally {
    loading.value = false
  }
}

// 生成分页数组
const pageNumbers = computed(() => {
  const totalPages = Math.ceil(total.value / pageSize.value)
  const pages = []
  for (let i = 1; i <= totalPages; i++) {
    pages.push(i)
  }
  return pages
})

onMounted(() => {
  fetchVocabulary()
})
</script>

<template>
  <div class="vocabulary-container">
    <div class="vocabulary-header">
      <h2>词库管理</h2>
      <p>管理违规词库，设置错误输入、正确输入和违规分数</p>
    </div>
    
    <!-- 操作栏 -->
    <div class="vocabulary-toolbar">
      <div class="search-box">
        <input 
          v-model="searchKeyword" 
          type="text" 
          placeholder="搜索错误输入或正确输入..."
          @keyup.enter="handleSearch"
        >
        <button @click="handleSearch" class="search-btn">搜索</button>
      </div>
      <button @click="openModal()" class="add-btn">+ 添加词库</button>
    </div>
    
    <!-- 词库列表 -->
    <div class="vocabulary-table-container">
      <table class="vocabulary-table">
        <thead>
          <tr>
            <th>ID</th>
            <th>错误输入</th>
            <th>正确输入</th>
            <th>违规分数</th>
            <th>状态</th>
            <th>创建时间</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading">
            <td colspan="7" class="loading-cell">加载中...</td>
          </tr>
          <tr v-else-if="vocabularyList.length === 0">
            <td colspan="7" class="empty-cell">暂无数据</td>
          </tr>
          <tr v-else v-for="item in vocabularyList" :key="item.id">
            <td>{{ item.id }}</td>
            <td class="wrong-input">{{ item.wrong_input }}</td>
            <td class="correct-input">{{ item.correct_input }}</td>
            <td>
              <span class="score-badge" :class="{
                'score-low': item.violation_score <= 30,
                'score-medium': item.violation_score > 30 && item.violation_score <= 70,
                'score-high': item.violation_score > 70
              }">
                {{ item.violation_score }}
              </span>
            </td>
            <td>
              <button 
                @click="toggleActive(item)" 
                class="status-btn"
                :class="{ active: item.is_active }"
              >
                {{ item.is_active ? '启用' : '禁用' }}
              </button>
            </td>
            <td>{{ item.created_at }}</td>
            <td class="actions">
              <button @click="openModal(item)" class="edit-btn">编辑</button>
              <button @click="deleteVocabulary(item.id!)" class="delete-btn">删除</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    
    <!-- 分页 -->
    <div v-if="total > pageSize" class="pagination">
      <button 
        @click="handlePageChange(currentPage - 1)" 
        :disabled="currentPage === 1"
        class="page-btn"
      >
        上一页
      </button>
      <button 
        v-for="page in pageNumbers" 
        :key="page"
        @click="handlePageChange(page)"
        class="page-btn"
        :class="{ active: currentPage === page }"
      >
        {{ page }}
      </button>
      <button 
        @click="handlePageChange(currentPage + 1)" 
        :disabled="currentPage === Math.ceil(total / pageSize)"
        class="page-btn"
      >
        下一页
      </button>
    </div>
    
    <!-- 新增/编辑模态框 -->
    <div v-if="showModal" class="modal-overlay" @click="closeModal">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>{{ editingItem ? '编辑词库' : '添加词库' }}</h3>
          <button @click="closeModal" class="close-btn">×</button>
        </div>
        
        <div class="modal-body">
          <div class="form-group">
            <label>错误输入 *</label>
            <input 
              v-model="formData.wrong_input" 
              type="text" 
              placeholder="请输入错误的词汇"
              :class="{ error: formErrors.wrong_input }"
            >
            <span v-if="formErrors.wrong_input" class="error-text">{{ formErrors.wrong_input }}</span>
          </div>
          
          <div class="form-group">
            <label>正确输入 *</label>
            <input 
              v-model="formData.correct_input" 
              type="text" 
              placeholder="请输入正确的词汇"
              :class="{ error: formErrors.correct_input }"
            >
            <span v-if="formErrors.correct_input" class="error-text">{{ formErrors.correct_input }}</span>
          </div>
          
          <div class="form-group">
            <label>违规分数 (1-100) *</label>
            <input 
              v-model.number="formData.violation_score" 
              type="number" 
              min="1" 
              max="100"
              placeholder="请输入1-100的分数"
              :class="{ error: formErrors.violation_score }"
            >
            <span v-if="formErrors.violation_score" class="error-text">{{ formErrors.violation_score }}</span>
          </div>
          
          <div class="form-group">
            <label class="checkbox-label">
              <input v-model="formData.is_active" type="checkbox">
              启用此词库项
            </label>
          </div>
        </div>
        
        <div class="modal-footer">
          <button @click="closeModal" class="cancel-btn">取消</button>
          <button @click="saveVocabulary" class="save-btn" :disabled="loading">
            {{ loading ? '保存中...' : '保存' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.vocabulary-container {
  padding: 20px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.vocabulary-header {
  margin-bottom: 30px;
}

.vocabulary-header h2 {
  color: #2c3e50;
  margin-bottom: 8px;
  font-size: 24px;
  font-weight: 600;
}

.vocabulary-header p {
  color: #7f8c8d;
  font-size: 14px;
}

.vocabulary-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  gap: 20px;
}

.search-box {
  display: flex;
  gap: 10px;
  flex: 1;
  max-width: 400px;
}

.search-box input {
  flex: 1;
  padding: 10px 15px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
}

.search-btn {
  padding: 10px 20px;
  background: #3498db;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  transition: background 0.3s;
}

.search-btn:hover {
  background: #2980b9;
}

.add-btn {
  padding: 10px 20px;
  background: #27ae60;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: background 0.3s;
}

.add-btn:hover {
  background: #229954;
}

.vocabulary-table-container {
  overflow-x: auto;
  margin-bottom: 20px;
}

.vocabulary-table {
  width: 100%;
  border-collapse: collapse;
  background: white;
}

.vocabulary-table th,
.vocabulary-table td {
  padding: 12px 15px;
  text-align: left;
  border-bottom: 1px solid #eee;
}

.vocabulary-table th {
  background: #f8f9fa;
  font-weight: 600;
  color: #2c3e50;
  font-size: 14px;
}

.vocabulary-table td {
  font-size: 14px;
  color: #34495e;
}

.wrong-input {
  color: #e74c3c;
  font-weight: 500;
}

.correct-input {
  color: #27ae60;
  font-weight: 500;
}

.score-badge {
  padding: 4px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
  color: white;
}

.score-low {
  background: #27ae60;
}

.score-medium {
  background: #f39c12;
}

.score-high {
  background: #e74c3c;
}

.status-btn {
  padding: 4px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  background: #f8f9fa;
  color: #6c757d;
  cursor: pointer;
  font-size: 12px;
  transition: all 0.3s;
}

.status-btn.active {
  background: #27ae60;
  color: white;
  border-color: #27ae60;
}

.status-btn:hover {
  background: #e9ecef;
}

.status-btn.active:hover {
  background: #229954;
}

.actions {
  display: flex;
  gap: 8px;
}

.edit-btn,
.delete-btn {
  padding: 4px 8px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  transition: background 0.3s;
}

.edit-btn {
  background: #3498db;
  color: white;
}

.edit-btn:hover {
  background: #2980b9;
}

.delete-btn {
  background: #e74c3c;
  color: white;
}

.delete-btn:hover {
  background: #c0392b;
}

.loading-cell,
.empty-cell {
  text-align: center;
  color: #7f8c8d;
  font-style: italic;
  padding: 40px;
}

.pagination {
  display: flex;
  justify-content: center;
  gap: 8px;
  margin-top: 20px;
}

.page-btn {
  padding: 8px 12px;
  border: 1px solid #ddd;
  background: white;
  color: #34495e;
  cursor: pointer;
  border-radius: 4px;
  font-size: 14px;
  transition: all 0.3s;
}

.page-btn:hover:not(:disabled) {
  background: #f8f9fa;
}

.page-btn.active {
  background: #3498db;
  color: white;
  border-color: #3498db;
}

.page-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 模态框样式 */
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
  border-radius: 8px;
  width: 90%;
  max-width: 500px;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #eee;
}

.modal-header h3 {
  margin: 0;
  color: #2c3e50;
  font-size: 18px;
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #7f8c8d;
  padding: 0;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.close-btn:hover {
  color: #2c3e50;
}

.modal-body {
  padding: 20px;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  color: #2c3e50;
  font-weight: 500;
  font-size: 14px;
}

.form-group input[type="text"],
.form-group input[type="number"] {
  width: 100%;
  padding: 10px 15px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
  transition: border-color 0.3s;
}

.form-group input[type="text"]:focus,
.form-group input[type="number"]:focus {
  outline: none;
  border-color: #3498db;
}

.form-group input.error {
  border-color: #e74c3c;
}

.error-text {
  color: #e74c3c;
  font-size: 12px;
  margin-top: 4px;
  display: block;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.checkbox-label input[type="checkbox"] {
  width: auto;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 20px;
  border-top: 1px solid #eee;
}

.cancel-btn,
.save-btn {
  padding: 10px 20px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: background 0.3s;
}

.cancel-btn {
  background: #f8f9fa;
  color: #6c757d;
  border: 1px solid #ddd;
}

.cancel-btn:hover {
  background: #e9ecef;
}

.save-btn {
  background: #27ae60;
  color: white;
}

.save-btn:hover:not(:disabled) {
  background: #229954;
}

.save-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .vocabulary-toolbar {
    flex-direction: column;
    align-items: stretch;
  }
  
  .search-box {
    max-width: none;
  }
  
  .vocabulary-table {
    font-size: 12px;
  }
  
  .vocabulary-table th,
  .vocabulary-table td {
    padding: 8px 10px;
  }
  
  .modal-content {
    width: 95%;
    margin: 20px;
  }
  
  .modal-body {
    padding: 15px;
  }
  
  .modal-footer {
    padding: 15px;
  }
}
</style>