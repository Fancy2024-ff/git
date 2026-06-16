import { describe, it, expect } from 'vitest'
import { MODES, DEFAULT_MODE, startLabelFor } from '../data/modes'
import { stepFromStarted, realModeBlockReason } from '../data/pipeline-events'

// Regression guards for the three-mode nav + live Timeline labels.

describe('运行模式', () => {
  it('恰好包含 Demo / Real / Live 三档', () => {
    const values = MODES.map(m => m.value)
    expect(values).toEqual(['demo', 'real', 'live'])
  })

  it('每档都有可读的中文按钮文案', () => {
    expect(MODES.find(m => m.value === 'demo')?.label).toContain('试运行')
    expect(MODES.find(m => m.value === 'real')?.label).toContain('生产运行')
    expect(MODES.find(m => m.value === 'live')?.label).toContain('实时分析')
  })

  it('默认模式是 demo（避免演示翻车）', () => {
    expect(DEFAULT_MODE).toBe('demo')
  })

  it('启动按钮文案随模式变化', () => {
    expect(startLabelFor('demo')).toBe('启动试运行')
    expect(startLabelFor('real')).toBe('启动生产运行')
    expect(startLabelFor('live')).toBe('启动实时分析')
  })

  it('每档数据来源指向正确路径', () => {
    expect(MODES.find(m => m.value === 'demo')?.source).toBe('data/inputs/demo/apps.json')
    expect(MODES.find(m => m.value === 'real')?.source).toBe('data/inputs/real/apps.json')
  })
})

describe('实时 Timeline 步骤映射', () => {
  it('step_started 的中文 name 成为步骤标题，不是技术 id', () => {
    const step = stepFromStarted({
      step: 'market_input',
      agent: 'MarketInputAgent',
      name: '读取市场数据',
      message: '读取市场数据',
    })
    expect(step.name).toBe('读取市场数据')
    expect(step.name).not.toBe('market_input')
    expect(step.agent).toBe('MarketInputAgent')
    expect(step.status).toBe('running')
  })

  it('没有 name 时退回 message', () => {
    const step = stepFromStarted({ step: 'gap_check', agent: 'GapCheckAgent', message: '覆盖检查' })
    expect(step.name).toBe('覆盖检查')
  })

  it('name 和 message 都缺失时才退回技术 id', () => {
    const step = stepFromStarted({ step: 'qa', agent: 'QACheckAgent' })
    expect(step.name).toBe('qa')
  })
})

describe('Real 模式启动前校验', () => {
  it('没有真实数据时返回提示，阻止启动', () => {
    expect(realModeBlockReason({ exists: false, apps: [] })).toContain('导入真实 App')
    expect(realModeBlockReason({ exists: true, apps: [] })).toContain('导入真实 App')
  })

  it('有数据时返回 null，允许启动', () => {
    expect(realModeBlockReason({ exists: true, apps: [{ name: 'x' }] })).toBeNull()
  })
})

