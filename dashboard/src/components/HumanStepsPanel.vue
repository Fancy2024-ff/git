<script setup lang="ts">
import { computed, ref } from 'vue'
import type { JobDetail } from '../types/job'

const props = defineProps<{ job: JobDetail }>()

const qa = computed(() => props.job.artifacts?.['qa-report.json'] || {})
const distPath = computed(() => qa.value.checks?.dist_path || props.job.miniapp_path || '')

const copied = ref(false)

function copyDistPath() {
  if (!distPath.value) return
  navigator.clipboard.writeText(distPath.value)
  copied.value = true
  setTimeout(() => { copied.value = false }, 1500)
}

const steps = [
  { num: 1, title: '登录微信公众平台', desc: '使用管理员账号登录 mp.weixin.qq.com' },
  { num: 2, title: '创建/选择小程序', desc: '进入小程序管理，选择对应的小程序' },
  { num: 3, title: '导入构建目录', desc: '在微信开发者工具中导入 dist 目录', special: true },
  { num: 4, title: '上传代码', desc: '点击上传，填写版本号和备注信息' },
  { num: 5, title: '填写应用详情', desc: '补充应用介绍、分类、标签等信息' },
  { num: 6, title: '上传截图', desc: '根据文案截取对应界面截图并上传' },
  { num: 7, title: '配置隐私政策', desc: '填写隐私政策和用户协议相关内容' },
  { num: 8, title: '提交审核', desc: '确认所有信息后提交审核' },
  { num: 9, title: '记录审核结果', desc: '审核通过后记录并发布上线' },
]
</script>

<template>
  <div class="human-steps">
    <div class="timeline">
      <div class="timeline-line"></div>
      <div
        v-for="step in steps"
        :key="step.num"
        class="step"
        :class="{ 'step--special': step.special }"
      >
        <div class="step-indicator">
          <span class="step-num">{{ step.num }}</span>
        </div>
        <div class="step-content">
          <div class="step-header">
            <h4 class="step-title">{{ step.title }}</h4>
            <span class="step-badge">待处理</span>
          </div>
          <p class="step-desc">{{ step.desc }}</p>
          <div v-if="step.special && distPath" class="dist-box">
            <code class="dist-code">{{ distPath }}</code>
            <button class="copy-btn" @click="copyDistPath">
              {{ copied ? 'Copied!' : 'Copy Path' }}
            </button>
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

.timeline {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 0;
}

.timeline-line {
  position: absolute;
  left: 17px;
  top: 20px;
  bottom: 20px;
  width: 2px;
  background: var(--color-border);
  z-index: 0;
}

.step {
  display: flex;
  gap: 16px;
  position: relative;
  z-index: 1;
  padding: 12px 0;
}

.step-indicator {
  flex-shrink: 0;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: var(--color-surface-solid);
  border: 2px solid var(--color-border);
  display: flex;
  align-items: center;
  justify-content: center;
}

.step--special .step-indicator {
  border-color: var(--color-blue);
  background: var(--color-blue-subtle);
}

.step-num {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-2);
}

.step--special .step-num {
  color: var(--color-blue);
}

.step-content {
  flex: 1;
  background: var(--color-surface-solid);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-card);
  padding: 16px 20px;
}

.step--special .step-content {
  border: 1px solid rgba(0, 113, 227, 0.15);
}

.step-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.step-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-1);
  margin: 0;
}

.step-badge {
  font-size: 11px;
  font-weight: 500;
  color: var(--color-orange);
  background: var(--color-orange-subtle);
  padding: 2px 8px;
  border-radius: 980px;
  white-space: nowrap;
}

.step-desc {
  font-size: 13px;
  color: var(--color-text-2);
  margin: 6px 0 0;
  line-height: 1.4;
}

.dist-box {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 12px;
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
  background: var(--color-blue-subtle);
  transform: translateY(-1px);
}
.copy-btn:active {
  transform: scale(0.98);
}
</style>
