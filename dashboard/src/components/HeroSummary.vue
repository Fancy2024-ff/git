<script setup lang="ts">
import { computed } from 'vue'
import type { JobDetail } from '../types/job'

const props = defineProps<{ job: JobDetail }>()

const candidate = computed(() => props.job.artifacts?.['candidate.json'] || {})
const opportunity = computed(() => props.job.artifacts?.['opportunity-report.json'] || {})
const qa = computed(() => props.job.artifacts?.['qa-report.json'] || {})

const appNameCn = computed(() => candidate.value.name_cn || candidate.value.name || '未知应用')
const appNameEn = computed(() => candidate.value.name || '')
const totalScore = computed(() => opportunity.value.total_score || 0)
const qaPassed = computed(() => qa.value.passed === true)
const buildPassed = computed(() => qa.value.checks?.build_passed === true)
const distExists = computed(() => qa.value.checks?.dist_exists === true)
const nextAction = computed(() => opportunity.value.next_action || '')
</script>

<template>
  <section class="hero">
    <h1 class="hero-title">{{ appNameCn }}</h1>
    <p class="hero-subtitle" v-if="appNameEn">{{ appNameEn }}</p>
    <div class="hero-pills">
      <span class="pill pill--blue" v-if="totalScore">
        Score {{ totalScore }}
      </span>
      <span class="pill pill--green" v-if="qaPassed">QA Passed</span>
      <span class="pill pill--green" v-if="buildPassed">Build Passed</span>
      <span class="pill pill--green" v-if="distExists">Dist Ready</span>
      <span class="pill pill--orange" v-if="!qaPassed && !buildPassed">Pending</span>
    </div>
    <p class="hero-next" v-if="nextAction">
      Next: {{ nextAction }}
    </p>
  </section>
</template>

<style scoped>
.hero {
  text-align: center;
  padding: 40px 20px 32px;
}

.hero-title {
  font-size: 28px;
  font-weight: 700;
  color: var(--color-text-1);
  letter-spacing: -0.02em;
  margin: 0;
}

.hero-subtitle {
  font-size: 14px;
  color: var(--color-text-2);
  margin: 4px 0 0;
}

.hero-pills {
  display: flex;
  justify-content: center;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 16px;
}

.pill {
  font-size: 12px;
  font-weight: 500;
  padding: 4px 12px;
  border-radius: 980px;
}
.pill--blue {
  background: var(--color-blue-subtle);
  color: var(--color-blue);
}
.pill--green {
  background: var(--color-green-subtle);
  color: #1a8d36;
}
.pill--orange {
  background: var(--color-orange-subtle);
  color: #cc7a00;
}

.hero-next {
  font-size: 13px;
  color: var(--color-text-2);
  margin-top: 12px;
}
</style>
