<script setup lang="ts">
import type { Agent } from '../data/mockData'

defineProps<{ agent: Agent }>()
</script>

<template>
  <div class="agent-card" :class="{ 'agent-card--idle': agent.status === 'idle' }">
    <div class="agent-card__header">
      <div class="agent-card__title">
        <span class="agent-card__name">{{ agent.nameCn }} Agent</span>
        <span class="agent-card__name-en">{{ agent.name }}</span>
      </div>
      <span class="agent-card__status" :class="`agent-card__status--${agent.status}`">
        <span v-if="agent.status === 'running'" class="spinner"></span>
        {{ agent.status === 'done' ? '已完成' : agent.status === 'running' ? '运行中' : '空闲' }}
      </span>
    </div>

    <div class="agent-card__io">
      <div class="io-row">
        <span class="io-label">输入 Input</span>
        <span class="io-value">{{ agent.input }}</span>
      </div>
      <div class="io-row">
        <span class="io-label">输出 Output</span>
        <span class="io-value">{{ agent.output }}</span>
      </div>
    </div>

    <div class="agent-card__footer">
      <span class="footer-label">最近运行</span>
      <span class="footer-value">{{ agent.lastRun }}</span>
    </div>
  </div>
</template>

<style scoped>
.agent-card {
  background: var(--color-surface);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-card);
  padding: var(--space-4);
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  transition: all var(--duration-fast) var(--ease-out);
}
.agent-card--idle { opacity: 0.55; }
.agent-card:hover { box-shadow: var(--shadow-md); }

.agent-card__header { display: flex; justify-content: space-between; align-items: flex-start; }
.agent-card__title { display: flex; flex-direction: column; gap: 1px; }
.agent-card__name { font-size: 13px; font-weight: 600; color: var(--color-text-primary); }
.agent-card__name-en { font-size: 11px; color: var(--color-text-tertiary); }

.agent-card__status {
  font-size: 11px;
  font-weight: 500;
  padding: 2px 8px;
  border-radius: var(--radius-full);
  display: flex;
  align-items: center;
  gap: 4px;
}
.agent-card__status--done { background: var(--color-green-subtle); color: #1a7a35; }
.agent-card__status--running { background: var(--color-accent-subtle); color: var(--color-accent); }
.agent-card__status--idle { background: var(--color-bg); color: var(--color-text-tertiary); }

.spinner {
  width: 10px; height: 10px;
  border: 1.5px solid var(--color-accent);
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.agent-card__io {
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  background: var(--color-bg);
  border-radius: var(--radius-sm);
  padding: var(--space-3);
}
.io-row { display: flex; flex-direction: column; gap: 1px; }
.io-label { font-size: 10px; font-weight: 600; color: var(--color-text-tertiary); text-transform: uppercase; letter-spacing: 0.04em; }
.io-value { font-size: 12px; color: var(--color-text-secondary); line-height: 1.4; }

.agent-card__footer { display: flex; justify-content: space-between; align-items: center; }
.footer-label { font-size: 11px; color: var(--color-text-tertiary); }
.footer-value { font-size: 11px; color: var(--color-text-secondary); font-weight: 500; }
</style>
