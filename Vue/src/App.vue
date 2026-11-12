<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue'
import ConsoleView from './components/ConsoleView.vue'
import StatusBar from './components/StatusBar.vue'
import { useExam } from './composables/useExam'

const exam = useExam()

function onKeydown(event: KeyboardEvent): void {
  if (event.repeat) return
  if (event.ctrlKey || event.altKey || event.metaKey) return
  if (event.key === 'Escape') {
    event.preventDefault()
    exam.handleKey('Escape')
    return
  }
  if (['1', '2', '3', '4'].includes(event.key)) {
    event.preventDefault()
    exam.handleKey(event.key)
  }
}

onMounted(() => {
  exam.start()
  window.addEventListener('keydown', onKeydown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', onKeydown)
})
</script>

<template>
  <div class="app">
    <header class="topbar">
      <h1>Экзамен на радиолюбительскую категорию</h1>
      <div class="topbar-right">
        <span class="hint">1..4 — ответить · Esc — завершить тест</span>
        <button class="restart" type="button" @click="exam.start()">Заново</button>
      </div>
    </header>

    <ConsoleView :items="exam.transcript" :phase="exam.phase.value" />

    <StatusBar
      :stats="exam.errorStats.value"
      :total="exam.total.value"
      :correct="exam.correct.value"
      :wrong="exam.wrong.value"
      :phase="exam.phase.value"
    />
  </div>
</template>

<style scoped>
.app {
  display: flex;
  flex-direction: column;
  height: 100vh;
  height: 100dvh;
}

.topbar {
  flex: 0 0 auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 10px 20px;
  border-bottom: 1px solid var(--border);
  background: var(--panel);
}

h1 {
  margin: 0;
  font-size: 15px;
  font-weight: 700;
  letter-spacing: 0.02em;
}

.topbar-right {
  display: flex;
  align-items: center;
  gap: 14px;
}

.hint {
  color: var(--fg-dim);
  font-size: 12px;
}

.restart {
  font: inherit;
  font-size: 12px;
  color: var(--fg);
  background: var(--panel-2);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 4px 12px;
  cursor: pointer;
}

.restart:hover {
  border-color: var(--accent);
  color: var(--accent);
}
</style>
