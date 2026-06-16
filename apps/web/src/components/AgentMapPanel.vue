<script setup lang="ts">
import { ref, computed } from 'vue'
import { AGENT_DEFS } from '../data/agents'

const AGENT_DEFINITIONS = AGENT_DEFS

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
