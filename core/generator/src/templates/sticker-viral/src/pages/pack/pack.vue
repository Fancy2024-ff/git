<!--
  sticker-viral 签名页：表情包批量打包页。模板身份标识页（base 没有）。
-->
<template>
  <view class="container">
    <text class="page-title">表情包合集</text>
    <view class="pack-grid">
      <view class="pack-cell" v-for="n in 9" :key="n"><text class="p-ph">😎</text></view>
    </view>
    <view class="pack-actions">
      <button class="btn-pack" @click="exportPack">导出表情包</button>
      <button class="btn-share" @click="shareToGroup">分享到群</button>
    </view>
  </view>
</template>

<script setup lang="ts">
function exportPack() {
  uni.showToast({ title: '已导出，可添加到微信表情', icon: 'none' })
}
function shareToGroup() {
  uni.showToast({ title: '分享卡片已生成', icon: 'none' })
}
</script>

<style scoped>
.container { padding: 32rpx; min-height: 100vh; background: #fffbeb; }
.page-title { font-size: 34rpx; font-weight: 600; color: #1d1d1f; display: block; margin-bottom: 24rpx; }
.pack-grid { display: flex; flex-wrap: wrap; gap: 14rpx; }
.pack-cell { width: 30%; height: 160rpx; background: #fff7ed; border-radius: 12rpx; display: flex; align-items: center; justify-content: center; }
.p-ph { font-size: 56rpx; }
.pack-actions { display: flex; gap: 16rpx; margin-top: 32rpx; }
.btn-pack { flex: 1; background: #f59e0b; color: #fff; border: none; border-radius: 12rpx; font-size: 28rpx; }
.btn-share { flex: 1; background: #fff; color: #b45309; border: 2rpx solid #f59e0b; border-radius: 12rpx; font-size: 28rpx; }
</style>
