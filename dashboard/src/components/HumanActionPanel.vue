<script setup lang="ts">
import { ref } from 'vue'
import { humanActions } from '../data/mockData'
import type { HumanAction } from '../data/mockData'

const actions = ref<HumanAction[]>(humanActions.map(a => ({ ...a })))

function toggleDone(id: string) {
  const action = actions.value.find(a => a.id === id)
  if (action) action.done = !action.done
}

function priorityColor(priority: HumanAction['priority']): string {
  if (priority === 'high') return 'var(--color-red)'
  if (priority === 'medium') return 'var(--color-orange)'
  return 'var(--color-text-tertiary)'
}

function priorityLabel(priority: HumanAction['priority']): string {
  if (priority === 'high') return '紧急'
  if (priority === 'medium') return '一般'
  return '低优'
}
</script>

<template>
  <div class="human-action-panel">
    <div class="section-header">
      <h2 class="section-title">当前需要你执行 <span class="section-title__en">Human Actions</span></h2>
      <p class="section-subtitle">系统已完成自动步骤，以下节点需要人工确认或平台后台操作。</p>
      <p class="section-meta">{{ actions.filter(a => !a.done).length }} 项待处理 · {{ actions.filter(a => a.done).length }} 项已完成</p>
    </div>

    <div class="action-list">
      <div
        v-for="action in actions"
        :key="action.id"
        class="action-card"
        :class="{ 'action-card--done': action.done }"
      >
        <div class="action-card__priority-bar" :style="{ background: priorityColor(action.priority) }"></div>
        <div class="action-card__body">
          <div class="action-card__top">
            <div class="action-card__header">
              <span class="priority-badge" :style="{ background: priorityColor(action.priority) }">{{ priorityLabel(action.priority) }}</span>
              <div class="action-card__titles">
                <h4 class="action-card__title" :class="{ 'action-card__title--done': action.done }">{{ action.title }}</h4>
                <span class="action-card__title-en">{{ action.titleEn }}</span>
              </div>
            </div>
            <button class="mark-done-btn" @click="toggleDone(action.id)">
              {{ action.done ? '撤销' : '标记完成' }}
            </button>
          </div>

          <p class="action-card__description" :class="{ 'action-card__description--done': action.done }">
            {{ action.description }}
          </p>

          <div class="action-card__footer">
            <span class="action-card__meta">
              <span class="meta-label">关联任务</span>
              <span class="meta-value">{{ action.jobName }}</span>
            </span>
            <span class="action-card__meta">
              <span class="meta-label">处理期限</span>
              <span class="meta-value" :class="action.deadline === '立即' ? 'meta-value--urgent' : ''">
                {{ action.deadline }}
              </span>
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.section-header { margin-bottom: var(--space-5); }
.section-title { font-size: 20px; font-weight: 600; color: var(--color-text-primary); letter-spacing: -0.02em; }
.section-title__en { font-size: 14px; font-weight: 400; color: var(--color-text-tertiary); margin-left: 6px; }
.section-subtitle { font-size: 13px; color: var(--color-text-secondary); margin-top: 3px; }
.section-meta { font-size: 12px; color: var(--color-text-tertiary); margin-top: 2px; }

.action-list { display: flex; flex-direction: column; gap: var(--space-3); }

.action-card {
  background: var(--color-surface);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-card);
  display: flex;
  overflow: hidden;
  transition: all var(--duration-fast) var(--ease-out);
}
.action-card--done { opacity: 0.45; }

.action-card__priority-bar { width: 3px; flex-shrink: 0; }

.action-card__body { flex: 1; padding: var(--space-4) var(--space-5); display: flex; flex-direction: column; gap: var(--space-2); }

.action-card__top { display: flex; align-items: flex-start; justify-content: space-between; gap: var(--space-3); }
.action-card__header { display: flex; align-items: flex-start; gap: var(--space-2); flex: 1; }

.priority-badge {
  font-size: 10px;
  font-weight: 600;
  color: #fff;
  padding: 2px 6px;
  border-radius: var(--radius-full);
  flex-shrink: 0;
  margin-top: 2px;
}

.action-card__titles { display: flex; flex-direction: column; gap: 0; }
.action-card__title { font-size: 14px; font-weight: 600; color: var(--color-text-primary); letter-spacing: -0.01em; line-height: 1.4; }
.action-card__title--done { text-decoration: line-through; color: var(--color-text-tertiary); }
.action-card__title-en { font-size: 11px; color: var(--color-text-tertiary); }

.mark-done-btn {
  font-size: 12px;
  font-weight: 500;
  padding: 4px 10px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--color-border-strong);
  background: transparent;
  color: var(--color-text-secondary);
  cursor: pointer;
  white-space: nowrap;
  transition: all var(--duration-fast) var(--ease-out);
  flex-shrink: 0;
}
.mark-done-btn:hover { background: var(--color-bg); color: var(--color-text-primary); }

.action-card__description { font-size: 13px; color: var(--color-text-secondary); line-height: 1.5; }
.action-card__description--done { text-decoration: line-through; color: var(--color-text-tertiary); }

.action-card__footer { display: flex; gap: var(--space-5); margin-top: var(--space-1); }
.action-card__meta { display: flex; gap: var(--space-1); align-items: center; }
.meta-label { font-size: 11px; color: var(--color-text-tertiary); font-weight: 500; }
.meta-value { font-size: 12px; color: var(--color-text-secondary); font-weight: 500; }
.meta-value--urgent { color: var(--color-red); font-weight: 600; }
</style>
