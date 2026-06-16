// 交付中心的纯逻辑：定义交付物清单 + 解析“复制什么”。
// copy 动作要复制真实路径/内容，不能是死按钮。

export type DeliverableKind = 'product' | 'engineering' | 'listing'
export type CopyMode = 'path' | 'content'

export interface DeliverableDef {
  key: string
  name: string
  kind: DeliverableKind
  purpose: string
  /** 下一步怎么用 */
  usage: string
  /** 复制路径 还是 复制内容 */
  copyMode: CopyMode
}

export const DELIVERABLES: DeliverableDef[] = [
  // 产品
  { key: 'candidate.json', name: '候选应用', kind: 'product', purpose: '筛选出的目标 App 信息', usage: '确认选中的应用是否符合预期', copyMode: 'content' },
  { key: 'opportunity-report.json', name: '机会评估', kind: 'product', purpose: '综合机会评分与推荐理由', usage: '向老板汇报“为什么值得做”', copyMode: 'content' },
  { key: 'prd.md', name: 'PRD 产品文档', kind: 'product', purpose: '小程序产品需求文档（可读版）', usage: '查看详情，确认产品方案', copyMode: 'content' },
  { key: 'prd.json', name: 'PRD（结构化）', kind: 'product', purpose: '结构化 PRD，供代码生成消费', usage: '工程消费，无需人工阅读', copyMode: 'content' },
  // 工程
  { key: 'miniapp', name: '小程序源码', kind: 'engineering', purpose: '生成的完整 uni-app 项目', usage: '复制路径，用微信开发者工具导入', copyMode: 'path' },
  { key: 'dist', name: '构建产物', kind: 'engineering', purpose: '编译后的 mp-weixin 包', usage: '复制路径，导入即可预览', copyMode: 'path' },
  { key: 'qa-report.json', name: 'QA 报告', kind: 'engineering', purpose: '安装/构建/编码校验结果', usage: '构建失败时查看 checks 字段', copyMode: 'content' },
  { key: 'pipeline-report.json', name: '流水线报告', kind: 'engineering', purpose: '完整执行步骤与状态', usage: '排查每一步耗时与结果', copyMode: 'content' },
  // 上架
  { key: 'listing-materials.md', name: '上架材料', kind: 'listing', purpose: '平台提交所需文案/隐私政策', usage: '查看详情，提交时复制使用', copyMode: 'content' },
  { key: 'publish-package', name: '发布包', kind: 'listing', purpose: '多平台提交目录', usage: '复制路径，按平台逐个提交', copyMode: 'path' },
  { key: 'human-actions.md', name: '人工操作清单', kind: 'listing', purpose: '需要人工完成的步骤', usage: '照清单逐项执行', copyMode: 'content' },
  { key: 'submission-readiness-report.json', name: '提交就绪度', kind: 'listing', purpose: '是否满足提交条件', usage: '查看阻塞项与下一步', copyMode: 'content' },
]

export interface JobLike {
  path?: string
  miniapp_path?: string
  artifacts?: Record<string, any>
}

/** 交付物是否已生成 */
export function hasDeliverable(job: JobLike | null, key: string): boolean {
  if (!job?.artifacts) return false
  if (key === 'miniapp') return !!job.miniapp_path
  if (key === 'dist') return !!job.artifacts['qa-report.json']?.checks?.dist_exists
  if (key === 'publish-package') return !!job.artifacts['submit-status.json']
  return !!job.artifacts[key]
}

/**
 * 解析复制动作。返回 { mode, value } —— value 为空字符串表示不可复制。
 * - miniapp：复制 job.miniapp_path
 * - dist：复制 qa-report.json.checks.dist_path
 * - publish-package：复制 `${job.path}/publish-package`
 * - 其它 JSON/MD：复制内容
 */
export function resolveCopy(job: JobLike | null, key: string): { mode: CopyMode; value: string } {
  if (!job) return { mode: 'path', value: '' }
  const arts = job.artifacts || {}

  if (key === 'miniapp') {
    return { mode: 'path', value: job.miniapp_path || '' }
  }
  if (key === 'dist') {
    return { mode: 'path', value: arts['qa-report.json']?.checks?.dist_path || '' }
  }
  if (key === 'publish-package') {
    return { mode: 'path', value: job.path ? `${job.path}/publish-package` : '' }
  }
  // JSON / MD：复制内容
  const data = arts[key]
  if (data === undefined || data === null) return { mode: 'content', value: '' }
  const text = typeof data === 'string' ? data : JSON.stringify(data, null, 2)
  return { mode: 'content', value: text }
}

/** 详情可查看：有内容（字符串或对象）即可 */
export function canViewDetail(job: JobLike | null, key: string): boolean {
  if (!job?.artifacts) return false
  if (key === 'miniapp' || key === 'dist' || key === 'publish-package') return false
  const data = job.artifacts[key]
  return data !== undefined && data !== null
}
