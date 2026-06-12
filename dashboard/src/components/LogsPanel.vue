<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{ logs: string[] }>()

const displayLogs = computed(() => props.logs.slice(0, 50))
</script>

<template>
  <div class="logs-panel">
    <div class="terminal">
      <div class="terminal-bar">
        <span class="dot red"></span>
        <span class="dot yellow"></span>
        <span class="dot green"></span>
        <span class="terminal-title">Pipeline Logs</span>
      </div>
      <div class="terminal-body">
        <template v-if="displayLogs.length">
          <div v-for="(line, i) in displayLogs" :key="i" class="log-line">{{ line }}</div>
        </template>
        <div v-else class="log-empty">暂无日志. 点击启动流水线后日志将在这里显示.</div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.logs-panel { animation: fadeIn 0.3s ease; }

.terminal {
  background: #1a1a1a;
  border-radius: var(--radius-lg, 12px);
  overflow: hidden;
}

.terminal-bar {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 14px;
  background: #252525;
}

.dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}
.dot.red { background: #ff5f57; }
.dot.yellow { background: #febc2e; }
.dot.green { background: #28c840; }

.terminal-title {
  flex: 1;
  text-align: center;
  font-size: 11px;
  color: #666;
}

.terminal-body {
  padding: 16px 20px;
  max-height: 400px;
  overflow-y: auto;
  font-family: var(--font-mono, 'SF Mono', monospace);
  font-size: 12px;
  line-height: 1.7;
}

.log-line { color: #d4d4d4; }
.log-empty { color: #666; }

@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
</style>
