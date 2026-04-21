import type { Job, JobStatus } from '../types/job'

const BASE = '/api'

export async function fetchJobs(params: {
  status?: string
  min_score?: number
  source?: string
} = {}): Promise<Job[]> {
  const qs = new URLSearchParams()
  if (params.status) qs.set('status', params.status)
  if (params.min_score != null) qs.set('min_score', String(params.min_score))
  if (params.source) qs.set('source', params.source)

  const res = await fetch(`${BASE}/jobs?${qs}`)
  if (!res.ok) throw new Error('Failed to fetch jobs')
  return res.json()
}

export async function patchJob(
  id: string,
  update: { status?: JobStatus; notes?: string },
): Promise<Job> {
  const res = await fetch(`${BASE}/jobs/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(update),
  })
  if (!res.ok) throw new Error('Failed to update job')
  return res.json()
}

export async function runPipeline(): Promise<{ message: string; jobs_fetched: number }> {
  const res = await fetch(`${BASE}/pipeline/run`, { method: 'POST' })
  if (!res.ok) throw new Error('Pipeline failed')
  return res.json()
}
