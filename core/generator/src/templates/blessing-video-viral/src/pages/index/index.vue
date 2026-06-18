<!-- blessing-video-viral template: festival greeting video/card with forwarding loop. -->
<template>
  <view class="container blessing-video-viral">
    <view class="hero">
      <text class="title">__APP_NAME__</text>
      <text class="subtitle">__APP_SUBTITLE__</text>
      <text class="badge">Greeting Video · Blessing Card</text>
    </view>

    <view class="card-preview">
      <text class="card-title">Best Wishes</text>
      <text class="card-name">To Someone Special</text>
      <text class="card-copy">Create a named blessing video and send it in one tap.</text>
    </view>

    <view class="actions">
      <button class="btn-primary" @click="goToForm">Make Blessing Video</button>
      <button class="btn-share" @click="shareBlessing">Send to Family Group</button>
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

function shareBlessing() {
  uni.showShareMenu({ withShareTicket: true } as any)
  uni.showToast({ title: 'Share to unlock festival styles', icon: 'none' })
}
</script>

<style scoped>
.container { padding: 40rpx; min-height: 100vh; background: linear-gradient(160deg, #fff7ed 0%, #fef9c3 52%, #f8f8f8 100%); }
.hero { text-align: center; padding: 56rpx 0 20rpx; }
.title { font-size: 44rpx; font-weight: bold; color: #3f2a12; display: block; }
.subtitle { font-size: 28rpx; color: #7c2d12; margin-top: 12rpx; display: block; }
.badge { display: inline-block; margin-top: 16rpx; padding: 6rpx 20rpx; background: #d97706; color: #fff; border-radius: 999rpx; font-size: 22rpx; }
.card-preview { margin: 28rpx 0; padding: 48rpx 32rpx; border-radius: 28rpx; background: radial-gradient(circle at top, #fef3c7, #fff); box-shadow: 0 16rpx 46rpx rgba(217, 119, 6, 0.16); text-align: center; border: 2rpx solid #fbbf24; }
.card-title { display: block; font-size: 42rpx; font-weight: 800; color: #92400e; }
.card-name { display: block; margin-top: 18rpx; font-size: 30rpx; color: #b45309; }
.card-copy { display: block; margin-top: 18rpx; font-size: 24rpx; color: #78716c; }
.actions { text-align: center; margin: 32rpx 0; }
.btn-primary { background: #d97706; color: #fff; border: none; border-radius: 14rpx; padding: 24rpx 48rpx; font-size: 30rpx; }
.btn-share { margin-top: 20rpx; background: #fff; color: #92400e; border: 2rpx solid #f59e0b; border-radius: 14rpx; padding: 20rpx 48rpx; font-size: 28rpx; }
.features { padding: 20rpx 0; }
.feature-item { background: rgba(255,255,255,0.86); padding: 24rpx; margin-bottom: 16rpx; border-radius: 14rpx; }
.feature-text { font-size: 28rpx; color: #333; }
</style>
