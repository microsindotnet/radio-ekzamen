import { computed, reactive, ref } from 'vue'
import { ANSWERS } from '../answers'
import { TICKETS, getTicket } from '../tickets'
import { TrainingSession } from '../training-algorithm'
import type { AnswerLetter, ShuffledChoice, Ticket } from '../core/types'

export type LineColor = 'default' | 'green' | 'red' | 'yellow' | 'dim'

export interface TextSegment {
  text: string
  color: LineColor
}

export type TranscriptItem =
  | { kind: 'text'; segments: TextSegment[] }
  | { kind: 'divider' }
  | { kind: 'image'; src: string }

export type Phase = 'answering' | 'finished'

/** Как в оригинале, всегда включён режим `-t -e`. */
const EXTEND = true

function shuffle<T>(items: T[]): T[] {
  const result = items.slice()
  for (let i = result.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1))
    ;[result[i], result[j]] = [result[j], result[i]]
  }
  return result
}

function choicesFor(ticket: Ticket): ShuffledChoice[] {
  const letters: AnswerLetter[] = ['a', 'b', 'c', 'd']
  const pairs = letters.map((letter, i) => ({ letter, text: ticket.answers[i] }))
  return shuffle(pairs)
}

function imageUrl(image: string): string {
  return `${import.meta.env.BASE_URL}media/${image}`
}

export function useExam() {
  const session = new TrainingSession()

  const transcript = reactive<TranscriptItem[]>([])
  const phase = ref<Phase>('answering')
  const total = ref(0)
  const correct = ref(0)

  const current = ref<{ ticket: Ticket; choices: ShuffledChoice[] } | null>(null)

  const errorStats = ref(session.stats.snapshot())

  function refreshStats(): void {
    errorStats.value = session.stats.snapshot()
  }

  function push(item: TranscriptItem): void {
    transcript.push(item)
  }

  function pushText(text: string, color: LineColor = 'default'): void {
    push({ kind: 'text', segments: [{ text, color }] })
  }

  function pushSegments(segments: TextSegment[]): void {
    push({ kind: 'text', segments })
  }

  function showTicket(ticket: Ticket): void {
    const choices = choicesFor(ticket)
    current.value = { ticket, choices }

    push({ kind: 'divider' })
    if (EXTEND && ticket.hard) {
      pushText(`Билет № ${ticket.number}`, 'yellow')
    } else {
      pushText(`Билет № ${ticket.number}`)
    }
    pushText('')
    pushText('Вопрос:')
    pushText(ticket.question)
    pushText('')
    if (ticket.image) {
      push({ kind: 'image', src: imageUrl(ticket.image) })
    }
    choices.forEach((choice, i) => pushText(`${i + 1}) ${choice.text}`))
    pushText('')
  }

  function nextTicket(): void {
    const number = session.next(EXTEND)
    showTicket(getTicket(number))
  }

  function answer(key: string): void {
    const state = current.value
    if (!state) return
    const selected = state.choices[Number.parseInt(key, 10) - 1]
    const correctLetter = ANSWERS[state.ticket.number]
    const isCorrect = selected.letter === correctLetter
    const correctText = state.ticket.answers['abcd'.indexOf(correctLetter)]

    if (isCorrect) {
      // «Правильно» зелёным, «, N» (номер ответа) — обычным цветом.
      pushSegments([
        { text: 'Правильно', color: 'green' },
        { text: `, ${key}`, color: 'default' },
      ])
    } else {
      // «Ошибка» красным, номер ошибочного ответа — обычным цветом,
      // затем правильный ответ.
      pushSegments([
        { text: 'Ошибка', color: 'red' },
        { text: `: ${key}`, color: 'default' },
      ])
      pushText(`Правильный ответ: ${correctText}`)
    }

    session.record(state.ticket.number, isCorrect)
    refreshStats()

    total.value += 1
    if (isCorrect) correct.value += 1

    nextTicket()
  }

  function finish(): void {
    phase.value = 'finished'
    current.value = null

    const wrong = total.value - correct.value
    const lines = [
      `Пройдено вопросов: ${total.value}`,
      `Из них верно: ${correct.value}`,
      `Ошибок: ${wrong}`,
    ]
    const width = Math.max(...lines.map((l) => l.length))
    const border = `+${'-'.repeat(width + 2)}+`

    push({ kind: 'divider' })
    pushText(border, 'dim')
    pushText(`| ${lines[0].padEnd(width)} |`)
    pushSegments([
      { text: '| Из них верно: ', color: 'default' },
      { text: String(correct.value), color: 'green' },
      { text: `${' '.repeat(width - lines[1].length)} |`, color: 'default' },
    ])
    pushSegments([
      { text: '| Ошибок: ', color: 'default' },
      { text: String(wrong), color: 'red' },
      { text: `${' '.repeat(width - lines[2].length)} |`, color: 'default' },
    ])
    pushText(border, 'dim')
  }

  function handleKey(key: string): void {
    if (phase.value !== 'answering') return
    if (key === 'Escape') {
      finish()
      return
    }
    if (['1', '2', '3', '4'].includes(key)) {
      answer(key)
    }
  }

  function start(): void {
    transcript.splice(0, transcript.length)
    phase.value = 'answering'
    total.value = 0
    correct.value = 0
    current.value = null
    session.reset()
    refreshStats()
    nextTicket()
  }

  const wrong = computed(() => total.value - correct.value)

  return {
    transcript,
    phase,
    total,
    correct,
    wrong,
    errorStats,
    totalTickets: TICKETS.length,
    start,
    handleKey,
  }
}
