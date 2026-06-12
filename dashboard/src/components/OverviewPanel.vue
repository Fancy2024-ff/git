<script setup lang="ts">
import { computed } from 'vue'
import type { JobDetail } from '../types/job'

const props = defineProps<{ job: JobDetail }>()

const candidate = computed(() => props.job.artifacts?.['candidate.json'] || {})
const opportunity = computed(() => props.job.artifacts?.['opportunity-report.json'] || {})
const qa = computed(() => props.job.artifacts?.['qa-report.json'] || {})
const gap = computed(() => props.job.artifacts?.['gap-check.json'] || {})
</script>

<template>
  <div class="overview">
    <!-- Job Meta -->
    <div class="meta">
      <span class="meta-item">Job: <strong>{{ job.id }}</strong></span>
      <span class="meta-item">应用: <strong>{{ candidate.name_cn || candidate.name || '—' }}</strong></span>
      <span v-if="candidate.name" class="meta-item en">{{ candidate.name }}</span>
    </div>

    <!-- 5-Dimension Scoring -->
    <div class="section-label">机会评分 Opportunity Score</div>
    <div class="scores">
      <div class="score-item">
        <div class="score-bar" :style="{ width: (opportunity.demand_score || 0) + '%' }"></div>
        <div class="score-info">
          <span class="score-name">需求强度</span>
          <span class="score-val">{{ opportunity.demand_score ?? '—' }}</span>
        </div>
      </div>
      <div class="score-item">
        <div class="score-bar bar-gap" :style="{ width: (opportunity.miniapp_gap_score || 0) + '%' }"></div>
        <div class="score-info">
          <span class="score-name">小程序缺口</span>
          <span class="score-val">{{ opportunity.miniapp_gap_score ?? '—' }}</span>
        </div>
      </div>
      <div class="score-item">
        <div class="score-bar bar-fit" :style="{ width: (opportunity.miniapp_fit_score || 0) + '%' }"></div>
        <div class="score-info">
          <span class="score-name">适配度</span>
          <span class="score-val">{{ opportunity.miniapp_fit_score ?? '—' }}</span>
        </div>
      </div>
      <div class="score-item">
        <div class="score-bar bar-impl" :style="{ width: (opportunity.implementation_score || 0) + '%' }"></div>
        <div class="score-info">
          <span class="score-name">实现难度</span>
          <span class="score-val">{{ opportunity.implementation_score ?? '—' }}</span>
        </div>
      </div>
      <div class="score-item">
        <div class="score-bar bar-risk" :style="{ width: (opportunity.risk_score || 0) + '%' }"></div>
        <div class="score-info">
          <span class="score-name">风险（高=安全）</span>
          <span class="score-val">{{ opportunity.risk_score ?? '—' }}</span>
        </div>
      </div>
    </div>

    <!-- Total + Recommendation -->
    <div class="total-row">
      <div class="total-score">{{ opportunity.total_score ?? '—' }}<span class="total-max">/100</span></div>
      <div class="rec-badge" :class="opportunity.recommendation === '立即执行' ? 'rec-go' : opportunity.recommendation === '暂缓' ? 'rec-no' : 'rec-maybe'">
        {{ opportunity.recommendation || '—' }}
      </div>
    </div>
    <div v-if="opportunity.reasons?.length" class="reasons">
      <span v-for="r in opportunity.reasons" :key="r" class="reason-tag good">{{ r }}</span>
    </div>
    <div v-if="opportunity.reject_reasons?.length" class="reasons">
      <span v-for="r in opportunity.reject_reasons" :key="r" class="reason-tag bad">{{ r }}</span>
    </div>

    <!-- Platform + Build Status -->
    <div class="section-label" style="margin-top:24px">状态 Status</div>
    <div class="cards">
      <div class="card">
        <div class="card-label">推荐平台</div>
        <div class="card-value platform">{{ gap.recommended_platforms?.join(', ') || '—' }}</div>
      </div>
      <div class="card">
        <div class="card-label">质量检查</div>
        <div class="card-value" :class="qa.passed ? 'pass' : 'fail'">{{ qa.passed ? '通过' : '未通过' }}</div>
      </div>
      <div class="card">
        <div class="card-label">构建验证</div>
        <div class="card-value" :class="qa.checks?.build_passed ? 'pass' : 'fail'">{{ qa.checks?.build_passed ? '通过' : '未验证' }}</div>
      </div>
      <div class="card">
        <div class="card-label">Dist 就绪</div>
        <div class="card-value" :class="qa.checks?.dist_exists ? 'pass' : 'fail'">{{ qa.checks?.dist_exists ? '就绪' : '未就绪' }}</div>
      </div>
    </div>

    <!-- Next Action -->
    <div v-if="opportunity.next_action" class="next-action">
      下一步: {{ opportunity.next_action }}
    </div>
  </div>
</template>

<style scoped>
.overview { animation: fadeIn 0.3s ease; }

.meta { display: flex; flex-wrap: wrap; gap: 16px; margin-bottom: 20px; font-size: 13px; color: var(--color-text-2); }
.meta-item strong { color: var(--color-text-1); font-weight: 500; }
.meta-item.en { color: var(--color-text-3); }

.section-label { font-size: 11px; font-weight: 600; color: var(--color-text-3); text-transform: uppercase; letter-spacing: 0.04em; margin-bottom: 12px; }

.scores { display: flex; flex-direction: column; gap: 8px; margin-bottom: 16px; }
.score-item { position: relative; background: rgba(0,0,0,0.03); border-radius: 6px; height: 28px; overflow: hidden; }
.score-bar { position: absolute; left: 0; top: 0; bottom: 0; background: var(--color-blue); opacity: 0.12; border-radius: 6px; transition: width 0.6s ease; }
.score-bar.bar-gap { background: var(--color-green); opacity: 0.12; }
.score-bar.bar-fit { background: #5856d6; opacity: 0.10; }
.score-bar.bar-impl { background: var(--color-orange); opacity: 0.12; }
.score-bar.bar-risk { background: #34c759; opacity: 0.10; }
.score-info { position: relative; display: flex; justify-content: space-between; align-items: center; height: 100%; padding: 0 12px; }
.score-name { font-size: 12px; color: var(--color-text-2); }
.score-val { font-size: 13px; font-weight: 600; color: var(--color-text-1); }

.total-row { display: flex; align-items: center; gap: 12px; margin-bottom: 8px; }
.total-score { font-size: 36px; font-weight: 700; color: var(--color-text-1); letter-spacing: -0.03em; }
.total-max { font-size: 16px; font-weight: 400; color: var(--color-text-3); }
.rec-badge { font-size: 13px; font-weight: 600; padding: 4px 12px; border-radius: 20px; }
.rec-go { background: var(--color-green-subtle); color: #1a7a35; }
.rec-maybe { background: var(--color-orange-subtle); color: #8a5a00; }
.rec-no { background: rgba(255,59,48,0.08); color: #c41e16; }

.reasons { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 6px; }
.reason-tag { font-size: 11px; padding: 3px 8px; border-radius: 4px; }
.reason-tag.good { background: var(--color-green-subtle); color: #1a7a35; }
.reason-tag.bad { background: rgba(255,59,48,0.08); color: #c41e16; }

.cards { display: grid; grid-template-columns: 1fr 1fr 1fr 1fr; gap: 12px; }
.card { background: var(--color-surface-solid, #fff); border-radius: var(--radius-md); padding: 16px; box-shadow: var(--shadow-card); }
.card-label { font-size: 10px; font-weight: 600; color: var(--color-text-3); text-transform: uppercase; letter-spacing: 0.03em; margin-bottom: 6px; }
.card-value { font-size: 15px; font-weight: 600; color: var(--color-text-1); }
.card-value.platform { font-size: 12px; font-weight: 500; }
.card-value.pass { color: #1d7a34; }
.card-value.fail { color: #c41e16; }

.next-action { margin-top: 16px; font-size: 13px; color: var(--color-text-2); padding: 10px 14px; background: var(--color-blue-subtle); border-radius: var(--radius-sm); }

@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }

@media (max-width: 768px) { .cards { grid-template-columns: 1fr 1fr; } }
</style>
