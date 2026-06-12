export interface PipelineNode {
  id: string
  label: string
  labelEn: string
  status: 'done' | 'running' | 'waiting' | 'blocked'
  duration?: string
  artifact?: string
  humanRequired?: boolean
}

export interface Job {
  id: string
  name: string
  nameCn: string
  source: string
  score: number
  stage: string
  platforms: string[]
  nextAction: string
  status: 'active' | 'paused' | 'completed'
}

export interface Agent {
  id: string
  name: string
  nameCn: string
  input: string
  output: string
  status: 'idle' | 'running' | 'done'
  lastRun: string
}

export interface HumanAction {
  id: string
  title: string
  titleEn: string
  description: string
  priority: 'high' | 'medium' | 'low'
  deadline: string
  jobName: string
  done: boolean
}

export interface PublishStep {
  id: string
  label: string
  labelEn: string
  automated: boolean
  status: 'done' | 'current' | 'pending'
}

export interface Artifact {
  id: string
  name: string
  label: string
  type: 'json' | 'markdown' | 'folder' | 'code'
  size: string
  timestamp: string
}

// --- MOCK DATA ---

export const pipelineNodes: PipelineNode[] = [
  { id: 'discover', label: '发现应用', labelEn: 'Discover', status: 'done', duration: '12s', artifact: '已扫描 147 个应用' },
  { id: 'analyze', label: '需求分析', labelEn: 'Analyze', status: 'done', duration: '8s', artifact: '需求报告 demand-report.json' },
  { id: 'gap', label: '覆盖检查', labelEn: 'Gap Check', status: 'done', duration: '6s', artifact: '发现 23 个缺口' },
  { id: 'prd', label: '生成 PRD', labelEn: 'PRD', status: 'done', duration: '18s', artifact: '产品方案 prd.json' },
  { id: 'code', label: '生成代码', labelEn: 'Codegen', status: 'running', duration: '34s...', artifact: '小程序项目 uni-app' },
  { id: 'qa', label: '质量检查', labelEn: 'QA', status: 'waiting' },
  { id: 'listing', label: '上架材料', labelEn: 'Listing', status: 'waiting' },
  { id: 'publish', label: '人工上架', labelEn: 'Publish', status: 'waiting', humanRequired: true },
  { id: 'review', label: '复盘迭代', labelEn: 'Review', status: 'waiting' },
]

export const jobs: Job[] = [
  {
    id: '1',
    name: 'AI Resume Builder',
    nameCn: 'AI 简历生成器',
    source: 'App Store',
    score: 92,
    stage: '生成代码',
    platforms: ['微信', '抖音'],
    nextAction: '等待代码生成完成 · Waiting for codegen',
    status: 'active',
  },
  {
    id: '2',
    name: 'AI Photo Enhancer',
    nameCn: 'AI 图片增强工具',
    source: 'Google Play',
    score: 87,
    stage: '上架材料',
    platforms: ['微信', '支付宝', 'Telegram'],
    nextAction: '确认上架材料 · Confirm listing',
    status: 'active',
  },
  {
    id: '3',
    name: 'Language Learning Coach',
    nameCn: '语言学习教练',
    source: 'App Store',
    score: 78,
    stage: '人工上架',
    platforms: ['微信', 'LINE'],
    nextAction: '上传至微信小程序后台 · Upload to WeChat',
    status: 'paused',
  },
]

export const agents: Agent[] = [
  { id: '1', name: 'Market Scanner', nameCn: '市场扫描', input: 'App Store / Google Play 排行榜数据', output: '原始应用列表（147 条）', status: 'done', lastRun: '2 分钟前' },
  { id: '2', name: 'Demand Analyst', nameCn: '需求洞察', input: '应用元数据、评分、评论', output: '需求分析报告 demand-analysis.json', status: 'done', lastRun: '2 分钟前' },
  { id: '3', name: 'Gap Checker', nameCn: '覆盖分析', input: '应用列表 + 小程序平台搜索', output: '机会列表 gap-opportunities.json（23 条）', status: 'done', lastRun: '1 分钟前' },
  { id: '4', name: 'PRD Generator', nameCn: '产品方案', input: '最优机会 + 需求分析', output: '产品文档 prd.json（9 个功能）', status: 'done', lastRun: '1 分钟前' },
  { id: '5', name: 'Code Generator', nameCn: '代码生成', input: 'PRD 产品文档', output: '小程序项目（生成中…）', status: 'running', lastRun: '当前' },
  { id: '6', name: 'QA Inspector', nameCn: '质量检查', input: '生成的项目代码', output: '—', status: 'idle', lastRun: '—' },
  { id: '7', name: 'Publish Assistant', nameCn: '上架助手', input: 'QA 通过的项目', output: '—', status: 'idle', lastRun: '—' },
]

export const humanActions: HumanAction[] = [
  {
    id: '1',
    title: '确认 AI 简历生成器 PRD',
    titleEn: 'Confirm PRD',
    description: '请审核系统生成的产品方案，确认功能范围后代码生成将继续执行。',
    priority: 'high',
    deadline: '立即',
    jobName: 'AI 简历生成器',
    done: false,
  },
  {
    id: '2',
    title: '上传代码到微信小程序后台',
    titleEn: 'Upload to WeChat',
    description: '下载生成的代码包，通过微信开发者工具或 CI 上传至小程序后台。',
    priority: 'medium',
    deadline: '今天',
    jobName: '语言学习教练',
    done: false,
  },
  {
    id: '3',
    title: '填写平台审核结果',
    titleEn: 'Fill Review Result',
    description: '平台审核完成后，请记录通过/拒绝状态及反馈意见，用于后续复盘。',
    priority: 'low',
    deadline: '审核完成后',
    jobName: 'AI 图片增强工具',
    done: false,
  },
]

export const publishSteps: PublishStep[] = [
  { id: '1', label: '生成小程序名称', labelEn: 'App Name', automated: true, status: 'done' },
  { id: '2', label: '生成应用简介', labelEn: 'Description', automated: true, status: 'done' },
  { id: '3', label: '选择服务类目', labelEn: 'Category', automated: true, status: 'done' },
  { id: '4', label: '准备截图素材', labelEn: 'Screenshots', automated: true, status: 'current' },
  { id: '5', label: '生成隐私政策', labelEn: 'Privacy Policy', automated: true, status: 'pending' },
  { id: '6', label: '构建代码包', labelEn: 'Code Package', automated: true, status: 'pending' },
  { id: '7', label: '人工提交审核', labelEn: 'Manual Submit', automated: false, status: 'pending' },
  { id: '8', label: '记录审核结果', labelEn: 'Review Tracking', automated: false, status: 'pending' },
]

export const artifacts: Artifact[] = [
  { id: '1', name: 'market-scan.json', label: '市场扫描数据', type: 'json', size: '24 KB', timestamp: '2 分钟前' },
  { id: '2', name: 'opportunity-report.json', label: '机会评分报告', type: 'json', size: '8 KB', timestamp: '2 分钟前' },
  { id: '3', name: 'demand-analysis.json', label: '需求分析报告', type: 'json', size: '12 KB', timestamp: '1 分钟前' },
  { id: '4', name: 'prd.json', label: '结构化 PRD', type: 'json', size: '18 KB', timestamp: '1 分钟前' },
  { id: '5', name: 'prd-readable.md', label: '产品文档', type: 'markdown', size: '6 KB', timestamp: '1 分钟前' },
  { id: '6', name: 'generated-miniapp/', label: '小程序代码', type: 'folder', size: '14 个文件', timestamp: '生成中…' },
  { id: '7', name: 'qa-report.json', label: '质检报告', type: 'json', size: '—', timestamp: '待生成' },
  { id: '8', name: 'listing-materials.md', label: '上架材料', type: 'markdown', size: '—', timestamp: '待生成' },
]
