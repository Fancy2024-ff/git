<script setup lang="ts">
import { computed } from 'vue'
import type { JobDetail } from '../types/job'

const props = defineProps<{ job: JobDetail }>()

const qa = computed(() => props.job.artifacts?.['qa-report.json'] || {})
const allPassed = computed(() => qa.value.passed === true)

const steps = [
  { id: 'input', label: 'Market Input', output: 'candidate.json', artifact: 'candidate.json' },
  { id: 'demand', label: 'Demand Analysis', output: 'demand data', artifact: 'candidate.json' },
  { id: 'gap', label: 'Gap Check', output: 'gap-check.json', artifact: 'gap-check.json' },
  { id: 'opportunity', label: 'Opportunity', output: 'opportunity-report.json', artifact: 'opportunity-report.json' },
  { id: 'prd', label: 'PRD', output: 'prd.md', artifact: 'prd.md' },
  { id: 'codegen', label: 'Codegen', output: 'miniapp code', artifact: null },
  { id: 'build', label: 'Build', output: 'dist/', artifact: null },
  { id: 'qa', label: 'QA', output: 'qa-report.json', artifact: 'qa-report.json' },
  { id: 'publish', label: 'Publish Package', output: 'listing + guide', artifact: 'listing-materials.json' },
]

function isStepDone(step: typeof steps[number]): boolean {
  if (allPassed.value) return true
  if (step.artifact && props.job.artifacts?.[step.artifact]) return true
  if (step.id === 'codegen' && (props.job.miniapp_path || (props.job.miniapp_files?.length ?? 0) > 0)) return true
  if (step.id === 'build' && qa.value.checks?.build_passed) return true
  return false
}
</script>

<template>
  <div class="pipeline">
    <div class="pipeline-scroll">
      <div class="pipeline-track">
        <div class="pipeline-line"></div>
        <div
          v-for="(step, idx) in steps"
          :key="step.id"
          class="pipeline-node"
        >
          <div class="node-circle" :class="isStepDone(step) ? 'node-circle--done' : 'node-circle--pending'">
            <span class="node-num">{{ idx + 1 }}</span>
          </div>
          <span class="node-label">{{ step.label }}</span>
          <span class="node-output">{{ step.output }}</span>
        </div>
      </div>
    </div>
    <div class="pipeline-summary" v-if="qa.checks">
      <div class="summary-item">
        <span class="summary-dot" :class="qa.checks.install_passed ? 'summary-dot--green' : 'summary-dot--gray'"></span>
        <span>Install</span>
      </div>
      <div class="summary-item">
        <span class="summary-dot" :class="qa.checks.build_passed ? 'summary-dot--green' : 'summary-dot--gray'"></span>
        <span>Build</span>
      </div>
      <div class="summary-item">
        <span class="summary-dot" :class="qa.checks.dist_exists ? 'summary-dot--green' : 'summary-dot--gray'"></span>
        <span>Dist</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.pipeline {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.pipeline-scroll {
  overflow-x: auto;
  padding: 20px 0;
  -webkit-overflow-scrolling: touch;
}

.pipeline-track {
  display: flex;
  align-items: flex-start;
  position: relative;
  min-width: max-content;
  padding: 0 20px;
}

.pipeline-line {
  position: absolute;
  top: 18px;
  left: 40px;
  right: 40px;
  height: 2px;
  background: var(--color-border);
  z-index: 0;
}

.pipeline-node {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  min-width: 90px;
  position: relative;
  z-index: 1;
}

.node-circle {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  font-weight: 600;
  transition: all 0.2s var(--ease-apple);
}
.node-circle--done {
  background: var(--color-green);
  color: #fff;
}
.node-circle--pending {
  background: var(--color-surface-solid);
  border: 2px solid var(--color-border);
  color: var(--color-text-3);
}

.node-num {
  line-height: 1;
}

.node-label {
  font-size: 11px;
  font-weight: 500;
  color: var(--color-text-1);
  text-align: center;
  white-space: nowrap;
}

.node-output {
  font-size: 10px;
  font-family: var(--font-mono);
  color: var(--color-text-3);
  text-align: center;
  max-width: 80px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.pipeline-summary {
  display: flex;
  gap: 24px;
  justify-content: center;
  padding: 16px 24px;
  background: var(--color-surface-solid);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
}

.summary-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: var(--color-text-2);
}

.summary-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}
.summary-dot--green {
  background: var(--color-green);
}
.summary-dot--gray {
  background: var(--color-text-3);
}
</style>
