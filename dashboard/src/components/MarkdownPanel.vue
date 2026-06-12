<script setup lang="ts">
defineProps<{
  content: string
  title: string
}>()
</script>

<template>
  <div class="md-panel">
    <h2 class="md-title">{{ title }}</h2>
    <div class="md-card">
      <pre class="md-content">{{ content || '暂无内容' }}</pre>
    </div>
  </div>
</template>

<style scoped>
.md-panel { animation: fadeIn 0.3s ease; }

.md-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text-1);
  margin-bottom: 16px;
}

.md-card {
  background: #fff;
  border-radius: var(--radius-lg, 12px);
  padding: 32px;
  box-shadow: var(--shadow-card, 0 1px 4px rgba(0,0,0,0.06));
}

.md-content {
  font-size: 14px;
  line-height: 1.8;
  color: var(--color-text-1);
  white-space: pre-wrap;
  word-break: break-word;
  font-family: var(--font-sans, -apple-system, BlinkMacSystemFont, sans-serif);
  margin: 0;
}

@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
</style>
