<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { api } from '../services/api'

const platforms = ref<any[]>([])
const filter = ref('all')

onMounted(async () => {
  try {
    const res = await api.getPlatforms()
    platforms.value = res.platforms
  } catch {}
})

const filters = [
  { id: 'all', label: '全部' },
  { id: 'high', label: '高推荐' },
  { id: 'active', label: '可上架' },
  { id: 'research', label: '待调研' },
  { id: 'not_supported', label: '暂不支持' },
]

const filtered = computed(() => {
  if (filter.value === 'all') return platforms.value
  if (filter.value === 'high') return platforms.value.filter(p => p.recommendation_level === 'high')
  if (filter.value === 'active') return platforms.value.filter(p => p.status === 'active')
  if (filter.value === 'research') return platforms.value.filter(p => p.status === 'research_needed')
  if (filter.value === 'not_supported') return platforms.value.filter(p => p.status === 'not_supported')
  return platforms.value
})

const stats = computed(() => ({
  total: platforms.value.length,
  active: platforms.value.filter(p => p.status === 'active').length,
  high: platforms.value.filter(p => p.recommendation_level === 'high').length,
  research: platforms.value.filter(p => p.status === 'research_needed').length,
  not_supported: platforms.value.filter(p => p.status === 'not_supported').length,
}))

function starsDisplay(n: number) { return '★'.repeat(n) + '☆'.repeat(5 - n) }

function statusColor(status: string) {
  if (status === 'active') return 'var(--color-green)'
  if (status === 'research_needed') return 'var(--color-orange)'
  return 'var(--color-text-3)'
}
</script>

<template>
  <div class="platforms">
    <!-- Stats row -->
    <div class="stats-row">
      <div class="stat">{{ stats.total }} <span>平台总数</span></div>
      <div class="stat green">{{ stats.active }} <span>可上架</span></div>
      <div class="stat blue">{{ stats.high }} <span>高推荐</span></div>
      <div class="stat orange">{{ stats.research }} <span>待调研</span></div>
      <div class="stat gray">{{ stats.not_supported }} <span>暂不支持</span></div>
    </div>

    <!-- Filters -->
    <div class="filter-row">
      <button v-for="f in filters" :key="f.id" class="filter-btn" :class="{ active: filter === f.id }" @click="filter = f.id">{{ f.label }}</button>
    </div>

    <!-- Platform cards -->
    <div class="platform-grid">
      <div v-for="p in filtered" :key="p.id" class="platform-card">
        <div class="card-header">
          <div class="card-name">{{ p.name_cn }}</div>
          <div class="card-name-en">{{ p.name_en }}</div>
          <span class="card-status" :style="{ color: statusColor(p.status) }">{{ p.status === 'active' ? '可上架' : p.status === 'research_needed' ? '待调研' : '暂不支持' }}</span>
        </div>
        <div class="card-meta">
          <span>{{ p.region?.join(', ') }}</span>
          <span>{{ p.platform_type }}</span>
          <span>{{ p.coverage }}</span>
        </div>
        <div class="card-stars">{{ starsDisplay(p.recommendation_stars) }}</div>
        <div class="card-details">
          <div v-if="p.entry_barrier"><span class="dl">门槛</span> {{ p.entry_barrier }}</div>
          <div v-if="p.review_policy"><span class="dl">审核</span> {{ p.review_policy }}</div>
          <div v-if="p.fee"><span class="dl">费用</span> {{ p.fee }}</div>
          <div v-if="p.automation_level"><span class="dl">自动化</span> {{ p.automation_level }}</div>
        </div>
        <div v-if="p.developer_url" class="card-link">
          <a :href="p.developer_url" target="_blank">开发者文档 →</a>
        </div>
        <div v-if="p.notes" class="card-notes">{{ p.notes }}</div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.platforms { animation: fadeIn 0.3s ease; }
.stats-row { display: flex; gap: 12px; margin-bottom: 20px; flex-wrap: wrap; }
.stat { background: var(--color-surface-solid); border-radius: var(--radius-md); padding: 14px 18px; font-size: 24px; font-weight: 700; box-shadow: var(--shadow-card); }
.stat span { display: block; font-size: 11px; font-weight: 500; color: var(--color-text-3); margin-top: 2px; }
.stat.green { color: var(--color-green); }
.stat.blue { color: var(--color-blue); }
.stat.orange { color: var(--color-orange); }
.stat.gray { color: var(--color-text-3); }

.filter-row { display: flex; gap: 6px; margin-bottom: 20px; flex-wrap: wrap; }
.filter-btn { padding: 6px 14px; border-radius: 20px; font-size: 12px; font-weight: 500; background: rgba(0,0,0,0.04); color: var(--color-text-2); border: none; cursor: pointer; transition: all 0.15s; }
.filter-btn.active { background: var(--color-text-1); color: #fff; }

.platform-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 16px; }
.platform-card { background: var(--color-surface-solid); border-radius: var(--radius-lg); padding: 20px; box-shadow: var(--shadow-card); transition: box-shadow 0.2s; }
.platform-card:hover { box-shadow: 0 4px 16px rgba(0,0,0,0.08); }
.card-header { margin-bottom: 8px; }
.card-name { font-size: 16px; font-weight: 600; color: var(--color-text-1); }
.card-name-en { font-size: 12px; color: var(--color-text-3); }
.card-status { font-size: 11px; font-weight: 600; }
.card-meta { display: flex; gap: 8px; font-size: 11px; color: var(--color-text-2); margin-bottom: 6px; }
.card-stars { font-size: 13px; color: var(--color-orange); margin-bottom: 8px; }
.card-details { font-size: 12px; color: var(--color-text-2); line-height: 1.8; }
.dl { font-weight: 600; color: var(--color-text-3); margin-right: 4px; }
.card-link { margin-top: 8px; }
.card-link a { font-size: 12px; color: var(--color-blue); text-decoration: none; }
.card-notes { margin-top: 8px; font-size: 11px; color: var(--color-text-3); font-style: italic; }
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
</style>
