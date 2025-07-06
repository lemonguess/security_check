<script setup lang="ts">
interface Props {
  activeTab: string
}

interface Emits {
  (e: 'switch-tab', tabName: string): void
}

defineProps<Props>()
const emit = defineEmits<Emits>()

const handleTabClick = (tabName: string) => {
  emit('switch-tab', tabName)
}
</script>

<template>
  <div class="tabs">
    <button 
      class="tab" 
      :class="{ active: activeTab === 'scraping' }"
      @click="handleTabClick('scraping')"
    >
      🔍 数据采集
    </button>
    <button 
      class="tab" 
      :class="{ active: activeTab === 'audit' }"
      @click="handleTabClick('audit')"
    >
      📋 内容审核
    </button>
  </div>
</template>

<style scoped>
.tabs {
  display: flex;
  background: #f8f9fa;
  border-bottom: 1px solid #e9ecef;
}

.tab {
  flex: 1;
  padding: 15px 25px;
  border: none;
  background: transparent;
  font-size: 16px;
  font-weight: 600;
  color: #6c757d;
  cursor: pointer;
  transition: all 0.3s ease;
  border-bottom: 3px solid transparent;
}

.tab:hover {
  background: #e9ecef;
  color: #495057;
}

.tab.active {
  color: #c41e3a;
  background: white;
  border-bottom-color: #c41e3a;
}

.tab.active:hover {
  background: white;
}
</style>