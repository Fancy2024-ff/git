<script setup lang="ts">
import type { JobDetail, PipelineMode } from '../types/job'
import { MODES, startLabelFor } from '../data/modes'

const props = defineProps<{
  currentJob: JobDetail | null
  running: boolean
  mode: PipelineMode
}>()

const emit = defineEmits<{
  'toggle-menu': []
  start: []
  'open-import': []
  'update:mode': [value: PipelineMode]
}>()

function getAppName(): string {
  const c = props.currentJob?.artifacts?.['candidate.json']
  return c?.name_cn || c?.name || '选择应用'
}

function shortJob(): string {
  const id = props.currentJob?.id || ''
  return id ? `Job ${id.slice(0, 13)}` : ''
}
</script>

<template>
  <nav class="nav">
    <div class="nav-inner">
      <!-- Left: brand -->
      <div class="nav-left">
        <span class="brand">Mini App Factory</span>
        <span class="brand-sub">Agent-driven Mini App Factory</span>
      </div>

      <!-- Center: current app selector -->
      <div class="nav-center">
        <button class="app-name-btn" @click="emit('toggle-menu')">
          <span class="app-name-text">{{ getAppName() }}</span>
          <svg class="chevron" width="10" height="6" viewBox="0 0 10 6" fill="none">
            <path d="M1 1L5 5L9 1" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </button>
        <span v-if="shortJob()" class="job-id">{{ shortJob() }}</span>
      </div>

      <!-- Right: import + mode + start -->
      <div class="nav-right">
        <button class="import-btn" @click="emit('open-import')">导入真实 App</button>
        <div class="mode-toggle">
          <button
            v-for="m in MODES"
            :key="m.value"
            class="mode-btn"
            :class="{ 'mode-btn--active': mode === m.value }"
            @click="emit('update:mode', m.value)"
          >{{ m.label.split(' / ')[1] || m.label }}</button>
        </div>
        <button class="start-btn" :disabled="running" @click="emit('start')">
          <span class="start-dot" :class="running ? 'start-dot--run' : 'start-dot--idle'"></span>
          {{ running ? '运行中...' : startLabelFor(mode) }}
        </button>
      </div>
    </div>
  </nav>
</template>

<style scoped>
.nav {
  position: fixed;
  top: 0; left: 0; right: 0;
  min-height: var(--nav-height);
  background: var(--color-surface);
  backdrop-filter: saturate(180%) blur(20px);
  -webkit-backdrop-filter: saturate(180%) blur(20px);
  border-bottom: 1px solid var(--color-border);
  z-index: 1000;
}

.nav-inner {
  max-width: 1280px;
  margin: 0 auto;
  min-height: var(--nav-height);
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 8px 24px;
  flex-wrap: wrap;            /* 小屏换行，不溢出 */
}

/* Left: fixed-ish, never shrinks the brand text */
.nav-left {
  display: flex;
  flex-direction: column;
  justify-content: center;
  flex-shrink: 0;
}
.brand {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text-1);
  letter-spacing: -0.01em;
  line-height: 1.2;
}
.brand-sub {
  font-size: 11px;
  color: var(--color-text-3);
  line-height: 1.2;
}

/* Center: flexible, takes the slack */
.nav-center {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1 1 auto;
  min-width: 0;
  justify-content: center;
}
.app-name-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  background: none;
  border: none;
  cursor: pointer;
  padding: 6px 12px;
  border-radius: var(--radius-sm);
  transition: background 0.15s;
  max-width: 100%;
}
.app-name-btn:hover { background: rgba(0, 0, 0, 0.04); }
.app-name-text {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-1);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.chevron { color: var(--color-text-3); flex-shrink: 0; }
.job-id {
  font-size: 11px;
  font-family: var(--font-mono);
  color: var(--color-text-3);
  white-space: nowrap;
}

/* Right: never squeezed, never vertical */
.nav-right {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}

.import-btn {
  font-size: 12px;
  font-weight: 500;
  color: var(--color-text-1);
  background: rgba(0, 0, 0, 0.06);
  border: none;
  border-radius: 980px;
  padding: 7px 14px;
  cursor: pointer;
  transition: background 0.15s;
  white-space: nowrap;
}
.import-btn:hover { background: rgba(0, 0, 0, 0.1); }

.mode-toggle {
  display: flex;
  background: rgba(0, 0, 0, 0.06);
  border-radius: 980px;
  padding: 2px;
  flex-shrink: 0;
}
.mode-btn {
  font-size: 12px;
  font-weight: 500;
  color: var(--color-text-2);
  background: none;
  border: none;
  border-radius: 980px;
  padding: 5px 12px;
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
  white-space: nowrap;
}
.mode-btn--active {
  background: #fff;
  color: var(--color-text-1);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}

.start-btn {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  font-size: 13px;
  font-weight: 500;
  color: #fff;
  background: var(--color-blue);
  border: none;
  border-radius: 980px;
  padding: 8px 18px;
  cursor: pointer;
  transition: transform 0.15s var(--ease-apple), opacity 0.15s;
  white-space: nowrap;
  flex-shrink: 0;
}
.start-btn:hover:not(:disabled) { transform: translateY(-1px); }
.start-btn:active:not(:disabled) { transform: scale(0.98); }
.start-btn:disabled { opacity: 0.6; cursor: not-allowed; }

.start-dot { width: 7px; height: 7px; border-radius: 50%; background: rgba(255,255,255,0.85); flex-shrink: 0; }
.start-dot--run { animation: pulse 1.2s infinite; }

/* Mobile: stack into rows, never horizontal scroll */
@media (max-width: 720px) {
  .nav-inner { padding: 8px 14px; gap: 10px; }
  .nav-center { order: 3; flex-basis: 100%; justify-content: flex-start; }
  .nav-right { order: 2; margin-left: auto; flex-wrap: wrap; justify-content: flex-end; }
  .brand-sub { display: none; }
}

@keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: 0.4; } }
</style>
