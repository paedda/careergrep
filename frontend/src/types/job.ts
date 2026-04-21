export type JobStatus = 'new' | 'seen' | 'applied' | 'rejected' | 'not_interested'

export interface Job {
  id: string
  source: string
  external_id: string
  company: string
  title: string
  url: string
  location: string | null
  remote: boolean | null
  posted_at: string
  fetched_at: string
  description: string
  description_text: string
  keyword_score: number
  claude_score: number | null
  claude_reasoning: string | null
  claude_red_flags: string[]
  status: JobStatus
  notes: string | null
}
