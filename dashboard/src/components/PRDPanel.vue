<script setup lang="ts">
import { computed, ref } from 'vue'
import type { JobDetail } from '../types/job'

const props = defineProps<{ job: JobDetail }>()

const candidate = computed(() => props.job.artifacts?.['candidate.json'] || {})
const opportunity = computed(() => props.job.artifacts?.['opportunity-report.json'] || {})
const showRawPrd = ref(false)

const prdContent = computed(() => {
  const a = props.job.artifacts?.['prd.md']
  if (typeof a === 'string') return a
  if (a?.content) return a.content
  return ''
})

const features = computed<string[]>(() => {
  return candidate.value.features_cn || candidate.value.features || []
})

const platforms = computed<string[]>(() => {
  return opportunity.value.target_platforms || []
})

const pages = [
  { name: '首页', desc: '应用主页面，展示核心功能入口' },
  { name: '表单', desc: '数据输入与提交页面' },
  { name: '结果', desc: '处理结果展示页面' },
  { name: '我的', desc: '用户个人中心与设置' },
]
</script>

<template>
  <div class="prd">
    <div class="product-card">
      <div class="product-header">
        <h2 class="product-name">{{ candidate.name_cn || candidate.name || '产品概览' }}</h2>
        <div class="product-meta">
          <span class="meta-item" v-if="platforms.length">
            {{ platforms.join(' / ') }}
          </span>
          <span class="meta-item" v-if="opportunity.total_score">
            Score: {{ opportunity.total_score }}
          </span>
          <span class="meta-item" v-if="opportunity.estimated_dev_days">
            约 {{ opportunity.estimated_dev_days }} 天开发
          </span>
        </div>
      </div>
      <p class="product-desc" v-if="candidate.description_cn">{{ candidate.description_cn }}</p>
    </div>

    <div class="section" v-if="features.length">
      <h3 class="section-title">Features</h3>
      <div class="features-grid">
        <div v-for="(feat, i) in features" :key="i" class="feature-card">
          <span class="feature-icon">✦</span>
          <span class="feature-text">{{ feat }}</span>
        </div>
      </div>
    </div>

    <div class="section">
      <h3 class="section-title">Page Structure</h3>
      <div class="pages-grid">
        <div v-for="page in pages" :key="page.name" class="page-card">
          <span class="page-name">{{ page.name }}</span>
          <span class="page-desc">{{ page.desc }}</span>
        </div>
      </div>
    </div>

    <div class="section" v-if="prdContent">
      <button class="collapse-btn" @click="showRawPrd = !showRawPrd">
        {{ showRawPrd ? '收起原始 PRD' : '查看原始 PRD' }}
        <svg class="collapse-icon" :class="{ 'collapse-icon--open': showRawPrd }" width="12" height="12" viewBox="0 0 12 12">
          <path d="M3 5L6 8L9 5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" fill="none"/>
        </svg>
      </button>
      <div v-if="showRawPrd" class="raw-prd">
        <pre class="raw-content">{{ prdContent }}</pre>
      </div>
    </div>
  </div>
</template>

<style scoped>
.prd {
  display: flex;
  flex-direction: column;
  gap: 32px;
}

.product-card {
  background: var(--color-surface-solid);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
  padding: 24px;
}

.product-header {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
}

.product-name {
  font-size: 20px;
  font-weight: 600;
  color: var(--color-text-1);
  margin: 0;
}

.product-meta {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.meta-item {
  font-size: 12px;
  font-weight: 500;
  color: var(--color-text-2);
  padding: 3px 10px;
  background: rgba(0, 0, 0, 0.03);
  border-radius: 980px;
}

.product-desc {
  font-size: 14px;
  color: var(--color-text-2);
  line-height: 1.6;
  margin: 12px 0 0;
}

.section-title {
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-text-3);
  margin: 0 0 16px;
}

.features-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.feature-card {
  background: var(--color-surface-solid);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-card);
  padding: 16px;
  display: flex;
  align-items: flex-start;
  gap: 10px;
}

.feature-icon {
  font-size: 14px;
  color: var(--color-blue);
  flex-shrink: 0;
  margin-top: 1px;
}

.feature-text {
  font-size: 13px;
  color: var(--color-text-1);
  line-height: 1.4;
}

.pages-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}

.page-card {
  background: var(--color-surface-solid);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-card);
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  text-align: center;
}

.page-name {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text-1);
}

.page-desc {
  font-size: 11px;
  color: var(--color-text-2);
  line-height: 1.4;
}

.collapse-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  background: none;
  border: none;
  font-size: 13px;
  font-weight: 500;
  color: var(--color-blue);
  cursor: pointer;
  padding: 0;
}
.collapse-btn:hover {
  text-decoration: underline;
}

.collapse-icon {
  transition: transform 0.2s var(--ease-apple);
}
.collapse-icon--open {
  transform: rotate(180deg);
}

.raw-prd {
  margin-top: 12px;
  background: var(--color-surface-solid);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-card);
  padding: 20px;
  overflow-x: auto;
}

.raw-content {
  font-family: var(--font-mono);
  font-size: 12px;
  line-height: 1.6;
  color: var(--color-text-1);
  white-space: pre-wrap;
  word-break: break-word;
  margin: 0;
}
</style>
