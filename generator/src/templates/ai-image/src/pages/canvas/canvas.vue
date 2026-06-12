<template>
  <view class="container">
    <view class="upload-card">
      <text class="title">上传图片</text>
      <view class="upload-area" @click="chooseImage">
        <image v-if="imageUrl" :src="imageUrl" mode="aspectFit" class="preview-img" />
        <text v-else class="upload-hint">点击选择图片</text>
      </view>
      <button class="btn-process" :disabled="!imageUrl" @click="processImage">开始处理</button>
    </view>
    <view v-if="resultUrl" class="result-card">
      <text class="result-title">处理结果</text>
      <image :src="resultUrl" mode="widthFix" class="result-img" />
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const imageUrl = ref('')
const resultUrl = ref('')

function chooseImage() {
  uni.chooseImage({
    count: 1,
    success: (res) => { imageUrl.value = res.tempFilePaths[0] }
  })
}

function processImage() {
  uni.showLoading({ title: '处理中...' })
  setTimeout(() => {
    uni.hideLoading()
    resultUrl.value = imageUrl.value
    uni.showToast({ title: 'AI 处理将在 API 接入后生效', icon: 'none' })
  }, 1500)
}
</script>

<style scoped>
.container { padding: 32rpx; min-height: 100vh; background: #f5f5f7; }
.upload-card { background: #fff; border-radius: 16rpx; padding: 32rpx; margin-bottom: 24rpx; }
.title { font-size: 34rpx; font-weight: 600; color: #1d1d1f; display: block; margin-bottom: 24rpx; }
.upload-area { width: 100%; height: 400rpx; background: #f5f5f7; border-radius: 12rpx; display: flex; align-items: center; justify-content: center; border: 2rpx dashed #d2d2d7; }
.preview-img { width: 100%; height: 100%; border-radius: 12rpx; }
.upload-hint { font-size: 28rpx; color: #aeaeb2; }
.btn-process { margin-top: 24rpx; background: #0071e3; color: #fff; border: none; border-radius: 12rpx; font-size: 30rpx; }
.btn-process:disabled { opacity: 0.5; }
.result-card { background: #fff; border-radius: 16rpx; padding: 32rpx; }
.result-title { font-size: 28rpx; font-weight: 600; color: #1d1d1f; display: block; margin-bottom: 16rpx; }
.result-img { width: 100%; border-radius: 12rpx; }
</style>
