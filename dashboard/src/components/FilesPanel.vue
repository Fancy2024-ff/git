<script setup lang="ts">
import { computed } from 'vue'
import type { JobDetail } from '../types/job'

const props = defineProps<{ job: JobDetail }>()

interface FileItem {
  name: string
  type: string
  icon: string
}

const artifacts = computed<FileItem[]>(() => {
  const a = props.job.artifacts || {}
  return Object.keys(a).map(name => ({
    name,
    type: getType(name),
    icon: getIcon(name),
  }))
})

const buildFiles = computed<FileItem[]>(() => {
  const files = props.job.miniapp_files || []
  return files.slice(0, 20).map(f => ({
    name: f.split('/').pop() || f,
    type: getType(f),
    icon: getIcon(f),
  }))
})

function getType(name: string): string {
  if (name.endsWith('.json')) return 'JSON'
  if (name.endsWith('.md')) return 'Markdown'
  if (name.endsWith('.js') || name.endsWith('.ts')) return 'Script'
  if (name.endsWith('.css') || name.endsWith('.wxss')) return 'Style'
  if (name.endsWith('.wxml') || name.endsWith('.html')) return 'Template'
  if (name.includes('.')) return name.split('.').pop()?.toUpperCase() || 'File'
  return 'Folder'
}

function getIcon(name: string): string {
  if (name.endsWith('.json')) return '{}'
  if (name.endsWith('.md')) return '◧'
  if (name.includes('/') || !name.includes('.')) return '▤'
  return '▢'
}

function downloadZip() {
  const base = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
  const key = import.meta.env.VITE_API_TOKEN || ''
  fetch(`${base}/api/jobs/${props.job.id}/download`, {
    headers: key ? { 'X-API-Key': key } : {}
  })
    .then(res => {
      if (!res.ok) throw new Error(`${res.status}`)
      return res.blob()
    })
    .then(blob => {
      const a = document.createElement('a')
      a.href = URL.createObjectURL(blob)
      a.download = `${props.job.id}-miniapp.zip`
      a.click()
    })
    .catch(() => alert('下载失败'))
}
</script>

<template>
  <div class="files">
    <div class="files-header">
      <button @click="downloadZip" class="btn-download">📦 下载 ZIP</button>
    </div>
    <div class="files-grid">
      <div class="files-col">
        <h3 class="col-title">Pipeline Artifacts</h3>
        <div class="file-list">
          <div v-if="artifacts.length === 0" class="empty-state">暂无产物文件</div>
          <div v-for="item in artifacts" :key="item.name" class="file-card">
            <span class="file-icon">{{ item.icon }}</span>
            <span class="file-name">{{ item.name }}</span>
            <span class="file-type">{{ item.type }}</span>
          </div>
        </div>
      </div>
      <div class="files-col">
        <h3 class="col-title">Build Output</h3>
        <div class="file-list">
          <div v-if="buildFiles.length === 0" class="empty-state">暂无构建产物</div>
          <div v-for="item in buildFiles" :key="item.name" class="file-card">
            <span class="file-icon">{{ item.icon }}</span>
            <span class="file-name">{{ item.name }}</span>
            <span class="file-type">{{ item.type }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.files {
  padding: 0;
}

.files-header {
  margin-bottom: 16px;
}

.btn-download {
  padding: 8px 16px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 500;
  background: var(--color-blue);
  color: #fff;
  border: none;
  cursor: pointer;
}
.btn-download:hover { opacity: 0.9; }

.files-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
}

.col-title {
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-text-3);
  margin: 0 0 12px;
}

.file-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.empty-state {
  font-size: 13px;
  color: var(--color-text-3);
  padding: 24px;
  text-align: center;
  background: var(--color-surface-solid);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-card);
}

.file-card {
  background: var(--color-surface-solid);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-card);
  padding: 12px 16px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.file-icon {
  font-family: var(--font-mono);
  font-size: 14px;
  color: var(--color-text-3);
  width: 24px;
  text-align: center;
  flex-shrink: 0;
}

.file-name {
  font-size: 13px;
  font-weight: 500;
  color: var(--color-text-1);
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-type {
  font-size: 11px;
  font-weight: 500;
  color: var(--color-text-3);
  background: rgba(0, 0, 0, 0.03);
  padding: 2px 8px;
  border-radius: 980px;
  flex-shrink: 0;
}
</style>

