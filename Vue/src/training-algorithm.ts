/**
 * Алгоритм тренировки.
 *
 * Здесь собраны две связанные части:
 *
 *   1. Учёт статистики ответов (аналог `src/stat.py` и файла `err_stat.txt`):
 *      ошибки (раздел `[Errors]`) и билеты с правильным ответом (`[Correct]`).
 *   2. Выбор следующего билета с учётом тренировочного счётчика и окна
 *      последних показанных билетов.
 *
 * Правила выбора билета:
 *
 *   - обычный случайный билет НИКОГДА не берётся из последних `RECENT_LIMIT`
 *     показанных (`recent`) — недавние билеты не должны повторяться;
 *   - обычный случайный билет НИКОГДА не берётся и из списка ошибочных:
 *     ошибочные билеты показываются ТОЛЬКО счётчиком `training`;
 *   - сложные билеты (`hard`) выпадают в 2 раза чаще простых;
 *   - билеты с правильным ответом (раздел `Correct`) выпадают в 2 раза реже;
 *   - тренировочный счётчик `training` показывает билет из списка ошибочных
 *     не раньше чем через `RECENT_LIMIT + G` вопросов (`G` — случайно 5..10).
 */

import { TICKETS } from './tickets'
import { INITIAL_ERR_STAT } from './errStat'

export const TICKET_MIN = 1
export const TICKET_MAX = 426

/**
 * Сколько последних показанных билетов нельзя вытянуть случайно.
 * Это исключает повтор недавних билетов (например, только что отвеченных).
 */
export const RECENT_LIMIT = 10

/** Множество номеров всех билетов (полный список для выбора). */
const ALL_NUMBERS: ReadonlySet<number> = new Set(TICKETS.map((t) => t.number))

/** Множество номеров билетов, помеченных как сложные (`hard`). */
export const HARD_NUMBERS: ReadonlySet<number> = new Set(
  TICKETS.filter((t) => t.hard).map((t) => t.number),
)

// ---------------------------------------------------------------------------
// Учёт статистики ошибочных ответов (аналог err_stat.txt)
// ---------------------------------------------------------------------------

export const STAT_WIDTH = 3

const STORAGE_KEY = 'radio-ekzamen:err_stat'

/** Разобранная статистика: ошибки и список билетов с правильным ответом. */
export interface StatsData {
  counts: Map<number, number>
  correct: Set<number>
}

/**
 * Разобрать текст статистики (разделы `[Errors]` и `[Correct]`).
 *
 * Поддерживается и старый формат (без заголовков): тогда все строки
 * `NNN ошибок K` считаются разделом `[Errors]`.
 */
export function parseErrStat(text: string): StatsData {
  const counts = new Map<number, number>()
  const correct = new Set<number>()
  let section: 'errors' | 'correct' = 'errors'
  for (const raw of text.split(/\r?\n/)) {
    const line = raw.trim()
    if (!line) continue
    const low = line.toLowerCase()
    if (low === '[errors]') {
      section = 'errors'
      continue
    }
    if (low === '[correct]') {
      section = 'correct'
      continue
    }
    if (section === 'correct') {
      const number = Number.parseInt(line, 10)
      if (Number.isInteger(number)) correct.add(number)
    } else {
      const parts = line.split(/\s+/)
      if (parts.length !== 3 || parts[1] !== 'ошибок') continue
      const number = Number.parseInt(parts[0], 10)
      const count = Number.parseInt(parts[2], 10)
      if (!Number.isInteger(number) || !Number.isInteger(count)) continue
      if (count > 0) counts.set(number, count)
    }
  }
  return { counts, correct }
}

/** Сериализовать статистику в текст формата `err_stat.txt`. */
export function formatErrStat(counts: Map<number, number>, correct: Set<number>): string {
  const lines = ['[Errors]']
  for (const number of [...counts.keys()].sort((a, b) => a - b)) {
    lines.push(`${String(number).padStart(STAT_WIDTH, '0')} ошибок ${counts.get(number)}`)
  }
  lines.push('')
  lines.push('[Correct]')
  for (const number of [...correct].sort((a, b) => a - b)) {
    lines.push(String(number).padStart(STAT_WIDTH, '0'))
  }
  return lines.join('\n') + '\n'
}

/**
 * Статистика ответов по билетам: ошибки (раздел `[Errors]`) и список билетов
 * с правильным ответом (раздел `[Correct]`).
 *
 * В браузере файла нет, поэтому данные хранятся в `localStorage` (при первом
 * открытии страницы подгружается исходное содержимое `err_stat.txt`).
 */
export class ErrorStats {
  private counts = new Map<number, number>()
  private correct = new Set<number>()

  constructor() {
    this.load()
  }

  load(): void {
    let text = localStorage.getItem(STORAGE_KEY)
    if (text === null) {
      text = INITIAL_ERR_STAT
      localStorage.setItem(STORAGE_KEY, text)
    }
    const data = parseErrStat(text)
    this.counts = data.counts
    this.correct = data.correct
  }

  save(): void {
    localStorage.setItem(STORAGE_KEY, formatErrStat(this.counts, this.correct))
  }

  /**
   * Обновить статистику по ответу на билет `number`.
   *
   * Ошибка увеличивает счётчик и удаляет билет из раздела `Correct`.
   * Правильный ответ уменьшает счётчик (при нуле строка удаляется) и
   * добавляет билет в раздел `Correct`.
   */
  record(number: number, correct: boolean): void {
    if (correct) {
      const count = (this.counts.get(number) ?? 0) - 1
      if (count > 0) this.counts.set(number, count)
      else this.counts.delete(number)
      this.correct.add(number)
    } else {
      this.counts.set(number, (this.counts.get(number) ?? 0) + 1)
      this.correct.delete(number)
    }
    this.save()
  }

  /** Текущее число ошибок по билету. */
  get(number: number): number {
    return this.counts.get(number) ?? 0
  }

  /** Отсортированные номера билетов с ошибками. */
  errorNumbers(): number[] {
    return [...this.counts.keys()].sort((a, b) => a - b)
  }

  /** Отсортированные номера билетов с правильным ответом. */
  correctNumbers(): number[] {
    return [...this.correct].sort((a, b) => a - b)
  }

  /** Был ли по билету правильный ответ (билет в разделе `Correct`). */
  isCorrect(number: number): boolean {
    return this.correct.has(number)
  }

  /** Число билетов, по которым есть ошибки. */
  get size(): number {
    return this.counts.size
  }

  /** Всего ошибок (сумма счётчиков). */
  totalErrors(): number {
    let total = 0
    for (const count of this.counts.values()) total += count
    return total
  }

  /** Снимок статистики для отображения: отсортированный список. */
  snapshot(): Array<{ number: number; count: number }> {
    return this.errorNumbers().map((number) => ({ number, count: this.get(number) }))
  }

  reset(): void {
    this.counts = new Map()
    this.correct = new Set()
    this.save()
  }
}

// ---------------------------------------------------------------------------
// Выбор билета
// ---------------------------------------------------------------------------

/** Целое число в диапазоне [min, max] включительно (аналог random.randint). */
function randInt(min: number, max: number): number {
  return min + Math.floor(Math.random() * (max - min + 1))
}

/** Взвешенный выбор одного элемента (аналог random.choices(k=1)). */
function weightedChoice<T>(items: T[], weights: number[]): T {
  let total = 0
  for (const w of weights) total += w
  let r = Math.random() * total
  for (let i = 0; i < items.length; i++) {
    r -= weights[i]
    if (r < 0) return items[i]
  }
  return items[items.length - 1]
}

/**
 * Случайный билет, не входящий в `excluded`.
 *
 * При `extend = true` сложные билеты (`hard`) выпадают в 2 раза чаще, а
 * билеты из `halved` (с правильным ответом) — в 2 раза реже.
 * `excluded` — номера, которые нельзя выдавать (последние показанные билеты
 * и ошибочные билеты).
 */
export function pickRandom(
  extend: boolean,
  excluded: ReadonlySet<number>,
  halved: ReadonlySet<number>,
  pool: ReadonlySet<number> = ALL_NUMBERS,
): number {
  if (extend) {
    const all = TICKETS.filter((t) => pool.has(t.number))
    let offers = all.filter((t) => !excluded.has(t.number))
    if (offers.length === 0) offers = all // защита: исключать стало нечего
    if (offers.length === 0) return TICKET_MIN // защита: пустой пул
    const population = offers.map((t) => t.number)
    const weights = offers.map(
      (t) => (t.hard ? 2 : 1) * (halved.has(t.number) ? 0.5 : 1),
    )
    return weightedChoice(population, weights)
  }
  const available = [...pool].filter((n) => !excluded.has(n))
  if (available.length === 0) {
    const any = [...pool]
    return any.length > 0 ? any[randInt(0, any.length - 1)] : TICKET_MIN
  }
  for (;;) {
    const number = available[randInt(0, available.length - 1)]
    if (halved.has(number) && Math.random() < 0.5) continue
    return number
  }
}

export interface PickResult {
  number: number
  training: number
}

/**
 * Выбрать следующий билет с учётом тренировочного счётчика.
 *
 * `training` — счётчик «тренировки». `recent` — последние показанные билеты
 * (не длиннее `RECENT_LIMIT`); их нельзя вытянуть случайно.
 *
 * Алгоритм:
 *
 *   1. Счётчик равен 0 и есть ошибочные билеты — заводим отсчёт
 *      `RECENT_LIMIT + G`, где `G` — случайное число 5..10. То есть
 *      ошибочный билет повторяется не раньше чем через `10 + G` вопросов.
 *   2. Счётчик больше 1 — обычный случайный билет (кроме `recent` и
 *      ошибочных; `hard` в 2 раза чаще, билеты из `Correct` в 2 раза реже),
 *      счётчик уменьшается на 1.
 *   3. Счётчик равен 1 — случайный билет из списка ошибочных. Если он не
 *      входит в `recent`, показываем его и сбрасываем счётчик в 0; если
 *      входит — показываем обычный случайный билет, а счётчик НЕ уменьшается,
 *      чтобы повторить попытку позже.
 *   4. Ошибочных билетов нет — обычный случайный билет.
 */
export function pickTicket(
  extend: boolean,
  stats: ErrorStats,
  training: number,
  recent: number[],
  pool: ReadonlySet<number> = ALL_NUMBERS,
): PickResult {
  const errNumbers = stats.errorNumbers().filter((n) => pool.has(n))
  const excludedRecent = new Set(recent)
  // Обычный случайный выбор исключает и последние показанные билеты, и все
  // ошибочные. Ошибочные показываются ТОЛЬКО счётчиком training, поэтому
  // повтор происходит строго не раньше чем через RECENT_LIMIT + G вопросов.
  const excludedRandom = new Set<number>([...recent, ...errNumbers])
  // Билеты с правильным ответом (раздел Correct) выпадают в 2 раза реже.
  const correctNumbers = new Set(stats.correctNumbers())

  // 1. Счётчик не активен, но есть ошибочные билеты — новый отсчёт
  //    RECENT_LIMIT + G (G случайно 5..10). Повтор ошибочного билета —
  //    не раньше чем через RECENT_LIMIT + G вопросов.
  if (training === 0 && errNumbers.length > 0) {
    training = RECENT_LIMIT + randInt(5, 10)
  }

  // 2. Обычный случайный билет (не recent, не ошибочный), счётчик -1.
  if (training > 1) {
    return { number: pickRandom(extend, excludedRandom, correctNumbers, pool), training: training - 1 }
  }

  // 3. Пора показать билет из списка ошибочных.
  if (training === 1) {
    if (errNumbers.length > 0) {
      const candidate = errNumbers[randInt(0, errNumbers.length - 1)]
      if (!excludedRecent.has(candidate)) {
        return { number: candidate, training: 0 }
      }
      // Ошибочный билет недавно показывали: показываем обычный, счётчик
      // НЕ уменьшается — повторим попытку позже.
      return { number: pickRandom(extend, excludedRandom, correctNumbers, pool), training: 1 }
    }
    training = 0
  }

  // 4. Ошибочных билетов нет — обычный случайный билет.
  return { number: pickRandom(extend, excludedRandom, correctNumbers, pool), training }
}

// ---------------------------------------------------------------------------
// Режимы прохождения теста
// ---------------------------------------------------------------------------

/** Вариант прохождения теста, выбираемый на стартовой странице. */
export type QuizMode = 'normal' | 'extended' | 'hard' | 'errors'

/** Ключ localStorage для сохранения выбранного варианта. */
export const MODE_STORAGE_KEY = 'radio-ekzamen:quiz_mode'

/** Вариант по умолчанию, если ранее выбор не сохранялся. */
export const DEFAULT_MODE: QuizMode = 'normal'

/** Доля приоритетных ошибочных билетов в режиме `hard` (~2/3). */
const HARD_ERROR_SHARE = 2 / 3

/** Варианты для выпадающего списка на стартовой странице. */
export const QUIZ_MODES: ReadonlyArray<{ value: QuizMode; label: string }> = [
  { value: 'normal', label: 'Обычный тест (случайный выбор билетов)' },
  { value: 'extended', label: 'Расширенный тест (учет статистики ответов)' },
  { value: 'hard', label: 'Только сложные билеты (помеченные как hard)' },
  { value: 'errors', label: 'Повторение ошибок (выдача билетов, где были ошибки)' },
]

/** Короткие названия режимов для заголовка страницы теста. */
export const QUIZ_MODE_LABELS: Record<QuizMode, string> = {
  normal: 'обычный тест',
  extended: 'расширенный тест',
  hard: 'только сложные билеты',
  errors: 'повторение ошибок',
}

export function isQuizMode(value: unknown): value is QuizMode {
  return (
    value === 'normal' ||
    value === 'extended' ||
    value === 'hard' ||
    value === 'errors'
  )
}

/** Прочитать сохранённый вариант прохождения теста. */
export function loadQuizMode(): QuizMode {
  try {
    const value = localStorage.getItem(MODE_STORAGE_KEY)
    return isQuizMode(value) ? value : DEFAULT_MODE
  } catch {
    return DEFAULT_MODE
  }
}

/** Сохранить выбранный вариант прохождения теста. */
export function saveQuizMode(mode: QuizMode): void {
  try {
    localStorage.setItem(MODE_STORAGE_KEY, mode)
  } catch {
    /* localStorage недоступен — работаем без сохранения */
  }
}

/** Ведётся ли статистика ответов в выбранном режиме. */
export function modeRecordsStats(mode: QuizMode): boolean {
  return mode !== 'errors'
}

/** Равновероятный случайный номер из `pool`, по возможности не из `excluded`. */
function pickUniform(pool: readonly number[], excluded: ReadonlySet<number>): number {
  if (pool.length === 0) return TICKET_MIN // защита: пустой пул
  let options = pool.filter((n) => !excluded.has(n))
  if (options.length === 0) options = [...pool]
  return options[randInt(0, options.length - 1)]
}

/**
 * Выбрать следующий билет согласно выбранному режиму прохождения.
 *
 * - `normal` — равновероятный случайный билет из общего списка, статистика
 *   правильных и ошибочных ответов на выбор НЕ влияет;
 * - `extended` — расширенный алгоритм (`pickTicket`), опирающийся на статистику;
 * - `hard` — только сложные билеты: билеты с ошибками выдаются преимущественно
 *   (~2/3), независимо от того, помечены ли они `hard`; остальное — случайные
 *   `hard`-билеты без ошибок (если ошибок нет — только случайные `hard`);
 * - `errors` — случайный билет только из списка ошибочных.
 */
export function pickForMode(
  mode: QuizMode,
  extend: boolean,
  stats: ErrorStats,
  training: number,
  recent: number[],
): PickResult {
  const recentSet = new Set(recent)
  switch (mode) {
    case 'normal':
      return { number: pickUniform([...ALL_NUMBERS], recentSet), training: 0 }
    case 'extended':
      return pickTicket(extend, stats, training, recent)
    case 'hard': {
      // Ошибочные билеты показываются преимущественно (~2/3), независимо от
      // того, помечены ли они hard; остальное — случайные сложные билеты.
      const errNumbers = stats.errorNumbers()
      const correctNumbers = new Set(stats.correctNumbers())
      if (errNumbers.length === 0) {
        return {
          number: pickRandom(extend, recentSet, correctNumbers, HARD_NUMBERS),
          training: 0,
        }
      }
      if (Math.random() < HARD_ERROR_SHARE) {
        // Приоритетная выдача ошибочного билета (по возможности не из recent).
        let options = errNumbers.filter((n) => !recentSet.has(n))
        if (options.length === 0) options = errNumbers
        return { number: options[randInt(0, options.length - 1)], training: 0 }
      }
      // «Наполнение» — случайный сложный билет без ошибок.
      const excluded = new Set<number>([...recentSet, ...errNumbers])
      return {
        number: pickRandom(extend, excluded, correctNumbers, HARD_NUMBERS),
        training: 0,
      }
    }
    case 'errors': {
      const errNumbers = stats.errorNumbers()
      if (errNumbers.length === 0) {
        return { number: pickUniform([...ALL_NUMBERS], recentSet), training: 0 }
      }
      return { number: pickUniform(errNumbers, recentSet), training: 0 }
    }
  }
}

// ---------------------------------------------------------------------------
// Сессия тренировки
// ---------------------------------------------------------------------------

/**
 * Состояние тренировки: статистика ошибок + счётчик `training` + окно
 * последних показанных билетов `recent`. Интерфейс для UI.
 */
export class TrainingSession {
  readonly stats: ErrorStats

  /** Текущий режим прохождения теста. */
  mode: QuizMode = DEFAULT_MODE

  private training = 0
  private recent: number[] = []

  constructor(stats: ErrorStats = new ErrorStats()) {
    this.stats = stats
  }

  /** Записать результат ответа (обновляет и сохраняет статистику ошибок). */
  record(number: number, correct: boolean): void {
    if (modeRecordsStats(this.mode)) this.stats.record(number, correct)
  }

  /** Выбрать номер следующего билета и сдвинуть окно последних показанных. */
  next(extend: boolean): number {
    const result = pickForMode(
      this.mode,
      extend,
      this.stats,
      this.training,
      this.recent,
    )
    this.training = result.training
    this.recent.push(result.number)
    if (this.recent.length > RECENT_LIMIT) this.recent.shift()
    return result.number
  }

  /**
   * Сбросить счётчик тренировки и окно последних билетов.
   * Статистика ошибок при этом сохраняется (как и в оригинале).
   */
  reset(): void {
    this.training = 0
    this.recent = []
  }
}
