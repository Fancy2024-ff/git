<script setup lang="ts">
import { pipelineNodes } from '../data/mockData'
</script>

<template>
  <div class="timeline-section">
    <div class="section-header">
      <h2 class="section-title">生产流水线 <span class="section-title__en">Pipeline</span></h2>
      <p class="section-subtitle">当前进度：已完成 {{ pipelineNodes.filter(n => n.status === 'done').length }} / {{ pipelineNodes.length }} 个阶段</p>
    </div>
    <div class="timeline-scroll">
      <div class="timeline-track">
        <div class="timeline-line"></div>
        <div
          v-for="node in pipelineNodes"
          :key="node.id"
          class="timeline-node"
          :class="`timeline-node--${node.status}`"
        >
          <div class="node-circle" :class="`node-circle--${node.status}`">
            <span v-if="node.status === 'done'" class="node-check">✓</span>
            <span v-else-if="node.humanRequired" class="node-icon">👤</span>
          </div>
          <div class="node-body">
            <span class="node-label">{{ node.label }}</span>
            <span class="node-label-en">{{ node.labelEn }}</span>
            <span v-if="node.duration" class="node-duration">{{ node.duration }}</span>
            <span v-if="node.artifact" class="node-artifact">{{ node.artifact }}</span>
            <span v-if="node.humanRequired" class="node-human-tag">人工 Manual</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.section-header { margin-bottom: var(--space-5); }

.section-title {
  font-size: 20px;
  font-weight: 600;
  color: var(--color-text-primary);
  letter-spacing: -0.02em;
  line-height: 1.3;
}
.section-title__en {
  font-size: 14px;
  font-weight: 400;
  color: var(--color-text-tertiary);
  margin-left: 6px;
}
.section-subtitle {
  font-size: 13px;
  color: var(--color-text-secondary);
  margin-top: 3px;
}

.timeline-scroll {
  overflow-x: auto;
  padding-bottom: var(--space-3);
}

.timeline-track {
  display: flex;
  align-items: flex-start;
  position: relative;
  min-width: max-content;
  padding: var(--space-4) 0 var(--space-2);
}

.timeline-line {
  position: absolute;
  top: calc(var(--space-4) + 12px);
  left: 12px;
  right: 12px;
  height: 1px;
  background: var(--color-border-strong);
  z-index: 0;
}

.timeline-node {
  display: flex;
  flex-direction: column;
  align-items: center;
  position: relative;
  z-index: 1;
  flex: 1;
  min-width: 96px;
  max-width: 120px;
}

.node-circle {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-size: 11px;
  transition: all var(--duration-normal) var(--ease-out);
}
.node-circle--done { background: var(--color-green); color: #fff; font-weight: 700; }
.node-circle--running { background: var(--color-accent); color: #fff; animation: pulse-ring 1.4s ease-in-out infinite; }
.node-circle--waiting { background: var(--color-surface); border: 1.5px solid var(--color-border-strong); }
.node-circle--blocked { background: var(--color-orange-subtle); border: 1.5px solid var(--color-orange); }

@keyframes pulse-ring {
  0%, 100% { box-shadow: 0 0 0 0 rgba(0, 113, 227, 0.4); }
  50% { box-shadow: 0 0 0 5px rgba(0, 113, 227, 0); }
}

.node-check { font-size: 11px; font-weight: 700; line-height: 1; }
.node-icon { font-size: 10px; }

.node-body {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-top: var(--space-2);
  gap: 1px;
  text-align: center;
  padding: 0 4px;
}

.node-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--color-text-primary);
  line-height: 1.3;
  white-space: nowrap;
}
.node-label-en {
  font-size: 10px;
  color: var(--color-text-tertiary);
  font-weight: 400;
}
.timeline-node--waiting .node-label { color: var(--color-text-tertiary); }
.timeline-node--waiting .node-label-en { color: var(--color-text-tertiary); opacity: 0.6; }

.node-duration {
  font-size: 10px;
  color: var(--color-text-secondary);
  font-variant-numeric: tabular-nums;
  margin-top: 2px;
}
.timeline-node--running .node-duration { color: var(--color-accent); }

.node-artifact {
  font-size: 10px;
  color: var(--color-text-tertiary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100px;
}

.node-human-tag {
  font-size: 9px;
  font-weight: 600;
  letter-spacing: 0.02em;
  background: var(--color-orange-subtle);
  color: #b86800;
  padding: 1px 5px;
  border-radius: var(--radius-full);
  margin-top: 2px;
}
</style>
