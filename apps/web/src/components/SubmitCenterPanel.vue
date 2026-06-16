<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import type { JobDetail } from '../types/job'
import { api } from '../services/api'
import { buildSubmitViews, reviewLabel, uploadLabel, type PlatformSubmitView } from '../data/submit-status'
import { toUserMessage } from '../data/error-messages'

const props = defineProps<{ job: JobDetail | null }>()

const authStatus = ref<any[]>([])
const loading = ref(true)
const loadError = ref('')
const uploadingId = ref('')
const uploadResult = ref<Record<string, { ok: boolean; msg: string }>>({})

async function loadAuth() {
  loading.value = true
  loadError.value = ''
  try {
    const res = await api.getPlatformAuth()
    authStatus.value = res.platforms || []
  } catch (e: any) {
    loadError.value = toUserMessage(e)
  } finally {
    loading.value = false
  }
}

onMounted(loadAuth)
watch(() => props.job?.id, () => { uploadResult.value = {} })

const views = computed<PlatformSubmitView[]>(() => {
  const art = props.job?.artifacts || {}
  const readiness = art['submission-readiness-report.json']
  const submitStatus = art['submit-status.json']
  const opportunity = art['opportunity-report.json']
  return buildSubmitViews({
    platformReadiness: readiness?.platform_readiness || [],
    submitStatus: submitStatus?.platforms || [],
    targetPlatforms: opportunity?.target_platforms || readiness?.target_platforms || [],
    authStatus: authStatus.value,
    distExists: !!art['qa-report.json']?.checks?.dist_exists,
  })
})

async function upload(v: PlatformSubmitView) {
  if (v.platform_id !== 'wechat' || !v.can_upload) return
  uploadingId.value = v.platform_id
  try {
    const res = await api.uploadWechat()
    uploadResult.value[v.platform_id] = res.upload_passed
      ? { ok: true, msg: '代码已上传到微信后台开发版本，下一步去 mp.weixin.qq.com 提交审核。' }
      : { ok: false, msg: res.reason || '上传未成功' }
  } catch (e: any) {
    uploadResult.value[v.platform_id] = { ok: false, msg: toUserMessage(e) }
  } finally {
    uploadingId.value = ''
  }
}
</script>

<template>
  <div class="submit-center">
    <div class="header">
      <h2 class="title">上架中心</h2>
      <p class="subtitle">每个平台能不能上架、缺什么、下一步谁来做</p>
    </div>

    <div v-if="loading" class="state-box">加载平台授权状态中…</div>
    <div v-else-if="loadError" class="state-box state-box--err">
      {{ loadError }}
      <button class="retry" @click="loadAuth">重试</button>
    </div>
    <div v-else-if="!job" class="state-box">暂无任务数据，请先启动试运行。</div>
    <div v-else-if="views.length === 0" class="state-box">该任务未生成平台就绪报告。</div>

    <div v-else class="platform-list">
      <div v-for="v in views" :key="v.platform_id" class="platform-card">
        <div class="pc-head">
          <div class="pc-name">
            {{ v.name_cn }}
            <span v-if="v.recommended" class="rec-chip">推荐投放</span>
            <span v-else class="rec-chip rec-chip--no">非目标平台</span>
          </div>
        </div>

        <div class="status-grid">
          <div class="sg-item">
            <span class="sg-label">授权</span>
            <span class="sg-val" :class="v.configured ? 'v--green' : 'v--gray'">{{ v.configured ? '已配置' : '未配置' }}</span>
          </div>
          <div class="sg-item">
            <span class="sg-label">构建产物</span>
            <span class="sg-val" :class="v.dist_exists ? 'v--green' : 'v--gray'">{{ v.dist_exists ? 'dist 存在' : '缺失' }}</span>
          </div>
          <div class="sg-item">
            <span class="sg-label">上传</span>
            <span class="sg-val" :class="'v--' + uploadLabel(v.upload_status).tone">{{ uploadLabel(v.upload_status).text }}</span>
          </div>
          <div class="sg-item">
            <span class="sg-label">审核</span>
            <span class="sg-val" :class="'v--' + reviewLabel(v.review_status).tone">{{ reviewLabel(v.review_status).text }}</span>
          </div>
        </div>

        <div v-if="!v.configured && v.missing_fields.length" class="missing">
          缺少配置：<span v-for="m in v.missing_fields" :key="m" class="miss-chip">{{ m }}</span>
        </div>

        <div class="next">
          <span class="next-owner" :class="v.next_owner === 'agent' ? 'owner--agent' : 'owner--human'">
            {{ v.next_owner === 'agent' ? 'Agent' : '人工' }}
          </span>
          <span class="next-text">{{ v.next_action }}</span>
        </div>

        <div v-if="v.platform_id === 'wechat'" class="action-area">
          <button
            class="upload-btn"
            :disabled="!v.can_upload || uploadingId === v.platform_id"
            @click="upload(v)"
          >
            {{ uploadingId === v.platform_id ? '上传中…' : v.can_upload ? '上传到微信开发版本' : '上传不可用（先配置授权）' }}
          </button>
          <div v-if="uploadResult[v.platform_id]" class="upload-res" :class="uploadResult[v.platform_id].ok ? 'res--ok' : 'res--fail'">
            {{ uploadResult[v.platform_id].msg }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.submit-center { animation: fadeIn 0.3s var(--ease-apple); }
.header { margin-bottom: 20px; }
.title { font-size: 24px; font-weight: 700; color: var(--color-text-1); }
.subtitle { font-size: 13px; color: var(--color-text-2); margin-top: 4px; }

.state-box { background: var(--color-surface-solid); border-radius: var(--radius-md); box-shadow: var(--shadow-card); padding: 32px; text-align: center; color: var(--color-text-2); font-size: 14px; }
.state-box--err { color: #991b1b; }
.retry { margin-left: 12px; font-size: 12px; padding: 4px 12px; border-radius: 6px; border: 1px solid var(--color-border); background: transparent; cursor: pointer; }

.platform-list { display: grid; grid-template-columns: repeat(auto-fill, minmax(340px, 1fr)); gap: 16px; }
.platform-card { background: var(--color-surface-solid); border-radius: var(--radius-lg); box-shadow: var(--shadow-card); padding: 20px; }
.pc-head { margin-bottom: 14px; }
.pc-name { font-size: 16px; font-weight: 600; color: var(--color-text-1); display: flex; align-items: center; gap: 8px; }
.rec-chip { font-size: 11px; font-weight: 500; padding: 2px 8px; border-radius: 980px; background: var(--color-blue-subtle); color: var(--color-blue); }
.rec-chip--no { background: rgba(0,0,0,0.04); color: var(--color-text-3); }

.status-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 12px; }
.sg-item { display: flex; align-items: center; justify-content: space-between; background: rgba(0,0,0,0.03); border-radius: var(--radius-sm); padding: 8px 10px; }
.sg-label { font-size: 12px; color: var(--color-text-3); }
.sg-val { font-size: 12px; font-weight: 600; }
.v--green { color: #166534; }
.v--blue { color: var(--color-blue); }
.v--orange { color: #92400e; }
.v--red { color: #991b1b; }
.v--gray { color: var(--color-text-3); }

.missing { font-size: 12px; color: #991b1b; margin-bottom: 12px; }
.miss-chip { background: rgba(255,59,48,0.08); padding: 1px 6px; border-radius: 4px; margin-right: 4px; font-family: var(--font-mono); }

.next { display: flex; align-items: flex-start; gap: 8px; padding: 10px; background: rgba(0,0,0,0.02); border-radius: var(--radius-sm); margin-bottom: 12px; }
.next-owner { font-size: 10px; font-weight: 600; padding: 2px 6px; border-radius: 4px; flex-shrink: 0; }
.owner--agent { background: var(--color-blue-subtle); color: var(--color-blue); }
.owner--human { background: var(--color-orange-subtle); color: #92400e; }
.next-text { font-size: 13px; color: var(--color-text-1); line-height: 1.5; }

.action-area { border-top: 1px solid var(--color-border); padding-top: 12px; }
.upload-btn { font-size: 13px; font-weight: 500; padding: 9px 16px; border-radius: 980px; background: var(--color-blue); color: #fff; border: none; cursor: pointer; width: 100%; }
.upload-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.upload-res { margin-top: 10px; font-size: 12px; padding: 8px 10px; border-radius: var(--radius-sm); line-height: 1.5; }
.res--ok { background: var(--color-green-subtle); color: #166534; }
.res--fail { background: rgba(255,59,48,0.08); color: #991b1b; }

@media (max-width: 600px) { .platform-list { grid-template-columns: 1fr; } }
@keyframes fadeIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
</style>
