<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { api } from '../services/api'

const jsonInput = ref('')
const saved = ref(false)
const savedCount = ref(0)
const validationError = ref('')
const existingApps = ref<any[]>([])
const loading = ref(false)

const exampleJson = `[
  {
    "name": "Example AI App",
    "name_cn": "示例 AI 应用",
    "source": "App Store",
    "category": "Productivity",
    "description": "An AI-powered productivity tool.",
    "rating": 4.7,
    "review_count": 12500,
    "downloads": 3500000,
    "monetization": "freemium",
    "features": ["AI task completion", "Smart scheduling"],
    "keywords": ["AI", "productivity"]
  }
]`

function validate(data: any): string {
  if (!Array.isArray(data)) return '数据必须是 JSON 数组格式'
  if (data.length === 0) return '至少需要一条 App 数据'
  for (let i = 0; i < data.length; i++) {
    const item = data[i]
    const n = i + 1
    if (!item || typeof item !== 'object') return `第 ${n} 项必须是对象`
    if (!item.name) return `第 ${n} 项缺少 name 字段`
    if (!item.source) return `第 ${n} 项缺少 source 字段`
    if (!item.category) return `第 ${n} 项缺少 category 字段`
    if (!item.description && !item.description_cn)
      return `第 ${n} 项缺少 description 或 description_cn`
    const feats = item.features || item.features_cn
    if (!Array.isArray(feats) || feats.length === 0)
      return `第 ${n} 项缺少 features 或 features_cn（至少一项）`
  }
  return ''
}

async function saveData() {
  validationError.value = ''
  saved.value = false
  let parsed: any
  try {
    parsed = JSON.parse(jsonInput.value)
  } catch {
    validationError.value = 'JSON 格式无效，请检查语法'
    return
  }
  const err = validate(parsed)
  if (err) {
    validationError.value = err
    return
  }
  loading.value = true
  try {
    const res = await api.saveRealInputs(parsed)
    saved.value = true
    savedCount.value = res?.saved ?? parsed.length
    jsonInput.value = ''
    await loadExisting()
  } catch (e: any) {
    validationError.value = formatBackendError(e)
  }
  loading.value = false
}

function formatBackendError(e: any): string {
  // api.post throws Error('<status> <statusText>'); try to surface detail.
  const detail = e?.detail
  if (detail?.errors?.length) {
    const lines = detail.errors.map((item: any) => {
      const fields = (item.errors || []).map((x: any) => `${x.field || '?'}: ${x.message}`).join('; ')
      return `第 ${item.index + 1} 项 — ${fields}`
    })
    return `后端校验失败:\n${lines.join('\n')}`
  }
  return `保存失败: ${e?.message || e}`
}

async function loadExisting() {
  try {
    const res = await api.getRealInputs()
    existingApps.value = res.apps || []
  } catch {}
}

onMounted(loadExisting)
</script>

<template>
  <div class="import-panel">
    <div class="header">
      <h2 class="title">导入真实 App 数据</h2>
      <p class="subtitle">粘贴 JSON 格式的 App 数据，保存后可使用 Real Mode 运行流水线</p>
    </div>

    <div class="input-section">
      <textarea
        v-model="jsonInput"
        class="json-input"
        placeholder="粘贴 JSON 数据..."
        rows="12"
      ></textarea>
      <div v-if="validationError" class="error-msg">{{ validationError }}</div>
      <div v-if="saved" class="success-msg">保存成功，已规范化 {{ savedCount }} 条数据</div>
      <button class="save-btn" :disabled="loading || !jsonInput.trim()" @click="saveData">
        {{ loading ? '保存中...' : 'Save' }}
      </button>
    </div>

    <div class="existing-section" v-if="existingApps.length">
      <h3 class="section-heading">已导入的应用 ({{ existingApps.length }})</h3>
      <div class="app-list">
        <div v-for="(app, i) in existingApps" :key="i" class="app-card">
          <span class="app-name">{{ app.name_cn || app.name }}</span>
          <span class="app-meta">{{ app.category }} · {{ app.source }}</span>
        </div>
      </div>
    </div>

    <div class="example-section">
      <h3 class="section-heading">示例格式</h3>
      <pre class="example-code">{{ exampleJson }}</pre>
    </div>
  </div>
</template>

<style scoped>
.import-panel {
  padding: 0;
}

.header {
  margin-bottom: 28px;
}

.title {
  font-size: 22px;
  font-weight: 600;
  color: var(--color-text-1);
  margin: 0 0 6px;
}

.subtitle {
  font-size: 14px;
  color: var(--color-text-2);
  margin: 0;
  line-height: 1.4;
}

.input-section {
  margin-bottom: 32px;
}

.json-input {
  width: 100%;
  padding: 16px;
  font-family: var(--font-mono);
  font-size: 13px;
  line-height: 1.5;
  color: var(--color-text-1);
  background: var(--color-surface-solid);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  resize: vertical;
  box-sizing: border-box;
  transition: border-color 0.15s;
}
.json-input:focus {
  outline: none;
  border-color: var(--color-blue);
}

.error-msg {
  font-size: 13px;
  color: #c41e16;
  margin-top: 8px;
  white-space: pre-line;
  line-height: 1.5;
}

.success-msg {
  font-size: 13px;
  color: var(--color-green, #34c759);
  margin-top: 8px;
}

.save-btn {
  margin-top: 12px;
  font-size: 14px;
  font-weight: 500;
  color: #fff;
  background: var(--color-blue);
  border: none;
  border-radius: 980px;
  padding: 9px 24px;
  cursor: pointer;
  transition: transform 0.12s var(--ease-apple), opacity 0.12s;
}
.save-btn:hover:not(:disabled) {
  transform: translateY(-1px);
}
.save-btn:active:not(:disabled) {
  transform: scale(0.98);
}
.save-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.section-heading {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text-1);
  margin: 0 0 12px;
}

.existing-section {
  margin-bottom: 32px;
}

.app-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.app-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: var(--color-surface-solid);
  border-radius: var(--radius-sm);
  box-shadow: var(--shadow-card);
  padding: 12px 16px;
}

.app-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-1);
}

.app-meta {
  font-size: 12px;
  color: var(--color-text-3);
}

.example-section {
  margin-bottom: 20px;
}

.example-code {
  background: rgba(0, 0, 0, 0.03);
  border-radius: var(--radius-md);
  padding: 16px;
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--color-text-2);
  line-height: 1.5;
  overflow-x: auto;
  margin: 0;
}
</style>
