<!-- funny-video-viral template: short funny clip generation with share loop. -->
<template>
  <view class="container funny-video-viral">
    <view class="hero">
      <text class="title">__APP_NAME__</text>
      <text class="subtitle">__APP_SUBTITLE__</text>
      <text class="badge">Funny Clip · Meme Video</text>
    </view>

    <view class="video-stage">
      <view class="timeline">
        <view class="shot" v-for="n in 4" :key="n"><text>Scene {{ n }}</text></view>
      </view>
      <text class="stage-caption">Pick a joke script, generate a 15s shareable clip.</text>
    </view>

    <view class="actions">
      <button class="btn-primary" @click="goToForm">Generate Funny Clip</button>
      <button class="btn-share" @click="shareChallenge">Start Share Challenge</button>
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

function shareChallenge() {
  uni.showShareMenu({ withShareTicket: true } as any)
  uni.showToast({ title: 'Share to unlock more joke scripts', icon: 'none' })
}
</script>

<style scoped>
.container { padding: 40rpx; min-height: 100vh; background: linear-gradient(160deg, #fee2e2 0%, #fff7ed 56%, #f8f8f8 100%); }
.hero { text-align: center; padding: 56rpx 0 20rpx; }
.title { font-size: 44rpx; font-weight: bold; color: #111827; display: block; }
.subtitle { font-size: 28rpx; color: #6b7280; margin-top: 12rpx; display: block; }
.badge { display: inline-block; margin-top: 16rpx; padding: 6rpx 20rpx; background: #ef4444; color: #fff; border-radius: 999rpx; font-size: 22rpx; }
.video-stage { background: #fff; border-radius: 24rpx; padding: 28rpx; box-shadow: 0 12rpx 40rpx rgba(239, 68, 68, 0.14); }
.timeline { display: flex; gap: 12rpx; }
.shot { flex: 1; height: 128rpx; border-radius: 16rpx; background: #fff1f2; border: 2rpx dashed #fb7185; display: flex; align-items: center; justify-content: center; color: #be123c; font-size: 22rpx; }
.stage-caption { display: block; margin-top: 20rpx; color: #6b7280; font-size: 24rpx; text-align: center; }
.actions { text-align: center; margin: 32rpx 0; }
.btn-primary { background: #ef4444; color: #fff; border: none; border-radius: 14rpx; padding: 24rpx 48rpx; font-size: 30rpx; }
.btn-share { margin-top: 20rpx; background: #fff; color: #be123c; border: 2rpx solid #fb7185; border-radius: 14rpx; padding: 20rpx 48rpx; font-size: 28rpx; }
.features { padding: 20rpx 0; }
.feature-item { background: rgba(255,255,255,0.86); padding: 24rpx; margin-bottom: 16rpx; border-radius: 14rpx; }
.feature-text { font-size: 28rpx; color: #333; }
</style>
