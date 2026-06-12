<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue'
import type { JobSummary } from '../types/job'

const props = defineProps<{
  jobs: JobSummary[]
  currentId: string | undefined
}>()

const emit = defineEmits<{
  select: [id: string]
  close: []
}>()

function onKeydown(e: KeyboardEvent) {
  if (e.key === 'Escape') emit('close')
}

onMounted(() => document.addEventListener('keydown', onKeydown))
onUnmounted(() => document.removeEventListener('keydown', onKeydown))
</script>

<template>
  <div class="mega-backdrop" @click="emit('close')">
    <div class="mega-menu" @click.stop>
      <div class="mega-grid">
        <div class="mega-left">
          <h3 class="mega-heading">最近任务 <span class="en">Recent Jobs</span></h3>
          <ul class="job-list">
            <li
              v-for="job in jobs"
              :key="job.id"
              class="job-item"
              :class="{ active: job.id === currentId }"
              @click="emit('select', job.id)"
            >
              <span class="job-item-name">{{ job.app_name || job.id }}</span>
              <span class="job-item-id">{{ job.id }}</span>
            </li>
            <li v-if="!jobs.length" class="job-empty">暂无任务记录</li>
          </ul>
        </div>
        <div class="mega-right">
          <h3 class="mega-heading">快捷操作 <span class="en">Quick Actions</span></h3>
          <ul class="action-list">
            <li class="action-item" @click="emit('select', currentId || '')">查看 PRD</li>
            <li class="action-item" @click="emit('select', currentId || '')">查看 QA</li>
            <li class="action-item" @click="emit('select', currentId || '')">查看上架材料</li>
            <li class="action-item" @click="emit('select', currentId || '')">查看人工操作</li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.mega-backdrop {
  position: fixed;
  top: var(--nav-height, 48px);
  left: 0;
  width: 100%;
  height: calc(100vh - var(--nav-height, 48px));
  z-index: 90;
}

.mega-menu {
  background: var(--color-bg, #fff);
  box-shadow: var(--shadow-elevated, 0 8px 32px rgba(0,0,0,0.12));
  padding: 40px;
  max-height: 360px;
  overflow-y: auto;
  animation: slideDown 0.22s var(--ease-apple, cubic-bezier(0.25, 0.1, 0.25, 1));
}

@keyframes slideDown {
  from { opacity: 0; transform: translateY(-12px); }
  to { opacity: 1; transform: translateY(0); }
}

.mega-grid {
  max-width: 960px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 40px;
}

.mega-heading {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-1);
  margin-bottom: 16px;
}
.mega-heading .en {
  font-weight: 400;
  color: var(--color-text-3);
  margin-left: 6px;
}

.job-list { list-style: none; padding: 0; margin: 0; }

.job-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  border-left: 3px solid transparent;
  transition: background 0.15s;
}
.job-item:hover { background: rgba(0, 0, 0, 0.03); }
.job-item.active { border-left-color: var(--color-accent, #007aff); background: rgba(0, 122, 255, 0.04); }

.job-item-name { font-size: 13px; font-weight: 500; color: var(--color-text-1); }
.job-item-id { font-size: 11px; color: var(--color-text-3); font-family: var(--font-mono); }
.job-empty { font-size: 13px; color: var(--color-text-3); padding: 10px 12px; }

.action-list { list-style: none; padding: 0; margin: 0; }
.action-item {
  font-size: 13px;
  color: var(--color-accent, #007aff);
  padding: 8px 0;
  cursor: pointer;
  transition: opacity 0.15s;
}
.action-item:hover { opacity: 0.7; }
</style>
