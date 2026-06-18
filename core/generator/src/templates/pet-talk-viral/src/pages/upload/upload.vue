<!--
  pet-talk-viral 签名页：素材上传 + 配音脚本。模板身份标识页（base 没有）。
-->
<template>
  <view class="container">
    <text class="page-title">上传素材</text>
    <view class="upload-box" @click="pickPhoto">
      <text class="upload-ph">点击上传宠物照片</text>
    </view>
    <text class="label">想让它说什么</text>
    <textarea class="script-input" v-model="script" placeholder="例如：主人，该喂饭啦~" />
    <button class="btn-generate" @click="generate" :loading="loading">生成说话视频</button>
  </view>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const script = ref('')
const loading = ref(false)

function pickPhoto() {
  uni.chooseImage({ count: 1 } as any)
}
function generate() {
  loading.value = true
  setTimeout(() => {
    loading.value = false
    uni.navigateTo({ url: '/pages/result/result' })
  }, 1500)
}
</script>

<style scoped>
.container { padding: 32rpx; min-height: 100vh; background: #f0fdf4; }
.page-title { font-size: 34rpx; font-weight: 600; color: #1d1d1f; display: block; margin-bottom: 24rpx; }
.upload-box { height: 280rpx; background: #fff; border: 4rpx dashed #16a34a; border-radius: 16rpx; display: flex; align-items: center; justify-content: center; }
.upload-ph { font-size: 28rpx; color: #16a34a; }
.label { display: block; margin: 28rpx 0 12rpx; font-size: 28rpx; color: #333; }
.script-input { width: 100%; min-height: 160rpx; padding: 20rpx; background: #fff; border-radius: 12rpx; font-size: 28rpx; }
.btn-generate { margin-top: 32rpx; background: #16a34a; color: #fff; border: none; border-radius: 12rpx; font-size: 30rpx; }
</style>
