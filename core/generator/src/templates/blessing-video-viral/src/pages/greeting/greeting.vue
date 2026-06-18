<template>
  <view class="page">
    <text class="title">Greeting Studio</text>
    <text class="desc">Choose names, festival style and send-ready copy.</text>
    <button class="btn" @click="render">Render Greeting</button>
  </view>
</template>

<script setup lang="ts">
function render() {
  uni.showToast({ title: 'Greeting rendered', icon: 'none' })
}
</script>

<style scoped>
.page { min-height: 100vh; padding: 48rpx; background: #fef3c7; }
.title { display: block; font-size: 42rpx; font-weight: 700; color: #3f2a12; }
.desc { display: block; margin: 16rpx 0 40rpx; color: #7c2d12; font-size: 28rpx; }
.btn { background: #d97706; color: #fff; border-radius: 14rpx; }
</style>
