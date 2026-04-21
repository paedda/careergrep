import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { fetchJobs, runPipeline } from './api/client'
import { FilterBar } from './components/FilterBar'
import { JobCard } from './components/JobCard'
import type { Job } from './types/job'

interface Filters {
  status: string
  min_score: number
  source: string
}

export default function App() {
  const queryClient = useQueryClient()
  const [filters, setFilters] = useState<Filters>({ status: 'new', min_score: 0, source: '' })

  const { data: jobs = [], isLoading, isError } = useQuery({
    queryKey: ['jobs', filters],
    queryFn: () => fetchJobs({
      status: filters.status || undefined,
      min_score: filters.min_score,
      source: filters.source || undefined,
    }),
  })

  const pipeline = useMutation({
    mutationFn: runPipeline,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['jobs'] }),
  })

  function handleUpdate(updated: Job) {
    // Optimistically update the cache so the UI reflects the change immediately
    queryClient.setQueryData<Job[]>(['jobs', filters], prev =>
      prev?.map(j => j.id === updated.id ? updated : j) ?? []
    )
  }

  const newCount = jobs.filter(j => j.status === 'new').length
  const appliedCount = jobs.filter(j => j.status === 'applied').length

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 px-6 py-4 flex items-center gap-4">
        <h1 className="text-xl font-bold text-gray-900">careergrep</h1>
        <div className="text-sm text-gray-500 flex gap-4">
          <span>{newCount} new</span>
          <span>{appliedCount} applied</span>
          <span>{jobs.length} shown</span>
        </div>
        {pipeline.isSuccess && (
          <span className="text-sm text-green-600">
            Pipeline done — {pipeline.data.jobs_fetched} new jobs fetched
          </span>
        )}
        {pipeline.isError && (
          <span className="text-sm text-red-600">Pipeline failed</span>
        )}
      </header>

      <FilterBar
        filters={filters}
        onChange={setFilters}
        onRunPipeline={() => pipeline.mutate()}
        running={pipeline.isPending}
      />

      <main className="max-w-4xl mx-auto p-4">
        {isLoading && (
          <p className="text-center text-gray-500 py-12">Loading jobs…</p>
        )}
        {isError && (
          <p className="text-center text-red-500 py-12">
            Failed to load jobs. Is the API running?
          </p>
        )}
        {!isLoading && !isError && jobs.length === 0 && (
          <p className="text-center text-gray-400 py-12">
            No jobs match the current filters.
          </p>
        )}
        <div className="flex flex-col gap-3">
          {jobs.map(job => (
            <JobCard key={job.id} job={job} onUpdate={handleUpdate} />
          ))}
        </div>
      </main>
    </div>
  )
}
