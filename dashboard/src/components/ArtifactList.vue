<script setup lang="ts">
defineProps<{ artifacts?: Record<string, any>; miniappFiles?: string[] }>()

function isJson(key: string) { return key.endsWith('.json') }
function isMd(key: string) { return key.endsWith('.md') }
</script>

<template>
  <div>
    <div class="section-header">
      <h2 class="section-title">产物文件 <span class="en">Artifacts</span></h2>
      <p class="section-subtitle">本次流水线生成的所有文件</p>
    </div>

    <div v-if="artifacts" class="artifact-grid">
      <div v-for="(_, key) in artifacts" :key="key" class="artifact-item">
        <span class="artifact-icon" :class="isJson(key) ? 'json' : isMd(key) ? 'md' : ''">
          {{ isJson(key) ? '{ }' : isMd(key) ? '◧' : '○' }}
        </span>
        <span class="artifact-name">{{ key }}</span>
      </div>
    </div>

    <div v-if="miniappFiles && miniappFiles.length" class="miniapp-section">
      <h4 class="miniapp-title">小程序项目文件 ({{ miniappFiles.length }})</h4>
      <div class="miniapp-list">
        <span v-for="f in miniappFiles.slice(0, 20)" :key="f" class="miniapp-file">{{ f }}</span>
        <span v-if="miniappFiles.length > 20" class="miniapp-file more">... +{{ miniappFiles.length - 20 }} more</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.section-header { margin-bottom: var(--space-5); }
.section-title { font-size: 20px; font-weight: 600; color: var(--color-text-primary); letter-spacing: -0.02em; }
.en { font-size: 13px; font-weight: 400; color: var(--color-text-tertiary); margin-left: 6px; }
.section-subtitle { font-size: 13px; color: var(--color-text-secondary); margin-top: 3px; }

.artifact-grid { display: flex; flex-wrap: wrap; gap: 8px; }
.artifact-item { display: flex; align-items: center; gap: 8px; background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius-sm); padding: 8px 12px; }
.artifact-icon { font-size: 11px; font-weight: 600; width: 24px; height: 24px; border-radius: 6px; display: flex; align-items: center; justify-content: center; background: var(--color-bg); color: var(--color-text-secondary); }
.artifact-icon.json { background: var(--color-accent-subtle); color: var(--color-accent); }
.artifact-icon.md { background: var(--color-green-subtle); color: #1a7a35; }
.artifact-name { font-size: 12px; font-family: var(--font-mono); color: var(--color-text-secondary); }

.miniapp-section { margin-top: 20px; }
.miniapp-title { font-size: 13px; font-weight: 600; color: var(--color-text-primary); margin-bottom: 8px; }
.miniapp-list { display: flex; flex-wrap: wrap; gap: 4px; }
.miniapp-file { font-size: 11px; font-family: var(--font-mono); color: var(--color-text-tertiary); background: var(--color-bg); padding: 2px 8px; border-radius: 4px; }
.miniapp-file.more { color: var(--color-text-secondary); font-style: italic; }
</style>
