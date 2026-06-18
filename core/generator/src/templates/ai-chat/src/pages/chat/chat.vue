<template>
  <view class="container">
    <scroll-view class="chat-area" scroll-y :scroll-top="scrollTop" :scroll-with-animation="true">
      <view v-for="(msg, i) in messages" :key="i" class="message" :class="msg.role === 'user' ? 'msg-user' : 'msg-ai'">
        <text class="msg-text">{{ msg.content }}</text>
      </view>
    </scroll-view>
    <view class="input-bar">
      <input class="chat-input" v-model="inputText" placeholder="输入消息..." @confirm="sendMessage" />
      <button class="send-btn" @click="sendMessage">发送</button>
    </view>
  </view>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const messages = ref<{ role: string; content: string }[]>([
  { role: 'ai', content: '你好！有什么我可以帮你的吗？' }
])
const inputText = ref('')
const scrollTop = ref(0)

function sendMessage() {
  if (!inputText.value.trim()) return
  messages.value.push({ role: 'user', content: inputText.value })
  const userMsg = inputText.value
  inputText.value = ''
  scrollTop.value = 99999
  setTimeout(() => {
    messages.value.push({ role: 'ai', content: `收到: "${userMsg}"\n\nAI 回复将在 API 接入后展示。` })
    scrollTop.value = 99999
  }, 800)
}
</script>

<style scoped>
.container { display: flex; flex-direction: column; height: 100vh; background: #f5f5f7; }
.chat-area { flex: 1; padding: 24rpx; }
.message { margin-bottom: 20rpx; max-width: 80%; }
.msg-user { margin-left: auto; }
.msg-ai { margin-right: auto; }
.msg-text { display: inline-block; padding: 16rpx 24rpx; border-radius: 16rpx; font-size: 28rpx; line-height: 1.5; }
.msg-user .msg-text { background: #0071e3; color: #fff; }
.msg-ai .msg-text { background: #fff; color: #333; }
.input-bar { display: flex; gap: 12rpx; padding: 16rpx 24rpx; background: #fff; border-top: 1rpx solid #e8e8ed; }
.chat-input { flex: 1; height: 72rpx; padding: 0 20rpx; border: 1rpx solid #e8e8ed; border-radius: 36rpx; font-size: 28rpx; }
.send-btn { background: #0071e3; color: #fff; border: none; border-radius: 36rpx; padding: 0 32rpx; font-size: 28rpx; height: 72rpx; line-height: 72rpx; }
</style>
