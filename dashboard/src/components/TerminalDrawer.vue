<script setup lang="ts">
import { ref, watch, nextTick } from 'vue'

const props = defineProps<{
  logs: string[]
  open: boolean
}>()

const emit = defineEmits<{
  toggle: []
}>()

const scrollRef = ref<HTMLElement | null>(null)

watch(() => props.logs.length, () => {
  if (props.open) {
    nextTick(() => {
      if (scrollRef.value) {
        scrollRef.value.scrollTop = scrollRef.value.scrollHeight
      }
    })
  }
})
</script>

<template>
  <div class="drawer" :class="{ 'drawer--open': open }">
    <div class="drawer-header" @click="emit('toggle')">
      <span class="drawer-title">运行日志</span>
      <span class="drawer-count">{{ logs.length }} 行</span>
      <button class="drawer-toggle">
        <svg
          :class="{ 'chevron--up': open }"
          class="chevron-icon"
          width="12"
          height="12"
          viewBox="0 0 12 12"
          fill="none"
        >
          <path d="M3 5L6 8L9 5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
      </button>
    </div>
    <div v-show="open" class="drawer-body" ref="scrollRef">
      <div v-if="logs.length === 0" class="drawer-empty">等待日志输出...</div>
      <div v-else class="log-lines">
        <div v-for="(line, i) in logs" :key="i" class="log-line">
          <span class="line-num">{{ i + 1 }}</span>
          <span class="line-text">{{ line }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.drawer {
  margin-top: 20px;
  border-radius: var(--radius-md);
  overflow: hidden;
  background: #1a1a1e;
  box-shadow: var(--shadow-card);
}

.drawer-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 16px;
  cursor: pointer;
  background: #222226;
  user-select: none;
}

.drawer-title {
  font-size: 12px;
  font-weight: 600;
  color: #a0a0a8;
}

.drawer-count {
  font-size: 11px;
  color: #6e6e76;
  font-family: var(--font-mono);
}

.drawer-toggle {
  margin-left: auto;
  background: none;
  border: none;
  cursor: pointer;
  color: #6e6e76;
  display: flex;
  align-items: center;
  padding: 2px;
}

.chevron-icon {
  transition: transform 0.2s var(--ease-apple);
}
.chevron--up {
  transform: rotate(180deg);
}

.drawer-body {
  max-height: 240px;
  overflow-y: auto;
  padding: 8px 0;
}

.drawer-empty {
  padding: 24px 16px;
  text-align: center;
  font-size: 12px;
  color: #6e6e76;
}

.log-lines {
  font-family: var(--font-mono);
  font-size: 11px;
  line-height: 1.6;
}

.log-line {
  display: flex;
  padding: 0 16px;
}
.log-line:hover {
  background: rgba(255, 255, 255, 0.03);
}

.line-num {
  width: 36px;
  flex-shrink: 0;
  color: #4a4a52;
  text-align: right;
  margin-right: 12px;
  user-select: none;
}

.line-text {
  color: #d4d4d8;
  white-space: pre-wrap;
  word-break: break-all;
}

.drawer-body::-webkit-scrollbar {
  width: 6px;
}
.drawer-body::-webkit-scrollbar-track {
  background: transparent;
}
.drawer-body::-webkit-scrollbar-thumb {
  background: #3a3a3e;
  border-radius: 3px;
}
</style>
