// 前端镜像：6 类 app_type + 运行能力等级。与 core/capabilities/app_types.py 对齐。
// 仅用于展示标签/中文名/颜色，判定逻辑以后端 artifact 为准。

export interface AppTypeMeta {
  id: string
  name_cn: string
  desc: string
}

export const APP_TYPES: Record<string, AppTypeMeta> = {
  text_ai: { id: 'text_ai', name_cn: '文本 AI', desc: '写作 / 翻译 / 摘要 / 问答' },
  image_ai: { id: 'image_ai', name_cn: '图像 AI', desc: '证件照 / 抠图 / 头像 / 增强' },
  ocr_scan: { id: 'ocr_scan', name_cn: 'OCR 扫描', desc: '识别 / 文档 / 票据提取' },
  speech_ai: { id: 'speech_ai', name_cn: '语音 AI', desc: '配音 / TTS / 语音转写' },
  video_light: { id: 'video_light', name_cn: '轻视频', desc: '摘要 / 封面 / 脚本' },
  utility_tool: { id: 'utility_tool', name_cn: '实用工具', desc: '计算 / 转换 / 查询' },
}

export function appTypeName(id: string | undefined): string {
  if (!id) return '未分类'
  return APP_TYPES[id]?.name_cn || id
}

export function appTypeDesc(id: string | undefined): string {
  if (!id) return ''
  return APP_TYPES[id]?.desc || ''
}

// 运行能力等级 → 中文标签 + 色调
export type RunnableLevel =
  | 'shell_only' | 'buildable' | 'submit_ready' | 'partially_runtime_ready' | 'runtime_ready'

export function runnableLevelLabel(level: string | undefined): { text: string; tone: string } {
  switch (level) {
    case 'runtime_ready': return { text: '可真实运行', tone: 'green' }
    case 'partially_runtime_ready': return { text: '部分可运行', tone: 'orange' }
    case 'submit_ready': return { text: '可提交（空壳）', tone: 'orange' }
    case 'buildable': return { text: '可构建（能力未接入）', tone: 'orange' }
    case 'shell_only': return { text: '仅骨架', tone: 'gray' }
    default: return { text: level || '未知', tone: 'gray' }
  }
}

export function feasibilityLabel(f: string | undefined): { text: string; tone: string } {
  switch (f) {
    case 'high': return { text: '高', tone: 'green' }
    case 'medium': return { text: '中', tone: 'orange' }
    case 'low': return { text: '低', tone: 'red' }
    default: return { text: '—', tone: 'gray' }
  }
}

// 能力 id → 中文短名（前端展示能力芯片用）
export const CAPABILITY_NAMES: Record<string, string> = {
  'text.generate': '文本',
  'image.process': '图像',
  'vision.ocr': 'OCR',
  'speech.tts': '语音',
  'speech.asr': '语音识别',
  'video.process': '视频',
  'utility.execute': '工具',
}

export function capabilityName(id: string): string {
  return CAPABILITY_NAMES[id] || id
}
