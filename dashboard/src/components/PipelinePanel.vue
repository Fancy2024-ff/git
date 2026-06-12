<script setup lang="ts">
import { computed } from 'vue'
import type { JobDetail } from '../types/job'

const props = defineProps<{ job: JobDetail }>()

const pipelineReport = computed(() => props.job.artifacts?.['pipeline-report.json'] || null)
const steps = computed(() => pipelineReport.value?.steps || [])

function statusClass(status: string) {
  if (status === 'passed') return 'node--passed'
  if (status === 'running') return 'node--running'
  if (status === 'failed') return 'node--failed'
  return 'node--pending'
}

function statusLabel(status: string) {
  if (status === 'passed') return '完成'
  if (status === 'running') return '运行中'
  if (status === 'failed') return '失败'
  return '等待'
}
</script>

<template>
  <div class="pipeline">
    <div v-if="steps.length === 0" class="empty">
      <p>暂无流水线数据。pipeline-report.json 未生成。</p>
    </div>

    <div v-else class="pipeline-scroll">
      <div class="pipeline-track">
        <div class="pipeline-line"></div>
        <div v-for="(step, idx) in steps" :key="idx" class="pipeline-node" :class="statusClass(step.status)">
          <div class="node-circle" :class="statusClass(step.status)">
            <span v-if="step.status === 'passed'" class="node-icon">&#10003;</span>
            <span v-else-if="step.status === 'failed'" class="node-icon">&#10007;</span>
            <span v-else-if="step.status === 'running'" class="node-icon spinner"></span>
            <span v-else class="node-num">{{ idx + 1 }}</span>
          </div>
          <div class="node-body">
            <span class="node-name">{{ step.name }}</span>
            <span class="node-agent">{{ step.agent }}</span>
            <span class="node-status" :class="statusClass(step.status)">{{ statusLabel(step.status) }}</span>
            <span v-if="step.artifact" class="node-artifact">{{ step.artifact }}</span>
            <span v-if="step.error" class="node-error">{{ step.error }}</span>
          </div>
        </div>
      </div>
    </div>

    <div v-if="pipelineReport" class="pipeline-meta">
      <span>Mode: {{ pipelineReport.mode }}</span>
      <span>Data: {{ pipelineReport.data_source }}</span>
      <span v-if="pipelineReport.total_passed !== undefined">Result: {{ pipelineReport.total_passed ? 'Passed' : 'Failed' }}</span>
    </div>
  </div>
</template>

<style scoped>
.pipeline { display: flex; flex-direction: column; gap: 20px; animation: fadeIn 0.3s ease; }
.empty { text-align: center; padding: 40px; color: var(--color-text-3); font-size: 14px; }

.pipeline-scroll { overflow-x: auto; padding: 16px 0; }
.pipeline-track { display: flex; align-items: flex-start; position: relative; min-width: max-content; gap: 4px; padding: 0 12px; }
.pipeline-line { position: absolute; top: 20px; left: 32px; right: 32px; height: 2px; background: var(--color-border); z-index: 0; }

.pipeline-node { display: flex; flex-direction: column; align-items: center; gap: 6px; min-width: 100px; position: relative; z-index: 1; }

.node-circle { width: 40px; height: 40px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 14px; font-weight: 600; transition: all 0.3s var(--ease-apple); }
.node-circle.node--passed { background: var(--color-green); color: #fff; }
.node-circle.node--running { background: var(--color-blue); color: #fff; animation: pulse 1.5s ease infinite; }
.node-circle.node--failed { background: var(--color-red); color: #fff; }
.node-circle.node--pending { background: var(--color-surface-solid); border: 2px solid var(--color-border); color: var(--color-text-3); }

@keyframes pulse { 0%, 100% { box-shadow: 0 0 0 0 rgba(0,113,227,0.3); } 50% { box-shadow: 0 0 0 8px rgba(0,113,227,0); } }

.node-icon { line-height: 1; }
.spinner { width: 14px; height: 14px; border: 2px solid rgba(255,255,255,0.3); border-top-color: #fff; border-radius: 50%; animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.node-num { line-height: 1; }

.node-body { display: flex; flex-direction: column; align-items: center; gap: 2px; text-align: center; }
.node-name { font-size: 11px; font-weight: 600; color: var(--color-text-1); }
.node-agent { font-size: 10px; color: var(--color-text-3); }
.node-status { font-size: 10px; font-weight: 500; }
.node-status.node--passed { color: var(--color-green); }
.node-status.node--running { color: var(--color-blue); }
.node-status.node--failed { color: var(--color-red); }
.node-status.node--pending { color: var(--color-text-3); }
.node-artifact { font-size: 9px; font-family: var(--font-mono); color: var(--color-text-3); max-width: 90px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.node-error { font-size: 9px; color: var(--color-red); max-width: 90px; }

.pipeline-meta { display: flex; gap: 16px; justify-content: center; font-size: 11px; color: var(--color-text-3); }

@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
</style>
