<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import type { JobDetail } from '../types/job'
import { api } from '../services/api'
import { toUserMessage } from '../data/error-messages'

const props = defineProps<{ job: JobDetail | null }>()

const platforms = ref<any[]>([])
const loading = ref(true)
const loadError = ref('')
const filter = ref<'all' | 'recommended' | 'high'>('all')

onMounted(async () => {
  try {
    const res = await api.getPlatforms()
    platforms.value = res.platforms || []
  } catch (e: any) {
    loadError.value = toUserMessage(e)
  } finally {
    loading.value = false
  }
})

// 当前项目推荐/不推荐（来自 opportunity + gap-check）
const targetSet = computed(() => {
  const o = props.job?.artifacts?.['opportunity-report.json']
  return new Set<string>(o?.target_platforms || [])
})
const gapChecked = computed(() => {
  const g = props.job?.artifacts?.['gap-check.json']
  const map = new Map<string, any>()
  for (const p of (g?.platforms_checked || [])) map.set(p.platform, p)
  return map
})

function recommendForProject(id: string): 'yes' | 'no' | 'unknown' {
  if (!props.job) return 'unknown'
  if (targetSet.value.has(id)) return 'yes'
  return 'no'
}

function evidenceStrength(id: string): string {
  const pc = gapChecked.value.get(id)
  if (!pc) return ''
  if (pc.coverage_level === 'missing') return '证据强（无同类覆盖）'
  if (pc.coverage_level === 'weak') return '证据中（覆盖薄弱）'
  return '证据弱（已有覆盖）'
}

const filtered = computed(() => {
  let list = platforms.value
  if (filter.value === 'recommended') list = list.filter(p => recommendForProject(p.id) === 'yes')
  if (filter.value === 'high') list = list.filter(p => p.recommendation_level === 'high')
  return list
})

function stars(n: number) { return '★'.repeat(n || 0) + '☆'.repeat(Math.max(0, 5 - (n || 0))) }
function statusText(s: string) { return s === 'active' ? '可上架' : s === 'research_needed' ? '待调研' : '暂不支持' }
</script>

<template>
  <div class="platforms">
    <div class="header">
      <h2 class="title">平台策略</h2>
      <p class="subtitle">为什么推荐这些平台投放，而不是平台百科</p>
    </div>

    <div class="filter-row">
      <button class="f-btn" :class="{ active: filter === 'all' }" @click="filter = 'all'">全部</button>
      <button class="f-btn" :class="{ active: filter === 'recommended' }" @click="filter = 'recommended'">本项目推荐</button>
      <button class="f-btn" :class="{ active: filter === 'high' }" @click="filter = 'high'">高推荐</button>
    </div>

    <div v-if="loading" class="state-box">加载平台库中…</div>
    <div v-else-if="loadError" class="state-box state-box--err">{{ loadError }}</div>
    <div v-else-if="filtered.length === 0" class="state-box">没有符合条件的平台。</div>

    <div v-else class="grid">
      <div v-for="p in filtered" :key="p.id" class="card">
        <div class="card-head">
          <div>
            <div class="c-name">{{ p.name_cn }}</div>
            <div class="c-en">{{ p.name_en }}</div>
          </div>
          <div class="c-rec">
            <span class="stars">{{ stars(p.recommendation_stars) }}</span>
            <span class="status-tag" :class="'stat--' + p.status">{{ statusText(p.status) }}</span>
          </div>
        </div>

        <!-- 当前项目推荐结论 -->
        <div v-if="job" class="project-verdict" :class="recommendForProject(p.id) === 'yes' ? 'pv--yes' : 'pv--no'">
          {{ recommendForProject(p.id) === 'yes' ? '✓ 当前项目推荐投放' : '— 当前项目不推荐' }}
          <span v-if="evidenceStrength(p.id)" class="evidence">· {{ evidenceStrength(p.id) }}</span>
        </div>

        <div class="rows">
          <div class="row"><span class="rk">为什么推荐</span><span class="rv">{{ p.coverage }} · 门槛{{ p.entry_barrier }} · {{ p.fee }}</span></div>
          <div class="row" v-if="p.fit_product_types?.length"><span class="rk">适合产品</span><span class="rv">{{ p.fit_product_types.join('、') }}</span></div>
          <div class="row" v-if="p.not_fit_product_types?.length"><span class="rk">不适合</span><span class="rv">{{ p.not_fit_product_types.join('、') }}</span></div>
          <div class="row"><span class="rk">自动化</span><span class="rv">{{ p.automation_level }} · {{ p.supports_cli_upload ? '支持 CLI 上传' : '不支持 CLI' }}</span></div>
          <div class="row" v-if="p.review_policy"><span class="rk">审核</span><span class="rv">{{ p.review_policy }}</span></div>
        </div>

        <a v-if="p.developer_url" :href="p.developer_url" target="_blank" class="dev-link">开发者入口 →</a>
        <p v-if="p.notes" class="notes">{{ p.notes }}</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.platforms { animation: fadeIn 0.3s var(--ease-apple); }
.header { margin-bottom: 16px; }
.title { font-size: 24px; font-weight: 700; color: var(--color-text-1); }
.subtitle { font-size: 13px; color: var(--color-text-2); margin-top: 4px; }

.filter-row { display: flex; gap: 6px; margin-bottom: 18px; flex-wrap: wrap; }
.f-btn { padding: 6px 14px; border-radius: 980px; font-size: 12px; font-weight: 500; background: rgba(0,0,0,0.04); color: var(--color-text-2); border: none; cursor: pointer; }
.f-btn.active { background: var(--color-text-1); color: #fff; }

.state-box { background: var(--color-surface-solid); border-radius: var(--radius-md); box-shadow: var(--shadow-card); padding: 32px; text-align: center; color: var(--color-text-2); font-size: 14px; }
.state-box--err { color: #991b1b; }

.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(340px, 1fr)); gap: 16px; }
.card { background: var(--color-surface-solid); border-radius: var(--radius-lg); box-shadow: var(--shadow-card); padding: 20px; }
.card-head { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px; }
.c-name { font-size: 16px; font-weight: 600; color: var(--color-text-1); }
.c-en { font-size: 12px; color: var(--color-text-3); }
.c-rec { text-align: right; }
.stars { display: block; font-size: 13px; color: var(--color-orange); }
.status-tag { font-size: 10px; font-weight: 600; }
.stat--active { color: #166534; }
.stat--research_needed { color: #92400e; }
.stat--not_supported { color: var(--color-text-3); }

.project-verdict { font-size: 13px; font-weight: 500; padding: 8px 10px; border-radius: var(--radius-sm); margin-bottom: 12px; }
.pv--yes { background: var(--color-green-subtle); color: #166534; }
.pv--no { background: rgba(0,0,0,0.03); color: var(--color-text-2); }
.evidence { font-weight: 400; color: var(--color-text-2); }

.rows { display: flex; flex-direction: column; gap: 6px; }
.row { display: flex; gap: 8px; font-size: 12px; line-height: 1.5; }
.rk { flex-shrink: 0; width: 64px; color: var(--color-text-3); font-weight: 600; }
.rv { color: var(--color-text-1); }

.dev-link { display: inline-block; margin-top: 12px; font-size: 12px; color: var(--color-blue); text-decoration: none; }
.notes { margin-top: 8px; font-size: 11px; color: var(--color-text-3); font-style: italic; }

@media (max-width: 600px) { .grid { grid-template-columns: 1fr; } }
@keyframes fadeIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
</style>
