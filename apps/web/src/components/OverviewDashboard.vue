<script setup lang="ts">
import { computed } from 'vue'
import type { JobDetail, PipelineMode } from '../types/job'
import {
  computeOverallStatus, statusLabel, oneLineConclusion,
  whyWorthIt, completionChecklist, blockers, nextActions,
} from '../data/overview'

const props = defineProps<{
  job: JobDetail | null
  running: boolean
  mode: PipelineMode
}>()

const emit = defineEmits<{ goto: [tab: string] }>()

const art = computed(() => props.job?.artifacts || {})
const input = computed(() => ({
  running: props.running,
  candidate: art.value['candidate.json'] || null,
  opportunity: art.value['opportunity-report.json'] || null,
  qa: art.value['qa-report.json'] || null,
  readiness: art.value['submission-readiness-report.json'] || null,
  pipelineReport: art.value['pipeline-report.json'] || null,
}))

const status = computed(() => computeOverallStatus(input.value))
const statusBadge = computed(() => statusLabel(status.value))
const conclusion = computed(() => oneLineConclusion(input.value))

const appCn = computed(() => input.value.candidate?.name_cn || input.value.opportunity?.app_name_cn || '—')
const appEn = computed(() => input.value.candidate?.name || input.value.opportunity?.app_name || '')
const score = computed(() => input.value.opportunity?.total_score ?? input.value.opportunity?.opportunity_score ?? null)
const recommendation = computed(() => input.value.opportunity?.recommendation || '')
const modeLabel = computed(() => ({ demo: '试运行', real: '生产运行', live: '实时分析' }[props.mode]))

const why = computed(() => whyWorthIt(input.value))
const checklist = computed(() => completionChecklist(input.value))
const block = computed(() => blockers(input.value))
const actions = computed(() => nextActions(input.value))

const hasJob = computed(() => !!props.job)

const guideSteps = [
  { t: '看机会', d: '为什么值得做', tab: 'overview' },
  { t: '看生产线', d: 'Agent 跑到哪一步', tab: 'pipeline' },
  { t: '看交付物', d: 'PRD / 代码 / 上架材料', tab: 'deliverables' },
  { t: '看上架中心', d: '哪些平台可提交、缺什么', tab: 'submit' },
]
</script>

<template>
  <div class="overview">
    <!-- Hero -->
    <section class="hero" :class="'hero--' + statusBadge.tone">
      <div class="hero-top">
        <div class="hero-app">
          <h1 class="hero-cn">{{ appCn }}</h1>
          <span class="hero-en">{{ appEn }}</span>
        </div>
        <span class="hero-status" :class="'tone--' + statusBadge.tone">{{ statusBadge.text }}</span>
      </div>
      <div class="hero-meta">
        <span v-if="job" class="meta-chip mono">{{ job.id }}</span>
        <span class="meta-chip">模式 · {{ modeLabel }}</span>
        <span v-if="score !== null" class="meta-chip">机会评分 · {{ score }}/100</span>
        <span v-if="recommendation" class="meta-chip strong">{{ recommendation }}</span>
      </div>
      <p class="hero-conclusion">{{ conclusion }}</p>
    </section>

    <!-- Three core cards -->
    <section class="cards">
      <!-- A: why worth it -->
      <div class="card">
        <h3 class="card-title">为什么值得做</h3>
        <div v-if="why" class="card-body">
          <div class="score-grid">
            <div class="score-cell"><span class="sc-num">{{ why.demand ?? '—' }}</span><span class="sc-lbl">需求强度</span></div>
            <div class="score-cell"><span class="sc-num">{{ why.gap ?? '—' }}</span><span class="sc-lbl">平台缺口</span></div>
            <div class="score-cell"><span class="sc-num">{{ why.fit ?? '—' }}</span><span class="sc-lbl">适配度</span></div>
          </div>
          <ul class="reason-list">
            <li v-for="(r, i) in why.reasons" :key="i">{{ r }}</li>
          </ul>
        </div>
        <p v-else class="card-empty">暂无数据</p>
      </div>

      <!-- B: completed -->
      <div class="card">
        <h3 class="card-title">系统完成了什么</h3>
        <div v-if="hasJob" class="card-body">
          <div v-for="item in checklist" :key="item.label" class="check-row">
            <span class="check-mark" :class="item.done ? 'mk--done' : 'mk--todo'">{{ item.done ? '✓' : '○' }}</span>
            <span class="check-label" :class="{ 'lbl--done': item.done }">{{ item.label }}</span>
          </div>
        </div>
        <p v-else class="card-empty">暂无数据</p>
      </div>

      <!-- C: blockers -->
      <div class="card">
        <h3 class="card-title">现在卡在哪里</h3>
        <div v-if="input.readiness" class="card-body">
          <template v-if="block.blocking.length || block.warning.length">
            <div v-for="(b, i) in block.blocking" :key="'b'+i" class="issue issue--block">{{ b }}</div>
            <div v-for="(w, i) in block.warning" :key="'w'+i" class="issue issue--warn">{{ w }}</div>
          </template>
          <p v-else class="all-clear">当前无阻塞</p>
        </div>
        <p v-else class="card-empty">暂无数据</p>
      </div>
    </section>

    <!-- Next actions -->
    <section class="next-section">
      <h3 class="section-title">下一步谁来做</h3>
      <div v-if="actions.length" class="action-cols">
        <div class="action-col">
          <h4 class="col-head col-head--agent">Agent 可做</h4>
          <div v-for="(a, i) in actions.filter(x => x.owner === 'agent')" :key="i" class="action-row">
            <span class="dot dot--agent"></span>{{ a.text }}
          </div>
          <p v-if="!actions.some(x => x.owner === 'agent')" class="col-empty">暂无</p>
        </div>
        <div class="action-col">
          <h4 class="col-head col-head--human">人工要做</h4>
          <div v-for="(a, i) in actions.filter(x => x.owner === 'human')" :key="i" class="action-row">
            <span class="dot dot--human"></span>{{ a.text }}
          </div>
          <p v-if="!actions.some(x => x.owner === 'human')" class="col-empty">暂无</p>
        </div>
      </div>
      <p v-else class="card-empty">暂无数据，先启动一次运行</p>
    </section>

    <!-- Demo guide -->
    <section class="guide-section">
      <h3 class="section-title">演示顺序</h3>
      <div class="guide-row">
        <button v-for="(g, i) in guideSteps" :key="i" class="guide-step" @click="emit('goto', g.tab)">
          <span class="guide-num">{{ i + 1 }}</span>
          <span class="guide-text"><b>{{ g.t }}</b>{{ g.d }}</span>
        </button>
      </div>
    </section>
  </div>
</template>

<style scoped>
.overview { animation: fadeIn 0.3s var(--ease-apple); display: flex; flex-direction: column; gap: 20px; }

/* Hero */
.hero { background: var(--color-surface-solid); border-radius: var(--radius-lg); box-shadow: var(--shadow-card); padding: 24px; border-left: 4px solid var(--color-text-3); }
.hero--blue { border-left-color: var(--color-blue); }
.hero--green { border-left-color: var(--color-green); }
.hero--orange { border-left-color: var(--color-orange); }
.hero--red { border-left-color: var(--color-red); }
.hero--gray { border-left-color: var(--color-text-3); }
.hero-top { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; }
.hero-cn { font-size: 24px; font-weight: 700; color: var(--color-text-1); line-height: 1.2; }
.hero-en { font-size: 13px; color: var(--color-text-3); }
.hero-status { font-size: 13px; font-weight: 600; padding: 5px 14px; border-radius: 980px; white-space: nowrap; flex-shrink: 0; }
.tone--blue { background: var(--color-blue-subtle); color: var(--color-blue); }
.tone--green { background: var(--color-green-subtle); color: #166534; }
.tone--orange { background: var(--color-orange-subtle); color: #92400e; }
.tone--red { background: rgba(255,59,48,0.08); color: #991b1b; }
.tone--gray { background: rgba(0,0,0,0.05); color: var(--color-text-2); }
.hero-meta { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 14px; }
.meta-chip { font-size: 12px; color: var(--color-text-2); background: rgba(0,0,0,0.04); padding: 4px 10px; border-radius: 6px; }
.meta-chip.mono { font-family: var(--font-mono); }
.meta-chip.strong { background: var(--color-blue-subtle); color: var(--color-blue); font-weight: 500; }
.hero-conclusion { margin-top: 16px; font-size: 15px; line-height: 1.6; color: var(--color-text-1); }

/* Cards */
.cards { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }
.card { background: var(--color-surface-solid); border-radius: var(--radius-lg); box-shadow: var(--shadow-card); padding: 20px; }
.card-title { font-size: 16px; font-weight: 600; color: var(--color-text-1); margin-bottom: 14px; }
.card-empty { font-size: 13px; color: var(--color-text-3); padding: 16px 0; text-align: center; }

.score-grid { display: flex; gap: 8px; margin-bottom: 12px; }
.score-cell { flex: 1; background: rgba(0,0,0,0.03); border-radius: var(--radius-sm); padding: 10px; text-align: center; }
.sc-num { display: block; font-size: 22px; font-weight: 700; color: var(--color-text-1); }
.sc-lbl { display: block; font-size: 11px; color: var(--color-text-3); margin-top: 2px; }
.reason-list { list-style: none; padding: 0; margin: 0; }
.reason-list li { font-size: 13px; color: var(--color-text-2); padding: 4px 0 4px 16px; position: relative; }
.reason-list li::before { content: '✓'; position: absolute; left: 0; color: var(--color-green); }

.check-row { display: flex; align-items: center; gap: 8px; padding: 5px 0; }
.check-mark { width: 18px; text-align: center; font-size: 14px; }
.mk--done { color: var(--color-green); }
.mk--todo { color: var(--color-text-3); }
.check-label { font-size: 13px; color: var(--color-text-1); }
.lbl--done { color: var(--color-text-2); }

.issue { font-size: 13px; padding: 8px 10px; border-radius: var(--radius-sm); margin-bottom: 6px; }
.issue--block { background: rgba(255,59,48,0.06); color: #991b1b; }
.issue--warn { background: var(--color-orange-subtle); color: #92400e; }
.all-clear { font-size: 14px; color: #166534; padding: 16px 0; text-align: center; }

/* Next actions */
.next-section, .guide-section { background: var(--color-surface-solid); border-radius: var(--radius-lg); box-shadow: var(--shadow-card); padding: 20px; }
.section-title { font-size: 16px; font-weight: 600; color: var(--color-text-1); margin-bottom: 14px; }
.action-cols { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
.col-head { font-size: 12px; font-weight: 600; margin-bottom: 8px; text-transform: uppercase; letter-spacing: 0.03em; }
.col-head--agent { color: var(--color-blue); }
.col-head--human { color: #92400e; }
.action-row { display: flex; align-items: flex-start; gap: 8px; font-size: 13px; color: var(--color-text-1); padding: 5px 0; line-height: 1.5; }
.dot { width: 8px; height: 8px; border-radius: 50%; margin-top: 6px; flex-shrink: 0; }
.dot--agent { background: var(--color-blue); }
.dot--human { background: var(--color-orange); }
.col-empty { font-size: 12px; color: var(--color-text-3); }

/* Guide */
.guide-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
.guide-step { display: flex; align-items: center; gap: 10px; background: rgba(0,0,0,0.03); border: none; border-radius: var(--radius-md); padding: 12px; cursor: pointer; text-align: left; transition: background 0.15s; }
.guide-step:hover { background: var(--color-blue-subtle); }
.guide-num { width: 24px; height: 24px; border-radius: 50%; background: var(--color-blue); color: #fff; font-size: 13px; font-weight: 600; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.guide-text { display: flex; flex-direction: column; font-size: 12px; color: var(--color-text-2); }
.guide-text b { font-size: 13px; color: var(--color-text-1); }

@media (max-width: 900px) {
  .cards { grid-template-columns: 1fr; }
  .action-cols { grid-template-columns: 1fr; }
  .guide-row { grid-template-columns: 1fr 1fr; }
}

@keyframes fadeIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
</style>
