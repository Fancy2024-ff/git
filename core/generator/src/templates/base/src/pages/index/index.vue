<template>
  <view class="container">
    <view class="hero">
      <text class="title">Welcome</text>
      <text class="subtitle">Mini App Template</text>
    </view>
    <button class="btn-primary" @click="navigateTo">开始使用</button>
  </view>
</template>

<script setup lang="ts">
function navigateTo() {
  uni.showToast({ title: '功能开发中', icon: 'none' })
}
</script>

<style scoped>
.container { padding: 40rpx; min-height: 100vh; background: #f8f8f8; display: flex; flex-direction: column; align-items: center; justify-content: center; }
.hero { text-align: center; margin-bottom: 60rpx; }
.title { font-size: 48rpx; font-weight: bold; color: #1d1d1f; display: block; }
.subtitle { font-size: 28rpx; color: #6e6e73; margin-top: 12rpx; display: block; }
.btn-primary { background: #0071e3; color: #fff; border: none; border-radius: 12rpx; padding: 24rpx 60rpx; font-size: 30rpx; }
</style>
