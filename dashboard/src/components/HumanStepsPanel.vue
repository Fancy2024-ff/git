<script setup lang="ts">
import { computed, ref } from 'vue'
import type { JobDetail } from '../types/job'

const props = defineProps<{ job: JobDetail }>()

const opportunity = computed(() => props.job.artifacts?.['opportunity-report.json'] || {})
const gap = computed(() => props.job.artifacts?.['gap-check.json'] || {})
const qa = computed(() => props.job.artifacts?.['qa-report.json'] || {})
const distPath = computed(() => qa.value.checks?.dist_path || props.job.miniapp_path || '')

const targetPlatforms = computed<string[]>(() => {
  return gap.value.target_platforms || opportunity.value.target_platforms || ['wechat']
})

interface PlatformConfig {
  id: string
  name: string
  loginUrl: string
  uploadDir: string
  materials: string[]
  reviewNotes: string
}

const platformConfigs: Record<string, PlatformConfig> = {
  wechat: {
    id: 'wechat',
    name: '微信',
    loginUrl: 'https://mp.weixin.qq.com',
    uploadDir: '微信开发者工具 → 导入项目 → 选择 dist 目录',
    materials: ['小程序 AppID', '应用图标 (1024x1024)', '应用截图 (至少3张)', '隐私政策文档', '用户协议'],
    reviewNotes: '审核周期约 1-3 个工作日，注意避免敏感词和版权问题',
  },
  alipay: {
    id: 'alipay',
    name: '支付宝',
    loginUrl: 'https://open.alipay.com/develop/miniapp',
    uploadDir: '支付宝小程序开发者工具 → 上传 dist 目录',
    materials: ['小程序 APPID', '应用图标', '应用截图', '营业执照（企业）', '服务协议'],
    reviewNotes: '审核约 2-5 个工作日，需确保服务类目与内容一致',
  },
  douyin: {
    id: 'douyin',
    name: '抖音',
    loginUrl: 'https://developer.open-douyin.com',
    uploadDir: '抖音开发者工具 → 上传 dist 目录',
    materials: ['小程序 AppID', '应用图标', '功能截图', '测试账号（如需登录）', '资质证明'],
    reviewNotes: '审核约 1-2 个工作日，视频类内容需额外审核',
  },
  telegram: {
    id: 'telegram',
    name: 'Telegram',
    loginUrl: 'https://core.telegram.org/bots#botfather',
    uploadDir: '通过 BotFather 配置 Web App URL，部署 dist 到 HTTPS 服务器',
    materials: ['Bot Token', 'Web App URL (HTTPS)', '应用描述', '应用图标'],
    reviewNotes: '无需审核，配置完成即可上线，注意 HTTPS 证书有效性',
  },
}

const activePlatforms = computed(() => {
  return targetPlatforms.value.map(p => {
    const key = p.toLowerCase().replace('微信', 'wechat').replace('支付宝', 'alipay').replace('抖音', 'douyin')
    return platformConfigs[key] || platformConfigs['wechat']
  })
})

const copied = ref(false)
function copyDistPath() {
  if (!distPath.value) return
  navigator.clipboard.writeText(distPath.value)
  copied.value = true
  setTimeout(() => { copied.value = false }, 1500)
}
</script>

<template>
  <div class="human-steps">
    <div v-for="platform in activePlatforms" :key="platform.id" class="platform-section">
      <h3 class="platform-heading">{{ platform.name }} 小程序提交</h3>

      <div class="steps-list">
        <div class="step-card">
          <div class="step-num">1</div>
          <div class="step-body">
            <h4 class="step-title">登录开放平台</h4>
            <a :href="platform.loginUrl" target="_blank" class="step-link">{{ platform.loginUrl }}</a>
          </div>
        </div>

        <div class="step-card">
          <div class="step-num">2</div>
          <div class="step-body">
            <h4 class="step-title">准备上架材料</h4>
            <ul class="materials-list">
              <li v-for="m in platform.materials" :key="m">{{ m }}</li>
            </ul>
          </div>
        </div>

        <div class="step-card step-card--special">
          <div class="step-num step-num--highlight">3</div>
          <div class="step-body">
            <h4 class="step-title">导入构建目录</h4>
            <p class="step-desc">{{ platform.uploadDir }}</p>
            <div v-if="distPath" class="dist-box">
              <code class="dist-code">{{ distPath }}</code>
              <button class="copy-btn" @click="copyDistPath">
                {{ copied ? '已复制' : 'Copy Path' }}
              </button>
            </div>
          </div>
        </div>

        <div class="step-card">
          <div class="step-num">4</div>
          <div class="step-body">
            <h4 class="step-title">提交审核</h4>
            <p class="step-desc review-note">{{ platform.reviewNotes }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.human-steps {
  padding: 0;
}

.platform-section {
  margin-bottom: 36px;
}
.platform-section:last-child {
  margin-bottom: 0;
}

.platform-heading {
  font-size: 17px;
  font-weight: 600;
  color: var(--color-text-1);
  margin: 0 0 16px;
  padding-bottom: 10px;
  border-bottom: 1px solid var(--color-border);
}

.steps-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.step-card {
  display: flex;
  gap: 14px;
  background: var(--color-surface-solid);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-card);
  padding: 16px 20px;
}

.step-card--special {
  border: 1px solid rgba(0, 113, 227, 0.15);
}

.step-num {
  flex-shrink: 0;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--color-surface-solid);
  border: 2px solid var(--color-border);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
  color: var(--color-text-2);
}

.step-num--highlight {
  border-color: var(--color-blue);
  color: var(--color-blue);
  background: var(--color-blue-subtle, rgba(0, 113, 227, 0.06));
}

.step-body {
  flex: 1;
}

.step-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-1);
  margin: 0 0 4px;
}

.step-desc {
  font-size: 13px;
  color: var(--color-text-2);
  margin: 0;
  line-height: 1.4;
}

.step-link {
  font-size: 13px;
  color: var(--color-blue);
  text-decoration: none;
  word-break: break-all;
}
.step-link:hover {
  text-decoration: underline;
}

.materials-list {
  margin: 4px 0 0;
  padding-left: 16px;
  font-size: 13px;
  color: var(--color-text-2);
  line-height: 1.6;
}

.review-note {
  font-style: italic;
}

.dist-box {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 10px;
  padding: 10px 12px;
  background: rgba(0, 0, 0, 0.03);
  border-radius: var(--radius-sm);
}

.dist-code {
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--color-text-1);
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
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
  white-space: nowrap;
  transition: transform 0.12s var(--ease-apple), background 0.12s;
}
.copy-btn:hover {
  background: var(--color-blue-subtle, rgba(0, 113, 227, 0.06));
  transform: translateY(-1px);
}
.copy-btn:active {
  transform: scale(0.98);
}
</style>
