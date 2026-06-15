<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue'
import type { JobSummary } from '../types/job'

const props = defineProps<{
  jobs: JobSummary[]
  currentId?: string
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

function getJobName(job: JobSummary): string {
  return job.app_name || job.id.slice(0, 8)
}
</script>

<template>
  <div class="mega-overlay" @click.self="emit('close')">
    <div class="mega">
      <div class="mega-inner">
        <div class="mega-col">
          <h3 class="mega-heading">Recent Jobs</h3>
          <ul class="job-list">
            <li
              v-for="job in jobs"
              :key="job.id"
              class="job-item"
              :class="{ 'job-item--active': job.id === currentId }"
              @click="emit('select', job.id)"
            >
              <span class="job-name">{{ getJobName(job) }}</span>
              <span class="job-id">{{ job.id.slice(0, 8) }}</span>
              <span v-if="job.qa_passed" class="job-badge job-badge--green">QA Passed</span>
              <span v-else-if="job.has_miniapp" class="job-badge job-badge--blue">Built</span>
            </li>
          </ul>
        </div>
        <div class="mega-col">
          <h3 class="mega-heading">Quick Actions</h3>
          <div class="quick-actions">
            <div class="action-card">
              <span class="action-icon">🚀</span>
              <span class="action-label">启动新流水线</span>
            </div>
            <div class="action-card">
              <span class="action-icon">📋</span>
              <span class="action-label">查看所有任务</span>
            </div>
          </div>
          <h3 class="mega-heading" style="margin-top: 24px;">Status</h3>
          <div class="status-row">
            <span class="status-pill status-pill--green">{{ jobs.filter(j => j.qa_passed).length }} Passed</span>
            <span class="status-pill status-pill--blue">{{ jobs.filter(j => j.has_miniapp).length }} Built</span>
            <span class="status-pill status-pill--gray">{{ jobs.length }} Total</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.mega-overlay {
  position: fixed;
  top: var(--nav-height);
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 999;
  background: rgba(0, 0, 0, 0.1);
  animation: fadeOverlay 0.2s var(--ease-apple);
}

.mega {
  background: var(--color-bg);
  border-bottom: 1px solid var(--color-border);
  box-shadow: var(--shadow-elevated);
  animation: slideDown 0.22s var(--ease-apple);
  transform-origin: top center;
}

.mega-inner {
  max-width: 960px;
  margin: 0 auto;
  padding: 32px 24px;
  display: grid;
  grid-template-columns: 1.2fr 1fr;
  gap: 48px;
}

.mega-heading {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-text-3);
  margin-bottom: 12px;
}
.job-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.job-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: background 0.12s;
}
.job-item:hover {
  background: rgba(0, 0, 0, 0.04);
}
.job-item--active {
  background: var(--color-blue-subtle);
}

.job-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-1);
}

.job-id {
  font-size: 12px;
  font-family: var(--font-mono);
  color: var(--color-text-3);
}

.job-badge {
  font-size: 11px;
  font-weight: 500;
  padding: 2px 8px;
  border-radius: 980px;
  margin-left: auto;
}
.job-badge--green {
  background: var(--color-green-subtle);
  color: #1a8d36;
}
.job-badge--blue {
  background: var(--color-blue-subtle);
  color: var(--color-blue);
}
.quick-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.action-card {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: background 0.12s;
}
.action-card:hover {
  background: rgba(0, 0, 0, 0.04);
}

.action-icon {
  font-size: 16px;
}

.action-label {
  font-size: 14px;
  color: var(--color-text-1);
}

.status-row {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.status-pill {
  font-size: 12px;
  font-weight: 500;
  padding: 4px 10px;
  border-radius: 980px;
}
.status-pill--green {
  background: var(--color-green-subtle);
  color: #1a8d36;
}
.status-pill--blue {
  background: var(--color-blue-subtle);
  color: var(--color-blue);
}
.status-pill--gray {
  background: rgba(0, 0, 0, 0.04);
  color: var(--color-text-2);
}

@keyframes slideDown {
  from { opacity: 0; transform: translateY(-8px); }
  to { opacity: 1; transform: translateY(0); }
}

@keyframes fadeOverlay {
  from { opacity: 0; }
  to { opacity: 1; }
}
</style>
