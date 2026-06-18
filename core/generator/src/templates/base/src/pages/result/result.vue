<template>
  <view class="container">
    <view class="result-card">
      <text class="result-title">处理结果</text>
      <view class="result-content">
        <text class="result-text">{{ resultText }}</text>
        <view v-if="!unlocked" class="watermark">预览 · 分享后解锁高清无水印</view>
      </view>
      <!-- 分享解锁 / 裂变钩子：分享到群聊或朋友圈后解锁高清、去水印、更多模板 -->
      <view v-if="!unlocked" class="unlock-box">
        <text class="unlock-tip">分享给好友即可解锁高清无水印结果，并解锁更多模板</text>
        <button class="btn-unlock" open-type="share" @click="shareToUnlock">分享解锁高清</button>
      </view>
      <view class="result-actions">
        <button class="btn-copy" @click="copyResult">复制结果</button>
        <button class="btn-share" open-type="share">分享作品</button>
        <button class="btn-back" @click="goBack">返回</button>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'

const resultText = ref('AI 处理结果将在这里展示。连接后端 API 后将返回真实结果。')
const unlocked = ref(false)

onLoad((options: any) => {
  if (options?.input) {
    resultText.value = `已处理输入内容（${decodeURIComponent(options.input).length} 字）\n\nAI 分析结果将在后端 API 接入后展示。`
  }
})

function copyResult() {
  uni.setClipboardData({ data: resultText.value })
}

// 分享解锁：用户分享后解锁高清/去水印结果（裂变激励机制）
function shareToUnlock() {
  unlocked.value = true
  uni.showToast({ title: '已解锁高清无水印', icon: 'success' })
}

function goBack() {
  uni.navigateBack()
}
</script>

<style scoped>
.container { padding: 32rpx; min-height: 100vh; background: #f5f5f7; }
.result-card { background: #fff; border-radius: 16rpx; padding: 32rpx; }
.result-title { font-size: 34rpx; font-weight: 600; color: #1d1d1f; margin-bottom: 24rpx; display: block; }
.result-content { background: #f5f5f7; border-radius: 12rpx; padding: 24rpx; min-height: 200rpx; margin-bottom: 24rpx; position: relative; }
.result-text { font-size: 28rpx; color: #333; white-space: pre-wrap; }
.watermark { margin-top: 16rpx; font-size: 22rpx; color: #b0b0b0; }
.unlock-box { background: #fff7e6; border: 1rpx solid #ffd591; border-radius: 12rpx; padding: 24rpx; margin-bottom: 24rpx; }
.unlock-tip { font-size: 24rpx; color: #d46b08; display: block; margin-bottom: 16rpx; }
.btn-unlock { background: #fa8c16; color: #fff; border: none; border-radius: 12rpx; font-size: 28rpx; }
.result-actions { display: flex; gap: 16rpx; }
.btn-copy { flex: 1; background: #0071e3; color: #fff; border: none; border-radius: 12rpx; font-size: 28rpx; }
.btn-share { flex: 1; background: #07c160; color: #fff; border: none; border-radius: 12rpx; font-size: 28rpx; }
.btn-back { flex: 1; background: #f5f5f7; color: #333; border: none; border-radius: 12rpx; font-size: 28rpx; }
</style>
