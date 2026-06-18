<!--
  sticker-viral 模板 · index 首页（覆盖 base）。
  题材身份：AI 表情包/贴纸。强调"批量生成 → 打包分享到微信"。
  token 契约与 base 一致。
-->
<template>
  <view class="container sticker-viral">
    <view class="hero">
      <text class="title">__APP_NAME__</text>
      <text class="subtitle">__APP_SUBTITLE__</text>
      <text class="badge">表情包 · 批量生成</text>
    </view>
    <view class="sticker-grid">
      <view class="sticker-cell" v-for="n in 8" :key="n"><text class="s-ph">😀</text></view>
    </view>
    <view class="actions">
      <button class="btn-primary" @click="goToForm">输入文字，生成表情</button>
      <button class="btn-pack" @click="packShare">打包保存到微信</button>
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
function packShare() {
  uni.showToast({ title: '表情包已打包，去微信添加', icon: 'none' })
}
</script>

<style scoped>
.container { padding: 40rpx; min-height: 100vh; background: linear-gradient(160deg, #fef3c7 0%, #f8f8f8 60%); }
.hero { text-align: center; padding: 48rpx 0 16rpx; }
.title { font-size: 44rpx; font-weight: bold; color: #1d1d1f; display: block; }
.subtitle { font-size: 28rpx; color: #6e6e73; margin-top: 12rpx; display: block; }
.badge { display: inline-block; margin-top: 16rpx; padding: 6rpx 20rpx; background: #f59e0b; color: #fff; border-radius: 999rpx; font-size: 22rpx; }
.sticker-grid { display: flex; flex-wrap: wrap; gap: 12rpx; justify-content: center; margin: 24rpx 0; }
.sticker-cell { width: 120rpx; height: 120rpx; background: #fff7ed; border-radius: 16rpx; display: flex; align-items: center; justify-content: center; }
.s-ph { font-size: 48rpx; }
.actions { text-align: center; margin: 24rpx 0; }
.btn-primary { background: #f59e0b; color: #fff; border: none; border-radius: 12rpx; padding: 24rpx 48rpx; font-size: 30rpx; }
.btn-pack { margin-top: 20rpx; background: #fff; color: #b45309; border: 2rpx solid #f59e0b; border-radius: 12rpx; padding: 20rpx 48rpx; font-size: 28rpx; }
.features { padding: 20rpx; }
.feature-item { background: #fff; padding: 24rpx; margin-bottom: 16rpx; border-radius: 12rpx; }
.feature-text { font-size: 28rpx; color: #333; }
</style>
