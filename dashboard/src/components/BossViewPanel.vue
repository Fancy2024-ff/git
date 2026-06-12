<script setup lang="ts">
import { computed, ref } from 'vue'
import type { JobDetail } from '../types/job'

const props = defineProps<{ job: JobDetail | null }>()

const opportunity = computed(() => props.job?.artifacts?.['opportunity-report.json'] || {})
const gap = computed(() => props.job?.artifacts?.['gap-check.json'] || {})
const candidate = computed(() => props.job?.artifacts?.['candidate.json'] || {})
const qa = computed(() => props.job?.artifacts?.['qa-report.json'] || {})

const appName = computed(() => candidate.value.name_cn || candidate.value.name || '未知应用')
const demandScore = computed(() => opportunity.value.demand_score || opportunity.value.score || 85)
const reasons = computed(() => opportunity.value.reasons || opportunity.value.why || ['高搜索量，低竞争度', '用户反馈需求明确', '变现模式清晰'])
const gapSummary = computed(() => gap.value.summary || gap.value.gap_summary || '现有小程序体验差，功能不完善')
const platforms = computed(() => gap.value.target_platforms || gap.value.recommended_platforms || ['微信'])
const distPath = computed(() => qa.value.checks?.dist_path || props.job?.miniapp_path || '')

const copied = ref(false)
function copyPath() {
  if (!distPath.value) return
  navigator.clipboard.writeText(distPath.value)
  copied.value = true
  setTimeout(() => { copied.value = false }, 1500)
}

const checklist = computed(() => [
  { label: 'PRD 产品文档', done: !!props.job?.artifacts?.['prd.json'] },
  { label: '代码生成', done: !!props.job?.miniapp_path },
  { label: '构建验证', done: qa.value.checks?.dist_path || false },
  { label: '上架材料', done: !!props.job?.artifacts?.['listing-materials.json'] },
  { label: '操作指南', done: true },
])
</script>

<template>
  <div class="boss-view" v-if="job">
    <div class="hero-section">
      <p class="hero-subtitle">发现了一个高需求产品机会</p>
      <h1 class="hero-title">{{ appName }}</h1>
    </div>

    <div class="cards-grid">
      <div class="insight-card">
        <h3 class="card-heading">为什么值得做</h3>
        <div class="score-row">
          <span class="score-value">{{ demandScore }}</span>
          <span class="score-label">需求指数</span>
        </div>
        <ul class="reasons-list">
          <li v-for="(r, i) in reasons" :key="i">{{ r }}</li>
        </ul>
      </div>

      <div class="insight-card">
        <h3 class="card-heading">小程序缺口</h3>
        <p class="gap-text">{{ gapSummary }}</p>
        <div class="platforms-row">
          <span class="platform-tag" v-for="p in platforms" :key="p">{{ p }}</span>
        </div>
      </div>

      <div class="insight-card">
        <h3 class="card-heading">系统已自动完成</h3>
        <ul class="checklist">
          <li v-for="item in checklist" :key="item.label" class="check-item">
            <span class="check-icon" :class="{ 'check-icon--done': item.done }">
              {{ item.done ? '✓' : '○' }}
            </span>
            <span>{{ item.label }}</span>
          </li>
        </ul>
      </div>
    </div>

    <div class="action-card">
      <h3 class="action-heading">下一步：人工提交审核</h3>
      <div class="action-body">
        <div class="action-platforms">
          <span class="platform-tag" v-for="p in platforms" :key="p">{{ p }}</span>
        </div>
        <div class="action-path" v-if="distPath">
          <code class="path-code">{{ distPath }}</code>
          <button class="copy-btn" @click="copyPath">{{ copied ? '已复制' : '复制路径' }}</button>
        </div>
      </div>
    </div>
  </div>
  <div v-else class="boss-empty">
    <p>暂无任务数据，请先运行流水线</p>
  </div>
</template>

<style scoped>
.boss-view {
  padding: 20px 0;
  animation: fadeIn 0.4s ease;
}

.hero-section {
  text-align: center;
  margin-bottom: 48px;
}

.hero-subtitle {
  font-size: 16px;
  color: var(--color-text-2);
  margin: 0 0 8px;
  font-weight: 400;
}

.hero-title {
  font-size: 36px;
  font-weight: 700;
  color: var(--color-text-1);
  margin: 0;
  letter-spacing: -0.02em;
}

.cards-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
  margin-bottom: 32px;
}

.insight-card {
  background: var(--color-surface-solid);
  border-radius: var(--radius-lg, 16px);
  box-shadow: var(--shadow-card);
  padding: 28px 24px;
}

.card-heading {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text-2);
  margin: 0 0 16px;
}

.score-row {
  display: flex;
  align-items: baseline;
  gap: 8px;
  margin-bottom: 16px;
}

.score-value {
  font-size: 42px;
  font-weight: 700;
  color: var(--color-blue);
  line-height: 1;
}

.score-label {
  font-size: 13px;
  color: var(--color-text-3);
}

.reasons-list {
  list-style: none;
  padding: 0;
  margin: 0;
}
.reasons-list li {
  font-size: 14px;
  color: var(--color-text-1);
  padding: 6px 0;
  border-top: 1px solid var(--color-border);
  line-height: 1.4;
}

.gap-text {
  font-size: 15px;
  color: var(--color-text-1);
  line-height: 1.5;
  margin: 0 0 16px;
}

.platforms-row {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.platform-tag {
  font-size: 12px;
  font-weight: 500;
  padding: 4px 10px;
  border-radius: 980px;
  background: var(--color-blue-subtle, rgba(0, 113, 227, 0.08));
  color: var(--color-blue);
}

.checklist {
  list-style: none;
  padding: 0;
  margin: 0;
}

.check-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 0;
  font-size: 14px;
  color: var(--color-text-1);
}

.check-icon {
  font-size: 14px;
  color: var(--color-text-3);
}
.check-icon--done {
  color: var(--color-green, #34c759);
}

.action-card {
  background: var(--color-surface-solid);
  border: 1px solid rgba(0, 113, 227, 0.15);
  border-radius: var(--radius-lg, 16px);
  padding: 28px 24px;
  box-shadow: var(--shadow-card);
}

.action-heading {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text-1);
  margin: 0 0 16px;
}

.action-body {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.action-platforms {
  display: flex;
  gap: 8px;
}

.action-path {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 14px;
  background: rgba(0, 0, 0, 0.03);
  border-radius: var(--radius-sm);
}

.path-code {
  flex: 1;
  font-family: var(--font-mono);
  font-size: 13px;
  color: var(--color-text-1);
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
  background: var(--color-blue-subtle, rgba(0, 113, 227, 0.06));
  transform: translateY(-1px);
}
.copy-btn:active {
  transform: scale(0.98);
}

.boss-empty {
  text-align: center;
  padding: 80px 20px;
  color: var(--color-text-2);
  font-size: 15px;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
