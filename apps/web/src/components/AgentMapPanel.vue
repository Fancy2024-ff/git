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
    id: 'market_input',
    name: '市场输入',
    nameEn: 'MarketInputAgent',
    phase: '数据',
    purpose: '读取候选 App 数据，支持 demo/real/live 三种模式',
    inputs: ['data/samples/apps.json', 'data/real_inputs/apps.json', 'iTunes Search API'],
    outputs: ['candidate.json'],
    codeLocation: 'core/pipeline/runner.py:market_input_agent',
    changeHint: '改数据源、搜索关键词或导入数据',
    implType: '规则',
  },
  {
    id: 'demand_analysis',
    name: '需求分析',
    nameEn: 'DemandAnalysisAgent',
    phase: '分析',
    purpose: '评估 App 需求强度：下载量、评分、评论、变现模式',
    inputs: ['candidate.json'],
    outputs: ['analysis.json'],
    codeLocation: 'core/pipeline/runner.py:demand_analysis_agent',
    changeHint: '改 demand_analysis_agent 里的评分阈值和权重',
    implType: '规则',
  },
  {
    id: 'gap_check',
    name: '平台缺口',
    nameEn: 'GapCheckAgent',
    phase: '分析',
    purpose: '检查各小程序平台是否已有同类产品，识别覆盖缺口',
    inputs: ['candidate.json', 'data/platforms/platform-registry.json'],
    outputs: ['gap-check.json'],
    codeLocation: 'core/pipeline/runner.py:gap_check_agent',
    changeHint: '改 gap_check_agent 或接入真实搜索 API',
    implType: '规则',
  },
  {
    id: 'opportunity_score',
    name: '机会评分',
    nameEn: 'OpportunityScoreAgent',
    phase: '分析',
    purpose: '5 维度综合评分：需求、缺口、适配、实现、风险',
    inputs: ['analysis.json', 'gap-check.json'],
    outputs: ['opportunity-report.json'],
    codeLocation: 'core/pipeline/runner.py:opportunity_score_agent',
    changeHint: '改 opportunity_score_agent 里的权重 weights dict',
    implType: '规则',
  },
  {
    id: 'prd_generation',
    name: '生成 PRD',
    nameEn: 'PRDAgent',
    phase: '生成',
    purpose: '根据 App 信息和机会评估生成产品需求文档',
    inputs: ['candidate.json', 'opportunity-report.json'],
    outputs: ['prd.md', 'prd.json'],
    codeLocation: 'core/pipeline/runner.py:prd_agent',
    changeHint: '改 prd_agent 里的模板字符串',
    implType: '模板',
  },
  {
    id: 'code_generation',
    name: '生成代码',
    nameEn: 'CodegenAgent',
    phase: '生成',
    purpose: '从 generator 模板生成 uni-app 小程序项目',
    inputs: ['prd.json', 'generator/src/templates/base', 'generator/src/templates/ai-tool'],
    outputs: ['generated/miniapp/', 'generator-source.json'],
    codeLocation: 'core/pipeline/runner.py:codegen_agent',
    changeHint: '改 generator/src/templates 下的模板文件',
    implType: '模板',
  },
  {
    id: 'publish_materials',
    name: '上架材料',
    nameEn: 'PublishMaterialsAgent',
    phase: '上架',
    purpose: '生成各平台上架所需的文案、隐私政策、审核备注',
    inputs: ['candidate.json', 'prd.json'],
    outputs: ['listing-materials.md', 'listing-materials.json'],
    codeLocation: 'core/pipeline/runner.py:publish_materials_agent',
    changeHint: '改 publish_materials_agent 里的模板',
    implType: '模板',
  },
  {
    id: 'submit_package',
    name: '提交审核包',
    nameEn: 'PublishPackageAgent',
    phase: '上架',
    purpose: '生成多平台提交目录和就绪报告',
    inputs: ['listing-materials.json', 'platform-registry.json'],
    outputs: ['publish-package/', 'submission-readiness-report.json', 'submit-status.json'],
    codeLocation: 'core/pipeline/runner.py (inline)',
    changeHint: '改提交包生成逻辑或平台注册表',
    implType: '规则',
  },
  {
    id: 'build_qa',
    name: '构建 + 质检',
    nameEn: 'QACheckAgent',
    phase: 'QA',
    purpose: '执行 npm install + build，检查文件完整性和编码',
    inputs: ['generated/miniapp/'],
    outputs: ['qa-report.json', 'dist/build/mp-weixin/'],
    codeLocation: 'core/pipeline/runner.py:qa_check_agent',
    changeHint: '看 qa-report.json 的 issues 字段',
    implType: 'API',
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
