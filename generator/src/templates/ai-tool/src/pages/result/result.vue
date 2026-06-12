<template>
  <view class="container">
    <view class="result-card">
      <text class="result-title">处理结果</text>
      <view class="result-content">
        <text class="result-text">{{ resultText }}</text>
      </view>
      <view class="result-actions">
        <button class="btn-copy" @click="copyResult">复制结果</button>
        <button class="btn-back" @click="goBack">返回</button>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'

const resultText = ref('AI 处理结果将在这里展示。')

onLoad((options: any) => {
  if (options?.input) {
    resultText.value = `已处理: ${decodeURIComponent(options.input).substring(0, 100)}...\n\n结果将在 API 接入后展示。`
  }
})

function copyResult() { uni.setClipboardData({ data: resultText.value }) }
function goBack() { uni.navigateBack() }
</script>

<style scoped>
.container { padding: 32rpx; min-height: 100vh; background: #f5f5f7; }
.result-card { background: #fff; border-radius: 16rpx; padding: 32rpx; }
.result-title { font-size: 34rpx; font-weight: 600; color: #1d1d1f; margin-bottom: 24rpx; display: block; }
.result-content { background: #f5f5f7; border-radius: 12rpx; padding: 24rpx; min-height: 200rpx; margin-bottom: 24rpx; }
.result-text { font-size: 28rpx; color: #333; white-space: pre-wrap; }
.result-actions { display: flex; gap: 16rpx; }
.btn-copy { flex: 1; background: #0071e3; color: #fff; border: none; border-radius: 12rpx; font-size: 28rpx; }
.btn-back { flex: 1; background: #f5f5f7; color: #333; border: none; border-radius: 12rpx; font-size: 28rpx; }
</style>
