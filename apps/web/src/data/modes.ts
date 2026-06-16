import type { PipelineMode } from '../types/job'

// 单一事实来源：三档运行模式。AppleTopNav 与 App.vue 共用，避免漂移。

export interface ModeDef {
  value: PipelineMode
  /** 顶部模式切换按钮文案 */
  label: string
  /** 启动按钮文案 */
  startLabel: string
  /** 数据来源说明（给小白看） */
  source: string
}

export const MODES: ModeDef[] = [
  { value: 'demo', label: 'Demo / 试运行', startLabel: '启动试运行', source: 'data/inputs/demo/apps.json' },
  { value: 'real', label: 'Real / 生产运行', startLabel: '启动生产运行', source: 'data/inputs/real/apps.json' },
  { value: 'live', label: 'Live / 实时分析', startLabel: '启动实时分析', source: '实时抓取 App Store / Google Play' },
]

/** 默认模式：demo（避免演示时网络不稳定直接翻车） */
export const DEFAULT_MODE: PipelineMode = 'demo'

export function startLabelFor(mode: PipelineMode): string {
  return MODES.find(m => m.value === mode)?.startLabel || '启动'
}
