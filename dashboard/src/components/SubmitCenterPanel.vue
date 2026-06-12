<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { api } from '../services/api'

const platforms = ref<any[]>([])
const uploading = ref(false)
const uploadResult = ref<any>(null)

onMounted(async () => {
  try {
    const res = await api.getPlatformAuth()
    platforms.value = res.platforms
  } catch {}
})

async function handleUpload(platformId: string) {
  if (platformId !== 'wechat') return
  uploading.value = true
  uploadResult.value = null
  try {
    uploadResult.value = await api.uploadWechat()
  } catch (e: any) {
    uploadResult.value = { upload_passed: false, reason: e.message }
  }
  uploading.value = false
}
</script>

<template>
  <div class="submit-center">
    <div class="header">
      <h3>提交中心</h3>
      <p class="subtitle">管理平台授权状态、自动上传和审核提交</p>
    </div>

    <div v-if="platforms.length === 0" class="empty">
      <p>暂无平台授权配置。请在 data/platform-auth/ 下添加配置文件。</p>
    </div>

    <div v-for="plat in platforms" :key="plat.platform_id" class="platform-card">
      <div class="platform-header">
        <h4>{{ plat.platform_name }}</h4>
        <span class="config-badge" :class="plat.configured ? 'badge-ok' : 'badge-no'">
          {{ plat.configured ? '已配置' : '未配置' }}
        </span>
      </div>

      <!-- One-time setup -->
      <div v-if="plat.one_time_setup?.length" class="setup-list">
        <div class="setup-title">一次性配置</div>
        <div v-for="s in plat.one_time_setup" :key="s.name" class="setup-item">
          <span class="setup-dot" :class="s.done ? 'dot-done' : 'dot-pending'"></span>
          <span>{{ s.name }}</span>
        </div>
      </div>

      <!-- Missing config -->
      <div v-if="plat.missing_config?.length" class="missing-list">
        <div class="missing-title">缺失配置</div>
        <span v-for="m in plat.missing_config" :key="m" class="missing-chip">{{ m }}</span>
      </div>

      <!-- Agent capabilities -->
      <div v-if="plat.agent_actions?.length" class="actions-list">
        <div class="actions-title">Agent 能力</div>
        <div v-for="a in plat.agent_actions" :key="a.name" class="action-item">
          <span class="action-dot" :class="a.enabled ? 'dot-done' : 'dot-pending'"></span>
          <span>{{ a.name }}</span>
          <span v-if="!a.enabled" class="action-disabled">未启用</span>
        </div>
      </div>

      <!-- Human actions required -->
      <div v-if="plat.human_actions?.length" class="human-list">
        <div class="human-title">需要人工操作</div>
        <div v-for="h in plat.human_actions" :key="h.name" class="human-item">
          <span>{{ h.name }}</span>
          <span class="human-reason">{{ h.reason }}</span>
        </div>
      </div>

      <!-- Upload button (wechat only for now) -->
      <div v-if="plat.platform_id === 'wechat'" class="upload-section">
        <button
          class="upload-btn"
          :disabled="!plat.can_upload || uploading"
          @click="handleUpload('wechat')"
        >
          {{ uploading ? '上传中...' : plat.can_upload ? '自动上传代码' : '上传不可用（需配置）' }}
        </button>
        <div v-if="uploadResult" class="upload-result" :class="uploadResult.upload_passed ? 'result-ok' : 'result-fail'">
          {{ uploadResult.upload_passed ? '上传成功' : uploadResult.reason }}
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.submit-center { animation: fadeIn 0.3s ease; }
.header { margin-bottom: 20px; }
.header h3 { font-size: 20px; font-weight: 600; color: var(--color-text-1); }
.subtitle { font-size: 13px; color: var(--color-text-2); margin-top: 4px; }
.empty { padding: 40px; text-align: center; color: var(--color-text-3); }

.platform-card { background: var(--color-surface-solid); border-radius: var(--radius-lg); padding: 20px; margin-bottom: 16px; box-shadow: var(--shadow-card); }
.platform-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
.platform-header h4 { font-size: 15px; font-weight: 600; color: var(--color-text-1); }
.config-badge { font-size: 11px; font-weight: 500; padding: 3px 8px; border-radius: 10px; }
.badge-ok { background: var(--color-green-subtle); color: #166534; }
.badge-no { background: rgba(255,59,48,0.08); color: #991b1b; }

.setup-list, .missing-list, .actions-list, .human-list { margin-bottom: 12px; }
.setup-title, .missing-title, .actions-title, .human-title { font-size: 11px; font-weight: 600; color: var(--color-text-3); text-transform: uppercase; margin-bottom: 6px; }
.setup-item, .action-item { display: flex; align-items: center; gap: 6px; font-size: 13px; padding: 3px 0; color: var(--color-text-1); }
.setup-dot, .action-dot { width: 8px; height: 8px; border-radius: 50%; }
.dot-done { background: var(--color-green); }
.dot-pending { background: var(--color-text-3); }
.action-disabled { font-size: 11px; color: var(--color-text-3); margin-left: auto; }

.missing-chip { font-size: 11px; padding: 2px 6px; background: rgba(255,59,48,0.08); color: #991b1b; border-radius: 4px; margin-right: 4px; }

.human-item { display: flex; justify-content: space-between; font-size: 13px; padding: 4px 0; }
.human-reason { font-size: 11px; color: var(--color-text-3); }

.upload-section { margin-top: 12px; padding-top: 12px; border-top: 1px solid var(--color-border); }
.upload-btn { padding: 8px 16px; border-radius: 8px; font-size: 13px; font-weight: 500; background: var(--color-blue); color: #fff; border: none; cursor: pointer; }
.upload-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.upload-result { margin-top: 8px; font-size: 12px; padding: 6px 10px; border-radius: 6px; }
.result-ok { background: var(--color-green-subtle); color: #166534; }
.result-fail { background: rgba(255,59,48,0.08); color: #991b1b; }

@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
</style>
