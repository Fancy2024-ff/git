// 单一事实来源：Pipeline 各 Agent 的真实定义。
// AgentMapPanel 和 AgentDetailPanel 都从这里读，避免两份数据漂移。
//
// codeLocation 全部指向真实存在的函数（core/pipeline/runner.py 内）。
// 行号是写入时的快照，函数名是稳定锚点 —— 若行号漂移，按函数名搜索即可。

export interface AgentDef {
  /** 与 pipeline-report.json 的 step 字段一致（runner.py step_start 的第一个参数） */
  id: string
  /** 与 step.agent 一致（runner.py step_start 的第三个参数），用于兜底匹配 */
  agentName: string
  name: string
  nameEn: string
  phase: string
  /** 这个 Agent 干什么（给小白看的一句话） */
  purpose: string
  /** 输入文件 / 数据源（真实路径） */
  inputs: string[]
  /** 输出文件（写入 data/outputs/{jobId}/ 下） */
  outputs: string[]
  /** 代码在哪（file:function 真实可追溯） */
  codeLocation: string
  /** 如果结果不对，改哪里 */
  changeHint: string
  /** 实现方式：规则 / 模板 / API / LLM */
  implType: string
}

export const AGENT_DEFS: AgentDef[] = [
  {
    id: 'market_input',
    agentName: 'MarketInputAgent',
    name: '市场输入',
    nameEn: 'MarketInputAgent',
    phase: '数据',
    purpose: '读取候选 App 数据，支持 demo（样例）/ real（导入）/ live（实时抓取）三种模式',
    inputs: ['data/inputs/demo/apps.json', 'data/inputs/real/apps.json', 'iTunes Search API（live 模式）'],
    outputs: ['candidate.json'],
    codeLocation: 'core/pipeline/runner.py:market_input_agent',
    changeHint: '换数据源或导入数据 → 改 data/inputs/real/apps.json；改抓取逻辑 → 改 market_input_agent',
    implType: '规则',
  },
  {
    id: 'demand_analysis',
    agentName: 'DemandAnalysisAgent',
    name: '需求分析',
    nameEn: 'DemandAnalysisAgent',
    phase: '分析',
    purpose: '评估 App 需求强度：下载量、评分、评论数、变现模式',
    inputs: ['candidate.json'],
    outputs: ['analysis.json'],
    codeLocation: 'core/pipeline/runner.py:demand_analysis_agent',
    changeHint: '评分偏高/偏低 → 改 demand_analysis_agent 里的阈值和权重',
    implType: '规则',
  },
  {
    id: 'gap_check',
    agentName: 'GapCheckAgent',
    name: '平台缺口',
    nameEn: 'GapCheckAgent',
    phase: '分析',
    purpose: '检查各小程序平台是否已有同类产品，识别覆盖缺口',
    inputs: ['candidate.json', 'data/platforms/platform-registry.json'],
    outputs: ['gap-check.json'],
    codeLocation: 'core/pipeline/runner.py:gap_check_agent',
    changeHint: '缺口判断不准 → 改 gap_check_agent，或接入真实搜索 API 替换代理搜索',
    implType: '规则',
  },
  {
    id: 'opportunity_score',
    agentName: 'OpportunityScoreAgent',
    name: '机会评分',
    nameEn: 'OpportunityScoreAgent',
    phase: '分析',
    purpose: '5 维度综合评分：需求、缺口、适配、实现、风险',
    inputs: ['analysis.json', 'gap-check.json'],
    outputs: ['opportunity-report.json'],
    codeLocation: 'core/pipeline/runner.py:opportunity_score_agent',
    changeHint: '评分排序不合理 → 改 opportunity_score_agent 里的 weights 权重字典',
    implType: '规则',
  },
  {
    id: 'prd_generation',
    agentName: 'PRDAgent',
    name: '生成 PRD',
    nameEn: 'PRDAgent',
    phase: '生成',
    purpose: '根据 App 信息和机会评估生成产品需求文档',
    inputs: ['candidate.json', 'opportunity-report.json'],
    outputs: ['prd.md', 'prd.json'],
    codeLocation: 'core/pipeline/runner.py:prd_agent',
    changeHint: 'PRD 内容/结构不对 → 改 prd_agent 里的模板字符串',
    implType: '模板',
  },
  {
    id: 'code_generation',
    agentName: 'CodegenAgent',
    name: '生成代码',
    nameEn: 'CodegenAgent',
    phase: '生成',
    purpose: '从模板生成 uni-app 小程序项目代码',
    inputs: ['prd.json', 'core/generator/src/templates/base', 'core/generator/src/templates/ai-tool'],
    outputs: ['generated/miniapp/', 'generator-source.json'],
    codeLocation: 'core/pipeline/runner.py:codegen_agent',
    changeHint: '生成的页面不对 → 改 core/generator/src/templates 下的模板文件',
    implType: '模板',
  },
  {
    id: 'publish_materials',
    agentName: 'PublishMaterialsAgent',
    name: '上架材料',
    nameEn: 'PublishMaterialsAgent',
    phase: '上架',
    purpose: '生成各平台上架所需的文案、隐私政策、审核备注',
    inputs: ['candidate.json', 'prd.json'],
    outputs: ['listing-materials.md', 'listing-materials.json'],
    codeLocation: 'core/pipeline/runner.py:publish_materials_agent',
    changeHint: '上架文案不对 → 改 publish_materials_agent 里的模板',
    implType: '模板',
  },
  {
    id: 'submit_package',
    agentName: 'PublishPackageAgent',
    name: '提交审核包',
    nameEn: 'PublishPackageAgent',
    phase: '上架',
    purpose: '生成多平台提交目录、提交指南和就绪报告',
    inputs: ['listing-materials.json', 'data/platforms/platform-registry.json'],
    outputs: ['publish-package/', 'submit-status.json'],
    codeLocation: 'core/pipeline/runner.py:run_pipeline（submit_package 段，约 L1934）',
    changeHint: '提交目录/平台清单不对 → 改 run_pipeline 的 submit_package 段或 platform-registry.json',
    implType: '规则',
  },
  {
    id: 'build_qa',
    agentName: 'QACheckAgent',
    name: '构建 + 质检',
    nameEn: 'QACheckAgent',
    phase: 'QA',
    purpose: '执行 npm install + npm run build:mp-weixin，检查文件完整性、编码、构建产物',
    inputs: ['generated/miniapp/'],
    outputs: ['qa-report.json', 'generated/miniapp/dist/build/mp-weixin/'],
    codeLocation: 'core/pipeline/runner.py:qa_check_agent',
    changeHint: 'QA 失败 → 看 qa-report.json 的 checks 字段；改校验规则 → 改 qa_check_agent',
    implType: 'API',
  },
  {
    id: 'readiness',
    agentName: 'ReadinessAgent',
    name: '提交就绪评估',
    nameEn: 'ReadinessAgent',
    phase: 'QA',
    purpose: '诚实回答“今天能否提交审核”：汇总阻塞项（缺 AppID/截图/真机测试等）',
    inputs: ['qa-report.json', 'opportunity-report.json', 'data/platforms/platform-registry.json'],
    outputs: ['submission-readiness-report.json', 'artifact-manifest.json'],
    codeLocation: 'core/pipeline/runner.py:build_submission_readiness',
    changeHint: 'readiness=false 的原因 → 看 submission-readiness-report.json 的 blocking_issues；改判定 → 改 build_submission_readiness',
    implType: '规则',
  },
]

/** 按 step id 或 agent 名查找定义，两种 key 都兼容 */
export function findAgentDef(key: string | undefined | null): AgentDef | null {
  if (!key) return null
  return AGENT_DEFS.find(d => d.id === key || d.agentName === key) || null
}
