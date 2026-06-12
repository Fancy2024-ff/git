<script setup lang="ts">
import { computed, ref } from 'vue'
import type { JobDetail } from '../types/job'

const props = defineProps<{ job: JobDetail }>()

const listing = computed(() => props.job.artifacts?.['listing-materials.json'] || {})

const appNameCn = computed(() => listing.value.app_name_cn || '')
const appNameEn = computed(() => listing.value.app_name_en || '')
const oneLiner = computed(() => listing.value.one_liner || '')
const description = computed(() => listing.value.description || '')
const category = computed(() => listing.value.category_suggestion || '')
const keywords = computed<string[]>(() => listing.value.keywords || [])
const versionNote = computed(() => listing.value.version_note || '')
const privacySummary = computed(() => listing.value.privacy_summary || '')
const userAgreement = computed(() => listing.value.user_agreement_summary || '')
const screenshots = computed<string[]>(() => listing.value.screenshot_copywriting || [])
const reviewNotes = computed(() => listing.value.review_notes || '')
const riskWarnings = computed<string[]>(() => listing.value.risk_warnings || [])

const copiedField = ref('')

function copyText(text: string, field: string) {
  navigator.clipboard.writeText(text)
  copiedField.value = field
  setTimeout(() => { copiedField.value = '' }, 1500)
}
</script>

<template>
  <div class="listing">
    <div class="card">
      <h3 class="card-title">Basic Info</h3>
      <div class="info-grid">
        <div class="info-row">
          <span class="info-label">应用名称 (中)</span>
          <span class="info-value">{{ appNameCn }}</span>
        </div>
        <div class="info-row">
          <span class="info-label">应用名称 (EN)</span>
          <span class="info-value">{{ appNameEn }}</span>
        </div>
        <div class="info-row">
          <span class="info-label">一句话简介</span>
          <span class="info-value">{{ oneLiner }}</span>
        </div>
        <div class="info-row">
          <span class="info-label">分类</span>
          <span class="info-value">{{ category }}</span>
        </div>
        <div class="info-row">
          <span class="info-label">版本说明</span>
          <span class="info-value">{{ versionNote }}</span>
        </div>
      </div>
      <div class="info-row" v-if="description" style="margin-top: 16px;">
        <span class="info-label">完整描述</span>
        <p class="info-desc">{{ description }}</p>
      </div>
    </div>

    <div class="card" v-if="keywords.length">
      <h3 class="card-title">Keywords</h3>
      <div class="chips">
        <span v-for="kw in keywords" :key="kw" class="chip">{{ kw }}</span>
      </div>
    </div>

    <div class="card" v-if="screenshots.length">
      <h3 class="card-title">Screenshot Copywriting</h3>
      <ol class="screenshot-list">
        <li v-for="(sc, i) in screenshots" :key="i" class="screenshot-item">
          {{ sc }}
        </li>
      </ol>
    </div>

    <div class="card" v-if="privacySummary || userAgreement">
      <h3 class="card-title">Privacy & Agreement</h3>
      <div class="privacy-section" v-if="privacySummary">
        <span class="privacy-label">隐私政策摘要</span>
        <p class="privacy-text">{{ privacySummary }}</p>
      </div>
      <div class="privacy-section" v-if="userAgreement">
        <span class="privacy-label">用户协议摘要</span>
        <p class="privacy-text">{{ userAgreement }}</p>
      </div>
    </div>

    <div class="card" v-if="reviewNotes">
      <h3 class="card-title">Review Notes</h3>
      <p class="review-text">{{ reviewNotes }}</p>
      <button class="copy-btn" @click="copyText(reviewNotes, 'review')">
        {{ copiedField === 'review' ? 'Copied!' : 'Copy' }}
      </button>
    </div>

    <div class="card" v-if="riskWarnings.length">
      <h3 class="card-title">Risk Warnings</h3>
      <ul class="risk-list">
        <li v-for="(w, i) in riskWarnings" :key="i" class="risk-item">
          <span class="risk-icon">⚠</span>
          <span>{{ w }}</span>
        </li>
      </ul>
    </div>
  </div>
</template>

<style scoped>
.listing {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.card {
  background: var(--color-surface-solid);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
  padding: 24px;
}

.card-title {
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-text-3);
  margin: 0 0 16px;
}

.info-grid {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.info-row {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.info-label {
  font-size: 11px;
  font-weight: 500;
  color: var(--color-text-3);
}

.info-value {
  font-size: 14px;
  color: var(--color-text-1);
}

.info-desc {
  font-size: 13px;
  color: var(--color-text-2);
  line-height: 1.6;
  margin: 4px 0 0;
}

.chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.chip {
  font-size: 12px;
  font-weight: 500;
  color: var(--color-blue);
  background: var(--color-blue-subtle);
  padding: 4px 12px;
  border-radius: 980px;
}

.screenshot-list {
  padding: 0 0 0 20px;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.screenshot-item {
  font-size: 13px;
  color: var(--color-text-1);
  line-height: 1.5;
}

.privacy-section {
  margin-bottom: 16px;
}
.privacy-section:last-child {
  margin-bottom: 0;
}

.privacy-label {
  font-size: 12px;
  font-weight: 500;
  color: var(--color-text-2);
}

.privacy-text {
  font-size: 13px;
  color: var(--color-text-1);
  line-height: 1.5;
  margin: 4px 0 0;
}

.review-text {
  font-size: 13px;
  color: var(--color-text-1);
  line-height: 1.5;
  margin: 0 0 12px;
}

.copy-btn {
  font-size: 12px;
  font-weight: 500;
  color: var(--color-blue);
  background: none;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  padding: 5px 12px;
  cursor: pointer;
  transition: transform 0.12s var(--ease-apple), background 0.12s;
}
.copy-btn:hover {
  background: var(--color-blue-subtle);
  transform: translateY(-1px);
}
.copy-btn:active {
  transform: scale(0.98);
}

.risk-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.risk-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  font-size: 13px;
  color: var(--color-text-1);
  line-height: 1.4;
}

.risk-icon {
  color: var(--color-orange);
  flex-shrink: 0;
}
</style>
