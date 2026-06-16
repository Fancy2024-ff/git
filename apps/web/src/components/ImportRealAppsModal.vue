<script setup lang="ts">
import { ref } from 'vue'
import { api } from '../services/api'

const emit = defineEmits<{
  close: []
  saved: [count: number]
}>()

const jsonText = ref('')
const saving = ref(false)
const fieldErrors = ref<{ index: number; field: string; message: string }[]>([])
const generalError = ref('')
const savedCount = ref<number | null>(null)

const PLACEHOLDER = `[
  {
    "name": "Example AI App",
    "name_cn": "示例 AI 应用",
    "source": "App Store",
    "category": "Productivity",
    "description": "An AI-powered tool.",
    "description_cn": "AI 驱动的工具。",
    "features": ["AI task"],
    "features_cn": ["AI 任务"],
    "downloads": 3500000,
    "rating": 4.7,
    "review_count": 12500,
    "monetization": "freemium"
  }
]`

function reset() {
  fieldErrors.value = []
  generalError.value = ''
  savedCount.value = null
}

async function save() {
  reset()
  saving.value = true
  let parsed: unknown
  try {
    parsed = JSON.parse(jsonText.value)
  } catch (e: any) {
    generalError.value = 'JSON 格式错误，无法解析：' + e.message
    saving.value = false
    return
  }
  if (!Array.isArray(parsed)) {
    generalError.value = '请粘贴一个 JSON 数组（最外层是 [ ... ]）。'
    saving.value = false
    return
  }
  try {
    const res = await api.saveRealInputs(parsed as any[])
    savedCount.value = res.saved
    emit('saved', res.saved)
  } catch (e: any) {
    // 后端 400 返回 { message, errors: [{ index, errors: [{ field, message }] }] }
    const detail = e?.detail
    if (detail?.errors && Array.isArray(detail.errors)) {
      const flat: { index: number; field: string; message: string }[] = []
      for (const item of detail.errors) {
        for (const err of item.errors || []) {
          flat.push({ index: item.index, field: err.field || '(根)', message: err.message })
        }
      }
      fieldErrors.value = flat
      generalError.value = detail.message || '校验失败，请修正下列字段。'
    } else {
      generalError.value = e?.message || '保存失败。'
    }
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div class="modal-overlay" @click.self="emit('close')">
    <div class="modal">
      <div class="modal-header">
        <h3 class="modal-title">导入真实 App</h3>
        <button class="close-btn" @click="emit('close')">✕</button>
      </div>

      <p class="modal-hint">
        粘贴一个 App 数据的 JSON 数组，保存后将写入
        <code>data/inputs/real/apps.json</code>，随后可切换到「Real / 生产运行」并启动。
      </p>

      <div v-if="savedCount !== null" class="success-block">
        <p class="success-title">已导入 {{ savedCount }} 个 App</p>
        <p class="success-line">保存路径：<code>data/inputs/real/apps.json</code></p>
        <p class="success-line">下一步：切换顶部「Real / 生产运行」并点击「启动生产运行」。</p>
      </div>

      <template v-else>
        <textarea
          v-model="jsonText"
          class="json-input"
          :placeholder="PLACEHOLDER"
          spellcheck="false"
        ></textarea>

        <div v-if="generalError" class="error-block">
          <p class="error-title">{{ generalError }}</p>
          <ul v-if="fieldErrors.length" class="error-list">
            <li v-for="(err, i) in fieldErrors" :key="i">
              第 {{ err.index + 1 }} 项 · <code>{{ err.field }}</code>：{{ err.message }}
            </li>
          </ul>
        </div>

        <div class="modal-footer">
          <button class="btn-cancel" @click="emit('close')">取消</button>
          <button class="btn-save" :disabled="saving || !jsonText.trim()" @click="save">
            {{ saving ? '保存中...' : '保存' }}
          </button>
        </div>
      </template>

      <div v-if="savedCount !== null" class="modal-footer">
        <button class="btn-save" @click="emit('close')">完成</button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
}
.modal {
  background: var(--color-surface-solid);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
  width: min(640px, 92vw);
  max-height: 86vh;
  overflow-y: auto;
  padding: 24px;
}
.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.modal-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text-1);
}
.close-btn {
  background: none;
  border: none;
  font-size: 16px;
  color: var(--color-text-3);
  cursor: pointer;
}
.modal-hint {
  font-size: 13px;
  color: var(--color-text-2);
  line-height: 1.5;
  margin: 12px 0 16px;
}
.modal-hint code,
.success-line code {
  font-family: var(--font-mono);
  font-size: 12px;
  background: var(--color-blue-subtle);
  color: var(--color-blue);
  padding: 1px 6px;
  border-radius: 4px;
}
.json-input {
  width: 100%;
  min-height: 260px;
  font-family: var(--font-mono);
  font-size: 12px;
  line-height: 1.5;
  padding: 12px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  resize: vertical;
  box-sizing: border-box;
}
.error-block {
  margin-top: 12px;
  padding: 12px;
  background: rgba(255, 59, 48, 0.05);
  border: 1px solid rgba(255, 59, 48, 0.15);
  border-radius: var(--radius-sm);
}
.error-title {
  font-size: 13px;
  font-weight: 600;
  color: #c41e16;
}
.error-list {
  margin: 8px 0 0;
  padding-left: 18px;
  font-size: 12px;
  color: #991b1b;
}
.error-list li { padding: 2px 0; }
.error-list code {
  font-family: var(--font-mono);
  background: rgba(255, 59, 48, 0.08);
  padding: 0 4px;
  border-radius: 3px;
}
.success-block {
  margin: 8px 0 16px;
  padding: 16px;
  background: var(--color-green-subtle);
  border-radius: var(--radius-sm);
}
.success-title {
  font-size: 15px;
  font-weight: 600;
  color: #166534;
}
.success-line {
  font-size: 13px;
  color: var(--color-text-2);
  margin-top: 6px;
}
.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 16px;
}
.btn-cancel {
  font-size: 13px;
  padding: 8px 16px;
  border-radius: 980px;
  border: 1px solid var(--color-border);
  background: transparent;
  color: var(--color-text-2);
  cursor: pointer;
}
.btn-save {
  font-size: 13px;
  font-weight: 500;
  padding: 8px 18px;
  border-radius: 980px;
  border: none;
  background: var(--color-blue);
  color: #fff;
  cursor: pointer;
}
.btn-save:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
