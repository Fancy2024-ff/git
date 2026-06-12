<script setup lang="ts">
import { ref, watch, nextTick, onMounted } from 'vue'

const props = defineProps<{
  tabs: { id: string; label: string }[]
  modelValue: string
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()

const containerRef = ref<HTMLElement | null>(null)
const highlightStyle = ref({ left: '0px', width: '0px' })

function updateHighlight() {
  if (!containerRef.value) return
  const activeBtn = containerRef.value.querySelector('.tab-btn--active') as HTMLElement
  if (activeBtn) {
    highlightStyle.value = {
      left: activeBtn.offsetLeft + 'px',
      width: activeBtn.offsetWidth + 'px'
    }
  }
}

watch(() => props.modelValue, () => nextTick(updateHighlight))
onMounted(() => nextTick(updateHighlight))
</script>

<template>
  <div class="tabs-wrapper">
    <div class="tabs-container" ref="containerRef">
      <div class="tabs-highlight" :style="highlightStyle"></div>
      <button
        v-for="tab in tabs"
        :key="tab.id"
        class="tab-btn"
        :class="{ 'tab-btn--active': modelValue === tab.id }"
        @click="emit('update:modelValue', tab.id)"
      >
        {{ tab.label }}
      </button>
    </div>
  </div>
</template>

<style scoped>
.tabs-wrapper {
  display: flex;
  justify-content: center;
  margin-top: 24px;
}

.tabs-container {
  position: relative;
  display: inline-flex;
  background: rgba(0, 0, 0, 0.05);
  border-radius: var(--radius-sm);
  padding: 3px;
}

.tabs-highlight {
  position: absolute;
  top: 3px;
  height: calc(100% - 6px);
  background: var(--color-surface-solid);
  border-radius: 6px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08), 0 0 0 1px rgba(0, 0, 0, 0.04);
  transition: left 0.25s var(--ease-apple), width 0.25s var(--ease-apple);
}

.tab-btn {
  position: relative;
  z-index: 1;
  border: none;
  background: none;
  padding: 6px 14px;
  font-size: 13px;
  font-weight: 500;
  color: var(--color-text-2);
  cursor: pointer;
  border-radius: 6px;
  transition: color 0.2s;
  white-space: nowrap;
}
.tab-btn--active {
  color: var(--color-text-1);
}
.tab-btn:hover:not(.tab-btn--active) {
  color: var(--color-text-1);
}
</style>
