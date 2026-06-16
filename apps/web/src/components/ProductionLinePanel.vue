<script setup lang="ts">
import { computed, ref } from 'vue'
import type { JobDetail, PipelineStep } from '../types/job'
import AgentTimeline from './AgentTimeline.vue'
import AgentDetailPanel from './AgentDetailPanel.vue'
import TerminalDrawer from './TerminalDrawer.vue'

const props = defineProps<{
  job: JobDetail | null
  running: boolean
  logs: string[]
  livePipelineSteps: PipelineStep[]
  selectedAgentId: string
}>()

const emit = defineEmits<{ 'select-agent': [agentId: string] }>()

const drawerOpen = ref(true)

const pipelineReport = computed(() => props.job?.artifacts?.['pipeline-report.json'])

// 运行中优先用实时步骤；否则用报告里的步骤
const steps = computed<PipelineStep[]>(() => {
  if (props.running && props.livePipelineSteps.length > 0) return props.livePipelineSteps
  if (pipelineReport.value?.steps) return pipelineReport.value.steps
  return []
})

const currentStep = computed(() => steps.value.find(s => s.status === 'running'))
const completedCount = computed(() => steps.value.filter(s => s.status === 'passed' || s.status === 'done').length)
const totalCount = computed(() => steps.value.length || 10)

const selectedStep = computed(() => {
  if (props.selectedAgentId) {
    const found = steps.value.find(s => s.step === props.selectedAgentId || s.agent === props.selectedAgentId)
    if (found) return found
  }
  const failed = steps.value.find(s => s.status === 'failed')
  if (failed) return failed
  const running = steps.value.find(s => s.status === 'running')
  if (running) return running
  return steps.value.length > 0 ? steps.value[steps.value.length - 1] : null
})
</script>

<template>
  <div class="production-line">
    <!-- Progress bar -->
    <div class="line-status">
      <div class="ls-left">
        <span class="ls-title">生产线进度</span>
        <span class="ls-count">{{ completedCount }} / {{ totalCount }} 步完成</span>
      </div>
      <div class="ls-mid">
        <div class="progress-track">
          <div class="progress-fill" :style="{ width: (completedCount / totalCount * 100) + '%' }"></div>
        </div>
      </div>
      <div class="ls-right">
        <template v-if="running && currentStep">
          <span class="live-dot"></span>
          <span class="ls-current">正在执行：{{ currentStep.name }}</span>
        </template>
        <span v-else-if="steps.length === 0" class="ls-idle">尚未运行</span>
        <span v-else class="ls-done">流程已结束</span>
      </div>
    </div>

    <div v-if="steps.length === 0" class="empty">
      <p class="empty-title">暂无生产线数据</p>
      <p class="empty-sub">点击右上角「启动试运行」后，这里会实时显示每一步</p>
    </div>

    <div v-else class="line-body">
      <div class="timeline-col">
        <AgentTimeline
          :steps="steps"
          :selected-id="selectedAgentId"
          @select="emit('select-agent', $event)"
        />
      </div>
      <div class="detail-col">
        <AgentDetailPanel :step="selectedStep" />
      </div>
    </div>

    <TerminalDrawer :logs="logs" :open="drawerOpen" @toggle="drawerOpen = !drawerOpen" />
  </div>
</template>

<style scoped>
.production-line { animation: fadeIn 0.3s var(--ease-apple); }

.line-status {
  display: flex; align-items: center; gap: 16px;
  background: var(--color-surface-solid); border-radius: var(--radius-md);
  box-shadow: var(--shadow-card); padding: 14px 18px; margin-bottom: 20px;
  flex-wrap: wrap;
}
.ls-left { display: flex; flex-direction: column; flex-shrink: 0; }
.ls-title { font-size: 14px; font-weight: 600; color: var(--color-text-1); }
.ls-count { font-size: 12px; color: var(--color-text-3); }
.ls-mid { flex: 1; min-width: 120px; }
.progress-track { height: 6px; background: rgba(0,0,0,0.06); border-radius: 3px; overflow: hidden; }
.progress-fill { height: 100%; background: var(--color-green); border-radius: 3px; transition: width 0.4s var(--ease-apple); }
.ls-right { display: flex; align-items: center; gap: 8px; flex-shrink: 0; }
.live-dot { width: 8px; height: 8px; border-radius: 50%; background: var(--color-blue); box-shadow: 0 0 6px rgba(0,113,227,0.5); animation: pulse 1.2s infinite; }
.ls-current { font-size: 13px; color: var(--color-blue); font-weight: 500; }
.ls-idle { font-size: 13px; color: var(--color-text-3); }
.ls-done { font-size: 13px; color: #166534; }

.empty { text-align: center; padding: 80px 20px; }
.empty-title { font-size: 18px; font-weight: 600; color: var(--color-text-1); }
.empty-sub { font-size: 13px; color: var(--color-text-2); margin-top: 6px; }

.line-body { display: grid; grid-template-columns: 300px 1fr; gap: 20px; min-height: 360px; }
.timeline-col { overflow-y: auto; max-height: 520px; }
.detail-col { min-width: 0; }

@media (max-width: 860px) {
  .line-body { grid-template-columns: 1fr; }
}

@keyframes fadeIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
@keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: 0.4; } }
</style>
