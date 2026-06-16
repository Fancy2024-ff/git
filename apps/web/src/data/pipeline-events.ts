import type { PipelineStep } from '../types/job'

// 把 WebSocket step_started 事件映射成 Timeline 用的 PipelineStep。
// 抽出来是为了单测保证：中文 name（msg.name / msg.message）不会退化成技术 id。

export interface StepStartedMsg {
  step?: string
  name?: string
  message?: string
  agent?: string
}

export function stepFromStarted(msg: StepStartedMsg): PipelineStep {
  return {
    step: msg.step || '',
    // 优先中文 name，其次 message，最后才退回技术 id
    name: msg.name || msg.message || msg.step || '',
    agent: msg.agent || msg.step || '',
    status: 'running',
  }
}

// Real 模式启动前的输入数据校验。返回 null 表示可启动，否则返回给用户的中文提示。
// 抽出来便于单测：保证“没有真实数据时不会去调 /api/pipeline/start”。
export function realModeBlockReason(inputs: { exists: boolean; apps: unknown[] }): string | null {
  if (!inputs.exists || inputs.apps.length === 0) {
    return '请先导入真实 App 数据（点击顶部「导入真实 App」），再启动生产运行。'
  }
  return null
}
