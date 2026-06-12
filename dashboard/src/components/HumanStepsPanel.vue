<script setup lang="ts">
import { computed, ref } from 'vue'
import type { JobDetail } from '../types/job'

const props = defineProps<{ job: JobDetail }>()

const readiness = computed(() => props.job.artifacts?.['submission-readiness-report.json'] || null)
const platforms = computed(() => readiness.value?.platform_readiness || [])
const rejected = computed(() => readiness.value?.rejected_platforms || [])
const distPath = computed(() => {
  const qa = props.job.artifacts?.['qa-report.json']
  return qa?.checks?.dist_path || props.job.miniapp_path || ''
})

const copied = ref('')
function copyText(text: string, label: string) {
  navigator.clipboard.writeText(text)
  copied.value = label
  setTimeout(() => { copied.value = '' }, 2000)
}
</script>

<template>
  <div class="human-steps">
    <div v-if="!readiness" class="empty">
      <p>暂无平台提交信息。请先运行 Pipeline 生成 submission-readiness-report.json。</p>
    </div>

    <template v-else>
      <div class="ready-banner" :class="readiness.is_ready_to_submit ? 'ready-banner--yes' : 'ready-banner--no'">
        {{ readiness.is_ready_to_submit ? '可以提交审核' : '尚未准备就绪' }}
      </div>

      <div v-if="readiness.warning_issues?.length" class="warnings">
        <div v-for="w in readiness.warning_issues" :key="w" class="warning-item">&#9888; {{ w }}</div>
      </div>

      <div v-if="distPath" class="dist-card">
        <div class="dist-label">构建产物目录 / Dist Path</div>
        <code class="dist-path">{{ distPath }}</code>
        <button class="copy-btn" @click="copyText(distPath, 'dist')">{{ copied === 'dist' ? '已复制' : '复制路径' }}</button>
      </div>

      <div v-for="plat in platforms" :key="plat.platform" class="platform-section">
        <div class="platform-header">
          <h3 class="platform-name">{{ plat.name_cn || plat.platform }}</h3>
          <span class="platform-name-en">{{ plat.name_en || '' }}</span>
          <span class="platform-badge" :class="plat.ready ? 'badge-green' : 'badge-orange'">
            {{ plat.ready ? '就绪' : '未就绪' }}
          </span>
        </div>

        <div class="platform-meta">
          <span v-if="plat.automation_level">自动化: {{ plat.automation_level }}</span>
          <span v-if="plat.cli_tool">CLI: {{ plat.cli_tool }}</span>
        </div>

        <div v-if="plat.submission_steps?.length" class="steps-list">
          <div v-for="(step, i) in plat.submission_steps" :key="i" class="step-item">
            <span class="step-num">{{ i + 1 }}</span>
            <span class="step-text">{{ step }}</span>
          </div>
        </div>

        <div v-if="plat.required_materials?.length" class="materials">
          <span class="materials-label">需要材料:</span>
          <span v-for="m in plat.required_materials" :key="m" class="material-chip">{{ m }}</span>
        </div>

        <div v-if="plat.compliance_risks?.length" class="risks">
          <span v-for="r in plat.compliance_risks" :key="r" class="risk-item">&#9888; {{ r }}</span>
        </div>

        <div class="platform-links">
          <a v-if="plat.submit_url" :href="plat.submit_url" target="_blank" class="link-btn">打开提交后台</a>
          <a v-if="plat.developer_url" :href="plat.developer_url" target="_blank" class="link-btn link-btn--ghost">开发者文档</a>
          <button v-if="plat.upload_path" class="link-btn link-btn--ghost" @click="copyText(plat.upload_path, plat.platform)">
            {{ copied === plat.platform ? '已复制' : '复制上传目录' }}
          </button>
        </div>
      </div>

      <div v-if="rejected.length" class="rejected-section">
        <h4>不推荐 / 暂不支持的平台</h4>
        <div v-for="r in rejected" :key="r.platform" class="rejected-item">
          <span class="rejected-name">{{ r.platform }}</span>
          <span class="rejected-reason">{{ r.reason }}</span>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.human-steps { animation: fadeIn 0.3s ease; }
.empty { text-align: center; padding: 40px; color: var(--color-text-3); }

.ready-banner { padding: 12px 20px; border-radius: var(--radius-md); font-size: 14px; font-weight: 600; margin-bottom: 20px; text-align: center; }
.ready-banner--yes { background: var(--color-green-subtle); color: #166534; }
.ready-banner--no { background: rgba(255,59,48,0.08); color: #991b1b; }

.warnings { margin-bottom: 16px; }
.warning-item { font-size: 12px; color: #92400e; background: var(--color-orange-subtle); padding: 6px 12px; border-radius: 6px; margin-bottom: 4px; }

.dist-card { background: var(--color-surface-solid); border-radius: var(--radius-md); padding: 16px 20px; box-shadow: var(--shadow-card); margin-bottom: 24px; display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
.dist-label { font-size: 11px; font-weight: 600; color: var(--color-text-3); text-transform: uppercase; }
.dist-path { font-size: 12px; font-family: var(--font-mono); color: var(--color-text-1); background: rgba(0,0,0,0.04); padding: 4px 8px; border-radius: 4px; flex: 1; word-break: break-all; }
.copy-btn { font-size: 11px; font-weight: 500; padding: 4px 10px; border-radius: 6px; border: 1px solid var(--color-border); background: transparent; color: var(--color-blue); cursor: pointer; }

.platform-section { background: var(--color-surface-solid); border-radius: var(--radius-lg); padding: 20px; box-shadow: var(--shadow-card); margin-bottom: 16px; }
.platform-header { display: flex; align-items: baseline; gap: 8px; margin-bottom: 10px; flex-wrap: wrap; }
.platform-name { font-size: 16px; font-weight: 600; color: var(--color-text-1); }
.platform-name-en { font-size: 12px; color: var(--color-text-3); }
.platform-badge { font-size: 10px; font-weight: 600; padding: 2px 8px; border-radius: 10px; }
.badge-green { background: var(--color-green-subtle); color: #166534; }
.badge-orange { background: var(--color-orange-subtle); color: #92400e; }

.platform-meta { display: flex; gap: 12px; font-size: 11px; color: var(--color-text-2); margin-bottom: 12px; }

.steps-list { margin-bottom: 12px; }
.step-item { display: flex; align-items: flex-start; gap: 8px; padding: 6px 0; }
.step-num { width: 20px; height: 20px; border-radius: 50%; background: var(--color-blue-subtle); color: var(--color-blue); font-size: 11px; font-weight: 600; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.step-text { font-size: 13px; color: var(--color-text-1); line-height: 1.4; }

.materials { margin-bottom: 8px; display: flex; flex-wrap: wrap; gap: 4px; align-items: center; }
.materials-label { font-size: 11px; color: var(--color-text-3); margin-right: 4px; }
.material-chip { font-size: 10px; padding: 2px 6px; background: rgba(0,0,0,0.04); border-radius: 4px; color: var(--color-text-2); }

.risks { margin-bottom: 8px; }
.risk-item { font-size: 11px; color: #92400e; display: block; }

.platform-links { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 12px; }
.link-btn { font-size: 12px; font-weight: 500; padding: 6px 12px; border-radius: 6px; text-decoration: none; cursor: pointer; border: none; background: var(--color-blue); color: #fff; }
.link-btn--ghost { background: transparent; border: 1px solid var(--color-border); color: var(--color-text-1); }

.rejected-section { margin-top: 24px; padding: 16px; background: rgba(0,0,0,0.02); border-radius: var(--radius-md); }
.rejected-section h4 { font-size: 13px; font-weight: 600; color: var(--color-text-2); margin-bottom: 8px; }
.rejected-item { display: flex; gap: 8px; font-size: 12px; padding: 4px 0; }
.rejected-name { font-weight: 500; color: var(--color-text-1); }
.rejected-reason { color: var(--color-text-3); }

@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
</style>
