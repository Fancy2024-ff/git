<script setup lang="ts">
defineProps<{
  tabs: { id: string; label: string }[]
  modelValue: string
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string]
}>()
</script>

<template>
  <div class="seg-container">
    <button
      v-for="tab in tabs"
      :key="tab.id"
      class="seg-btn"
      :class="{ active: modelValue === tab.id }"
      @click="emit('update:modelValue', tab.id)"
    >
      {{ tab.label }}
    </button>
  </div>
</template>

<style scoped>
.seg-container {
  display: inline-flex;
  background: rgba(0, 0, 0, 0.04);
  border-radius: 10px;
  padding: 3px;
  gap: 2px;
}

.seg-btn {
  padding: 6px 14px;
  font-size: 13px;
  font-weight: 500;
  border: none;
  background: transparent;
  color: var(--color-text-2);
  border-radius: 8px;
  cursor: pointer;
  transition: background 0.2s ease, color 0.2s ease, box-shadow 0.2s ease;
}

.seg-btn:hover { color: var(--color-text-1); }

.seg-btn.active {
  background: #fff;
  color: var(--color-text-1);
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
}
</style>
