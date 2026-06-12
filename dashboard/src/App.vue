<script setup lang="ts">
import { ref, onMounted } from 'vue'
import HeroPanel from './components/HeroPanel.vue'
import PipelineTimeline from './components/PipelineTimeline.vue'
import HumanActionPanel from './components/HumanActionPanel.vue'
import PublishFlow from './components/PublishFlow.vue'
import ArtifactList from './components/ArtifactList.vue'

const API = 'http://localhost:8000'

const latestJob = ref<any>(null)
const pipelineRunning = ref(false)
const pipelineLogs = ref<string[]>([])
const error = ref('')

async function fetchLatestJob() {
  try {
    const res = await fetch(`${API}/api/jobs/latest`)
    if (res.ok) latestJob.value = await res.json()
  } catch { /* API not running yet */ }
}

async function onStartPipeline() {
  pipelineRunning.value = true
  pipelineLogs.value = []
  error.value = ''
  try {
    const res = await fetch(`${API}/api/demo/start`, { method: 'POST' })
    const data = await res.json()
    if (data.success) {
      pipelineLogs.value = data.logs || []
      // Reload latest job
      await fetchLatestJob()
    } else {
      error.value = `Pipeline failed (exit code ${data.exit_code})`
      pipelineLogs.value = data.logs || []
    }
  } catch (e: any) {
    error.value = `API connection failed: ${e.message}. Please start: cd agents && python server.py`
  }
  pipelineRunning.value = false
}

onMounted(fetchLatestJob)

function getArtifact(name: string): any {
  return latestJob.value?.artifacts?.[name]
}

function getMdContent(name: string): string {
  const a = getArtifact(name)
  if (typeof a === 'string') return a
  if (a?.content) return a.content
  return ''
}
</script>

<template>
  <div class="app-wrapper">
    <!-- Hero -->
    <div class="section animate-in animate-in-1">
      <HeroPanel
        :running="pipelineRunning"
        :job-id="latestJob?.id"
        @start-pipeline="onStartPipeline"
      />
    </div>

    <!-- Error -->
    <div v-if="error" class="section">
      <div class="error-card">{{ error }}</div>
    </div>

    <!-- Pipeline Status from QA -->
    <div v-if="latestJob" class="section animate-in animate-in-2">
      <PipelineTimeline :qa="getArtifact('qa-report.json')" />
    </div>

    <!-- Job Summary -->
    <div v-if="latestJob" class="section animate-in animate-in-3">
      <div class="section-header">
        <h2 class="section-title">当前任务 <span class="en">Job Detail</span></h2>
        <p class="section-subtitle">Job ID: {{ latestJob.id }}</p>
      </div>
      <div class="job-summary">
        <div class="summary-card">
          <div class="summary-label">应用</div>
          <div class="summary-value">{{ getArtifact('candidate.json')?.name_cn || '—' }}</div>
          <div class="summary-sub">{{ getArtifact('candidate.json')?.name || '' }}</div>
        </div>
        <div class="summary-card">
          <div class="summary-label">机会评分</div>
          <div class="summary-value score">{{ getArtifact('opportunity-report.json')?.opportunity_score || '—' }}</div>
          <div class="summary-sub">{{ getArtifact('opportunity-report.json')?.recommendation || '' }}</div>
        </div>
        <div class="summary-card">
          <div class="summary-label">QA 结果</div>
          <div class="summary-value" :class="getArtifact('qa-report.json')?.passed ? 'pass' : 'fail'">
            {{ getArtifact('qa-report.json')?.passed ? '通过' : '未通过' }}
          </div>
          <div class="summary-sub">构建: {{ getArtifact('qa-report.json')?.checks?.build_verified ? '已验证' : '未验证' }}</div>
        </div>
        <div class="summary-card">
          <div class="summary-label">小程序路径</div>
          <div class="summary-value path">{{ latestJob.miniapp_path || '—' }}</div>
        </div>
      </div>
    </div>

    <!-- Human Actions -->
    <div v-if="getMdContent('human-actions.md')" class="section animate-in animate-in-4">
      <HumanActionPanel :content="getMdContent('human-actions.md')" />
    </div>

    <!-- PRD + Listing side by side -->
    <div v-if="latestJob" class="section animate-in animate-in-5">
      <div class="two-col">
        <div class="doc-card">
          <h3 class="doc-title">产品文档 <span class="en">PRD</span></h3>
          <pre class="doc-content">{{ getMdContent('prd.md').slice(0, 2000) }}</pre>
        </div>
        <div class="doc-card">
          <h3 class="doc-title">上架材料 <span class="en">Listing</span></h3>
          <pre class="doc-content">{{ getMdContent('listing-materials.md').slice(0, 2000) }}</pre>
        </div>
      </div>
    </div>

    <!-- Artifacts list -->
    <div v-if="latestJob" class="section animate-in animate-in-6">
      <ArtifactList :artifacts="latestJob.artifacts" :miniapp-files="latestJob.miniapp_files" />
    </div>

    <!-- Logs -->
    <div v-if="pipelineLogs.length" class="section animate-in animate-in-7">
      <div class="section-header">
        <h2 class="section-title">运行日志 <span class="en">Pipeline Logs</span></h2>
      </div>
      <div class="console">
        <div class="console-bar">
          <span class="dot r"></span><span class="dot y"></span><span class="dot g"></span>
          <span class="console-title">run_demo_pipeline.py</span>
        </div>
        <div class="console-body">
          <div v-for="(line, i) in pipelineLogs" :key="i">{{ line }}</div>
        </div>
      </div>
    </div>

    <!-- Empty state -->
    <div v-if="!latestJob && !pipelineRunning" class="section">
      <div class="empty-state">
        <p>暂无任务数据。请先启动后端 API，然后点击「启动流水线」。</p>
        <code>cd agents && python server.py</code>
      </div>
    </div>
  </div>
</template>

<style scoped>
.app-wrapper { padding: var(--space-12) 0 var(--space-16); }
.app-wrapper > .section { margin-bottom: 48px; }

.section-header { margin-bottom: var(--space-5); }
.section-title { font-size: 20px; font-weight: 600; color: var(--color-text-primary); letter-spacing: -0.02em; }
.en { font-size: 13px; font-weight: 400; color: var(--color-text-tertiary); margin-left: 6px; }
.section-subtitle { font-size: 13px; color: var(--color-text-secondary); margin-top: 3px; }

.error-card { background: var(--color-red-subtle); color: #991b1b; padding: 12px 16px; border-radius: var(--radius-sm); font-size: 13px; }

.job-summary { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 12px; }
.summary-card { background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius-md); padding: 16px; }
.summary-label { font-size: 11px; font-weight: 600; color: var(--color-text-tertiary); text-transform: uppercase; letter-spacing: 0.03em; margin-bottom: 4px; }
.summary-value { font-size: 20px; font-weight: 700; color: var(--color-text-primary); letter-spacing: -0.02em; }
.summary-value.score { color: var(--color-accent); }
.summary-value.pass { color: var(--color-green); }
.summary-value.fail { color: var(--color-red); }
.summary-value.path { font-size: 11px; font-weight: 500; font-family: var(--font-mono); word-break: break-all; }
.summary-sub { font-size: 12px; color: var(--color-text-tertiary); margin-top: 2px; }

.two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
@media (max-width: 768px) { .two-col { grid-template-columns: 1fr; } }
.doc-card { background: var(--color-surface); border: 1px solid var(--color-border); border-radius: var(--radius-md); padding: 20px; overflow: hidden; }
.doc-title { font-size: 15px; font-weight: 600; margin-bottom: 12px; color: var(--color-text-primary); }
.doc-content { font-size: 12px; line-height: 1.6; color: var(--color-text-secondary); white-space: pre-wrap; word-break: break-word; max-height: 400px; overflow-y: auto; font-family: var(--font-sans); }

.console { background: #1a1a1a; border-radius: var(--radius-md); overflow: hidden; }
.console-bar { display: flex; align-items: center; gap: 6px; padding: 10px 14px; background: #252525; }
.dot { width: 10px; height: 10px; border-radius: 50%; }
.dot.r { background: #ff5f57; }
.dot.y { background: #febc2e; }
.dot.g { background: #28c840; }
.console-title { flex: 1; text-align: center; font-size: 11px; color: #666; }
.console-body { padding: 14px 18px; max-height: 300px; overflow-y: auto; font-family: var(--font-mono); font-size: 11px; line-height: 1.7; color: #d4d4d4; }

.empty-state { text-align: center; padding: 60px 20px; color: var(--color-text-tertiary); }
.empty-state code { display: block; margin-top: 12px; font-size: 13px; color: var(--color-text-secondary); }
</style>
