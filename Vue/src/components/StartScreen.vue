<script setup lang="ts">
import { QUIZ_MODES, type QuizMode } from '../training-algorithm'

const mode = defineModel<QuizMode>({ required: true })
const emit = defineEmits<{ start: [] }>()
</script>

<template>
  <div class="start">
    <div class="start-main">
      <h1>Экзамен на радиолюбительскую категорию</h1>
      <label class="field">
        <span class="field-label">Выберите вариант прохождения теста:</span>
        <select v-model="mode" class="select">
          <option
            v-for="option in QUIZ_MODES"
            :key="option.value"
            :value="option.value"
          >
            {{ option.label }}
          </option>
        </select>
      </label>
    </div>

    <footer class="start-footer">
      <button class="start-btn" type="button" @click="emit('start')">
        Запустить тест
      </button>
    </footer>
  </div>
</template>

<style scoped>
.start {
  display: flex;
  flex-direction: column;
  height: 100vh;
  height: 100dvh;
}

.start-main {
  flex: 1 1 auto;
  min-height: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 24px;
  padding: 20px;
  text-align: center;
}

h1 {
  margin: 0;
  font-size: 18px;
  font-weight: 700;
  letter-spacing: 0.02em;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 10px;
  width: min(100%, 480px);
  text-align: left;
}

.field-label {
  color: var(--fg-dim);
  font-size: 13px;
}

.select {
  font: inherit;
  font-size: 14px;
  color: var(--fg);
  background: var(--panel-2);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 8px 10px;
  cursor: pointer;
}

.select:focus {
  outline: none;
  border-color: var(--accent);
}

.start-footer {
  flex: 0 0 auto;
  display: flex;
  justify-content: center;
  padding: 16px 20px calc(16px + env(safe-area-inset-bottom, 0px));
  border-top: 1px solid var(--border);
  background: var(--panel);
}

.start-btn {
  font: inherit;
  font-size: 15px;
  font-weight: 700;
  color: #0d1117;
  background: var(--accent);
  border: 1px solid var(--accent);
  border-radius: 8px;
  padding: 10px 28px;
  cursor: pointer;
}

.start-btn:hover {
  filter: brightness(1.1);
}
</style>
