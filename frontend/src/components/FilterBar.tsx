interface Filters {
  status: string
  min_score: number
  source: string
}

interface Props {
  filters: Filters
  onChange: (f: Filters) => void
  onRunPipeline: () => void
  running: boolean
}

const STATUSES = ['', 'new', 'seen', 'applied', 'not_interested', 'rejected']
const SOURCES = ['', 'greenhouse', 'ashby', 'workable', 'lever', 'arbeitnow', 'remoteok']

export function FilterBar({ filters, onChange, onRunPipeline, running }: Props) {
  return (
    <div className="flex flex-wrap gap-3 items-center p-4 bg-gray-50 border-b border-gray-200">
      <select
        className="border border-gray-300 rounded px-2 py-1 text-sm bg-white"
        value={filters.status}
        onChange={e => onChange({ ...filters, status: e.target.value })}
      >
        {STATUSES.map(s => (
          <option key={s} value={s}>{s || 'All statuses'}</option>
        ))}
      </select>

      <select
        className="border border-gray-300 rounded px-2 py-1 text-sm bg-white"
        value={filters.source}
        onChange={e => onChange({ ...filters, source: e.target.value })}
      >
        {SOURCES.map(s => (
          <option key={s} value={s}>{s || 'All sources'}</option>
        ))}
      </select>

      <label className="flex items-center gap-1 text-sm text-gray-600">
        Min score
        <input
          type="number"
          min={0}
          max={20}
          className="border border-gray-300 rounded px-2 py-1 w-16 text-sm"
          value={filters.min_score}
          onChange={e => onChange({ ...filters, min_score: Number(e.target.value) })}
        />
      </label>

      <button
        onClick={onRunPipeline}
        disabled={running}
        className="ml-auto px-3 py-1 text-sm rounded bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-50 cursor-pointer"
      >
        {running ? 'Running…' : 'Run pipeline'}
      </button>
    </div>
  )
}
