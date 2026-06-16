<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue'
import type { JobSummary, JobDetail, PipelineMode, PipelineStep } from './types/job'
import { api, connectPipelineWS, type WSHandle } from './services/api'
import { DEFAULT_MODE } from './data/modes'
import { upsertStepStarted, applyStepFinished, realModeBlockReason } from './data/pipeline-events'
import { toUserMessage } from './data/error-messages'
import AppleTopNav from './components/AppleTopNav.vue'
import JobMegaMenu from './components/JobMegaMenu.vue'
import SegmentedTabs from './components/SegmentedTabs.vue'
import OverviewDashboard from './components/OverviewDashboard.vue'
import ProductionLinePanel from './components/ProductionLinePanel.vue'
import AgentMapPanel from './components/AgentMapPanel.vue'
import DeliverablesPanel from './components/DeliverablesPanel.vue'
import SubmitCenterPanel from './components/SubmitCenterPanel.vue'
import PlatformsPanel from './components/PlatformsPanel.vue'
import ImportRealAppsModal from './components/ImportRealAppsModal.vue'

const jobs = ref<JobSummary[]>([])
const currentJob = ref<JobDetail | null>(null)
const menuOpen = ref(false)
const running = ref(false)
const logs = ref<string[]>([])
const activeTab = ref('overview')
const error = ref('')
const wsStatus = ref('')
const mode = ref<PipelineMode>(DEFAULT_MODE)
const livePipelineSteps = ref<PipelineStep[]>([])
const selectedAgentId = ref('')
const importOpen = ref(false)

function setMode(value: PipelineMode) { mode.value = value }

function onImportSaved(count: number) {
  mode.value = 'real'
  error.value = ''
  void count
}

let wsHandle: WSHandle | null = null
let statusTimer: ReturnType<typeof setInterval> | null = null

const tabs = [
  { id: 'overview', label: '总览' },
  { id: 'pipeline', label: '生产线' },
  { id: 'deliverables', label: '交付中心' },
  { id: 'submit', label: '上架中心' },
  { id: 'agents', label: 'Agent 说明' },
  { id: 'platforms', label: '平台策略' },
]

async function loadJobs() {
  try {
    const res = await api.getJobs()
    jobs.value = res.jobs
  } catch (e: any) {
    error.value = toUserMessage(e)
  }
}

async function loadLatest() {
  try {
    currentJob.value = await api.getLatestJob()
  } catch (e: any) {
    if (e?.status !== 404) {
      error.value = toUserMessage(e)
    }
  }
}

async function selectJob(id: string) {
  menuOpen.value = false
  try {
    currentJob.value = await api.getJob(id)
  } catch (e: any) {
    error.value = toUserMessage(e)
  }
}

function teardownWatchers() {
  if (wsHandle) { wsHandle.disconnect(); wsHandle = null }
  if (statusTimer) { clearInterval(statusTimer); statusTimer = null }
}

function finishRun(jobId?: string) {
  running.value = false
  wsStatus.value = ''
  teardownWatchers()
  if (jobId) {
    selectJob(jobId)
    loadJobs()
  } else {
    loadJobs()
  }
}

function startStatusPolling(jobId: string) {
  if (statusTimer) clearInterval(statusTimer)
  statusTimer = setInterval(async () => {
    try {
      const s = await api.getPipelineStatus()
      if (!s.running) {
        finishRun(jobId)
      }
    } catch {
      /* transient backend hiccup - keep polling */
    }
  }, 4000)
}

async function startPipeline() {
  running.value = true
  error.value = ''
  wsStatus.value = ''
  logs.value = []
  livePipelineSteps.value = []
  selectedAgentId.value = ''
  activeTab.value = 'pipeline'
  teardownWatchers()
  try {
    if (mode.value === 'real') {
      const inputs = await api.getRealInputs()
      const block = realModeBlockReason(inputs)
      if (block) {
        error.value = block
        running.value = false
        return
      }
    }
    const res = await api.startPipeline(mode.value)
    if (!res.accepted) {
      error.value = '流水线未被接受，请稍后重试。'
      running.value = false
      return
    }
    if (res.job_id) {
      startStatusPolling(res.job_id)
      wsHandle = connectPipelineWS(res.job_id, {
        onMessage: (msg) => {
          if (msg.type === 'log' || msg.type === 'step_log') {
            logs.value.push(msg.data || msg.message || '')
            if (logs.value.length > 3000) {
              logs.value.splice(0, logs.value.length - 3000)
            }
          }
          if (msg.type === 'step_started') {
            // upsert：相同 step/agent 只更新，不重复新增
            livePipelineSteps.value = upsertStepStarted(livePipelineSteps.value, msg)
            selectedAgentId.value = msg.agent || msg.step || selectedAgentId.value
          }
          if (msg.type === 'step_finished') {
            livePipelineSteps.value = applyStepFinished(livePipelineSteps.value, msg)
          }
          if (msg.type === 'pipeline_failed') {
            const reason = msg.user_message || msg.error || '未知错误'
            if (mode.value === 'live') {
              error.value = `实时数据源失败（${reason}）。实时分析依赖 App Store / Google Play 在线抓取，可切换 Demo（试运行）或 Real（生产运行）验证流程。`
            } else {
              error.value = '流水线失败：' + reason
            }
            finishRun(msg.job_id)
          }
          if (msg.type === 'pipeline_finished') {
            finishRun(msg.job_id)
          }
        },
        onError: (info) => {
          if (info.code === 4001) {
            error.value = '认证失败，请检查 VITE_API_TOKEN 是否与后端 DASHBOARD_API_KEY 一致。'
          }
        },
        onReconnect: (attempt) => {
          wsStatus.value = `连接断开，重试中… (第 ${attempt} 次)`
        },
        onClose: () => {
          wsStatus.value = '实时日志连接已断开，改用状态轮询'
        },
      })
    }
  } catch (e: any) {
    error.value = toUserMessage(e)
    running.value = false
    teardownWatchers()
  }
}

function handleSelectAgent(agentId: string) {
  selectedAgentId.value = agentId
}

onMounted(async () => {
  await loadJobs()
  await loadLatest()
})

onBeforeUnmount(() => {
  teardownWatchers()
})
</script>

<template>
  <div class="app" :class="{ 'app--dimmed': menuOpen }">
    <AppleTopNav
      :current-job="currentJob"
      :running="running"
      :mode="mode"
      @toggle-menu="menuOpen = !menuOpen"
      @start="startPipeline"
      @open-import="importOpen = true"
      @update:mode="setMode"
    />

    <ImportRealAppsModal
      v-if="importOpen"
      @close="importOpen = false"
      @saved="onImportSaved"
    />

    <JobMegaMenu
      v-if="menuOpen"
      :jobs="jobs"
      :current-id="currentJob?.id"
      @select="selectJob"
      @close="menuOpen = false"
    />

    <main class="main" @click="menuOpen = false">
      <div v-if="error" class="error-banner">
        {{ error }}
        <button class="retry-btn" @click="error = ''; loadJobs(); loadLatest()">重试</button>
      </div>

      <div v-if="wsStatus && running" class="ws-banner">{{ wsStatus }}</div>

      <SegmentedTabs :tabs="tabs" v-model="activeTab" />

      <div class="panel-area">
        <OverviewDashboard
          v-if="activeTab === 'overview'"
          :job="currentJob"
          :running="running"
          :mode="mode"
          @goto="activeTab = $event"
        />
        <ProductionLinePanel
          v-if="activeTab === 'pipeline'"
          :job="currentJob"
          :running="running"
          :logs="logs"
          :live-pipeline-steps="livePipelineSteps"
          :selected-agent-id="selectedAgentId"
          @select-agent="handleSelectAgent"
        />
        <DeliverablesPanel v-if="activeTab === 'deliverables'" :job="currentJob" />
        <SubmitCenterPanel v-if="activeTab === 'submit'" :job="currentJob" />
        <AgentMapPanel v-if="activeTab === 'agents'" />
        <PlatformsPanel v-if="activeTab === 'platforms'" :job="currentJob" />
      </div>
    </main>
  </div>
</template>

<style scoped>
.app {
  min-height: 100vh;
  background: var(--color-bg);
  background-image: radial-gradient(ellipse at 70% 0%, rgba(0,113,227,0.03) 0%, transparent 60%);
  transition: filter 0.2s;
}
.app--dimmed .main {
  filter: blur(2px) brightness(0.97);
  pointer-events: none;
}

.main {
  max-width: 1080px;
  margin: 0 auto;
  padding: calc(var(--nav-height) + 16px) 24px 48px;
}

.error-banner {
  background: rgba(255, 59, 48, 0.08);
  color: #c41e16;
  padding: 10px 16px;
  border-radius: var(--radius-sm);
  font-size: 13px;
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.retry-btn {
  font-size: 12px;
  padding: 4px 10px;
  border-radius: 6px;
  border: 1px solid rgba(196, 30, 22, 0.3);
  background: transparent;
  color: #c41e16;
  cursor: pointer;
}

.ws-banner {
  background: rgba(255, 149, 0, 0.08);
  color: #92400e;
  padding: 8px 16px;
  border-radius: var(--radius-sm);
  font-size: 12px;
  margin-bottom: 12px;
}

.panel-area {
  margin-top: 24px;
}

.empty {
  text-align: center;
  padding: 100px 20px;
}
.empty-title {
  font-size: 20px;
  font-weight: 600;
  color: var(--color-text-1);
}
.empty-sub {
  font-size: 14px;
  color: var(--color-text-2);
  margin-top: 8px;
}
.empty-code {
  display: block;
  margin-top: 16px;
  font-family: var(--font-mono);
  font-size: 13px;
  color: var(--color-text-2);
}
</style>
