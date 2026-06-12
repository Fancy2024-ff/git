<script setup lang="ts">
import { computed } from 'vue'
import type { JobDetail } from '../types/job'

const props = defineProps<{ job: JobDetail }>()

const artifactKeys = computed(() => {
  return Object.keys(props.job.artifacts || {})
})

const miniappFiles = computed(() => {
  const files = props.job.miniapp_files || []
  return files.slice(0, 25)
})
</script>

<template>
  <div class="files-panel">
    <div class="files-grid">
      <div class="files-section">
        <h3 class="files-heading">产物文件 <span class="en">Artifacts</span></h3>
        <ul class="file-list">
          <li v-for="key in artifactKeys" :key="key" class="file-item">
            <svg class="file-icon" width="14" height="14" viewBox="0 0 16 16" fill="none">
              <path d="M4 1h5l4 4v9a1 1 0 01-1 1H4a1 1 0 01-1-1V2a1 1 0 011-1z" stroke="currentColor" stroke-width="1.2"/>
              <path d="M9 1v4h4" stroke="currentColor" stroke-width="1.2"/>
            </svg>
            <span class="file-name">{{ key }}</span>
          </li>
          <li v-if="!artifactKeys.length" class="file-empty">暂无产物</li>
        </ul>
      </div>

      <div class="files-section">
        <h3 class="files-heading">小程序文件 <span class="en">Miniapp</span></h3>
        <ul class="file-list">
          <li v-for="file in miniappFiles" :key="file" class="file-item">
            <svg class="file-icon" width="14" height="14" viewBox="0 0 16 16" fill="none">
              <path d="M4 1h5l4 4v9a1 1 0 01-1 1H4a1 1 0 01-1-1V2a1 1 0 011-1z" stroke="currentColor" stroke-width="1.2"/>
              <path d="M9 1v4h4" stroke="currentColor" stroke-width="1.2"/>
            </svg>
            <span class="file-name">{{ file }}</span>
          </li>
          <li v-if="!miniappFiles.length" class="file-empty">暂无文件</li>
        </ul>
      </div>
    </div>
  </div>
</template>
<style scoped>
.files-panel { animation: fadeIn 0.3s ease; }

.files-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
}

.files-heading {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-1);
  margin-bottom: 12px;
}
.files-heading .en {
  font-weight: 400;
  color: var(--color-text-3);
  margin-left: 6px;
}

.file-list { list-style: none; padding: 0; margin: 0; }

.file-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 0;
  border-bottom: 1px solid var(--color-border, rgba(0,0,0,0.06));
}

.file-icon { color: var(--color-text-3); flex-shrink: 0; }

.file-name {
  font-size: 12px;
  font-family: var(--font-mono);
  color: var(--color-text-2);
  word-break: break-all;
}

.file-empty {
  font-size: 12px;
  color: var(--color-text-3);
  padding: 8px 0;
}

@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
</style>
