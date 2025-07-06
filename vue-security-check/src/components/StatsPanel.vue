<script setup lang="ts">
import { ref, onMounted } from 'vue'

interface Stats {
  totalAudits: string
  successRate: string
  avgProcessingTime: string
  todayAudits: string
}

const stats = ref<Stats>({
  totalAudits: '-',
  successRate: '-',
  avgProcessingTime: '-',
  todayAudits: '-'
})

const loadStats = async () => {
  try {
    const API_BASE = `${window.location.protocol}//${window.location.hostname}:6188`
    const response = await fetch(`${API_BASE}/api/v1/moderation/stats`)
    if (response.ok) {
      const data = await response.json()
      if (data.success) {
        stats.value = {
          totalAudits: data.data.total_audits?.toString() || '0',
          successRate: `${data.data.success_rate?.toFixed(1)}%` || '0%',
          avgProcessingTime: `${data.data.avg_processing_time?.toFixed(2)}s` || '0s',
          todayAudits: data.data.today_audits?.toString() || '0'
        }
      }
    }
  } catch (error) {
    console.error('加载统计数据失败:', error)
    const errorMessage = error instanceof Error ? error.message : '未知错误'
    window.showNotification(`统计数据加载失败: ${errorMessage}`, 'error')
  }
}

onMounted(() => {
  loadStats()
})
</script>

<template>
  <div class="stats-container">
    <div class="stats-grid">
      <div class="stat-card">
        <h3>{{ stats.totalAudits }}</h3>
        <p>总审核量</p>
      </div>
      <div class="stat-card">
        <h3>{{ stats.successRate }}</h3>
        <p>成功率</p>
      </div>
      <div class="stat-card">
        <h3>{{ stats.avgProcessingTime }}</h3>
        <p>平均处理时间</p>
      </div>
      <div class="stat-card">
        <h3>{{ stats.todayAudits }}</h3>
        <p>今日审核量</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.stats-container {
  padding: 30px;
  background: white;
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
</style>