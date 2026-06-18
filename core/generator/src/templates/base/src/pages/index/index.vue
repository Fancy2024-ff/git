<!--
  Data-injected template page (single source of the index page structure).
  Placeholder tokens below are substituted by BOTH generation consumers
  (core/pipeline/runner.py and core/generator/src/codegen/page-builder.ts)
  via the shared token contract. Do not re-author this markup in Python.
-->
<template>
  <view class="container">
    <view class="hero">
      <text class="title">__APP_NAME__</text>
      <text class="subtitle">__APP_SUBTITLE__</text>
    </view>
    <view class="actions">
      <button class="btn-primary" @click="goToForm">开始使用</button>
    </view>
    <view class="features">
      <view class="feature-item" v-for="(f, i) in features" :key="i">
        <text class="feature-text">{{ f }}</text>
      </view>
    </view>
  </view>
</template>

<script setup lang="ts">
const features = __APP_FEATURES_JSON__

function goToForm() {
  uni.navigateTo({ url: '/pages/form/form' })
}
</script>

<style scoped>
.container { padding: 40rpx; min-height: 100vh; background: #f8f8f8; }
.hero { text-align: center; padding: 80rpx 0 40rpx; }
.title { font-size: 44rpx; font-weight: bold; color: #1d1d1f; display: block; }
.subtitle { font-size: 28rpx; color: #6e6e73; margin-top: 12rpx; display: block; }
.actions { text-align: center; margin: 40rpx 0; }
.btn-primary { background: #0071e3; color: #fff; border: none; border-radius: 12rpx; padding: 24rpx 60rpx; font-size: 30rpx; }
.features { padding: 20rpx; }
.feature-item { background: #fff; padding: 24rpx; margin-bottom: 16rpx; border-radius: 12rpx; }
.feature-text { font-size: 28rpx; color: #333; }
</style>
