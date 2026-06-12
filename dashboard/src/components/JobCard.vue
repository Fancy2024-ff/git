<script setup lang="ts">
import type { Job } from '../data/mockData'

defineProps<{ job: Job }>()

function scoreColor(score: number): string {
  if (score >= 85) return 'var(--color-green)'
  if (score >= 70) return 'var(--color-accent)'
  return 'var(--color-orange)'
}
</script>

<template>
  <div class="job-card">
    <div class="job-card__header">
      <div class="job-card__names">
        <h4 class="job-card__name">{{ job.nameCn }}</h4>
        <span class="job-card__name-en">{{ job.name }}</span>
      </div>
      <span class="job-card__score" :style="{ color: scoreColor(job.score) }">{{ job.score }}</span>
    </div>

    <div class="job-card__meta">
      <span class="meta-tag meta-tag--source">{{ job.source }}</span>
      <span class="meta-tag meta-tag--stage">{{ job.stage }}</span>
    </div>

    <div class="job-card__platforms">
      <span v-for="p in job.platforms" :key="p" class="platform-tag">{{ p }}</span>
    </div>

    <p class="job-card__next">{{ job.nextAction }}</p>

    <div class="job-card__footer">
      <span class="status-dot" :class="`status-dot--${job.status}`"></span>
      <span class="status-text">{{ job.status === 'active' ? '进行中' : job.status === 'paused' ? '等待人工' : '已完成' }}</span>
      <a class="view-link">查看详情 →</a>
    </div>
  </div>
</template>

<style scoped>
.job-card {
  background: var(--color-surface);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
  padding: var(--space-5);
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
  transition: box-shadow var(--duration-normal) var(--ease-out), transform var(--duration-normal) var(--ease-out);
}
.job-card:hover { box-shadow: var(--shadow-lg); transform: translateY(-1px); }

.job-card__header { display: flex; justify-content: space-between; align-items: flex-start; }
.job-card__names { display: flex; flex-direction: column; gap: 1px; }
.job-card__name { font-size: 15px; font-weight: 600; color: var(--color-text-primary); letter-spacing: -0.01em; }
.job-card__name-en { font-size: 12px; color: var(--color-text-tertiary); }
.job-card__score { font-size: 24px; font-weight: 700; letter-spacing: -0.03em; line-height: 1; }

.job-card__meta { display: flex; gap: var(--space-2); }
.meta-tag { font-size: 11px; font-weight: 500; padding: 2px 7px; border-radius: var(--radius-full); }
.meta-tag--source { background: var(--color-bg); color: var(--color-text-secondary); }
.meta-tag--stage { background: var(--color-accent-subtle); color: var(--color-accent); }

.job-card__platforms { display: flex; gap: 4px; flex-wrap: wrap; }
.platform-tag { font-size: 11px; font-weight: 500; padding: 2px 8px; border-radius: var(--radius-full); background: var(--color-bg); color: var(--color-text-secondary); border: 1px solid var(--color-border); }

.job-card__next { font-size: 13px; color: var(--color-text-secondary); line-height: 1.5; }

.job-card__footer { display: flex; align-items: center; gap: var(--space-2); margin-top: auto; padding-top: var(--space-2); border-top: 1px solid var(--color-border); }
.status-dot { width: 6px; height: 6px; border-radius: 50%; }
.status-dot--active { background: var(--color-green); }
.status-dot--paused { background: var(--color-orange); }
.status-dot--completed { background: var(--color-text-tertiary); }
.status-text { font-size: 12px; color: var(--color-text-secondary); }
.view-link { margin-left: auto; font-size: 12px; font-weight: 500; color: var(--color-accent); cursor: pointer; text-decoration: none; }
.view-link:hover { text-decoration: underline; }
</style>
