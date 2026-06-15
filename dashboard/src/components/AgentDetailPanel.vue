<script setup lang="ts">
import { computed } from 'vue'
import type { PipelineStep } from '../types/job'

const props = defineProps<{
  step: PipelineStep | null
}>()

interface AgentDef {
  id: string
  name: string
  nameEn: string
  purpose: string
  inputs: string[]
  outputs: string[]
  codeLocation: string
  changeHint: string
  implType: string
}

const AGENT_DEFS: AgentDef[] = [
  {
    id: 'candidate-finder',
    name: '候选发现',
    nameEn: 'Candidate Finder',
    purpose: '从输入源中发现和筛选潜在的小程序候选应用',
    inputs: ['real-inputs/apps.json 或 demo 数据'],
    outputs: ['candidate.json'],
    codeLocation: 'agents/steps/candidate_finder.py',
    changeHint: '修改筛选逻辑或数据源配置',
    implType: '规则',
  },
  {
    id: 'market-analyst',
    name: '市场分析',
    nameEn: 'Market Analyst',
    purpose: '分析候选应用的市场机会和竞争环境',
    inputs: ['candidate.json'],
    outputs: ['market-analysis.json'],
    codeLocation: 'agents/steps/market_analyst.py',
    changeHint: '调整分析维度或评分权重',
    implType: 'LLM',
  },
  {
    id: 'gap-checker',
    name: '差距检查',
    nameEn: 'Gap Checker',
    purpose: '检查候选应用与目标平台要求之间的差距',
    inputs: ['candidate.json', 'market-analysis.json'],
    outputs: ['gap-check.json'],
    codeLocation: 'agents/steps/gap_checker.py',
    changeHint: '更新平台要求规则集',
    implType: '规则',
  },
  {
    id: 'opportunity-scorer',
    name: '机会评分',
    nameEn: 'Opportunity Scorer',
    purpose: '综合评估候选应用的上架机会得分',
    inputs: ['candidate.json', 'market-analysis.json', 'gap-check.json'],
    outputs: ['opportunity-report.json'],
    codeLocation: 'agents/steps/opportunity_scorer.py',
    changeHint: '调整评分公式或阈值',
    implType: '规则',
  },
  {
    id: 'prd-writer',
    name: 'PRD 撰写',
    nameEn: 'PRD Writer',
    purpose: '生成小程序产品需求文档',
    inputs: ['candidate.json', 'opportunity-report.json'],
    outputs: ['prd.json'],
    codeLocation: 'agents/steps/prd_writer.py',
    changeHint: '修改 PRD 模板或生成提示词',
    implType: 'LLM',
  },
  {
    id: 'code-generator',
    name: '代码生成',
    nameEn: 'Code Generator',
    purpose: '根据 PRD 生成小程序源代码',
    inputs: ['prd.json', '模板库'],
    outputs: ['generated/miniapp/'],
    codeLocation: 'agents/steps/code_generator.py',
    changeHint: '更新代码模板或生成策略',
    implType: '模板',
  },
  {
    id: 'build-verify',
    name: '构建验证',
    nameEn: 'Build Verify',
    purpose: '编译构建并验证小程序产物完整性',
    inputs: ['generated/miniapp/'],
    outputs: ['dist/', 'build-result.json'],
    codeLocation: 'agents/steps/build_verify.py',
    changeHint: '调整构建工具链配置',
    implType: 'API',
  },
  {
    id: 'qa-checker',
    name: 'QA 检查',
    nameEn: 'QA Checker',
    purpose: '对构建产物进行质量检查和合规验证',
    inputs: ['dist/', 'prd.json'],
    outputs: ['qa-report.json'],
    codeLocation: 'agents/steps/qa_checker.py',
    changeHint: '添加或修改 QA 检查规则',
    implType: '规则',
  },
  {
    id: 'listing-preparer',
    name: '上架准备',
    nameEn: 'Listing Preparer',
    purpose: '准备平台上架所需的所有材料',
    inputs: ['candidate.json', 'dist/', 'qa-report.json'],
    outputs: ['listing-materials.json', 'submission-readiness.json'],
    codeLocation: 'agents/steps/listing_preparer.py',
    changeHint: '更新平台上架材料要求',
    implType: '模板',
  },
]

const agentDef = computed(() => {
  if (!props.step) return AGENT_DEFS[0] || null
  return AGENT_DEFS.find(d => d.id === props.step!.agent) || null
})

function getImplColor(type: string): string {
  if (type === 'LLM') return 'impl--llm'
  if (type === 'API') return 'impl--api'
  if (type === '模板') return 'impl--template'
  return 'impl--rule'
}

function getStatusBadgeClass(status?: string): string {
  if (!status) return ''
  if (status === 'passed' || status === 'done') return 'badge--green'
  if (status === 'running') return 'badge--blue'
  if (status === 'failed') return 'badge--red'
  return 'badge--gray'
}

function getStatusLabel(status?: string): string {
  if (!status) return ''
  if (status === 'passed' || status === 'done') return '完成'
  if (status === 'running') return '运行中'
  if (status === 'failed') return '失败'
  return '等待中'
}
</script>

<template>
  <div class="detail-panel">
    <div v-if="agentDef" class="detail-content">
      <div class="detail-header">
        <h3 class="detail-name">{{ agentDef.name }}</h3>
        <span
          v-if="step?.status"
          class="status-badge"
          :class="getStatusBadgeClass(step.status)"
        >{{ getStatusLabel(step.status) }}</span>
      </div>
      <p class="detail-name-en">{{ agentDef.nameEn }}</p>

      <div class="detail-section">
        <h4 class="section-title">用途</h4>
        <p class="section-body">{{ agentDef.purpose }}</p>
      </div>

      <div class="detail-section">
        <h4 class="section-title">输入</h4>
        <ul class="io-list">
          <li v-for="inp in agentDef.inputs" :key="inp">{{ inp }}</li>
        </ul>
      </div>

      <div class="detail-section">
        <h4 class="section-title">输出</h4>
        <ul class="io-list">
          <li v-for="out in agentDef.outputs" :key="out">{{ out }}</li>
        </ul>
      </div>

      <div class="detail-section">
        <h4 class="section-title">代码位置</h4>
        <code class="code-loc">{{ agentDef.codeLocation }}</code>
      </div>

      <div class="detail-section">
        <h4 class="section-title">如需修改</h4>
        <p class="section-body hint">{{ agentDef.changeHint }}</p>
      </div>

      <div class="detail-footer">
        <span class="impl-badge" :class="getImplColor(agentDef.implType)">
          {{ agentDef.implType }}
        </span>
      </div>

      <div v-if="step?.error" class="error-block">
        <h4 class="section-title">错误信息</h4>
        <p class="error-text">{{ step.error }}</p>
      </div>
    </div>

    <div v-else class="detail-empty">
      <p>选择一个 Agent 查看详情</p>
    </div>
  </div>
</template>

<style scoped>
.detail-panel {
  background: var(--color-surface-solid);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
  padding: 24px;
  min-height: 320px;
}

.detail-content {
  animation: fadeIn 0.2s ease;
}

.detail-header {
  display: flex;
  align-items: center;
  gap: 10px;
}

.detail-name {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text-1);
}

.status-badge {
  font-size: 11px;
  font-weight: 500;
  padding: 2px 8px;
  border-radius: 980px;
}
.badge--green {
  background: var(--color-green-subtle);
  color: #166534;
}
.badge--blue {
  background: var(--color-blue-subtle);
  color: var(--color-blue);
}
.badge--red {
  background: rgba(255, 59, 48, 0.08);
  color: #991b1b;
}
.badge--gray {
  background: rgba(0, 0, 0, 0.04);
  color: var(--color-text-3);
}

.detail-name-en {
  font-size: 13px;
  color: var(--color-text-3);
  margin-top: 2px;
  margin-bottom: 20px;
}

.detail-section {
  margin-bottom: 16px;
}

.section-title {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  color: var(--color-text-3);
  margin-bottom: 4px;
}

.section-body {
  font-size: 13px;
  color: var(--color-text-1);
  line-height: 1.5;
}

.section-body.hint {
  color: var(--color-text-2);
  font-style: italic;
}

.io-list {
  list-style: none;
  padding: 0;
  margin: 0;
}
.io-list li {
  font-size: 13px;
  color: var(--color-text-1);
  padding: 2px 0;
  font-family: var(--font-mono);
}
.io-list li::before {
  content: '›';
  margin-right: 6px;
  color: var(--color-text-3);
}

.code-loc {
  font-size: 12px;
  font-family: var(--font-mono);
  color: var(--color-blue);
  background: var(--color-blue-subtle);
  padding: 3px 8px;
  border-radius: 4px;
}

.detail-footer {
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid var(--color-border);
}

.impl-badge {
  font-size: 11px;
  font-weight: 600;
  padding: 3px 10px;
  border-radius: 980px;
}
.impl--rule {
  background: var(--color-green-subtle);
  color: #166534;
}
.impl--llm {
  background: rgba(175, 82, 222, 0.08);
  color: #7c3aed;
}
.impl--api {
  background: var(--color-orange-subtle);
  color: #92400e;
}
.impl--template {
  background: var(--color-blue-subtle);
  color: var(--color-blue);
}

.error-block {
  margin-top: 16px;
  padding: 12px;
  background: rgba(255, 59, 48, 0.04);
  border-radius: var(--radius-sm);
  border: 1px solid rgba(255, 59, 48, 0.12);
}
.error-text {
  font-size: 12px;
  color: #991b1b;
  font-family: var(--font-mono);
  white-space: pre-wrap;
  word-break: break-all;
}

.detail-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 200px;
  color: var(--color-text-3);
  font-size: 14px;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}
</style>
