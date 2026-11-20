export type AnswerLetter = 'a' | 'b' | 'c' | 'd'

export interface Ticket {
  number: number
  question: string
  answers: [string, string, string, string]
  image: string | null
  hard: boolean
  explanation?: string | null
}

export interface ShuffledChoice {
  letter: AnswerLetter
  text: string
}
