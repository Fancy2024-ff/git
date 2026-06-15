<script setup lang="ts">
import { computed } from 'vue'
import type { JobDetail } from '../types/job'

const props = defineProps<{
  job: JobDetail | null
}>()

interface DeliverableItem {
  key: string
  name: string
  purpose: string
}

const PRODUCT_DELIVERABLES: DeliverableItem[] = [
  { key: 'candidate.json', name: '候选应用', purpose: '筛选出的目标应用信息' },
  { key: 'market-analysis.json', name: '市场分析', purpose: '市场机会和竞争分析报告' },
  { key: 'gap-check.json', name: '差距检查', purpose: '平台要求差距分析' },
  { key: 'opportunity-report.json', name: '机会评估', purpose: '综合机会评分和推荐' },
  { key: 'prd.json', name: '产品需求文档', purpose: '小程序 PRD 规格书' },
]

const ENGINEERING_DELIVERABLES: DeliverableItem[] = [
  { key: 'miniapp', name: '小程序源码', purpose: '生成的完整小程序代码' },
  { key: 'dist', name: '构建产物', purpose: '编译后的可部署包' },
  { key: 'qa-report.json', name: 'QA 报告', purpose: '质量检查和合规验证结果' },
  { key: 'pipeline-report.json', name: '流水线报告', purpose: '完整的执行步骤和状态' },
]

const LISTING_DELIVERABLES: DeliverableItem[] = [
  { key: 'listing-materials.json', name: '上架材料', purpose: '平台提交所需的描述、截图等' },
  { key: 'publish-package.json', name: '发布包', purpose: '打包后的提交文件' },
  { key: 'human-actions.json', name: '人工操作清单', purpose: '需要人工完成的步骤列表' },
  { key: 'submission-readiness.json', name: '提交就绪度', purpose: '是否满足提交条件的检查' },
]

function hasArtifact(key: string): boolean {
  if (!props.job?.artifacts) return false
  if (key === 'miniapp') return !!props.job.miniapp_path
  if (key === 'dist') return !!(props.job.artifacts['build-result.json']?.success)
  return !!props.job.artifacts[key]
}

function getArtifactPreview(key: string): string {
  if (!props.job?.artifacts) return ''
  const data = props.job.artifacts[key]
  if (!data) return ''
  if (typeof data === 'string') return data.slice(0, 80)
  if (data.name_cn) return data.name_cn
  if (data.name) return data.name
  if (data.score !== undefined) return `评分: ${data.score}`
  if (data.qa_passed !== undefined) return data.qa_passed ? 'QA 通过' : 'QA 未通过'
  return ''
}

function copyArtifact(key: string) {
  if (!props.job?.artifacts) return
  const data = props.job.artifacts[key]
  if (!data) return
  const text = typeof data === 'string' ? data : JSON.stringify(data, null, 2)
  navigator.clipboard.writeText(text)
}
</script>

<template>
  <div class="deliverables">
    <!-- Section 1: Product -->
    <section class="section">
      <h3 class="section-heading">产品交付物</h3>
      <div class="items-grid">
        <div v-for="item in PRODUCT_DELIVERABLES" :key="item.key" class="item-card">
          <div class="item-header">
            <span class="item-name">{{ item.name }}</span>
            <span class="item-badge" :class="hasArtifact(item.key) ? 'badge--ready' : 'badge--missing'">
              {{ hasArtifact(item.key) ? '就绪' : '缺失' }}
            </span>
          </div>
          <p class="item-purpose">{{ item.purpose }}</p>
          <p v-if="hasArtifact(item.key)" class="item-preview">{{ getArtifactPreview(item.key) }}</p>
          <div class="item-actions" v-if="hasArtifact(item.key)">
            <button class="action-btn" @click="copyArtifact(item.key)">复制</button>
          </div>
        </div>
      </div>
    </section>

    <!-- Section 2: Engineering -->
    <section class="section">
      <h3 class="section-heading">工程交付物</h3>
      <div class="items-grid">
        <div v-for="item in ENGINEERING_DELIVERABLES" :key="item.key" class="item-card">
          <div class="item-header">
            <span class="item-name">{{ item.name }}</span>
            <span class="item-badge" :class="hasArtifact(item.key) ? 'badge--ready' : 'badge--missing'">
              {{ hasArtifact(item.key) ? '就绪' : '缺失' }}
            </span>
          </div>
          <p class="item-purpose">{{ item.purpose }}</p>
          <p v-if="hasArtifact(item.key)" class="item-preview">{{ getArtifactPreview(item.key) }}</p>
          <div class="item-actions" v-if="hasArtifact(item.key)">
            <button class="action-btn" @click="copyArtifact(item.key)">复制</button>
          </div>
        </div>
      </div>
    </section>

    <!-- Section 3: Listing -->
    <section class="section">
      <h3 class="section-heading">上架交付物</h3>
      <div class="items-grid">
        <div v-for="item in LISTING_DELIVERABLES" :key="item.key" class="item-card">
          <div class="item-header">
            <span class="item-name">{{ item.name }}</span>
            <span class="item-badge" :class="hasArtifact(item.key) ? 'badge--ready' : 'badge--missing'">
              {{ hasArtifact(item.key) ? '就绪' : '缺失' }}
            </span>
          </div>
          <p class="item-purpose">{{ item.purpose }}</p>
          <p v-if="hasArtifact(item.key)" class="item-preview">{{ getArtifactPreview(item.key) }}</p>
          <div class="item-actions" v-if="hasArtifact(item.key)">
            <button class="action-btn" @click="copyArtifact(item.key)">复制</button>
          </div>
        </div>
      </div>
    </section>

    <div v-if="!job" class="empty-state">
      <p>暂无任务数据，请先运行流水线</p>
    </div>
  </div>
</template>

<style scoped>
.deliverables {
  animation: fadeIn 0.3s var(--ease-apple);
}

.section {
  margin-bottom: 28px;
}

.section-heading {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text-1);
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--color-border);
}

.items-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 12px;
}

.item-card {
  background: var(--color-surface-solid);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-card);
  padding: 16px;
  transition: box-shadow 0.2s;
}
.item-card:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
}

.item-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
}

.item-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-1);
}

.item-badge {
  font-size: 11px;
  font-weight: 500;
  padding: 2px 8px;
  border-radius: 980px;
}
.badge--ready {
  background: var(--color-green-subtle);
  color: #166534;
}
.badge--missing {
  background: rgba(0, 0, 0, 0.04);
  color: var(--color-text-3);
}

.item-purpose {
  font-size: 12px;
  color: var(--color-text-2);
  margin-bottom: 6px;
}

.item-preview {
  font-size: 11px;
  color: var(--color-text-3);
  font-family: var(--font-mono);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-bottom: 8px;
}

.item-actions {
  display: flex;
  gap: 6px;
}

.action-btn {
  font-size: 11px;
  font-weight: 500;
  padding: 3px 10px;
  border-radius: 6px;
  border: 1px solid var(--color-border);
  background: transparent;
  color: var(--color-text-2);
  cursor: pointer;
  transition: background 0.12s;
}
.action-btn:hover {
  background: rgba(0, 0, 0, 0.03);
}

.empty-state {
  text-align: center;
  padding: 40px;
  color: var(--color-text-3);
  font-size: 14px;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
