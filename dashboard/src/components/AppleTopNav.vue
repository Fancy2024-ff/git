<script setup lang="ts">
import type { JobDetail } from '../types/job'

const props = defineProps<{
  currentJob: JobDetail | null
  running: boolean
}>()

const emit = defineEmits<{
  'toggle-menu': []
  start: []
}>()

function qaStatus(): boolean {
  const qa = props.currentJob?.artifacts?.['qa-report.json']
  return qa?.passed === true
}
</script>

<template>
  <nav class="nav">
    <div class="nav-inner">
      <div class="nav-left">
        <span class="brand">Mini App Factory</span>
      </div>

      <div class="nav-center" @click="emit('toggle-menu')">
        <template v-if="currentJob">
          <span class="job-name">{{ currentJob.artifacts?.['candidate.json']?.name_cn || currentJob.id }}</span>
          <span class="job-id">{{ currentJob.id }}</span>
          <svg class="chevron" width="10" height="6" viewBox="0 0 10 6" fill="none">
            <path d="M1 1L5 5L9 1" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </template>
        <template v-else>
          <span class="job-name">选择任务</span>
        </template>
      </div>

      <div class="nav-right">
        <span v-if="currentJob" class="status-pill" :class="{ passed: qaStatus() }">
          {{ qaStatus() ? 'QA 通过' : 'QA 未通过' }}
        </span>
        <button class="start-btn" :disabled="running" @click="emit('start')">
          {{ running ? '运行中...' : '启动流水线' }}
        </button>
      </div>
    </div>
  </nav>
</template>

<style scoped>
.nav {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: var(--nav-height, 48px);
  background: rgba(255, 255, 255, 0.72);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-bottom: 1px solid var(--color-border);
  z-index: 100;
}

.nav-inner {
  max-width: 960px;
  margin: 0 auto;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
}

.nav-left { flex: 1; }
.brand { font-size: 15px; font-weight: 600; color: var(--color-text-1); }

.nav-center {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  padding: 4px 12px;
  border-radius: 6px;
  transition: background 0.15s;
}
.nav-center:hover { background: rgba(0, 0, 0, 0.04); }

.job-name { font-size: 13px; font-weight: 500; color: var(--color-text-1); }
.job-id { font-size: 11px; color: var(--color-text-3); }
.chevron { color: var(--color-text-3); margin-left: 2px; }

.nav-right {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 10px;
}

.status-pill {
  font-size: 11px;
  font-weight: 500;
  padding: 3px 8px;
  border-radius: 10px;
  background: rgba(255, 59, 48, 0.1);
  color: #c41e16;
}
.status-pill.passed {
  background: rgba(52, 199, 89, 0.1);
  color: #1d7a34;
}

.start-btn {
  font-size: 12px;
  font-weight: 500;
  padding: 6px 14px;
  border-radius: 16px;
  border: none;
  background: var(--color-accent, #007aff);
  color: #fff;
  cursor: pointer;
  transition: opacity 0.15s;
}
.start-btn:hover { opacity: 0.85; }
.start-btn:disabled { opacity: 0.5; cursor: not-allowed; }
</style>
