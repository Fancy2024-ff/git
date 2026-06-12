<script setup lang="ts">
defineProps<{
  running?: boolean
  jobId?: string
}>()

defineEmits<{
  (e: 'start-pipeline'): void
}>()
</script>

<template>
  <div class="hero">
    <div class="hero__chips">
      <span v-if="running" class="chip chip--blue">
        <span class="chip__dot chip__dot--blue chip__dot--pulse"></span>
        流水线运行中
      </span>
      <span v-else-if="jobId" class="chip chip--green">
        <span class="chip__dot chip__dot--green"></span>
        最新任务: {{ jobId }}
      </span>
      <span v-else class="chip chip--gray">
        <span class="chip__dot chip__dot--gray"></span>
        等待启动
      </span>
    </div>

    <h1 class="hero__title">Mini App Factory</h1>
    <p class="hero__title-cn">小程序生产工厂</p>
    <p class="hero__subtitle">
      Agent 驱动的高需求应用生产流水线<br>
      <span class="hero__subtitle-en">Discover demand · Generate mini apps · Prepare publishing.</span>
    </p>

    <div class="hero__actions">
      <button class="btn btn--primary" :disabled="running" @click="$emit('start-pipeline')">
        {{ running ? '运行中...' : '启动流水线' }} <span class="btn__en">{{ running ? 'Running' : 'Start Pipeline' }}</span>
      </button>
    </div>
  </div>
</template>

<style scoped>
.hero { padding: var(--space-12) 0 var(--space-10); }
.hero__chips { display: flex; gap: var(--space-2); flex-wrap: wrap; margin-bottom: var(--space-6); }
.chip { display: inline-flex; align-items: center; gap: 6px; padding: 4px 10px; border-radius: var(--radius-full); font-size: 12px; font-weight: 500; }
.chip--green { background: var(--color-green-subtle); color: #1a7a35; }
.chip--blue { background: var(--color-accent-subtle); color: var(--color-accent); }
.chip--gray { background: var(--color-bg); color: var(--color-text-tertiary); }
.chip__dot { width: 6px; height: 6px; border-radius: 50%; flex-shrink: 0; }
.chip__dot--green { background: var(--color-green); }
.chip__dot--blue { background: var(--color-accent); }
.chip__dot--gray { background: var(--color-text-tertiary); }
.chip__dot--pulse { animation: pulse-dot 1.4s ease-in-out infinite; }
.hero__title { font-size: 48px; font-weight: 700; letter-spacing: -0.04em; line-height: 1.1; color: var(--color-text-primary); margin-bottom: 2px; }
.hero__title-cn { font-size: 20px; font-weight: 500; color: var(--color-text-secondary); letter-spacing: 0.02em; margin-bottom: var(--space-4); }
.hero__subtitle { font-size: 16px; color: var(--color-text-primary); line-height: 1.7; max-width: 560px; margin-bottom: var(--space-8); }
.hero__subtitle-en { font-size: 13px; color: var(--color-text-tertiary); }
.hero__actions { display: flex; gap: var(--space-3); align-items: center; }
.btn { display: inline-flex; align-items: center; gap: 6px; height: 40px; padding: 0 var(--space-5); border-radius: var(--radius-sm); font-size: 14px; font-weight: 500; transition: all 150ms ease; cursor: pointer; }
.btn__en { font-size: 12px; opacity: 0.7; font-weight: 400; }
.btn--primary { background: var(--color-accent); color: #fff; border: none; }
.btn--primary:hover { background: #005abf; }
.btn--primary:disabled { opacity: 0.5; cursor: not-allowed; }
</style>
