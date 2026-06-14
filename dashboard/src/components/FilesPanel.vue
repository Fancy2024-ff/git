<script setup lang="ts">
import { computed } from 'vue'
import type { JobDetail } from '../types/job'

const props = defineProps<{ job: JobDetail }>()

interface ManifestItem {
  path: string
  title: string
  purpose: string
  status: 'ready' | 'needs_review' | 'blocked' | 'draft'
  affects_submission: boolean
  next_action: string
}

interface FileItem {
  name: string
  type: string
  icon: string
}

// Prefer the structured artifact-manifest.json when present.
const manifest = computed<ManifestItem[]>(() => {
  const m = props.job.artifacts?.['artifact-manifest.json']
  return Array.isArray(m?.items) ? m.items : []
})

const statusMeta: Record<string, { label: string; cls: string }> = {
  ready: { label: '可用', cls: 'st-ready' },
  needs_review: { label: '待人工确认', cls: 'st-review' },
  blocked: { label: '阻塞', cls: 'st-blocked' },
  draft: { label: '草稿', cls: 'st-draft' },
}

function statusLabel(s: string) { return statusMeta[s]?.label || s }
function statusClass(s: string) { return statusMeta[s]?.cls || 'st-draft' }

const artifacts = computed<FileItem[]>(() => {
  const a = props.job.artifacts || {}
  return Object.keys(a).map(name => ({ name, type: getType(name), icon: getIcon(name) }))
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

    <!-- Preferred: structured manifest with purpose + status -->
    <div v-if="manifest.length" class="manifest-list">
      <h3 class="col-title">产物状态</h3>
      <div v-for="item in manifest" :key="item.path" class="manifest-card">
        <div class="mf-main">
          <span class="mf-title">{{ item.title }}</span>
          <span class="mf-status" :class="statusClass(item.status)">{{ statusLabel(item.status) }}</span>
          <span v-if="item.affects_submission" class="mf-affects">影响提交</span>
        </div>
        <div class="mf-path">{{ item.path }}</div>
        <div class="mf-purpose">{{ item.purpose }}</div>
        <div v-if="item.next_action && item.next_action !== '无'" class="mf-next">下一步：{{ item.next_action }}</div>
      </div>
    </div>

    <!-- Fallback: plain file lists -->
    <div v-else class="files-grid">
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

@media (max-width: 640px) {
  .files-grid { grid-template-columns: 1fr; }
}

.manifest-list { display: flex; flex-direction: column; gap: 10px; }
.manifest-card {
  background: var(--color-surface-solid);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-card);
  padding: 14px 16px;
}
.mf-main { display: flex; align-items: center; gap: 8px; }
.mf-title { font-size: 14px; font-weight: 600; color: var(--color-text-1); }
.mf-status { font-size: 11px; font-weight: 600; padding: 2px 8px; border-radius: 980px; }
.st-ready { background: var(--color-green-subtle); color: #166534; }
.st-review { background: rgba(255,149,0,0.12); color: #92400e; }
.st-blocked { background: rgba(255,59,48,0.10); color: #991b1b; }
.st-draft { background: rgba(0,0,0,0.05); color: var(--color-text-3); }
.mf-affects { font-size: 10px; color: var(--color-blue); background: var(--color-blue-subtle); padding: 2px 6px; border-radius: 4px; }
.mf-path { font-size: 11px; font-family: var(--font-mono); color: var(--color-text-3); margin-top: 4px; }
.mf-purpose { font-size: 12px; color: var(--color-text-2); margin-top: 4px; }
.mf-next { font-size: 12px; color: #92400e; margin-top: 6px; }

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

