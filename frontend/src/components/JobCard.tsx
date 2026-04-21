import { useState } from 'react'
import type { Job, JobStatus } from '../types/job'
import { patchJob } from '../api/client'

interface Props {
  job: Job
  onUpdate: (updated: Job) => void
}

const STATUS_LABELS: Record<JobStatus, string> = {
  new: 'New',
  seen: 'Seen',
  applied: 'Applied',
  rejected: 'Rejected',
  not_interested: 'Not interested',
}

const STATUS_COLORS: Record<JobStatus, string> = {
  new: 'bg-blue-100 text-blue-800',
  seen: 'bg-gray-100 text-gray-700',
  applied: 'bg-green-100 text-green-800',
  rejected: 'bg-red-100 text-red-700',
  not_interested: 'bg-yellow-100 text-yellow-800',
}

export function JobCard({ job, onUpdate }: Props) {
  const [expanded, setExpanded] = useState(false)
  const [updating, setUpdating] = useState(false)

  async function setStatus(status: JobStatus) {
    setUpdating(true)
    const updated = await patchJob(job.id, { status })
    onUpdate(updated)
    setUpdating(false)
  }

  const score = job.claude_score ?? job.keyword_score
  const scoreLabel = job.claude_score != null ? `Claude: ${job.claude_score}/10` : `KW: ${job.keyword_score}`
  const postedDate = new Date(job.posted_at).toLocaleDateString()

  return (
    <div className="border border-gray-200 rounded-lg bg-white shadow-sm">
      {/* Header row */}
      <div className="p-4">
        <div className="flex items-start gap-3">
          {/* Score badge */}
          <div className={`flex-shrink-0 w-12 rounded-lg flex flex-col items-center justify-center py-1 ${score >= 7 ? 'bg-green-100 text-green-800' : score >= 4 ? 'bg-yellow-100 text-yellow-800' : 'bg-gray-100 text-gray-600'}`}>
            <span className="text-lg font-bold leading-none">{score}</span>
            <span className="text-[10px] font-medium uppercase tracking-wide opacity-70">score</span>
          </div>

          <div className="flex-1 min-w-0">
            <div className="flex flex-wrap items-center gap-2 mb-1">
              <a
                href={job.url}
                target="_blank"
                rel="noopener noreferrer"
                className="font-semibold text-gray-900 hover:text-indigo-600 truncate"
              >
                {job.title}
              </a>
              <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${STATUS_COLORS[job.status]}`}>
                {STATUS_LABELS[job.status]}
              </span>
            </div>

            <div className="text-sm text-gray-500 flex flex-wrap gap-x-3 gap-y-0.5">
              <span className="font-medium text-gray-700">{job.company}</span>
              {job.location && <span>{job.location}</span>}
              {job.remote && <span className="text-indigo-600">Remote</span>}
              <span>{job.source}</span>
              <span>{postedDate}</span>
            </div>

            {/* Claude reasoning */}
            {job.claude_reasoning && (
              <p className="mt-1 text-sm text-gray-600 italic">{job.claude_reasoning}</p>
            )}

            {/* Red flags */}
            {job.claude_red_flags.length > 0 && (
              <div className="mt-1 flex flex-wrap gap-1">
                {job.claude_red_flags.map((flag, i) => (
                  <span key={i} className="text-xs bg-red-50 text-red-700 px-2 py-0.5 rounded">
                    {flag}
                  </span>
                ))}
              </div>
            )}
          </div>

          <button
            onClick={() => setExpanded(e => !e)}
            className="flex-shrink-0 text-gray-400 hover:text-gray-600 text-sm px-2 cursor-pointer"
          >
            {expanded ? '▲' : '▼'}
          </button>
        </div>

        {/* Action buttons */}
        <div className="mt-3 flex flex-wrap gap-2 ml-13">
          {(['applied', 'not_interested', 'new'] as JobStatus[]).map(s => (
            <button
              key={s}
              disabled={updating || job.status === s}
              onClick={() => setStatus(s)}
              className="text-xs px-2 py-1 rounded border border-gray-300 hover:bg-gray-50 disabled:opacity-40 cursor-pointer"
            >
              {STATUS_LABELS[s]}
            </button>
          ))}
          <span className="text-xs text-gray-400 self-center">{scoreLabel}</span>
        </div>
      </div>

      {/* Expanded description */}
      {expanded && (
        <div className="border-t border-gray-100 p-4">
          <div
            className="prose prose-sm max-w-none text-gray-700 text-sm leading-relaxed max-h-96 overflow-y-auto"
            dangerouslySetInnerHTML={{ __html: job.description }}
          />
        </div>
      )}
    </div>
  )
}
