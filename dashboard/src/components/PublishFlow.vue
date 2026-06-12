<script setup lang="ts">
import { publishSteps } from '../data/mockData'
</script>

<template>
  <div class="publish-flow">
    <div class="section-header">
      <h2 class="section-title">真实上架流程 <span class="section-title__en">Publishing</span></h2>
      <p class="section-subtitle">系统自动准备材料，平台提交保留人工确认</p>
    </div>

    <div class="steps-list">
      <div
        v-for="(step, i) in publishSteps"
        :key="step.id"
        class="step-item"
        :class="[
          `step-item--${step.status}`,
          step.automated ? 'step-item--auto' : 'step-item--manual'
        ]"
      >
        <div class="step-indicator">
          <span class="step-dot" :class="`step-dot--${step.status}`">
            <span v-if="step.status === 'done'" class="step-check">✓</span>
          </span>
          <span v-if="i < publishSteps.length - 1" class="step-line" :class="`step-line--${step.status}`"></span>
        </div>
        <div class="step-content">
          <div class="step-main">
            <span class="step-label">{{ step.label }}</span>
            <span class="step-label-en">{{ step.labelEn }}</span>
          </div>
          <span class="step-tag" :class="step.automated ? 'step-tag--auto' : 'step-tag--manual'">
            {{ step.automated ? '系统自动' : '人工处理' }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.section-header { margin-bottom: var(--space-5); }
.section-title { font-size: 18px; font-weight: 600; color: var(--color-text-primary); letter-spacing: -0.02em; }
.section-title__en { font-size: 13px; font-weight: 400; color: var(--color-text-tertiary); margin-left: 6px; }
.section-subtitle { font-size: 12px; color: var(--color-text-secondary); margin-top: 3px; }

.steps-list { display: flex; flex-direction: column; }

.step-item {
  display: flex;
  gap: var(--space-3);
  padding: var(--space-2) 0;
}

.step-indicator {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex-shrink: 0;
  width: 20px;
}

.step-dot {
  width: 18px; height: 18px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-size: 10px;
}
.step-dot--done { background: var(--color-green); color: #fff; }
.step-dot--current { background: var(--color-accent); box-shadow: 0 0 0 3px var(--color-accent-subtle); }
.step-dot--pending { background: var(--color-surface); border: 1.5px solid var(--color-border-strong); }

.step-check { font-weight: 700; font-size: 9px; }

.step-line {
  width: 1px;
  flex: 1;
  min-height: 12px;
  margin: 3px 0;
}
.step-line--done { background: var(--color-green); opacity: 0.4; }
.step-line--current { background: var(--color-accent); opacity: 0.3; }
.step-line--pending { background: var(--color-border-strong); }

.step-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex: 1;
  min-height: 28px;
  gap: var(--space-2);
}

.step-main { display: flex; flex-direction: column; gap: 0; }
.step-label { font-size: 13px; font-weight: 500; color: var(--color-text-primary); }
.step-label-en { font-size: 10px; color: var(--color-text-tertiary); }
.step-item--pending .step-label { color: var(--color-text-tertiary); }

.step-tag {
  font-size: 10px;
  font-weight: 500;
  padding: 2px 6px;
  border-radius: var(--radius-full);
  flex-shrink: 0;
}
.step-tag--auto { background: var(--color-bg); color: var(--color-text-secondary); }
.step-tag--manual { background: var(--color-orange-subtle); color: #b86800; }
</style>
