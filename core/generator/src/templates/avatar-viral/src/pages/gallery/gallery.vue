<!--
  avatar-viral 签名页：头像结果画廊。模板身份标识页（base 没有）。
-->
<template>
  <view class="container">
    <text class="page-title">我的头像</text>
    <view class="gallery">
      <view class="cell" v-for="n in 6" :key="n">
        <text class="cell-ph">样式 {{ n }}</text>
      </view>
    </view>
    <button class="btn-save" @click="saveAndShare">保存并分享</button>
  </view>
</template>

<script setup lang="ts">
function saveAndShare() {
  uni.showToast({ title: '分享卡片已生成', icon: 'none' })
}
</script>

<style scoped>
.container { padding: 32rpx; min-height: 100vh; background: #faf5ff; }
.page-title { font-size: 34rpx; font-weight: 600; color: #1d1d1f; display: block; margin-bottom: 24rpx; }
.gallery { display: flex; flex-wrap: wrap; gap: 16rpx; }
.cell { width: 30%; height: 200rpx; background: #ede9fe; border-radius: 12rpx; display: flex; align-items: center; justify-content: center; }
.cell-ph { font-size: 24rpx; color: #7c3aed; }
.btn-save { margin-top: 32rpx; background: #7c3aed; color: #fff; border: none; border-radius: 12rpx; font-size: 30rpx; }
</style>
