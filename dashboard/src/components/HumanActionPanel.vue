<script setup lang="ts">
defineProps<{ content: string }>()
</script>

<template>
  <div>
    <div class="section-header">
      <h2 class="section-title">当前需要你执行 <span class="en">Human Actions</span></h2>
      <p class="section-subtitle">系统已完成自动步骤，以下内容需要人工操作。</p>
    </div>
    <div class="ha-card">
      <pre class="ha-content">{{ content }}</pre>
    </div>
  </div>
</template>

<style scoped>
.section-header { margin-bottom: var(--space-5); }
.section-title { font-size: 20px; font-weight: 600; color: var(--color-text-primary); letter-spacing: -0.02em; }
.en { font-size: 13px; font-weight: 400; color: var(--color-text-tertiary); margin-left: 6px; }
.section-subtitle { font-size: 13px; color: var(--color-text-secondary); margin-top: 3px; }
.ha-card { background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius-md); padding: 20px; }
.ha-content { font-size: 13px; line-height: 1.7; color: var(--color-text-secondary); white-space: pre-wrap; word-break: break-word; font-family: var(--font-sans); max-height: 500px; overflow-y: auto; }
</style>
