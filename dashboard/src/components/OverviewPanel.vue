<script setup lang="ts">
import { computed, ref } from 'vue'
import type { JobDetail } from '../types/job'

const props = defineProps<{ job: JobDetail }>()

const opportunity = computed(() => props.job.artifacts?.['opportunity-report.json'] || {})
const qa = computed(() => props.job.artifacts?.['qa-report.json'] || {})

const totalScore = computed(() => opportunity.value.total_score ?? '-')
const demandScore = computed(() => opportunity.value.demand_score ?? '-')
const gapScore = computed(() => opportunity.value.miniapp_gap_score ?? '-')
const riskScore = computed(() => opportunity.value.risk_score ?? '-')
const nextAction = computed(() => opportunity.value.next_action || '暂无')
const distPath = computed(() => qa.value.checks?.dist_path || props.job.miniapp_path || '')

const copied = ref(false)

function copyDistPath() {
  if (!distPath.value) return
  navigator.clipboard.writeText(distPath.value)
  copied.value = true
  setTimeout(() => { copied.value = false }, 1500)
}

const checklist = computed(() => [
  { label: 'PRD 产品需求文档', done: !!props.job.artifacts?.['prd.md'] },
  { label: 'Code 代码生成', done: !!props.job.miniapp_path || (props.job.miniapp_files?.length ?? 0) > 0 },
  { label: 'QA 质量验证', done: !!props.job.artifacts?.['qa-report.json'] },
  { label: 'Listing 上架材料', done: !!props.job.artifacts?.['listing-materials.json'] || !!props.job.artifacts?.['listing-materials.md'] },
  { label: 'Guide 人工操作指南', done: !!props.job.artifacts?.['human-actions.md'] },
])
</script>

<template>
  <div class="overview">
    <div class="metrics-grid">
      <div class="metric-card metric-card--primary">
        <span class="metric-label">Opportunity Score</span>
        <span class="metric-value metric-value--blue">{{ totalScore }}</span>
      </div>
      <div class="metric-card">
        <span class="metric-label">Demand Score</span>
        <span class="metric-value">{{ demandScore }}</span>
      </div>
      <div class="metric-card">
        <span class="metric-label">Gap Score</span>
        <span class="metric-value">{{ gapScore }}</span>
      </div>
      <div class="metric-card">
        <span class="metric-label">Risk Score</span>
        <span class="metric-value">{{ riskScore }}</span>
      </div>
    </div>

    <div class="action-card">
      <div class="action-header">
        <span class="action-title">Next Action</span>
      </div>
      <p class="action-text">{{ nextAction }}</p>
      <div class="action-dist" v-if="distPath">
        <code class="dist-path">{{ distPath }}</code>
        <button class="copy-btn" @click="copyDistPath">
          {{ copied ? 'Copied!' : 'Copy Dist Path' }}
        </button>
      </div>
    </div>

    <div class="checklist-card">
      <h3 class="checklist-title">Pipeline Products</h3>
      <ul class="checklist">
        <li v-for="item in checklist" :key="item.label" class="check-item">
          <span class="check-icon" :class="item.done ? 'check-icon--done' : 'check-icon--pending'">
            {{ item.done ? '✓' : '○' }}
          </span>
          <span class="check-label">{{ item.label }}</span>
        </li>
      </ul>
    </div>
  </div>
</template>

<style scoped>
.overview {
  display: flex;
  flex-direction: column;
  gap: 32px;
}

.metrics-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.metric-card {
  background: var(--color-surface-solid);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.metric-label {
  font-size: 12px;
  font-weight: 500;
  color: var(--color-text-2);
  text-transform: uppercase;
  letter-spacing: 0.03em;
}

.metric-value {
  font-size: 32px;
  font-weight: 700;
  color: var(--color-text-1);
  letter-spacing: -0.02em;
}
.metric-value--blue {
  color: var(--color-blue);
}

.action-card {
  background: var(--color-surface-solid);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
  padding: 24px;
}

.action-header {
  margin-bottom: 8px;
}

.action-title {
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  color: var(--color-text-3);
}

.action-text {
  font-size: 15px;
  color: var(--color-text-1);
  margin: 0 0 16px;
  line-height: 1.5;
}

.action-dist {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: rgba(0, 0, 0, 0.03);
  border-radius: var(--radius-sm);
}

.dist-path {
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--color-text-2);
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.copy-btn {
  font-size: 12px;
  font-weight: 500;
  color: var(--color-blue);
  background: none;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  padding: 5px 12px;
  cursor: pointer;
  white-space: nowrap;
  transition: transform 0.12s var(--ease-apple), background 0.12s;
}
.copy-btn:hover {
  background: var(--color-blue-subtle);
  transform: translateY(-1px);
}
.copy-btn:active {
  transform: scale(0.98);
}

.checklist-card {
  background: var(--color-surface-solid);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
  padding: 24px;
}

.checklist-title {
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  color: var(--color-text-3);
  margin: 0 0 16px;
}

.checklist {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.check-item {
  display: flex;
  align-items: center;
  gap: 10px;
}

.check-icon {
  font-size: 14px;
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
}
.check-icon--done {
  background: var(--color-green-subtle);
  color: #1a8d36;
  font-weight: 600;
}
.check-icon--pending {
  color: var(--color-text-3);
}

.check-label {
  font-size: 14px;
  color: var(--color-text-1);
}
</style>
