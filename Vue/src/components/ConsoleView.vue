<script setup lang="ts">
import { nextTick, ref, watch } from 'vue'
import type { Phase, TranscriptItem } from '../composables/useExam'

const props = defineProps<{ items: TranscriptItem[]; phase: Phase }>()

const scroller = ref<HTMLElement | null>(null)

watch(
  () => [props.items.length, props.phase],
  async () => {
    await nextTick()
    if (scroller.value) scroller.value.scrollTop = scroller.value.scrollHeight
  },
  { flush: 'post' },
)
</script>

<template>
  <div ref="scroller" class="console">
    <template v-for="(item, index) in items" :key="index">
      <hr v-if="item.kind === 'divider'" class="divider" />
      <div v-else-if="item.kind === 'image'" class="image-row">
        <img :src="item.src" class="ticket-image" alt="Иллюстрация к билету" />
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
