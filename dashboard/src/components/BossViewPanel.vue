<script setup lang="ts">
import { computed } from 'vue'
import type { JobDetail } from '../types/job'

const props = defineProps<{ job: JobDetail | null }>()

const opp = computed(() => props.job?.artifacts?.['opportunity-report.json'] || null)
const readiness = computed(() => props.job?.artifacts?.['submission-readiness-report.json'] || null)
const qa = computed(() => props.job?.artifacts?.['qa-report.json'] || null)

// Support both the new (ready_to_submit) and legacy (is_ready_to_submit) shapes.
const isReady = computed(() =>
  readiness.value ? !!(readiness.value.ready_to_submit ?? readiness.value.is_ready_to_submit) : false
)
const blockingIssues = computed<string[]>(() => readiness.value?.blocking_issues || [])
const warningIssues = computed<string[]>(() => readiness.value?.warning_issues || [])
const humanActions = computed<string[]>(() => readiness.value?.human_actions || [])
</script>

<template>
  <div class="boss-view">
    <div v-if="!job" class="empty">暂无数据</div>
    <template v-else>
      <!-- Headline -->
      <div class="headline">
        <h2 v-if="opp">{{ opp.app_name_cn }}</h2>
        <p v-if="opp" class="score-line">机会评分 <strong>{{ opp.total_score }}</strong>/100 · {{ opp.recommendation || '暂无推荐' }}</p>
        <p v-else class="no-data">暂无机会评分数据</p>
      </div>

      <!-- Scores -->
      <div v-if="opp" class="scores-grid">
        <div class="score-card"><div class="sc-label">需求强度</div><div class="sc-value">{{ opp.demand_score }}</div></div>
        <div class="score-card"><div class="sc-label">小程序缺口</div><div class="sc-value">{{ opp.miniapp_gap_score }}</div></div>
        <div class="score-card"><div class="sc-label">适配度</div><div class="sc-value">{{ opp.miniapp_fit_score }}</div></div>
        <div class="score-card"><div class="sc-label">实现难度</div><div class="sc-value">{{ opp.implementation_score }}</div></div>
        <div class="score-card"><div class="sc-label">风险</div><div class="sc-value">{{ opp.risk_score }}</div></div>
      </div>

      <!-- Reasons -->
      <div v-if="opp?.reasons?.length" class="reasons-section">
        <h4>推荐理由</h4>
        <span v-for="r in opp.reasons" :key="r" class="reason-tag good">{{ r }}</span>
      </div>
      <div v-if="opp?.reject_reasons?.length" class="reasons-section">
        <h4>风险提示</h4>
        <span v-for="r in opp.reject_reasons" :key="r" class="reason-tag bad">{{ r }}</span>
      </div>

      <!-- Readiness -->
      <div v-if="readiness" class="readiness-section">
        <h4>提交审核状态</h4>
        <div class="ready-badge" :class="isReady ? 'ready-yes' : 'ready-no'">
          {{ isReady ? '✓ 可以提交审核' : '✗ 当前不能提交审核' }}
        </div>
        <div v-if="!isReady && blockingIssues.length" class="blockings">
          <div class="block-heading">阻塞原因（必须先解决）</div>
          <div v-for="b in blockingIssues" :key="b" class="block-item">• {{ b }}</div>
        </div>
        <div v-if="warningIssues.length" class="warnings">
          <div class="warn-heading">提示</div>
          <span v-for="w in warningIssues" :key="w" class="warn-item">• {{ w }}</span>
        </div>
        <div v-if="humanActions.length" class="human-actions">
          <div class="human-heading">需要人工完成</div>
          <div v-for="h in humanActions" :key="h" class="human-item">→ {{ h }}</div>
        </div>
      </div>
      <div v-else class="no-data">暂无提交审核数据</div>

      <!-- Platforms -->
      <div v-if="readiness?.target_platforms?.length" class="platforms-section">
        <h4>目标平台</h4>
        <span v-for="p in readiness.target_platforms" :key="p" class="platform-chip">{{ p }}</span>
      </div>
      <div v-if="readiness?.rejected_platforms?.length" class="platforms-section">
        <h4>不可提交平台</h4>
        <div v-for="r in readiness.rejected_platforms" :key="r.platform" class="rejected-item">{{ r.platform }}: {{ r.reason }}</div>
      </div>

      <!-- Next action -->
      <div v-if="readiness?.next_action" class="next-action">
        下一步: {{ readiness.next_action }}
      </div>

      <!-- Dist path -->
      <div v-if="qa?.checks?.dist_path" class="dist-section">
        <span class="dist-label">构建产物</span>
        <code class="dist-path">{{ qa.checks.dist_path }}</code>
      </div>
    </template>
  </div>
</template>

<style scoped>
.boss-view { animation: fadeIn 0.3s ease; }
.empty, .no-data { color: var(--color-text-3); font-size: 14px; padding: 20px 0; }
.headline { margin-bottom: 24px; }
.headline h2 { font-size: 28px; font-weight: 700; color: var(--color-text-1); }
.score-line { font-size: 16px; color: var(--color-text-2); margin-top: 4px; }
.score-line strong { font-size: 24px; color: var(--color-blue); }
.scores-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 12px; margin-bottom: 20px; }
.score-card { background: var(--color-surface-solid); border-radius: var(--radius-md); padding: 16px; box-shadow: var(--shadow-card); text-align: center; }
.sc-label { font-size: 11px; color: var(--color-text-3); font-weight: 500; text-transform: uppercase; }
.sc-value { font-size: 24px; font-weight: 700; color: var(--color-text-1); margin-top: 4px; }
.reasons-section { margin-bottom: 16px; }
.reasons-section h4 { font-size: 13px; font-weight: 600; color: var(--color-text-2); margin-bottom: 8px; }
.reason-tag { font-size: 12px; padding: 3px 8px; border-radius: 4px; margin-right: 4px; display: inline-block; margin-bottom: 4px; }
.reason-tag.good { background: var(--color-green-subtle); color: #166534; }
.reason-tag.bad { background: rgba(255,59,48,0.08); color: #991b1b; }
.readiness-section { margin-bottom: 16px; }
.readiness-section h4 { font-size: 13px; font-weight: 600; color: var(--color-text-2); margin-bottom: 8px; }
.ready-badge { display: inline-block; font-size: 13px; font-weight: 600; padding: 6px 14px; border-radius: 8px; margin-bottom: 8px; }
.ready-yes { background: var(--color-green-subtle); color: #166534; }
.ready-no { background: rgba(255,59,48,0.08); color: #991b1b; }
.warnings { margin-top: 8px; }
.warn-heading, .block-heading, .human-heading { font-size: 11px; font-weight: 700; text-transform: uppercase; margin: 8px 0 4px; }
.warn-heading { color: #92400e; }
.block-heading { color: #991b1b; }
.human-heading { color: var(--color-text-2); }
.warn-item { display: block; font-size: 12px; color: #92400e; padding: 2px 0; }
.blockings { margin-top: 8px; padding: 10px 12px; background: rgba(255,59,48,0.06); border-radius: var(--radius-sm); }
.block-item { display: block; font-size: 13px; color: #991b1b; padding: 2px 0; font-weight: 500; }
.human-actions { margin-top: 8px; }
.human-item { display: block; font-size: 12px; color: var(--color-text-2); padding: 2px 0; }
.platforms-section { margin-bottom: 16px; }
.platforms-section h4 { font-size: 13px; font-weight: 600; color: var(--color-text-2); margin-bottom: 6px; }
.platform-chip { font-size: 12px; padding: 3px 8px; background: var(--color-blue-subtle); color: var(--color-blue); border-radius: 4px; margin-right: 4px; }
.rejected-item { font-size: 12px; color: var(--color-text-3); padding: 2px 0; }
.next-action { font-size: 13px; padding: 12px 16px; background: var(--color-blue-subtle); border-radius: var(--radius-sm); color: var(--color-text-1); margin-bottom: 16px; }
.dist-section { display: flex; align-items: center; gap: 8px; }
.dist-label { font-size: 11px; color: var(--color-text-3); }
.dist-path { font-size: 11px; font-family: var(--font-mono); color: var(--color-text-1); background: rgba(0,0,0,0.04); padding: 4px 8px; border-radius: 4px; }
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
</style>
