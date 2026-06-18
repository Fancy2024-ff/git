<template>
  <view class="container">
    <view class="profile-header">
      <view class="avatar">
        <text class="avatar-text">U</text>
      </view>
      <text class="username">未登录</text>
      <button class="btn-login" @click="login">微信登录</button>
    </view>
    <view class="menu-list">
      <view class="menu-item"><text>历史记录</text><text class="arrow">→</text></view>
      <view class="menu-item"><text>使用额度</text><text class="quota">3/3 次</text></view>
      <view class="menu-item"><text>升级 Pro</text><text class="arrow">→</text></view>
      <view class="menu-item"><text>意见反馈</text><text class="arrow">→</text></view>
      <view class="menu-item"><text>关于</text><text class="arrow">→</text></view>
    </view>
  </view>
</template>

<script setup lang="ts">
function login() {
  uni.showToast({ title: '登录功能开发中', icon: 'none' })
}
</script>

<style scoped>
.container { padding: 32rpx; min-height: 100vh; background: #f5f5f7; }
.profile-header { background: #fff; border-radius: 16rpx; padding: 40rpx; text-align: center; margin-bottom: 24rpx; }
.avatar { width: 100rpx; height: 100rpx; background: #e8e8ed; border-radius: 50%; margin: 0 auto 16rpx; display: flex; align-items: center; justify-content: center; }
.avatar-text { font-size: 36rpx; color: #6e6e73; }
.username { font-size: 30rpx; color: #1d1d1f; display: block; margin-bottom: 16rpx; }
.btn-login { background: #0071e3; color: #fff; border: none; border-radius: 12rpx; font-size: 28rpx; padding: 16rpx 40rpx; }
.menu-list { background: #fff; border-radius: 16rpx; overflow: hidden; }
.menu-item { display: flex; justify-content: space-between; padding: 28rpx 32rpx; border-bottom: 1rpx solid #f0f0f0; font-size: 28rpx; color: #333; }
.menu-item:last-child { border-bottom: none; }
.arrow { color: #aeaeb2; }
.quota { color: #0071e3; font-size: 26rpx; }
</style>
