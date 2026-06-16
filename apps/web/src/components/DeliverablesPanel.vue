<script setup lang="ts">
import { ref, computed } from 'vue'
import type { JobDetail } from '../types/job'
import { DELIVERABLES, hasDeliverable, resolveCopy, canViewDetail, type DeliverableKind } from '../data/deliverables'

const props = defineProps<{ job: JobDetail | null }>()

const copiedKey = ref('')
const detailKey = ref('')

const SECTIONS: { kind: DeliverableKind; title: string }[] = [
  { kind: 'product', title: '产品交付物' },
  { kind: 'engineering', title: '工程交付物' },
  { kind: 'listing', title: '上架交付物' },
]

function itemsOf(kind: DeliverableKind) {
  return DELIVERABLES.filter(d => d.kind === kind)
}

function status(key: string): { text: string; cls: string } {
  if (hasDeliverable(props.job, key)) return { text: '已生成', cls: 'st--ready' }
  return { text: '缺失', cls: 'st--missing' }
}

async function copy(key: string) {
  const { value } = resolveCopy(props.job, key)
  if (!value) return
  try {
    await navigator.clipboard.writeText(value)
    copiedKey.value = key
    setTimeout(() => { if (copiedKey.value === key) copiedKey.value = '' }, 1500)
  } catch { /* clipboard unavailable */ }
}

const detailContent = computed(() => {
  if (!detailKey.value || !props.job?.artifacts) return ''
  const data = props.job.artifacts[detailKey.value]
  if (data === undefined || data === null) return ''
  return typeof data === 'string' ? data : JSON.stringify(data, null, 2)
})

function copyLabel(key: string): string {
  const { mode } = resolveCopy(props.job, key)
  return mode === 'path' ? '复制路径' : '复制内容'
}
</script>

<template>
  <div class="deliverables">
    <section v-for="sec in SECTIONS" :key="sec.kind" class="section">
      <h3 class="section-heading">{{ sec.title }}</h3>
      <div class="items-grid">
        <div v-for="item in itemsOf(sec.kind)" :key="item.key" class="item-card">
          <div class="item-header">
            <span class="item-name">{{ item.name }}</span>
            <span class="item-badge" :class="status(item.key).cls">{{ status(item.key).text }}</span>
          </div>
          <p class="item-purpose">{{ item.purpose }}</p>
          <p class="item-usage"><span class="usage-tag">下一步</span>{{ item.usage }}</p>
          <div class="item-actions" v-if="hasDeliverable(job, item.key)">
            <button class="action-btn" @click="copy(item.key)">
              {{ copiedKey === item.key ? '已复制 ✓' : copyLabel(item.key) }}
            </button>
            <button v-if="canViewDetail(job, item.key)" class="action-btn" @click="detailKey = item.key">查看详情</button>
          </div>
          <div v-else class="item-disabled">未生成，运行流水线后可用</div>
        </div>
      </div>
    </section>

    <!-- Detail drawer -->
    <div v-if="detailKey" class="detail-overlay" @click.self="detailKey = ''">
      <div class="detail-modal">
        <div class="detail-head">
          <span class="detail-title">{{ detailKey }}</span>
          <button class="detail-close" @click="detailKey = ''">✕</button>
        </div>
        <pre class="detail-pre">{{ detailContent }}</pre>
      </div>
    </div>

    <div v-if="!job" class="empty-state">
      <p>暂无任务数据，请先启动试运行</p>
    </div>
  </div>
</template>

<style scoped>
.deliverables { animation: fadeIn 0.3s var(--ease-apple); }
.section { margin-bottom: 28px; }
.section-heading { font-size: 16px; font-weight: 600; color: var(--color-text-1); margin-bottom: 12px; padding-bottom: 8px; border-bottom: 1px solid var(--color-border); }
.items-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 12px; }

.item-card { background: var(--color-surface-solid); border-radius: var(--radius-md); box-shadow: var(--shadow-card); padding: 16px; display: flex; flex-direction: column; }
.item-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px; }
.item-name { font-size: 14px; font-weight: 600; color: var(--color-text-1); }
.item-badge { font-size: 11px; font-weight: 500; padding: 2px 8px; border-radius: 980px; }
.st--ready { background: var(--color-green-subtle); color: #166534; }
.st--missing { background: rgba(0,0,0,0.04); color: var(--color-text-3); }
.item-purpose { font-size: 12px; color: var(--color-text-2); margin-bottom: 8px; }
.item-usage { font-size: 12px; color: var(--color-text-1); margin-bottom: 12px; line-height: 1.5; }
.usage-tag { font-size: 10px; font-weight: 600; color: var(--color-blue); background: var(--color-blue-subtle); padding: 1px 6px; border-radius: 4px; margin-right: 6px; }
.item-actions { display: flex; gap: 8px; margin-top: auto; }
.action-btn { font-size: 12px; font-weight: 500; padding: 5px 12px; border-radius: 8px; border: 1px solid var(--color-border); background: transparent; color: var(--color-text-1); cursor: pointer; transition: background 0.12s; }
.action-btn:hover { background: var(--color-blue-subtle); color: var(--color-blue); }
.item-disabled { font-size: 11px; color: var(--color-text-3); margin-top: auto; }

.detail-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.4); display: flex; align-items: center; justify-content: center; z-index: 2000; }
.detail-modal { background: var(--color-surface-solid); border-radius: var(--radius-lg); box-shadow: var(--shadow-elevated); width: min(720px, 92vw); max-height: 84vh; display: flex; flex-direction: column; }
.detail-head { display: flex; align-items: center; justify-content: space-between; padding: 16px 20px; border-bottom: 1px solid var(--color-border); }
.detail-title { font-size: 14px; font-weight: 600; font-family: var(--font-mono); color: var(--color-text-1); }
.detail-close { background: none; border: none; font-size: 16px; color: var(--color-text-3); cursor: pointer; }
.detail-pre { margin: 0; padding: 20px; overflow: auto; font-family: var(--font-mono); font-size: 12px; line-height: 1.6; color: var(--color-text-1); white-space: pre-wrap; word-break: break-word; }

.empty-state { text-align: center; padding: 40px; color: var(--color-text-3); font-size: 14px; }

@media (max-width: 600px) { .items-grid { grid-template-columns: 1fr; } }
@keyframes fadeIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
</style>
