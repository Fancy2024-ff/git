<script setup lang="ts">
import { computed } from 'vue'
import type { JobDetail } from '../types/job'

const props = defineProps<{ job: JobDetail }>()

const candidate = computed(() => props.job.artifacts?.['candidate.json'] || {})
const opportunity = computed(() => props.job.artifacts?.['opportunity-report.json'] || {})
const qa = computed(() => props.job.artifacts?.['qa-report.json'] || {})
</script>

<template>
  <div class="overview">
    <div class="meta">
      <span class="meta-item">Job ID: <strong>{{ job.id }}</strong></span>
      <span class="meta-item">应用: <strong>{{ candidate.name_cn || candidate.name || '—' }}</strong></span>
      <span v-if="candidate.name" class="meta-item en">{{ candidate.name }}</span>
      <span v-if="job.timestamp" class="meta-item">{{ job.timestamp }}</span>
    </div>

    <div class="cards">
      <div class="card">
        <div class="card-label">机会评分 Score</div>
        <div class="card-value score">{{ opportunity.opportunity_score ?? '—' }}</div>
        <div class="card-sub">{{ opportunity.recommendation || '' }}</div>
      </div>

      <div class="card">
        <div class="card-label">质量检查 QA</div>
        <div class="card-value" :class="qa.passed ? 'pass' : 'fail'">
          {{ qa.passed ? '✓ 通过' : '✗ 未通过' }}
        </div>
        <div class="card-sub">{{ qa.summary || '' }}</div>
      </div>

      <div class="card">
        <div class="card-label">构建验证 Build</div>
        <div class="card-value" :class="qa.checks?.build_passed ? 'pass' : 'fail'">
          {{ qa.checks?.build_verified ? '已验证' : '未验证' }}
        </div>
        <div class="card-sub">{{ qa.checks?.build_passed ? '构建通过' : '构建未通过' }}</div>
      </div>
      <div class="card">
        <div class="card-label">产物就绪 Dist</div>
        <div class="card-value" :class="qa.checks?.dist_exists ? 'pass' : 'fail'">
          {{ qa.checks?.dist_exists ? '已就绪' : '未就绪' }}
        </div>
        <div class="card-sub">{{ job.miniapp_path || '—' }}</div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.overview { animation: fadeIn 0.3s ease; }

.meta {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  margin-bottom: 24px;
  font-size: 13px;
  color: var(--color-text-2);
}
.meta-item strong { color: var(--color-text-1); font-weight: 500; }
.meta-item.en { color: var(--color-text-3); }

.cards {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.card {
  background: var(--color-surface-solid, #fff);
  border-radius: var(--radius-lg, 12px);
  padding: 24px;
  box-shadow: var(--shadow-card, 0 1px 4px rgba(0,0,0,0.06));
}

.card-label {
  font-size: 11px;
  font-weight: 600;
  color: var(--color-text-3);
  text-transform: uppercase;
  letter-spacing: 0.03em;
  margin-bottom: 8px;
}

.card-value {
  font-size: 28px;
  font-weight: 700;
  color: var(--color-text-1);
  letter-spacing: -0.02em;
}
.card-value.score { color: var(--color-accent, #007aff); }
.card-value.pass { color: #1d7a34; }
.card-value.fail { color: #c41e16; }

.card-sub {
  font-size: 12px;
  color: var(--color-text-3);
  margin-top: 4px;
  word-break: break-all;
}

@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
</style>
