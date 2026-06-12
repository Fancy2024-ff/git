<script setup lang="ts">
defineProps<{ qa?: any }>()

const steps = [
  { label: '发现应用', en: 'Discover' },
  { label: '需求分析', en: 'Analyze' },
  { label: '覆盖检查', en: 'Gap' },
  { label: '机会评分', en: 'Score' },
  { label: '生成 PRD', en: 'PRD' },
  { label: '生成代码', en: 'Codegen' },
  { label: '上架材料', en: 'Listing' },
  { label: '人工操作', en: 'Manual' },
  { label: '质量检查', en: 'QA' },
]
</script>

<template>
  <div>
    <div class="section-header">
      <h2 class="section-title">生产流水线 <span class="en">Pipeline</span></h2>
      <p class="section-subtitle" v-if="qa">
        QA {{ qa.passed ? '通过' : '未通过' }} · {{ qa.total_size_readable }} · {{ qa.total_files }} 个文件
      </p>
    </div>
    <div class="timeline">
      <div v-for="(step, i) in steps" :key="i" class="node" :class="qa ? 'node--done' : 'node--waiting'">
        <div class="node-circle">
          <span v-if="qa" class="check">✓</span>
        </div>
        <div class="node-label">{{ step.label }}</div>
        <div class="node-en">{{ step.en }}</div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.section-header { margin-bottom: var(--space-5); }
.section-title { font-size: 20px; font-weight: 600; color: var(--color-text-primary); letter-spacing: -0.02em; }
.en { font-size: 13px; font-weight: 400; color: var(--color-text-tertiary); margin-left: 6px; }
.section-subtitle { font-size: 13px; color: var(--color-text-secondary); margin-top: 3px; }

.timeline { display: flex; gap: 4px; overflow-x: auto; padding: var(--space-4) 0; }
.node { display: flex; flex-direction: column; align-items: center; min-width: 80px; flex: 1; }
.node-circle { width: 22px; height: 22px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 10px; }
.node--done .node-circle { background: var(--color-green); color: #fff; }
.node--waiting .node-circle { background: var(--color-surface); border: 1.5px solid var(--color-border-strong); }
.check { font-weight: 700; }
.node-label { font-size: 11px; font-weight: 600; color: var(--color-text-primary); margin-top: 6px; text-align: center; }
.node-en { font-size: 10px; color: var(--color-text-tertiary); }
.node--waiting .node-label { color: var(--color-text-tertiary); }
</style>
