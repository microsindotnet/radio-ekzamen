<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import ConsoleView from './components/ConsoleView.vue'
import StartScreen from './components/StartScreen.vue'
import StatusBar from './components/StatusBar.vue'
import { useExam } from './composables/useExam'
import { loadQuizMode, saveQuizMode, QUIZ_MODE_LABELS } from './training-algorithm'

const exam = useExam()

const started = ref(false)
const mode = ref(loadQuizMode())

const modeLabel = computed(() => QUIZ_MODE_LABELS[exam.mode.value])

watch(mode, (value) => saveQuizMode(value))

function startTest(): void {
  saveQuizMode(mode.value)
  exam.start(mode.value)
  started.value = true
}

function onKeydown(event: KeyboardEvent): void {
  if (!started.value) return
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
  window.addEventListener('keydown', onKeydown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', onKeydown)
})
</script>

<template>
  <StartScreen v-if="!started" v-model="mode" @start="startTest" />

  <div v-else class="app">
    <header class="topbar">
      <h1>Экзамен на радиолюбительскую категорию ({{ modeLabel }})</h1>
      <div class="topbar-right">
        <button class="action" type="button" @click="exam.handleKey('Escape')">
          Завершить
        </button>
      </div>
    </header>

    <ConsoleView
      :items="exam.transcript"
      :phase="exam.phase.value"
      :active-ticket="exam.activeTicket.value"
      @answer="exam.handleKey(String($event))"
    />

    <StatusBar
      :stats="exam.errorStats.value"
      :total="exam.total.value"
      :correct="exam.correct.value"
      :wrong="exam.wrong.value"
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

.action {
  font: inherit;
  font-size: 12px;
  color: var(--fg);
  background: var(--panel-2);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 4px 12px;
  cursor: pointer;
}

.action:hover {
  border-color: var(--accent);
  color: var(--accent);
}
</style>
