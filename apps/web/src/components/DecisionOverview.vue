<script setup lang="ts">
import { computed } from 'vue'
import type { JobDetail } from '../types/job'

const props = defineProps<{
  job: JobDetail | null
}>()

const opportunity = computed(() => {
  return props.job?.artifacts?.['opportunity-report.json'] || null
})

const viral = computed(() => {
  return props.job?.artifacts?.['viral-score.json'] || null
})

const templateSelection = computed(() => {
  return props.job?.artifacts?.['template-selection.json'] || null
})

const pipelineReport = computed(() => {
  return props.job?.artifacts?.['pipeline-report.json'] || null
})

const submissionReadiness = computed(() => {
  return props.job?.artifacts?.['submission-readiness-report.json'] || null
})


const completionItems = computed(() => {
  if (!pipelineReport.value?.steps) return []
  return pipelineReport.value.steps.map((s: any) => ({
    name: s.name,
    done: s.status === 'passed' || s.status === 'done',
  }))
})

const nextActions = computed(() => {
  const actions: { type: string; text: string }[] = []
  if (submissionReadiness.value?.blocking?.length) {
    for (const b of submissionReadiness.value.blocking) {
      actions.push({ type: 'human', text: b })
    }
  }
  if (submissionReadiness.value?.warnings?.length) {
    for (const w of submissionReadiness.value.warnings) {
      actions.push({ type: 'system', text: w })
    }
  }
  if (actions.length === 0 && submissionReadiness.value?.is_ready) {
    actions.push({ type: 'system', text: '所有检查已通过，可以提交上架' })
  }
  return actions
})
</script>

<template>
  <div class="decision-overview">
    <!-- Card 1: Opportunity Score -->
    <div class="card">
      <h3 class="card-title">机会评分</h3>
      <div v-if="opportunity" class="card-body">
        <div class="score-row">
          <span class="score-number">{{ opportunity.total_score ?? opportunity.opportunity_score ?? opportunity.score ?? '--' }}</span>
          <span class="score-max">/ 100</span>
          <span
            class="score-badge"
            :class="{
              'badge--green': (opportunity.recommendation || '').includes('推荐') || (opportunity.recommendation || '').toLowerCase().includes('go'),
              'badge--orange': (opportunity.recommendation || '').includes('谨慎'),
              'badge--red': (opportunity.recommendation || '').includes('不')
            }"
          >{{ opportunity.recommendation || '待评估' }}</span>
        </div>
        <div v-if="opportunity.reasons?.length" class="reasons">
          <div v-for="(r, i) in opportunity.reasons" :key="i" class="reason-item">
            <span class="reason-bullet">{{ Number(i) + 1 }}.</span>
            <span>{{ r }}</span>
          </div>
        </div>
        <div v-if="opportunity.dimensions" class="dimensions">
          <div v-for="(val, key) in opportunity.dimensions" :key="String(key)" class="dim-item">
            <span class="dim-label">{{ key }}</span>
            <span class="dim-value">{{ val }}</span>
          </div>
        </div>
      </div>
      <div v-else class="card-empty">暂无数据</div>
    </div>

    <!-- Card 1b: Viral Decision -->
    <div class="card">
      <h3 class="card-title">传播型决策</h3>
      <div v-if="viral" class="card-body">
        <div class="score-row">
          <span class="score-number">{{ viral.viral_score ?? '--' }}</span>
          <span class="score-max">/ 100</span>
          <span class="score-badge badge--green">{{ viral.tier || 'unknown' }}</span>
        </div>
        <div class="dimensions">
          <div v-for="(val, key) in viral.dimensions" :key="String(key)" class="dim-item">
            <span class="dim-label">{{ key }}</span>
            <span class="dim-value">{{ val }}</span>
          </div>
        </div>
        <div v-if="templateSelection" class="template-line">
          模板：{{ templateSelection.selected_template }} · {{ templateSelection.theme_label }}
        </div>
      </div>
      <div v-else class="card-empty">暂无数据</div>
    </div>

    <!-- Card 2: Completion Checklist -->
    <div class="card">
      <h3 class="card-title">完成度检查</h3>
      <div v-if="completionItems.length" class="card-body">
        <div class="checklist">
          <div v-for="item in completionItems" :key="item.name" class="check-item">
            <span class="check-icon" :class="item.done ? 'check--done' : 'check--pending'">
              {{ item.done ? '✓' : '○' }}
            </span>
            <span class="check-text" :class="{ 'text--done': item.done }">{{ item.name }}</span>
          </div>
        </div>
        <div class="checklist-summary">
          {{ completionItems.filter((i: any) => i.done).length }} / {{ completionItems.length }} 步骤完成
        </div>
      </div>
      <div v-else class="card-empty">该任务未生成流水线报告</div>
    </div>

    <!-- Card 3: Submission Readiness -->
    <div class="card">
      <h3 class="card-title">提交就绪度</h3>
      <div v-if="submissionReadiness" class="card-body">
        <div class="ready-status">
          <span class="ready-dot" :class="(submissionReadiness.is_ready_to_submit || submissionReadiness.is_ready) ? 'dot--green' : 'dot--orange'"></span>
          <span class="ready-text">{{ (submissionReadiness.is_ready_to_submit || submissionReadiness.is_ready) ? '就绪，可以提交' : '尚未就绪' }}</span>
        </div>
        <div v-if="(submissionReadiness.blocking_issues || submissionReadiness.blocking)?.length" class="block-list">
          <h4 class="sub-heading">阻塞项</h4>
          <div v-for="(b, i) in (submissionReadiness.blocking_issues || submissionReadiness.blocking || [])" :key="i" class="block-item block-item--red">
            {{ b }}
          </div>
        </div>
        <div v-if="(submissionReadiness.warning_issues || submissionReadiness.warnings)?.length" class="block-list">
          <h4 class="sub-heading">警告</h4>
          <div v-for="(w, i) in (submissionReadiness.warning_issues || submissionReadiness.warnings || [])" :key="i" class="block-item block-item--orange">
            {{ w }}
          </div>
        </div>
      </div>
      <div v-else class="card-empty">暂无数据</div>
    </div>

    <!-- Card 4: Next Actions -->
    <div class="card">
      <h3 class="card-title">下一步行动</h3>
      <div v-if="nextActions.length" class="card-body">
        <div v-for="(action, i) in nextActions" :key="i" class="action-item">
          <span class="action-type" :class="action.type === 'human' ? 'type--human' : 'type--system'">
            {{ action.type === 'human' ? '人工' : '系统' }}
          </span>
          <span class="action-text">{{ action.text }}</span>
        </div>
      </div>
      <div v-else class="card-empty">暂无数据</div>
    </div>
  </div>
</template>

<style scoped>
.decision-overview {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  animation: fadeIn 0.3s var(--ease-apple);
}

.card {
  background: var(--color-surface-solid);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
  padding: 20px;
}

.card-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-1);
  margin-bottom: 14px;
}

.card-body {
  font-size: 13px;
}

.card-empty {
  font-size: 13px;
  color: var(--color-text-3);
  padding: 20px 0;
  text-align: center;
}

/* Score card */
.score-row {
  display: flex;
  align-items: baseline;
  gap: 4px;
  margin-bottom: 12px;
}
.score-number {
  font-size: 32px;
  font-weight: 700;
  color: var(--color-text-1);
}
.score-max {
  font-size: 14px;
  color: var(--color-text-3);
}
.score-badge {
  margin-left: 12px;
  font-size: 11px;
  font-weight: 500;
  padding: 2px 8px;
  border-radius: 980px;
  background: rgba(0, 0, 0, 0.04);
  color: var(--color-text-2);
}
.badge--green { background: var(--color-green-subtle); color: #166534; }
.badge--orange { background: var(--color-orange-subtle); color: #92400e; }
.badge--red { background: rgba(255, 59, 48, 0.08); color: #991b1b; }

.reasons { margin-top: 8px; }
.reason-item {
  display: flex;
  gap: 6px;
  font-size: 12px;
  color: var(--color-text-2);
  padding: 3px 0;
}
.reason-bullet { color: var(--color-text-3); font-weight: 600; }

.dimensions { margin-top: 10px; display: flex; flex-wrap: wrap; gap: 8px; }
.dim-item { font-size: 12px; background: rgba(0,0,0,0.03); padding: 3px 8px; border-radius: 4px; }
.dim-label { color: var(--color-text-3); margin-right: 4px; }
.dim-value { color: var(--color-text-1); font-weight: 500; }
.template-line { margin-top: 12px; font-size: 12px; color: var(--color-text-2); }

/* Checklist */
.checklist { display: flex; flex-direction: column; gap: 4px; }
.check-item { display: flex; align-items: center; gap: 8px; padding: 3px 0; }
.check-icon { width: 18px; text-align: center; font-size: 13px; }
.check--done { color: var(--color-green); }
.check--pending { color: var(--color-text-3); }
.check-text { font-size: 13px; color: var(--color-text-1); }
.text--done { color: var(--color-text-2); }
.checklist-summary {
  margin-top: 10px;
  font-size: 12px;
  color: var(--color-text-3);
  padding-top: 8px;
  border-top: 1px solid var(--color-border);
}

/* Readiness */
.ready-status { display: flex; align-items: center; gap: 8px; margin-bottom: 12px; }
.ready-dot { width: 10px; height: 10px; border-radius: 50%; }
.dot--green { background: var(--color-green); }
.dot--orange { background: var(--color-orange); }
.ready-text { font-size: 14px; font-weight: 500; color: var(--color-text-1); }

.block-list { margin-top: 8px; }
.sub-heading { font-size: 11px; font-weight: 600; color: var(--color-text-3); margin-bottom: 4px; text-transform: uppercase; }
.block-item { font-size: 12px; padding: 4px 8px; border-radius: 4px; margin-bottom: 4px; }
.block-item--red { background: rgba(255, 59, 48, 0.06); color: #991b1b; }
.block-item--orange { background: var(--color-orange-subtle); color: #92400e; }

/* Actions */
.action-item { display: flex; align-items: center; gap: 8px; padding: 6px 0; }
.action-type {
  font-size: 10px;
  font-weight: 600;
  padding: 2px 6px;
  border-radius: 4px;
  text-transform: uppercase;
  flex-shrink: 0;
}
.type--human { background: var(--color-orange-subtle); color: #92400e; }
.type--system { background: var(--color-blue-subtle); color: var(--color-blue); }
.action-text { font-size: 13px; color: var(--color-text-1); }

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>


