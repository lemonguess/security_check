<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'

interface Props {
  dashboardType?: 'time' | 'platform'
}

const props = withDefaults(defineProps<Props>(), {
  dashboardType: 'time'
})

interface TimeStats {
  todayAlerts: number
  todayResolutions: number
  weekAlerts: number
  weekResolutions: number
  monthAlerts: number
  monthResolutions: number
  yearAlerts: number
  yearResolutions: number
}

interface PlatformStats {
  provincialExternalAlerts: number
  provincialExternalResolutions: number
  municipalExternalAlerts: number
  municipalExternalResolutions: number
  provincialMediaAlerts: number
  provincialMediaResolutions: number
  municipalMediaAlerts: number
  municipalMediaResolutions: number
}

const timeStats = ref<TimeStats>({
  todayAlerts: 0,
  todayResolutions: 0,
  weekAlerts: 0,
  weekResolutions: 0,
  monthAlerts: 0,
  monthResolutions: 0,
  yearAlerts: 0,
  yearResolutions: 0
})

const platformStats = ref<PlatformStats>({
  provincialExternalAlerts: 0,
  provincialExternalResolutions: 0,
  municipalExternalAlerts: 0,
  municipalExternalResolutions: 0,
  provincialMediaAlerts: 0,
  provincialMediaResolutions: 0,
  municipalMediaAlerts: 0,
  municipalMediaResolutions: 0
})

const selectedTimeRange = ref('today')
const customStartDate = ref('')
const customEndDate = ref('')

const loadTimeStats = async () => {
  try {
    const API_BASE = `${window.location.protocol}//${window.location.hostname}:6188`
    const response = await fetch(`${API_BASE}/api/v1/dashboard/time-stats`)
    if (response.ok) {
      const data = await response.json()
      if (data.success) {
        timeStats.value = data.data
      }
    }
  } catch (error) {
    console.error('加载时段统计数据失败:', error)
  }
}

const loadPlatformStats = async () => {
  try {
    const API_BASE = `${window.location.protocol}//${window.location.hostname}:6188`
    const response = await fetch(`${API_BASE}/api/v1/dashboard/platform-stats`)
    if (response.ok) {
      const data = await response.json()
      if (data.success) {
        platformStats.value = data.data
      }
    }
  } catch (error) {
    console.error('加载平台统计数据失败:', error)
  }
}

const queryCustomRange = async () => {
  if (!customStartDate.value || !customEndDate.value) {
    window.showNotification('请选择开始和结束日期', 'warning')
    return
  }
  
  try {
    const API_BASE = `${window.location.protocol}//${window.location.hostname}:6188`
    const response = await fetch(`${API_BASE}/api/v1/dashboard/custom-range?start=${customStartDate.value}&end=${customEndDate.value}`)
    if (response.ok) {
      const data = await response.json()
      if (data.success) {
        // 处理自定义时间段查询结果
        console.log('自定义时间段数据:', data.data)
      }
    }
  } catch (error) {
    console.error('查询自定义时间段数据失败:', error)
  }
}

onMounted(() => {
  if (props.dashboardType === 'time') {
    loadTimeStats()
  } else if (props.dashboardType === 'platform') {
    loadPlatformStats()
  }
})
</script>

<template>
  <div class="stats-container">
    <!-- 全时段看板 -->
    <div v-if="dashboardType === 'time'" class="time-dashboard">
      <h2 class="dashboard-title">全时段看板</h2>
      
      <!-- 时段统计卡片 -->
      <div class="stats-grid">
        <div class="stat-card">
          <h3>{{ timeStats.todayAlerts }}</h3>
          <p>今日预警</p>
          <small>处置: {{ timeStats.todayResolutions }}</small>
        </div>
        <div class="stat-card">
          <h3>{{ timeStats.weekAlerts }}</h3>
          <p>本周预警</p>
          <small>处置: {{ timeStats.weekResolutions }}</small>
        </div>
        <div class="stat-card">
          <h3>{{ timeStats.monthAlerts }}</h3>
          <p>本月预警</p>
          <small>处置: {{ timeStats.monthResolutions }}</small>
        </div>
        <div class="stat-card">
          <h3>{{ timeStats.yearAlerts }}</h3>
          <p>今年预警</p>
          <small>处置: {{ timeStats.yearResolutions }}</small>
        </div>
      </div>
      
      <!-- 趋势图区域 -->
      <div class="chart-section">
        <h3>预警与处置趋势</h3>
        <div class="chart-placeholder">
          <p>趋势图将在此显示（预警线和处置线）</p>
        </div>
      </div>
      
      <!-- 自定义时间段查询 -->
      <div class="custom-query">
        <h3>自定义时间段查询</h3>
        <div class="query-form">
          <input 
            v-model="customStartDate" 
            type="date" 
            placeholder="开始日期"
            class="date-input"
          >
          <input 
            v-model="customEndDate" 
            type="date" 
            placeholder="结束日期"
            class="date-input"
          >
          <button @click="queryCustomRange" class="query-btn">查询</button>
        </div>
      </div>
    </div>
    
    <!-- 全平台看板 -->
    <div v-else-if="dashboardType === 'platform'" class="platform-dashboard">
      <h2 class="dashboard-title">全平台看板</h2>
      
      <div class="platform-sections">
        <!-- 省局外网 -->
        <div class="platform-section">
          <h3>省局外网</h3>
          <div class="platform-stats">
            <div class="stat-item">
              <span class="stat-label">预警:</span>
              <span class="stat-value">{{ platformStats.provincialExternalAlerts }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">处置:</span>
              <span class="stat-value">{{ platformStats.provincialExternalResolutions }}</span>
            </div>
          </div>
        </div>
        
        <!-- 市州外网 -->
        <div class="platform-section">
          <h3>市州外网</h3>
          <div class="platform-stats">
            <div class="stat-item">
              <span class="stat-label">预警:</span>
              <span class="stat-value">{{ platformStats.municipalExternalAlerts }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">处置:</span>
              <span class="stat-value">{{ platformStats.municipalExternalResolutions }}</span>
            </div>
          </div>
        </div>
        
        <!-- 省局新媒体 -->
        <div class="platform-section">
          <h3>省局新媒体</h3>
          <div class="platform-stats">
            <div class="stat-item">
              <span class="stat-label">预警:</span>
              <span class="stat-value">{{ platformStats.provincialMediaAlerts }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">处置:</span>
              <span class="stat-value">{{ platformStats.provincialMediaResolutions }}</span>
            </div>
          </div>
        </div>
        
        <!-- 市州新媒体 -->
        <div class="platform-section">
          <h3>市州新媒体</h3>
          <div class="platform-stats">
            <div class="stat-item">
              <span class="stat-label">预警:</span>
              <span class="stat-value">{{ platformStats.municipalMediaAlerts }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">处置:</span>
              <span class="stat-value">{{ platformStats.municipalMediaResolutions }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.stats-container {
  padding: 30px;
  background: white;
  min-height: 100vh;
}

.dashboard-title {
  font-size: 1.8em;
  color: #2c3e50;
  margin-bottom: 30px;
  text-align: center;
  font-weight: 600;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.stat-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 25px;
  border-radius: 12px;
  text-align: center;
  box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 15px 35px rgba(102, 126, 234, 0.4);
}

.stat-card h3 {
  font-size: 2.2em;
  margin-bottom: 8px;
  font-weight: 700;
}

.stat-card p {
  font-size: 1em;
  opacity: 0.9;
  margin: 0;
}

.stat-card small {
  font-size: 0.8em;
  opacity: 0.8;
  display: block;
  margin-top: 5px;
}

/* 趋势图区域 */
.chart-section {
  margin: 40px 0;
  padding: 30px;
  background: #f8f9fa;
  border-radius: 12px;
  border: 1px solid #e9ecef;
}

.chart-section h3 {
  color: #495057;
  margin-bottom: 20px;
  font-size: 1.3em;
}

.chart-placeholder {
  height: 300px;
  background: white;
  border: 2px dashed #dee2e6;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #6c757d;
  font-style: italic;
}

/* 自定义查询区域 */
.custom-query {
  margin-top: 40px;
  padding: 25px;
  background: #f8f9fa;
  border-radius: 12px;
  border: 1px solid #e9ecef;
}

.custom-query h3 {
  color: #495057;
  margin-bottom: 20px;
  font-size: 1.3em;
}

.query-form {
  display: flex;
  gap: 15px;
  align-items: center;
  flex-wrap: wrap;
}

.date-input {
  padding: 10px 15px;
  border: 1px solid #ced4da;
  border-radius: 6px;
  font-size: 14px;
  min-width: 150px;
}

.query-btn {
  padding: 10px 20px;
  background: #007bff;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  transition: background 0.3s ease;
}

.query-btn:hover {
  background: #0056b3;
}

/* 全平台看板样式 */
.platform-sections {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 25px;
}

.platform-section {
  background: #f8f9fa;
  padding: 25px;
  border-radius: 12px;
  border: 1px solid #e9ecef;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.platform-section:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
}

.platform-section h3 {
  color: #495057;
  margin-bottom: 20px;
  font-size: 1.3em;
  text-align: center;
  padding-bottom: 10px;
  border-bottom: 2px solid #dee2e6;
}

.platform-stats {
  display: flex;
  justify-content: space-around;
  align-items: center;
}

.stat-item {
  text-align: center;
  padding: 15px;
}

.stat-label {
  display: block;
  color: #6c757d;
  font-size: 0.9em;
  margin-bottom: 8px;
}

.stat-value {
  display: block;
  color: #495057;
  font-size: 1.8em;
  font-weight: 600;
}
</style>