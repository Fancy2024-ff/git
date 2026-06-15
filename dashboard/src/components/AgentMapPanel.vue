<script setup lang="ts">
import { ref, computed } from 'vue'

interface AgentDef {
  id: string
  name: string
  nameEn: string
  phase: string
  purpose: string
  inputs: string[]
  outputs: string[]
  codeLocation: string
  changeHint: string
  implType: string
}

const AGENT_DEFINITIONS: AgentDef[] = [
  {
    id: 'candidate-finder',
    name: '候选发现',
    nameEn: 'Candidate Finder',
    phase: '数据',
    purpose: '从输入源中发现和筛选潜在的小程序候选应用，支持 demo 和 real 两种数据模式',
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
    phase: '分析',
    purpose: '分析候选应用的市场机会和竞争环境，生成市场洞察报告',
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
    phase: '分析',
    purpose: '检查候选应用与目标平台要求之间的差距，识别需要补充的功能或材料',
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
    phase: '分析',
    purpose: '综合评估候选应用的上架机会得分，输出推荐决策',
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
    phase: '生成',
    purpose: '根据候选信息和机会评估，自动生成小程序产品需求文档',
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
    phase: '生成',
    purpose: '根据 PRD 生成完整的小程序源代码，包含页面、组件和配置文件',
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
    phase: 'QA',
    purpose: '编译构建小程序并验证产物完整性，确保可以正常运行',
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
    phase: 'QA',
    purpose: '对构建产物进行质量检查和合规验证，输出 QA 报告',
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
    phase: '上架',
    purpose: '准备平台上架所需的所有材料，包括描述、截图、分类等',
    inputs: ['candidate.json', 'dist/', 'qa-report.json'],
    outputs: ['listing-materials.json', 'submission-readiness.json'],
    codeLocation: 'agents/steps/listing_preparer.py',
    changeHint: '更新平台上架材料要求',
    implType: '模板',
  },
]

const PHASES = ['全部', '数据', '分析', '生成', 'QA', '上架']

const selectedPhase = ref('全部')
const selectedAgentId = ref(AGENT_DEFINITIONS[0]?.id || '')

const filteredAgents = computed(() => {
  if (selectedPhase.value === '全部') return AGENT_DEFINITIONS
  return AGENT_DEFINITIONS.filter(a => a.phase === selectedPhase.value)
})

const selectedAgent = computed(() => {
  return AGENT_DEFINITIONS.find(a => a.id === selectedAgentId.value) || AGENT_DEFINITIONS[0]
})

function getImplColor(type: string): string {
  if (type === 'LLM') return 'impl--llm'
  if (type === 'API') return 'impl--api'
  if (type === '模板') return 'impl--template'
  return 'impl--rule'
}

function getPhaseColor(phase: string): string {
  if (phase === '数据') return 'phase--data'
  if (phase === '分析') return 'phase--analysis'
  if (phase === '生成') return 'phase--generate'
  if (phase === 'QA') return 'phase--qa'
  if (phase === '上架') return 'phase--listing'
  return ''
}
</script>

<template>
  <div class="agent-map">
    <!-- Phase filter -->
    <div class="phase-filter">
      <button
        v-for="phase in PHASES"
        :key="phase"
        class="phase-btn"
        :class="{ 'phase-btn--active': selectedPhase === phase }"
        @click="selectedPhase = phase"
      >{{ phase }}</button>
    </div>

    <div class="map-layout">
      <!-- Agent list -->
      <div class="agent-list">
        <div
          v-for="agent in filteredAgents"
          :key="agent.id"
          class="agent-item"
          :class="{ 'agent-item--active': selectedAgentId === agent.id }"
          @click="selectedAgentId = agent.id"
        >
          <div class="agent-item-header">
            <span class="agent-item-name">{{ agent.name }}</span>
            <span class="phase-tag" :class="getPhaseColor(agent.phase)">{{ agent.phase }}</span>
          </div>
          <span class="agent-item-en">{{ agent.nameEn }}</span>
        </div>
      </div>

      <!-- Agent detail -->
      <div class="agent-detail" v-if="selectedAgent">
        <div class="detail-header">
          <h3 class="detail-name">{{ selectedAgent.name }}</h3>
          <span class="impl-badge" :class="getImplColor(selectedAgent.implType)">{{ selectedAgent.implType }}</span>
        </div>
        <p class="detail-en">{{ selectedAgent.nameEn }}</p>
        <p class="detail-phase">
          阶段:
          <span class="phase-tag" :class="getPhaseColor(selectedAgent.phase)">{{ selectedAgent.phase }}</span>
        </p>

        <div class="detail-section">
          <h4 class="section-title">用途</h4>
          <p class="section-body">{{ selectedAgent.purpose }}</p>
        </div>

        <div class="detail-section">
          <h4 class="section-title">输入</h4>
          <ul class="io-list">
            <li v-for="inp in selectedAgent.inputs" :key="inp">{{ inp }}</li>
          </ul>
        </div>

        <div class="detail-section">
          <h4 class="section-title">输出</h4>
          <ul class="io-list">
            <li v-for="out in selectedAgent.outputs" :key="out">{{ out }}</li>
          </ul>
        </div>

        <div class="detail-section">
          <h4 class="section-title">代码位置</h4>
          <code class="code-loc">{{ selectedAgent.codeLocation }}</code>
        </div>

        <div class="detail-section">
          <h4 class="section-title">如需修改</h4>
          <p class="section-body hint">{{ selectedAgent.changeHint }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.agent-map {
  animation: fadeIn 0.3s var(--ease-apple);
}

.phase-filter {
  display: flex;
  gap: 6px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}
.phase-btn {
  padding: 6px 14px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 500;
  background: rgba(0, 0, 0, 0.04);
  color: var(--color-text-2);
  border: none;
  cursor: pointer;
  transition: all 0.15s;
}
.phase-btn--active {
  background: var(--color-text-1);
  color: #fff;
}

.map-layout {
  display: grid;
  grid-template-columns: 260px 1fr;
  gap: 20px;
}

.agent-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
  max-height: 520px;
  overflow-y: auto;
}

.agent-item {
  padding: 10px 12px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: background 0.12s;
}
.agent-item:hover {
  background: rgba(0, 0, 0, 0.03);
}
.agent-item--active {
  background: var(--color-blue-subtle);
}

.agent-item-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.agent-item-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--color-text-1);
}
.agent-item-en {
  font-size: 11px;
  color: var(--color-text-3);
}

.phase-tag {
  font-size: 10px;
  font-weight: 600;
  padding: 2px 6px;
  border-radius: 4px;
}
.phase--data { background: var(--color-blue-subtle); color: var(--color-blue); }
.phase--analysis { background: rgba(175, 82, 222, 0.08); color: #7c3aed; }
.phase--generate { background: var(--color-green-subtle); color: #166534; }
.phase--qa { background: var(--color-orange-subtle); color: #92400e; }
.phase--listing { background: rgba(255, 59, 48, 0.08); color: #991b1b; }

.agent-detail {
  background: var(--color-surface-solid);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-card);
  padding: 24px;
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
.detail-en {
  font-size: 13px;
  color: var(--color-text-3);
  margin-top: 2px;
}
.detail-phase {
  font-size: 12px;
  color: var(--color-text-2);
  margin-top: 6px;
  margin-bottom: 20px;
}

.detail-section { margin-bottom: 16px; }
.section-title {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  color: var(--color-text-3);
  margin-bottom: 4px;
}
.section-body { font-size: 13px; color: var(--color-text-1); line-height: 1.5; }
.section-body.hint { color: var(--color-text-2); font-style: italic; }

.io-list { list-style: none; padding: 0; margin: 0; }
.io-list li {
  font-size: 13px;
  color: var(--color-text-1);
  padding: 2px 0;
  font-family: var(--font-mono);
}
.io-list li::before { content: '›'; margin-right: 6px; color: var(--color-text-3); }

.code-loc {
  font-size: 12px;
  font-family: var(--font-mono);
  color: var(--color-blue);
  background: var(--color-blue-subtle);
  padding: 3px 8px;
  border-radius: 4px;
}

.impl-badge {
  font-size: 11px;
  font-weight: 600;
  padding: 3px 10px;
  border-radius: 980px;
}
.impl--rule { background: var(--color-green-subtle); color: #166534; }
.impl--llm { background: rgba(175, 82, 222, 0.08); color: #7c3aed; }
.impl--api { background: var(--color-orange-subtle); color: #92400e; }
.impl--template { background: var(--color-blue-subtle); color: var(--color-blue); }

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
