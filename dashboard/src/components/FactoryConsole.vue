<script setup lang="ts">
import { computed } from 'vue'
import type { JobDetail, PipelineStep } from '../types/job'
import AgentTimeline from './AgentTimeline.vue'
import AgentDetailPanel from './AgentDetailPanel.vue'
import TerminalDrawer from './TerminalDrawer.vue'
import { ref } from 'vue'

const props = defineProps<{
  job: JobDetail | null
  running: boolean
  logs: string[]
  livePipelineSteps: PipelineStep[]
  selectedAgentId: string
}>()

const emit = defineEmits<{
  'select-agent': [agentId: string]
}>()

const drawerOpen = ref(true)

const pipelineReport = computed(() => {
  return props.job?.artifacts?.['pipeline-report.json']
})

const steps = computed<PipelineStep[]>(() => {
  if (props.running && props.livePipelineSteps.length > 0) {
    return props.livePipelineSteps
  }
  if (pipelineReport.value?.steps) {
    return pipelineReport.value.steps
  }
  return []
})

const currentStep = computed(() => {
  return steps.value.find(s => s.status === 'running')
})

const completedCount = computed(() => {
  return steps.value.filter(s => s.status === 'passed' || s.status === 'done').length
})

const totalCount = computed(() => {
  return steps.value.length || 9
})

const selectedStep = computed(() => {
  if (!props.selectedAgentId) return steps.value[0] || null
  return steps.value.find(s => s.agent === props.selectedAgentId) || steps.value[0] || null
})

const appName = computed(() => {
  const c = props.job?.artifacts?.['candidate.json']
  return c?.name_cn || c?.name || ''
})

const jobMode = computed(() => {
  return pipelineReport.value?.mode || ''
})
</script>

<template>
  <div class="factory-console">
    <!-- Status bar -->
    <div class="status-bar">
      <div class="status-item" v-if="appName">
        <span class="status-label">应用</span>
        <span class="status-value">{{ appName }}</span>
      </div>
      <div class="status-item" v-if="jobMode">
        <span class="status-label">模式</span>
        <span class="status-value">{{ jobMode }}</span>
      </div>
      <div class="status-item" v-if="job">
        <span class="status-label">Job</span>
        <span class="status-value mono">{{ job.id.slice(0, 8) }}</span>
      </div>
      <div class="status-item">
        <span class="status-label">进度</span>
        <span class="status-value">{{ completedCount }}/{{ totalCount }}</span>
      </div>
      <div class="status-item" v-if="currentStep">
        <span class="status-label">当前</span>
        <span class="status-value running-text">{{ currentStep.name }}</span>
      </div>
      <div class="status-dot-wrapper" v-if="running">
        <span class="status-dot-live"></span>
        <span class="status-running-label">运行中</span>
      </div>
    </div>

    <!-- Main content area -->
    <div class="console-body">
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

    <!-- Terminal drawer -->
    <TerminalDrawer
      :logs="logs"
      :open="drawerOpen"
      @toggle="drawerOpen = !drawerOpen"
    />
  </div>
</template>

<style scoped>
.factory-console {
  animation: fadeIn 0.3s var(--ease-apple);
}

.status-bar {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 10px 16px;
  background: var(--color-surface-solid);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-card);
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.status-label {
  font-size: 11px;
  font-weight: 500;
  color: var(--color-text-3);
  text-transform: uppercase;
}

.status-value {
  font-size: 13px;
  font-weight: 500;
  color: var(--color-text-1);
}

.status-value.mono {
  font-family: var(--font-mono);
  font-size: 12px;
}

.running-text {
  color: var(--color-blue);
}

.status-dot-wrapper {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-left: auto;
}

.status-dot-live {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--color-green);
  box-shadow: 0 0 6px rgba(52, 199, 89, 0.4);
  animation: pulse 1.5s infinite;
}

.status-running-label {
  font-size: 12px;
  font-weight: 500;
  color: var(--color-green);
}

.console-body {
  display: grid;
  grid-template-columns: 280px 1fr;
  gap: 20px;
  min-height: 360px;
}

.timeline-col {
  overflow-y: auto;
  max-height: 480px;
}

.detail-col {
  min-width: 0;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
