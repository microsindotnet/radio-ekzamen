<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import type { Phase, TranscriptItem } from '../composables/useExam'

const props = defineProps<{
  items: TranscriptItem[]
  phase: Phase
  activeTicket: number | null
}>()

const emit = defineEmits<{ (e: 'answer', n: number): void }>()

const scroller = ref<HTMLElement | null>(null)
const content = ref<HTMLElement | null>(null)

// «Прилипание» к низу: пока пользователь у нижней границы, держим последние
// строки и приглашение ввода видимыми. Если он пролистал вверх — не мешаем.
const STICK_THRESHOLD = 48
let stick = true
let observer: ResizeObserver | null = null

function isAtBottom(): boolean {
  const el = scroller.value
  if (!el) return true
  return el.scrollHeight - el.scrollTop - el.clientHeight < STICK_THRESHOLD
}

function scrollToBottom(): void {
  const el = scroller.value
  if (el) el.scrollTop = el.scrollHeight
}

function onScroll(): void {
  stick = isAtBottom()
}

// Клик по квадратной кнопке-цифре = нажатие клавиши 1..4.
function choose(n: number, event: MouseEvent): void {
  // снять фокус, чтобы Enter/Space на кнопке не «отвечали» повторно
  ;(event.currentTarget as HTMLElement | null)?.blur()
  emit('answer', n)
}

onMounted(() => {
  // Картинка билета догружается асинхронно и увеличивает высоту контента уже
  // после первичной прокрутки. ResizeObserver дотягивает скролл до низа,
  // чтобы приглашение ввода не оказалось ниже видимой области.
  observer = new ResizeObserver(() => {
    if (stick) scrollToBottom()
  })
  if (content.value) observer.observe(content.value)
  scrollToBottom()
})

onBeforeUnmount(() => {
  observer?.disconnect()
  observer = null
})

watch(
  () => [props.items.length, props.phase],
  async () => {
    stick = true
    await nextTick()
    scrollToBottom()
  },
  { flush: 'post' },
)
</script>

<template>
  <div ref="scroller" class="console" @scroll="onScroll">
    <div ref="content" class="console-content">
      <template v-for="(item, index) in items" :key="index">
        <hr v-if="item.kind === 'divider'" class="divider" />
        <div v-else-if="item.kind === 'image'" class="image-row">
          <img :src="item.src" class="ticket-image" alt="Иллюстрация к билету" />
        </div>
        <div v-else-if="item.kind === 'choice'" class="choice">
          <button
            type="button"
            class="choice-btn"
            :disabled="phase !== 'answering' || item.ticket !== activeTicket"
            @click="choose(item.n, $event)"
          >
            {{ item.n }}
          </button>
          <span class="choice-text">{{ item.text }}</span>
        </div>
        <div v-else class="line">
          <span
            v-for="(seg, segIndex) in item.segments"
            :key="segIndex"
            :class="`c-${seg.color}`"
            >{{ seg.text }}</span
          >
        </div>
      </template>

      <div v-if="phase === 'answering'" class="line prompt">
        Выберите ответ (1..4) или Esc: <span class="cursor">█</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.console {
  flex: 1 1 auto;
  min-height: 0;
  overflow-y: auto;
  padding: 16px 20px;
  font-size: 14px;
  line-height: 1.5;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}

.line {
  white-space: pre-wrap;
}

.choice {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  margin: 3px 0;
}

.choice-btn {
  flex: 0 0 auto;
  width: 22px;
  height: 22px;
  margin-top: 1px;
  padding: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font: inherit;
  font-size: 12px;
  line-height: 1;
  color: var(--fg);
  background: var(--panel-2);
  border: 1px solid var(--border);
  border-radius: 4px;
  cursor: pointer;
}

.choice-btn:hover:not(:disabled) {
  border-color: var(--accent);
  color: var(--accent);
}

.choice-btn:disabled {
  opacity: 0.4;
  cursor: default;
}

.choice-text {
  flex: 1 1 auto;
  min-width: 0;
  white-space: pre-wrap;
}

.divider {
  border: 0;
  border-top: 1px solid var(--border);
  margin: 12px 0 8px;
  opacity: 0.6;
}

.c-default {
  color: var(--fg);
}
.c-dim {
  color: var(--fg-dim);
}
.c-green {
  color: var(--green);
}
.c-red {
  color: var(--red);
}
.c-yellow {
  color: var(--yellow);
}

.image-row {
  margin: 8px 0 12px;
  padding-left: 4px;
}

.ticket-image {
  max-width: min(100%, 640px);
  max-height: 420px;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: #fff;
}

.prompt {
  color: var(--fg);
}

.cursor {
  color: var(--accent);
  animation: blink 1s steps(1) infinite;
}

@keyframes blink {
  50% {
    opacity: 0;
  }
}
</style>
