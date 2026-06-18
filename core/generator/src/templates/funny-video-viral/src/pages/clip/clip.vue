<template>
  <view class="page">
    <text class="title">Clip Studio</text>
    <text class="desc">Arrange scenes, captions and punchlines before sharing.</text>
    <button class="btn" @click="preview">Preview Clip</button>
  </view>
</template>

<script setup lang="ts">
function preview() {
  uni.showToast({ title: 'Preview generated', icon: 'none' })
}
</script>

<style scoped>
.page { min-height: 100vh; padding: 48rpx; background: #fff7ed; }
.title { display: block; font-size: 42rpx; font-weight: 700; color: #111827; }
.desc { display: block; margin: 16rpx 0 40rpx; color: #6b7280; font-size: 28rpx; }
.btn { background: #ef4444; color: #fff; border-radius: 14rpx; }
</style>
