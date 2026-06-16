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

function sameStep(a: { step?: string; agent?: string }, b: { step?: string; agent?: string }): boolean {
  if (a.step && b.step) return a.step === b.step
  return !!a.agent && a.agent === b.agent
}

/**
 * Upsert a step_started event into the live step list.
 * 相同 step（或 agent）只更新，不重复新增 —— 修复重复 step_started 导致 Timeline 重复显示。
 * 返回新数组（不可变），便于 Vue 响应式与单测。
 */
export function upsertStepStarted(steps: PipelineStep[], msg: StepStartedMsg): PipelineStep[] {
  const incoming = stepFromStarted(msg)
  const idx = steps.findIndex(s => sameStep(s, incoming))
  if (idx >= 0) {
    const next = steps.slice()
    next[idx] = { ...next[idx], name: incoming.name, agent: incoming.agent, status: 'running' }
    return next
  }
  return [...steps, incoming]
}

export interface StepFinishedMsg {
  step?: string
  agent?: string
  name?: string
  status?: string
  success?: boolean
  artifact?: string
  error?: string
}

/**
 * Apply a step_finished event: find the matching step and update its status.
 * 找不到则追加（兜底）。返回新数组。
 */
export function applyStepFinished(steps: PipelineStep[], msg: StepFinishedMsg): PipelineStep[] {
  const status = msg.success === false || msg.status === 'failed' ? 'failed' : 'passed'
  const idx = steps.findIndex(s => sameStep(s, { step: msg.step, agent: msg.agent }))
  if (idx >= 0) {
    const next = steps.slice()
    next[idx] = {
      ...next[idx],
      status,
      artifact: msg.artifact || next[idx].artifact,
      error: msg.error || next[idx].error,
    }
    return next
  }
  return [...steps, {
    step: msg.step || '',
    name: msg.name || msg.step || '',
    agent: msg.agent || msg.step || '',
    status,
    artifact: msg.artifact,
    error: msg.error,
  }]
}

// Real 模式启动前的输入数据校验。返回 null 表示可启动，否则返回给用户的中文提示。
// 抽出来便于单测：保证“没有真实数据时不会去调 /api/pipeline/start”。
export function realModeBlockReason(inputs: { exists: boolean; apps: unknown[] }): string | null {
  if (!inputs.exists || inputs.apps.length === 0) {
    return '请先导入真实 App 数据（点击顶部「导入真实 App」），再启动生产运行。'
  }
  return null
}
