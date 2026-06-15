<script setup lang="ts">
import { computed } from 'vue'
import type { PipelineStep } from '../types/job'

const props = defineProps<{
  steps: PipelineStep[]
  selectedId: string
}>()

const emit = defineEmits<{
  select: [stepId: string]
}>()

const AGENT_LABELS: Record<string, string> = {
  'candidate-finder': 'Candidate Finder',
  'market-analyst': 'Market Analyst',
  'gap-checker': 'Gap Checker',
  'opportunity-scorer': 'Opportunity Scorer',
  'prd-writer': 'PRD Writer',
  'code-generator': 'Code Generator',
  'build-verify': 'Build Verify',
  'qa-checker': 'QA Checker',
  'listing-preparer': 'Listing Preparer',
}

function getStatusClass(status: string): string {
  if (status === 'passed' || status === 'done') return 'circle--passed'
  if (status === 'running') return 'circle--running'
  if (status === 'failed') return 'circle--failed'
  return 'circle--pending'
}

function getStatusText(status: string): string {
  if (status === 'passed' || status === 'done') return '完成'
  if (status === 'running') return '运行中'
  if (status === 'failed') return '失败'
  return '等待中'
}

function getSubtitle(step: PipelineStep): string {
  return AGENT_LABELS[step.agent] || step.agent || ''
}
</script>

<template>
  <div class="timeline">
    <div
      v-for="(step, idx) in steps"
      :key="step.agent || idx"
      class="timeline-item"
      :class="{ 'timeline-item--active': selectedId === step.agent }"
      @click="emit('select', step.agent)"
    >
      <div class="timeline-left">
        <div class="circle" :class="getStatusClass(step.status)">
          <span class="circle-num">{{ idx + 1 }}</span>
        </div>
        <div v-if="idx < steps.length - 1" class="connector"></div>
      </div>
      <div class="timeline-content">
        <div class="step-name">{{ step.name }}</div>
        <div class="step-subtitle">{{ getSubtitle(step) }}</div>
        <div class="step-meta">
          <span class="step-status" :class="'status--' + step.status">{{ getStatusText(step.status) }}</span>
          <span v-if="step.artifact" class="step-artifact">{{ step.artifact }}</span>
        </div>
      </div>
    </div>
    <div v-if="steps.length === 0" class="empty-timeline">
      <span class="empty-text">暂无步骤数据</span>
    </div>
  </div>
</template>

<style scoped>
.timeline {
  display: flex;
  flex-direction: column;
}

.timeline-item {
  display: flex;
  gap: 12px;
  padding: 10px 12px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: background 0.15s;
}
.timeline-item:hover {
  background: rgba(0, 0, 0, 0.03);
}
.timeline-item--active {
  background: var(--color-blue-subtle);
}

.timeline-left {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.circle {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.circle-num {
  font-size: 11px;
  font-weight: 600;
  color: #fff;
}

.circle--passed {
  background: var(--color-green);
}
.circle--running {
  background: var(--color-blue);
  animation: pulseCircle 1.5s infinite;
}
.circle--failed {
  background: var(--color-red);
}
.circle--pending {
  background: var(--color-text-3);
}

.connector {
  width: 2px;
  flex: 1;
  min-height: 12px;
  background: var(--color-border);
  margin: 4px 0;
}

.timeline-content {
  flex: 1;
  min-width: 0;
  padding-top: 2px;
}

.step-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-1);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.step-subtitle {
  font-size: 11px;
  color: var(--color-text-3);
  margin-top: 1px;
}

.step-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 4px;
}

.step-status {
  font-size: 11px;
  font-weight: 500;
  padding: 1px 6px;
  border-radius: 4px;
}
.status--passed, .status--done {
  background: var(--color-green-subtle);
  color: #166534;
}
.status--running {
  background: var(--color-blue-subtle);
  color: var(--color-blue);
}
.status--failed {
  background: rgba(255, 59, 48, 0.08);
  color: #991b1b;
}
.status--pending {
  background: rgba(0, 0, 0, 0.04);
  color: var(--color-text-3);
}

.step-artifact {
  font-size: 11px;
  color: var(--color-text-2);
  font-family: var(--font-mono);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.empty-timeline {
  padding: 40px 16px;
  text-align: center;
}
.empty-text {
  font-size: 13px;
  color: var(--color-text-3);
}

@keyframes pulseCircle {
  0%, 100% { box-shadow: 0 0 0 0 rgba(0, 113, 227, 0.4); }
  50% { box-shadow: 0 0 0 6px rgba(0, 113, 227, 0); }
}
</style>
