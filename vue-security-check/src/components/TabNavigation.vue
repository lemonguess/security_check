<!-- TabNavigation.vue -->
<script setup lang="ts">
interface Tab {
  id: string;
  label: string;
}

interface Props {
  activeTab: string;
  tabs: Tab[];
}

defineProps<Props>()

const emit = defineEmits<{
  (e: 'switch-tab', tab: string): void
}>()

const switchTab = (tab: string) => {
  emit('switch-tab', tab)
}
</script>

<template>
  <div class="sub-tab-navigation">
    <div 
      v-for="tab in tabs" 
      :key="tab.id"
      class="sub-tab-item"
      :class="{ active: activeTab === tab.id }"
      @click="switchTab(tab.id)"
    >
      {{ tab.label }}
    </div>
  </div>
</template>

<style scoped>
.sub-tab-navigation {
  display: flex;
  background: #f0f2f5;
  border-bottom: 1px solid #e4e7ed;
  padding: 0 20px;
}

.sub-tab-item {
  padding: 15px 25px;
  cursor: pointer;
  font-weight: 500;
  color: #606266;
  border-bottom: 3px solid transparent;
  transition: all 0.3s ease;
}

.sub-tab-item:hover {
  color: #409eff;
}

.sub-tab-item.active {
  color: #409eff;
  border-bottom: 3px solid #409eff;
  font-weight: 600;
}
</style>