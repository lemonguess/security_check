<script setup lang="ts">
interface ColumnType {
  type: string
  icon: string
  title: string
  desc: string
}

interface Props {
  columnTypes: ColumnType[]
  selectedType: string
  disabled?: boolean
  title?: string
}

interface Emits {
  (e: 'select', type: string): void
}

withDefaults(defineProps<Props>(), {
  disabled: false,
  title: '📂 选择抓取栏目类型'
})

const emit = defineEmits<Emits>()

const handleSelect = (type: string) => {
  emit('select', type)
}
</script>

<template>
  <div class="column-type-selection">
    <h3>{{ title }}</h3>
    <div class="column-type-grid">
      <div
        v-for="columnType in columnTypes"
        :key="columnType.type"
        class="column-type-card"
        :class="{ 
          selected: selectedType === columnType.type,
          disabled: disabled
        }"
        @click="!disabled && handleSelect(columnType.type)"
      >
        <div class="column-icon">{{ columnType.icon }}</div>
        <div class="column-title">{{ columnType.title }}</div>
        <div class="column-desc">{{ columnType.desc }}</div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.column-type-selection {
  margin-bottom: 20px;
}

.column-type-selection h3 {
  margin-bottom: 20px;
  color: #333;
  font-size: 1.3em;
}

.column-type-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 15px;
  margin-bottom: 20px;
}

.column-type-card {
  background: white;
  border: 2px solid #e9ecef;
  border-radius: 12px;
  padding: 20px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
  color: #333;
}

.column-type-card:hover:not(.disabled) {
  border-color: #c41e3a;
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(196, 30, 58, 0.15);
}

.column-type-card.selected {
  border-color: #c41e3a;
  background: linear-gradient(135deg, #c41e3a 0%, #8b1538 100%);
  color: white;
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(196, 30, 58, 0.3);
}

.column-type-card.disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.column-type-card.disabled:hover {
  transform: none;
  box-shadow: none;
  border-color: #e9ecef;
}

.column-icon {
  font-size: 2.5em;
  margin-bottom: 10px;
}

.column-title {
  font-size: 1.1em;
  font-weight: 600;
  margin-bottom: 8px;
}

.column-desc {
  font-size: 0.9em;
  opacity: 0.8;
  line-height: 1.4;
}

.column-type-card.selected .column-desc {
  opacity: 0.9;
}
</style>