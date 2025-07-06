<script setup lang="ts">
import { ref, computed } from 'vue'

interface Props {
  title: string
  progress: number
  status: string
  results?: any
  showCloseBtn: boolean
}

interface Emits {
  (e: 'close'): void
  (e: 'countdown-redirect'): void
}

defineProps<Props>()
const emit = defineEmits<Emits>()

const handleClose = () => {
  emit('close')
}

const handleCountdownRedirect = () => {
  emit('countdown-redirect')
}
</script>

<template>
  <div class="scrape-modal">
    <div class="scrape-modal-content">
      <h3>{{ title }}</h3>
      
      <div class="scrape-progress">
        <div 
          class="scrape-progress-bar" 
          :style="{ width: `${progress}%` }"
        ></div>
      </div>
      
      <div class="scrape-status">{{ status }}</div>
      
      <div v-if="results" class="scrape-results">
        <h4>🎯 抓取结果</h4>
        <div class="stats-grid">
          <div class="stat-card">
            <h3>{{ results.total_scraped || 0 }}</h3>
            <p>抓取内容数</p>
          </div>
          <div class="stat-card">
            <h3>{{ results.processing_time || '0s' }}</h3>
            <p>处理时间</p>
          </div>
        </div>
        
        <div class="countdown-section">
          <p>🔄 3秒后自动跳转到内容审核页面...</p>
          <div class="countdown-timer">
            <span id="countdown">3</span>
          </div>
        </div>
      </div>
      
      <button 
        v-if="showCloseBtn" 
        class="btn btn-secondary" 
        @click="handleClose"
      >
        关闭
      </button>
    </div>
  </div>
</template>

<style scoped>
.scrape-modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.scrape-modal-content {
  background: white;
  padding: 30px;
  border-radius: 15px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
  max-width: 500px;
  width: 90%;
  text-align: center;
}

.scrape-modal-content h3 {
  margin-bottom: 20px;
  color: #333;
  font-size: 1.5em;
}

.scrape-progress {
  width: 100%;
  height: 8px;
  background: #e9ecef;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 15px;
}

.scrape-progress-bar {
  height: 100%;
  background: linear-gradient(135deg, #c41e3a 0%, #8b1538 100%);
  border-radius: 4px;
  transition: width 0.3s ease;
}

.scrape-status {
  color: #666;
  margin-bottom: 20px;
  font-size: 14px;
}

.scrape-results {
  margin: 20px 0;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
}

.scrape-results h4 {
  margin-bottom: 15px;
  color: #333;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 15px;
  margin-bottom: 20px;
}

.stat-card {
  background: white;
  padding: 15px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.stat-card h3 {
  font-size: 1.5em;
  margin-bottom: 5px;
  color: #c41e3a;
}

.stat-card p {
  font-size: 0.9em;
  color: #666;
  margin: 0;
}

.countdown-section {
  margin-top: 20px;
  padding: 15px;
  background: #e3f2fd;
  border-radius: 8px;
  border-left: 4px solid #2196f3;
}

.countdown-section p {
  margin-bottom: 10px;
  color: #1976d2;
  font-weight: 500;
}

.countdown-timer {
  font-size: 2em;
  font-weight: bold;
  color: #2196f3;
}

.btn {
  padding: 12px 25px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-secondary {
  background: #6c757d;
  color: white;
}

.btn-secondary:hover {
  background: #5a6268;
  transform: translateY(-2px);
}
</style>