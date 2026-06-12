<script setup lang="ts">
import { artifacts } from '../data/mockData'

function typeIcon(type: string): string {
  if (type === 'json') return '{ }'
  if (type === 'markdown') return '◧'
  if (type === 'folder') return '▤'
  return '◇'
}

function typeColor(type: string): string {
  if (type === 'json') return 'var(--color-accent-subtle)'
  if (type === 'markdown') return 'var(--color-green-subtle)'
  if (type === 'folder') return 'var(--color-orange-subtle)'
  return 'var(--color-bg)'
}

function isPending(timestamp: string): boolean {
  return timestamp === '待生成' || timestamp === '生成中…'
}
</script>

<template>
  <div class="artifact-list">
    <div class="section-header">
      <h2 class="section-title">产物文件 <span class="section-title__en">Artifacts</span></h2>
      <p class="section-subtitle">每一步的输入输出文件，便于追踪和复盘</p>
    </div>

    <div class="artifacts">
      <div
        v-for="artifact in artifacts"
        :key="artifact.id"
        class="artifact-item"
        :class="{ 'artifact-item--pending': isPending(artifact.timestamp) }"
      >
        <span class="artifact-icon" :style="{ background: typeColor(artifact.type) }">{{ typeIcon(artifact.type) }}</span>
        <div class="artifact-info">
          <span class="artifact-label">{{ artifact.label }}</span>
          <span class="artifact-name">{{ artifact.name }}</span>
        </div>
        <div class="artifact-meta">
          <span class="artifact-size">{{ artifact.size }}</span>
          <span class="artifact-time">{{ artifact.timestamp }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.section-header { margin-bottom: var(--space-5); }
.section-title { font-size: 18px; font-weight: 600; color: var(--color-text-primary); letter-spacing: -0.02em; }
.section-title__en { font-size: 13px; font-weight: 400; color: var(--color-text-tertiary); margin-left: 6px; }
.section-subtitle { font-size: 12px; color: var(--color-text-secondary); margin-top: 3px; }

.artifacts { display: flex; flex-direction: column; gap: 2px; }

.artifact-item {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-sm);
  transition: background var(--duration-fast);
}
.artifact-item:hover { background: var(--color-bg); }
.artifact-item--pending { opacity: 0.45; }

.artifact-icon {
  width: 28px; height: 28px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 600;
  color: var(--color-text-secondary);
  flex-shrink: 0;
}

.artifact-info { flex: 1; display: flex; flex-direction: column; gap: 0; min-width: 0; }
.artifact-label { font-size: 13px; font-weight: 500; color: var(--color-text-primary); }
.artifact-name { font-size: 11px; font-family: var(--font-mono); color: var(--color-text-tertiary); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

.artifact-meta { display: flex; flex-direction: column; align-items: flex-end; gap: 0; flex-shrink: 0; }
.artifact-size { font-size: 11px; color: var(--color-text-secondary); font-variant-numeric: tabular-nums; }
.artifact-time { font-size: 10px; color: var(--color-text-tertiary); }
</style>
