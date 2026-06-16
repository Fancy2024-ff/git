import { describe, it, expect } from 'vitest'
import {
  computeOverallStatus, oneLineConclusion, nextActions,
  whyWorthIt, blockers, completionChecklist, type OverviewInput,
} from '../data/overview'

function base(over: Partial<OverviewInput> = {}): OverviewInput {
  return {
    running: false, candidate: null, opportunity: null,
    qa: null, readiness: null, pipelineReport: null, ...over,
  }
}

describe('overview 状态计算', () => {
  it('无任何数据 → idle', () => {
    expect(computeOverallStatus(base())).toBe('idle')
  })

  it('running=true → running', () => {
    expect(computeOverallStatus(base({ running: true }))).toBe('running')
  })

  it('有步骤失败 → failed', () => {
    const s = base({ pipelineReport: { steps: [{ status: 'failed', name: '构建' }] } })
    expect(computeOverallStatus(s)).toBe('failed')
  })

  it('qa passed + readiness 就绪 → ready', () => {
    const s = base({
      qa: { passed: true }, pipelineReport: { steps: [] },
      readiness: { is_ready_to_submit: true },
    })
    expect(computeOverallStatus(s)).toBe('ready')
  })

  it('qa passed + 有阻塞 → not_ready', () => {
    const s = base({
      qa: { passed: true }, pipelineReport: { steps: [] },
      readiness: { is_ready_to_submit: false, blocking_issues: ['缺 AppID'] },
    })
    expect(computeOverallStatus(s)).toBe('not_ready')
  })
})

describe('一句话结论', () => {
  it('idle 提示先启动', () => {
    expect(oneLineConclusion(base())).toContain('启动试运行')
  })
  it('not_ready 含阻塞数量', () => {
    const s = base({
      candidate: { name_cn: 'AI 写作助手' },
      qa: { passed: true, checks: { build_passed: true } },
      pipelineReport: { steps: [] },
      readiness: { is_ready_to_submit: false, blocking_issues: ['a', 'b', 'c'] },
    })
    const txt = oneLineConclusion(s)
    expect(txt).toContain('AI 写作助手')
    expect(txt).toContain('3 项阻塞')
  })
})

describe('nextActions 按责任人', () => {
  it('就绪时让人工去提交', () => {
    const a = nextActions(base({ readiness: { is_ready_to_submit: true } }))
    expect(a).toEqual([{ owner: 'human', text: '去对应平台后台提交审核' }])
  })

  it('未就绪时人工动作来自 human_actions，且构建通过给 Agent 动作', () => {
    const a = nextActions(base({
      qa: { checks: { build_passed: true } },
      readiness: {
        is_ready_to_submit: false,
        human_actions: ['配置 AppID', '准备截图'],
      },
    }))
    const human = a.filter(x => x.owner === 'human').map(x => x.text)
    const agent = a.filter(x => x.owner === 'agent')
    expect(human).toContain('配置 AppID')
    expect(human).toContain('准备截图')
    expect(agent.length).toBeGreaterThan(0)
  })

  it('无 readiness → 空', () => {
    expect(nextActions(base())).toEqual([])
  })
})

describe('卡片数据', () => {
  it('whyWorthIt 取三个分数和前 3 理由', () => {
    const w = whyWorthIt(base({
      opportunity: {
        demand_score: 88, miniapp_gap_score: 85.7, miniapp_fit_score: 75,
        reasons: ['r1', 'r2', 'r3', 'r4'],
      },
    }))
    expect(w).not.toBeNull()
    expect(w!.demand).toBe(88)
    expect(w!.reasons).toHaveLength(3)
  })

  it('blockers 区分阻塞与警告', () => {
    const b = blockers(base({ readiness: { blocking_issues: ['x'], warning_issues: ['y', 'z'] } }))
    expect(b.blocking).toEqual(['x'])
    expect(b.warning).toEqual(['y', 'z'])
  })

  it('completionChecklist 反映构建状态', () => {
    const c = completionChecklist(base({ qa: { checks: { build_passed: true } } }))
    const build = c.find(i => i.label.includes('构建'))
    expect(build?.done).toBe(true)
  })
})
