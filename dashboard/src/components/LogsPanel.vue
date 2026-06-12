<script setup lang="ts">
import { ref, watch, nextTick } from 'vue'

const props = defineProps<{ logs: string[] }>()

const scrollRef = ref<HTMLElement | null>(null)

watch(() => props.logs.length, () => {
  nextTick(() => {
    if (scrollRef.value) {
      scrollRef.value.scrollTop = scrollRef.value.scrollHeight
    }
  })
})
</script>

<template>
  <div class="terminal">
    <div class="terminal-header">
      <div class="traffic-lights">
        <span class="dot dot--red"></span>
        <span class="dot dot--yellow"></span>
        <span class="dot dot--green"></span>
      </div>
      <span class="terminal-title">Pipeline Logs</span>
    </div>
    <div class="terminal-body" ref="scrollRef">
      <div v-if="logs.length === 0" class="empty-logs">
        <span class="empty-text">No logs yet</span>
        <span class="empty-sub">启动流水线后日志将显示在此处</span>
      </div>
      <pre v-else class="log-content"><code><span v-for="(line, i) in logs" :key="i" class="log-line">{{ line }}
</span></code></pre>
    </div>
  </div>
</template>

<style scoped>
.terminal {
  background: #1e1e1e;
  border-radius: var(--radius-lg);
  overflow: hidden;
  box-shadow: var(--shadow-elevated);
}

.terminal-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: #2d2d2d;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.traffic-lights {
  display: flex;
  gap: 6px;
}

.dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}
.dot--red { background: #ff5f56; }
.dot--yellow { background: #ffbd2e; }
.dot--green { background: #27c93f; }

.terminal-title {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
  font-weight: 500;
}

.terminal-body {
  padding: 16px;
  max-height: 480px;
  overflow-y: auto;
  overflow-x: hidden;
}

.empty-logs {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 60px 20px;
}

.empty-text {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.4);
  font-weight: 500;
}

.empty-sub {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.25);
}

.log-content {
  margin: 0;
  font-family: var(--font-mono);
  font-size: 12px;
  line-height: 1.6;
  color: rgba(255, 255, 255, 0.85);
  white-space: pre-wrap;
  word-break: break-all;
}

.log-line {
  display: block;
}
</style>
