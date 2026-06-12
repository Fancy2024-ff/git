<script setup lang="ts">
import { ref, watch, nextTick, computed } from 'vue'

const props = defineProps<{ logs: string[] }>()

const scrollRef = ref<HTMLElement | null>(null)
const lastLogTime = ref(0)
const now = ref(Date.now())

let timer: ReturnType<typeof setInterval> | null = null
timer = setInterval(() => { now.value = Date.now() }, 1000)

const isLive = computed(() => {
  return lastLogTime.value > 0 && (now.value - lastLogTime.value) < 3000
})

watch(() => props.logs.length, () => {
  lastLogTime.value = Date.now()
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
      <span class="terminal-info">
        <span v-if="isLive" class="live-indicator"><span class="live-dot"></span> Live</span>
        <span class="line-count">{{ logs.length }} lines</span>
      </span>
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

.terminal-info {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 10px;
}

.live-indicator {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 11px;
  color: #27c93f;
  font-weight: 600;
}

.live-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #27c93f;
  animation: pulse 1.2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

.line-count {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.35);
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
