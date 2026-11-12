<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  stats: Array<{ number: number; count: number }>
  total: number
  correct: number
  wrong: number
  phase: 'answering' | 'finished'
}>()

const fileLines = computed(() =>
  props.stats.map(
    (row) => `${String(row.number).padStart(3, '0')} ошибок ${row.count}`,
  ),
)

const totalErrors = computed(() =>
  props.stats.reduce((sum, row) => sum + row.count, 0),
)
</script>

<template>
  <footer class="status">
    <div class="status-head">
      <span class="title">Статистика ошибок</span>
      <span class="counters">
        <span>Билетов с ошибками: <b>{{ stats.length }}</b></span>
        <span>Всего ошибок: <b class="c-red">{{ totalErrors }}</b></span>
        <span class="sep">|</span>
        <span>Пройдено: <b>{{ total }}</b></span>
        <span>Верно: <b class="c-green">{{ correct }}</b></span>
        <span>Ошибок: <b class="c-red">{{ wrong }}</b></span>
        <span v-if="phase === 'finished'" class="finished">тест завершён (Esc)</span>
      </span>
    </div>
    <div class="status-body">
      <p v-if="fileLines.length === 0" class="empty">Ошибок нет.</p>
      <ol v-else class="err-list">
        <li v-for="line in fileLines" :key="line" class="err-line">{{ line }}</li>
      </ol>
    </div>
  </footer>
</template>

<style scoped>
.status {
  flex: 0 0 auto;
  border-top: 1px solid var(--border);
  background: var(--panel);
  padding: 10px 16px 12px;
}

.status-head {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 12px;
  margin-bottom: 8px;
}

.title {
  font-weight: 700;
  color: var(--accent);
}

.counters {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  color: var(--fg-dim);
  font-size: 13px;
}

.counters b {
  color: var(--fg);
}

.sep {
  color: var(--border);
}

.finished {
  color: var(--yellow);
}

.status-body {
  max-height: 120px;
  overflow-y: auto;
  background: var(--panel-2);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 6px 10px;
}

.err-list {
  margin: 0;
  padding: 0;
  list-style: none;
  columns: 220px;
  font-size: 13px;
}

.err-line {
  color: var(--fg);
}

.empty {
  margin: 0;
  color: var(--fg-dim);
  font-size: 13px;
}

.c-green {
  color: var(--green);
}
.c-red {
  color: var(--red);
}
</style>
