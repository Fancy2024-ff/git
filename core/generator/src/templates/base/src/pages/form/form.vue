<!--
  Data-injected template page (single source of the form page structure).
  The placeholder token below is substituted by BOTH generation consumers
  (core/pipeline/runner.py and the Node page-builder) via the shared token
  contract. Do not re-author this markup in Python.
-->
<template>
  <view class="container">
    <view class="form-card">
      <text class="form-title">__APP_FEATURE_TITLE__</text>
      <textarea class="input-area" v-model="inputText" placeholder="请输入内容..." />
      <button class="btn-submit" @click="handleSubmit" :loading="loading">开始处理</button>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const inputText = ref('')
const loading = ref(false)

async function handleSubmit() {
  if (!inputText.value.trim()) {
    uni.showToast({ title: '请输入内容', icon: 'none' })
    return
  }
  loading.value = true
  setTimeout(() => {
    loading.value = false
    uni.navigateTo({ url: '/pages/result/result?input=' + encodeURIComponent(inputText.value) })
  }, 1500)
}
</script>

<style scoped>
.container { padding: 32rpx; min-height: 100vh; background: #f5f5f7; }
.form-card { background: #fff; border-radius: 16rpx; padding: 32rpx; }
.form-title { font-size: 34rpx; font-weight: 600; color: #1d1d1f; margin-bottom: 24rpx; display: block; }
.input-area { width: 100%; min-height: 240rpx; padding: 20rpx; border: 1rpx solid #e8e8ed; border-radius: 12rpx; font-size: 28rpx; }
.btn-submit { margin-top: 32rpx; background: #0071e3; color: #fff; border: none; border-radius: 12rpx; font-size: 30rpx; }
</style>
