<script setup lang="ts">
const props = defineProps<{ qa: any }>()

const steps = [
  { id: 'discover', label: '发现应用' },
  { id: 'analyze', label: '需求分析' },
  { id: 'coverage', label: '覆盖检查' },
  { id: 'score', label: '机会评分' },
  { id: 'prd', label: '生成 PRD' },
  { id: 'code', label: '生成代码' },
  { id: 'listing', label: '上架材料' },
  { id: 'actions', label: '人工操作' },
  { id: 'qa', label: '质量检查' },
]

function stepDone(): boolean {
  return props.qa?.passed === true
}
</script>

<template>
  <div class="pipeline">
    <div class="grid">
      <div v-for="step in steps" :key="step.id" class="step-card">
        <div class="step-dot" :class="{ done: stepDone() }"></div>
        <div class="step-label">{{ step.label }}</div>
        <div class="step-status">{{ stepDone() ? '完成' : '待执行' }}</div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.pipeline { animation: fadeIn 0.3s ease; }

.grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.step-card {
  background: var(--color-surface-solid, #fff);
  border-radius: var(--radius-md, 10px);
  padding: 16px;
  box-shadow: var(--shadow-card, 0 1px 4px rgba(0,0,0,0.06));
  text-align: center;
}

.step-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--color-text-3, #999);
  margin: 0 auto 8px;
  transition: background 0.2s;
}
.step-dot.done { background: #34c759; }

.step-label {
  font-size: 13px;
  font-weight: 500;
  color: var(--color-text-1);
  margin-bottom: 4px;
}

.step-status {
  font-size: 11px;
  color: var(--color-text-3);
}

@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
</style>
