<script setup lang="ts">
import { ref, onMounted } from 'vue'
import type { JobSummary, JobDetail } from './types/job'
import { api, connectPipelineWS } from './services/api'
import AppleTopNav from './components/AppleTopNav.vue'
import JobMegaMenu from './components/JobMegaMenu.vue'
import HeroSummary from './components/HeroSummary.vue'
import SegmentedTabs from './components/SegmentedTabs.vue'
import OverviewPanel from './components/OverviewPanel.vue'
import PipelinePanel from './components/PipelinePanel.vue'
import PRDPanel from './components/PRDPanel.vue'
import ListingPanel from './components/ListingPanel.vue'
import HumanStepsPanel from './components/HumanStepsPanel.vue'
import FilesPanel from './components/FilesPanel.vue'
import LogsPanel from './components/LogsPanel.vue'
import BossViewPanel from './components/BossViewPanel.vue'
import ImportPanel from './components/ImportPanel.vue'
import PlatformsPanel from './components/PlatformsPanel.vue'

const jobs = ref<JobSummary[]>([])
const currentJob = ref<JobDetail | null>(null)
const menuOpen = ref(false)
const running = ref(false)
const logs = ref<string[]>([])
const activeTab = ref('overview')
const error = ref('')
const mode = ref<'demo' | 'real'>('demo')
const showImport = ref(false)

const tabs = [
  { id: 'overview', label: '总览' },
  { id: 'pipeline', label: '流水线' },
  { id: 'prd', label: 'PRD' },
  { id: 'listing', label: '上架材料' },
  { id: 'actions', label: '人工操作' },
  { id: 'files', label: '产物文件' },
  { id: 'platforms', label: '平台库' },
  { id: 'logs', label: '日志' },
  { id: 'boss', label: '演示' },
  { id: 'import', label: '导入' },
]

async function loadJobs() {
  try {
    const res = await api.getJobs()
    jobs.value = res.jobs
  } catch {}
}

async function loadLatest() {
  try {
    currentJob.value = await api.getLatestJob()
  } catch {}
}

async function selectJob(id: string) {
  menuOpen.value = false
  try {
    currentJob.value = await api.getJob(id)
  } catch (e: any) {
    error.value = e.message
  }
}

async function startPipeline() {
  running.value = true
  error.value = ''
  logs.value = []
  activeTab.value = 'logs'
  try {
    const res = await api.startPipeline(mode.value)
    logs.value = res.logs || []
    if (res.success && res.job_id) {
      await loadJobs()
      await selectJob(res.job_id)
      activeTab.value = 'overview'
    } else {
      error.value = `Pipeline failed (exit ${res.exit_code})`
    }
  } catch (e: any) {
    error.value = `API error: ${e.message}`
  }
  running.value = false
}

onMounted(async () => {
  await loadJobs()
  await loadLatest()
  connectPipelineWS((msg) => {
    if (msg.type === 'log') logs.value.push(msg.data)
    if (msg.type === 'status' && msg.running) { running.value = true }
    if (msg.type === 'complete') { running.value = false; loadJobs(); loadLatest(); }
  })
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
      @update:mode="mode = $event"
    />

    <JobMegaMenu
      v-if="menuOpen"
      :jobs="jobs"
      :current-id="currentJob?.id"
      @select="selectJob"
      @close="menuOpen = false"
    />

    <main class="main" @click="menuOpen = false">
      <div v-if="error" class="error-banner">{{ error }}</div>

      <div v-if="currentJob" class="content">
        <HeroSummary :job="currentJob" />

        <SegmentedTabs :tabs="tabs" v-model="activeTab" />

        <div class="panel-area">
          <OverviewPanel v-if="activeTab === 'overview'" :job="currentJob" />
          <PipelinePanel v-if="activeTab === 'pipeline'" :job="currentJob" />
          <PRDPanel v-if="activeTab === 'prd'" :job="currentJob" />
          <ListingPanel v-if="activeTab === 'listing'" :job="currentJob" />
          <HumanStepsPanel v-if="activeTab === 'actions'" :job="currentJob" />
          <FilesPanel v-if="activeTab === 'files'" :job="currentJob" />
          <PlatformsPanel v-if="activeTab === 'platforms'" />
          <LogsPanel v-if="activeTab === 'logs'" :logs="logs" />
          <BossViewPanel v-if="activeTab === 'boss'" :job="currentJob" />
          <ImportPanel v-if="activeTab === 'import'" />
        </div>
      </div>

      <div v-else class="empty">
        <p class="empty-title">暂无任务数据</p>
        <p class="empty-sub">请确认后端已启动，然后点击「启动流水线」</p>
        <code class="empty-code">cd agents && python server.py</code>
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
  max-width: 960px;
  margin: 0 auto;
  padding: calc(var(--nav-height) + 24px) 24px 48px;
}

.error-banner {
  background: rgba(255, 59, 48, 0.08);
  color: #c41e16;
  padding: 10px 16px;
  border-radius: var(--radius-sm);
  font-size: 13px;
  margin-bottom: 20px;
}

.content {
  animation: fadeIn 0.3s var(--ease-apple);
}

.panel-area {
  margin-top: 32px;
}

.empty {
  text-align: center;
  padding: 120px 20px;
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

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
