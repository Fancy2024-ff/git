// 总览页的纯逻辑：把 artifacts 汇总成决策者能看懂的结论 + 下一步行动。
// 全部纯函数，便于单测；组件只负责渲染。

export type OverallStatus = 'idle' | 'running' | 'failed' | 'not_ready' | 'ready' | 'done'

export interface OverviewInput {
  running: boolean
  candidate: any | null
  opportunity: any | null
  qa: any | null
  readiness: any | null
  pipelineReport: any | null
  classification?: any | null
  runtime?: any | null
  executionReport?: any | null
}

export interface NextAction {
  owner: 'agent' | 'human'
  text: string
}

/** 当前总状态：运行中 / 失败 / 可提交 / 暂不可提交 / 已完成 / 无任务 */
export function computeOverallStatus(input: OverviewInput): OverallStatus {
  if (input.running) return 'running'
  if (!input.candidate && !input.pipelineReport) return 'idle'

  const steps = input.pipelineReport?.steps || []
  if (steps.some((s: any) => s.status === 'failed')) return 'failed'

  const qaPassed = !!input.qa?.passed
  const ready = !!(input.readiness?.is_ready_to_submit ?? input.readiness?.ready_to_submit)
  if (qaPassed && ready) return 'ready'
  if (qaPassed && input.readiness) return 'not_ready'
  if (input.pipelineReport) return 'done'
  return 'idle'
}

/** 状态中文标签 + 颜色语义（蓝运行/绿可提交/橙阻塞/红失败/灰空） */
export function statusLabel(status: OverallStatus): { text: string; tone: string } {
  switch (status) {
    case 'running': return { text: '运行中', tone: 'blue' }
    case 'failed': return { text: '失败', tone: 'red' }
    case 'ready': return { text: '可提交', tone: 'green' }
    case 'not_ready': return { text: '暂不可提交', tone: 'orange' }
    case 'done': return { text: '已完成', tone: 'green' }
    default: return { text: '无任务', tone: 'gray' }
  }
}

/** 一句话结论：一眼看懂当前发生了什么 */
export function oneLineConclusion(input: OverviewInput): string {
  const status = computeOverallStatus(input)
  const appName = input.candidate?.name_cn || input.candidate?.name || input.opportunity?.app_name_cn || '小程序'

  if (status === 'idle') return '当前无任务，请先点击右上角「启动试运行」。'

  if (status === 'running') {
    const steps = input.pipelineReport?.steps || []
    const cur = steps.find((s: any) => s.status === 'running')
    if (cur) return `系统正在执行：${cur.name || cur.agent}。`
    return '系统正在运行流水线…'
  }

  if (status === 'failed') {
    const steps = input.pipelineReport?.steps || []
    const failed = steps.find((s: any) => s.status === 'failed')
    return `任务失败：${failed?.name || failed?.agent || '某一步'}未通过，请查看生产线的错误原因。`
  }

  const buildPassed = !!(input.qa?.checks?.build_passed)
  const target = buildPassed ? '微信小程序构建通过' : '构建未完成'

  if (status === 'ready') {
    return `「${appName}」已完成，${target}，当前满足提交条件，可进入上架中心。`
  }
  if (status === 'not_ready') {
    const n = (input.readiness?.blocking_issues || []).length
    return `「${appName}」已完成，${target}，但暂不可提交：还有 ${n} 项阻塞（见“现在卡在哪里”）。`
  }
  return `「${appName}」流程已结束。`
}

/** 系统完成了什么（卡片 B） */
export function completionChecklist(input: OverviewInput): { label: string; done: boolean }[] {
  const a = input
  const checks = a.qa?.checks || {}
  return [
    { label: '生成 PRD 产品文档', done: !!a.opportunity },
    { label: '生成小程序代码', done: !!checks.files_exist || !!a.qa },
    { label: '微信构建通过', done: !!checks.build_passed },
    { label: '生成上架材料', done: !!(a.readiness || a.pipelineReport?.steps?.some((s: any) => s.step === 'publish_materials' && (s.status === 'passed' || s.status === 'done'))) },
    { label: '生成提交包', done: !!a.readiness?.platform_readiness?.length },
  ]
}

/** 为什么值得做（卡片 A） */
export function whyWorthIt(input: OverviewInput): {
  demand: number | null
  gap: number | null
  fit: number | null
  reasons: string[]
} | null {
  const o = input.opportunity
  if (!o) return null
  return {
    demand: o.demand_score ?? null,
    gap: o.miniapp_gap_score ?? null,
    fit: o.miniapp_fit_score ?? null,
    reasons: (o.reasons || []).slice(0, 3),
  }
}

/** 现在卡在哪里（卡片 C）：阻塞 + 警告 */
export function blockers(input: OverviewInput): { blocking: string[]; warning: string[] } {
  const r = input.readiness
  return {
    blocking: r?.blocking_issues || [],
    warning: r?.warning_issues || [],
  }
}

/** 下一步行动：按责任人分 Agent / 人工 */
export function nextActions(input: OverviewInput): NextAction[] {
  const out: NextAction[] = []
  const r = input.readiness
  if (!r) return out

  const ready = !!(r.is_ready_to_submit ?? r.ready_to_submit)
  if (ready) {
    out.push({ owner: 'human', text: '去对应平台后台提交审核' })
    return out
  }

  // 人工动作来自 readiness.human_actions（真实数据）
  for (const h of (r.human_actions || [])) {
    out.push({ owner: 'human', text: h })
  }
  // Agent 可做：构建已通过时可重新跑 QA / 上传开发版本
  if (input.qa?.checks?.build_passed) {
    out.push({ owner: 'agent', text: '配置授权后，自动上传微信开发版本' })
  }
  if (input.qa && !input.qa.passed) {
    out.push({ owner: 'agent', text: '修复后重新运行 QA 构建检查' })
  }
  if (out.length === 0) {
    out.push({ owner: 'agent', text: '重新运行 Pipeline 生成完整产物' })
  }
  return out
}

/** 能力工厂总览：app_type / 可行性 / 运行等级 / 缺失能力（卡片用）。 */
export interface CapabilityOverview {
  appType: string | null
  feasibility: string | null
  confidence: number | null
  runnableLevel: string | null
  runtimeReady: boolean
  requiredCapabilities: string[]
  configuredCapabilities: string[]
  missingCapabilities: string[]
  /** 工厂侧能力执行就绪（capability_runtime）vs 生成小程序自身能跑（app_runtime）——诚实区分 */
  factoryCapabilityReady: boolean
  appRuntimeRunnable: boolean
  appRuntimeReason: string
}

export function capabilityOverview(input: OverviewInput): CapabilityOverview | null {
  const c = input.classification
  const r = input.runtime
  const ex = input.executionReport
  if (!c && !r && !ex) return null
  const capRuntime = ex?.capability_runtime || {}
  const factoryReady = Object.values(capRuntime).some(
    (v: any) => Array.isArray(v?.executable_operations) && v.executable_operations.length > 0
  )
  return {
    appType: c?.app_type ?? ex?.app_type ?? null,
    feasibility: c?.miniapp_feasibility ?? null,
    confidence: c?.app_type_confidence ?? null,
    runnableLevel: r?.runnable_level ?? ex?.runnable_level ?? null,
    runtimeReady: !!r?.runtime_ready,
    requiredCapabilities: c?.required_capabilities ?? ex?.required_capabilities ?? [],
    configuredCapabilities: r?.configured_capabilities ?? ex?.configured_capabilities ?? [],
    missingCapabilities: r?.missing_capabilities ?? ex?.missing_capabilities ?? [],
    factoryCapabilityReady: factoryReady,
    appRuntimeRunnable: !!ex?.app_runtime?.runnable,
    appRuntimeReason: ex?.app_runtime?.reason ?? '',
  }
}
