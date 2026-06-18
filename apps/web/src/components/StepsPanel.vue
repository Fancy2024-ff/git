<script setup lang="ts">
import { ref, computed } from 'vue'
import { STEP_DEFINITIONS, PHASES } from '../data/stepDefinitions'

const selectedPhase = ref('全部')
const selectedStepId = ref(STEP_DEFINITIONS[0]?.id || '')

const filteredSteps = computed(() => {
  if (selectedPhase.value === '全部') return STEP_DEFINITIONS
  return STEP_DEFINITIONS.filter(s => s.phase === selectedPhase.value)
})

const selectedStep = computed(() => {
  return STEP_DEFINITIONS.find(s => s.id === selectedStepId.value) || STEP_DEFINITIONS[0]
})

function getImplColor(type: string): string {
  if (type === 'API') return 'impl--api'
  if (type === '模板') return 'impl--template'
  if (type === '可选') return 'impl--optional'
  return 'impl--rule'
}

function getPhaseColor(phase: string): string {
  if (phase === '数据') return 'phase--data'
  if (phase === '分析') return 'phase--analysis'
  if (phase === '生成') return 'phase--generate'
  if (phase === '增长') return 'phase--growth'
  if (phase === 'QA') return 'phase--qa'
  if (phase === '上架') return 'phase--listing'
  if (phase === '发布') return 'phase--publish'
  return ''
}
</script>

<template>
  <div class="steps-map">
    <div class="phase-filter">
      <button v-for="phase in PHASES" :key="phase" class="phase-btn" :class="{ 'phase-btn--active': selectedPhase === phase }" @click="selectedPhase = phase">{{ phase }}</button>
    </div>

    <div class="map-layout">
      <div class="step-list">
        <div v-for="step in filteredSteps" :key="step.id" class="step-item" :class="{ 'step-item--active': selectedStepId === step.id }" @click="selectedStepId = step.id">
          <div class="step-item-header">
            <span class="step-item-name">{{ step.name }}</span>
            <span class="phase-tag" :class="getPhaseColor(step.phase)">{{ step.phase }}</span>
          </div>
          <span class="step-item-en">{{ step.nameEn }}</span>
        </div>
      </div>

      <div class="step-detail" v-if="selectedStep">
        <div class="detail-header">
          <h3 class="detail-name">{{ selectedStep.name }}</h3>
          <span class="impl-badge" :class="getImplColor(selectedStep.implType)">{{ selectedStep.implType }}</span>
        </div>
        <p class="detail-en">{{ selectedStep.nameEn }}</p>
        <p class="detail-phase">阶段：<span class="phase-tag" :class="getPhaseColor(selectedStep.phase)">{{ selectedStep.phase }}</span></p>

        <div class="detail-section"><h4 class="section-title">用途</h4><p class="section-body">{{ selectedStep.purpose }}</p><p class="section-body hint">开发视角：{{ selectedStep.devPurpose }}</p></div>
        <div class="detail-section"><h4 class="section-title">输入</h4><ul class="io-list"><li v-for="inp in selectedStep.inputs" :key="inp">{{ inp }}</li></ul></div>
        <div class="detail-section"><h4 class="section-title">输出</h4><ul class="io-list"><li v-for="out in selectedStep.outputs" :key="out">{{ out }}</li></ul></div>
        <div class="detail-section"><h4 class="section-title">代码位置（能力域真源）</h4><code class="code-loc">{{ selectedStep.codeLocation }}</code></div>
        <div class="detail-section"><h4 class="section-title">规则 / 模板位置</h4><code class="code-loc">{{ selectedStep.rulesLocation }}</code></div>
        <div class="detail-section"><h4 class="section-title">自动化边界</h4><p class="section-body">自动：{{ selectedStep.automation }}</p><p class="section-body hint">人工：{{ selectedStep.humanRequired }}</p></div>
        <div class="detail-section"><h4 class="section-title">结果不对改哪里</h4><p class="section-body hint">{{ selectedStep.changeHint }}</p></div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.steps-map { animation: fadeIn 0.3s var(--ease-apple); }
.phase-filter { display: flex; gap: 6px; margin-bottom: 20px; flex-wrap: wrap; }
.phase-btn { padding: 6px 14px; border-radius: 20px; font-size: 12px; font-weight: 500; background: rgba(0, 0, 0, 0.04); color: var(--color-text-2); border: none; cursor: pointer; transition: all 0.15s; }
.phase-btn--active { background: var(--color-text-1); color: #fff; }
.map-layout { display: grid; grid-template-columns: 260px 1fr; gap: 20px; }
.step-list { display: flex; flex-direction: column; gap: 4px; max-height: 520px; overflow-y: auto; }
.step-item { padding: 10px 12px; border-radius: var(--radius-sm); cursor: pointer; transition: background 0.12s; }
.step-item:hover { background: rgba(0, 0, 0, 0.03); }
.step-item--active { background: var(--color-blue-subtle); }
.step-item-header { display: flex; align-items: center; justify-content: space-between; }
.step-item-name { font-size: 14px; font-weight: 500; color: var(--color-text-1); }
.step-item-en { font-size: 11px; color: var(--color-text-3); }
.phase-tag { font-size: 10px; font-weight: 600; padding: 2px 6px; border-radius: 4px; }
.phase--data { background: var(--color-blue-subtle); color: var(--color-blue); }
.phase--analysis { background: rgba(175, 82, 222, 0.08); color: #7c3aed; }
.phase--generate { background: var(--color-green-subtle); color: #166534; }
.phase--growth { background: rgba(22, 163, 74, 0.08); color: #15803d; }
.phase--qa { background: var(--color-orange-subtle); color: #92400e; }
.phase--listing { background: rgba(255, 59, 48, 0.08); color: #991b1b; }
.phase--publish { background: rgba(0, 0, 0, 0.06); color: var(--color-text-2); }
.step-detail { background: var(--color-surface-solid); border-radius: var(--radius-lg); box-shadow: var(--shadow-card); padding: 24px; }
.detail-header { display: flex; align-items: center; gap: 10px; }
.detail-name { font-size: 18px; font-weight: 600; color: var(--color-text-1); }
.detail-en { font-size: 13px; color: var(--color-text-3); margin-top: 2px; }
.detail-phase { font-size: 12px; color: var(--color-text-2); margin-top: 6px; margin-bottom: 20px; }
.detail-section { margin-bottom: 16px; }
.section-title { font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.03em; color: var(--color-text-3); margin-bottom: 4px; }
.section-body { font-size: 13px; color: var(--color-text-1); line-height: 1.5; }
.section-body.hint { color: var(--color-text-2); font-style: italic; }
.io-list { list-style: none; padding: 0; margin: 0; }
.io-list li { font-size: 13px; color: var(--color-text-1); padding: 2px 0; font-family: var(--font-mono); }
.io-list li::before { content: '›'; margin-right: 6px; color: var(--color-text-3); }
.code-loc { font-size: 12px; font-family: var(--font-mono); color: var(--color-blue); background: var(--color-blue-subtle); padding: 3px 8px; border-radius: 4px; word-break: break-all; }
.impl-badge { font-size: 11px; font-weight: 600; padding: 3px 10px; border-radius: 980px; }
.impl--rule { background: var(--color-green-subtle); color: #166534; }
.impl--api { background: var(--color-orange-subtle); color: #92400e; }
.impl--template { background: var(--color-blue-subtle); color: var(--color-blue); }
.impl--optional { background: rgba(0, 0, 0, 0.05); color: var(--color-text-2); }
@keyframes fadeIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
@media (max-width: 760px) { .map-layout { grid-template-columns: 1fr; } }
</style>
