<script setup lang="ts">
import { jobs, agents } from './data/mockData'
import HeroPanel from './components/HeroPanel.vue'
import PipelineTimeline from './components/PipelineTimeline.vue'
import JobCard from './components/JobCard.vue'
import AgentCard from './components/AgentCard.vue'
import HumanActionPanel from './components/HumanActionPanel.vue'
import PublishFlow from './components/PublishFlow.vue'
import ArtifactList from './components/ArtifactList.vue'

function onStartPipeline() {
  console.log('Start Pipeline triggered')
}
</script>

<template>
  <div class="app-wrapper">
    <!-- Hero -->
    <div class="section animate-in animate-in-1">
      <HeroPanel @start-pipeline="onStartPipeline" />
    </div>

    <!-- Pipeline Timeline -->
    <div class="section animate-in animate-in-2">
      <PipelineTimeline />
    </div>

    <!-- Job Cards -->
    <div class="section animate-in animate-in-3">
      <div class="section-header">
        <h2 class="section-title">进行中的生产任务 <span class="section-title__en">Active Jobs</span></h2>
        <p class="section-subtitle">本轮正在跟踪 {{ jobs.length }} 个小程序生产任务</p>
      </div>
      <div class="jobs-grid">
        <JobCard v-for="job in jobs" :key="job.id" :job="job" />
      </div>
    </div>

    <!-- Human Actions -->
    <div class="section animate-in animate-in-4">
      <HumanActionPanel />
    </div>

    <!-- Agent Cards -->
    <div class="section animate-in animate-in-5">
      <div class="section-header">
        <h2 class="section-title">Agent 协作网络 <span class="section-title__en">Agent Mesh</span></h2>
        <p class="section-subtitle">当前流水线中所有 Agent 的运行状态</p>
      </div>
      <div class="agents-grid">
        <AgentCard v-for="agent in agents" :key="agent.id" :agent="agent" />
      </div>
    </div>

    <!-- Publish Flow + Artifacts side by side -->
    <div class="section animate-in animate-in-6">
      <div class="bottom-row">
        <PublishFlow class="bottom-row__item" />
        <ArtifactList class="bottom-row__item" />
      </div>
    </div>
  </div>
</template>

<style scoped>
.app-wrapper {
  padding: var(--space-12) 0 var(--space-16);
}

.app-wrapper > .section {
  margin-bottom: 64px;
}

.section-header {
  margin-bottom: var(--space-5);
}

.section-title {
  font-size: 20px;
  font-weight: 600;
  color: var(--color-text-primary);
  letter-spacing: -0.02em;
  line-height: 1.3;
}

.section-title__en {
  font-size: 14px;
  font-weight: 400;
  color: var(--color-text-tertiary);
  margin-left: 6px;
}

.section-subtitle {
  font-size: 13px;
  color: var(--color-text-secondary);
  margin-top: 3px;
}

.jobs-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: var(--space-4);
}

.agents-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: var(--space-4);
}

.bottom-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--space-8);
  align-items: start;
}

@media (max-width: 768px) {
  .bottom-row {
    grid-template-columns: 1fr;
  }
}
</style>
