import React, { useState } from 'react'
import { Table2, Clock, Rows, ChevronLeft, ChevronRight } from 'lucide-react'

const PAGE_SIZE = 20

function MetricPill({ icon: Icon, label, value, color = 'text-accent' }) {
  return (
    <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-surface-700 border border-white/5">
      <Icon size={12} className={color} />
      <span className="text-[10px] text-slate-500 uppercase tracking-wider">{label}</span>
      <span className={`text-xs font-semibold ${color}`}>{value}</span>
    </div>
  )
}

export default function ResultsPanel({ data, columns, rowCount, executionMs }) {
  const [page, setPage] = useState(0)

  if (!data || data.length === 0) {
    return (
      <div className="rounded-2xl border border-white/5 bg-surface-800/50 p-8 text-center animate-fade-in">
        <Table2 size={32} className="mx-auto mb-3 text-slate-600" />
        <p className="text-sm text-slate-500">No results returned for this query.</p>
      </div>
    )
  }

  const totalPages = Math.ceil(data.length / PAGE_SIZE)
  const pageData   = data.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE)
  const cols       = columns.length > 0 ? columns : Object.keys(data[0])

  const formatCell = (val) => {
    if (val === null || val === undefined) return <span className="text-slate-600 italic text-xs">null</span>
    if (typeof val === 'number') return <span className="text-amber-300 font-mono">{val.toLocaleString()}</span>
    const str = String(val)
    // Date-like
    if (/^\d{4}-\d{2}-\d{2}/.test(str)) return <span className="text-sky-300 font-mono text-xs">{str}</span>
    // Status badges
    const statusColors = {
      delivered:  'bg-emerald-500/15 text-emerald-400 border-emerald-500/25',
      shipped:    'bg-blue-500/15 text-blue-400 border-blue-500/25',
      processing: 'bg-yellow-500/15 text-yellow-400 border-yellow-500/25',
      cancelled:  'bg-red-500/15 text-red-400 border-red-500/25',
      refunded:   'bg-purple-500/15 text-purple-400 border-purple-500/25',
      pending:    'bg-slate-500/15 text-slate-400 border-slate-500/25',
      completed:  'bg-emerald-500/15 text-emerald-400 border-emerald-500/25',
      failed:     'bg-red-500/15 text-red-400 border-red-500/25',
      active:     'bg-emerald-500/15 text-emerald-400 border-emerald-500/25',
    }
    if (statusColors[str.toLowerCase()]) {
      return (
        <span className={`inline-block px-2 py-0.5 rounded-full text-xs border font-medium
                         ${statusColors[str.toLowerCase()]}`}>
          {str}
        </span>
      )
    }
    return str
  }

  return (
    <div className="space-y-3 animate-slide-up">
      {/* Metrics bar */}
      <div className="flex flex-wrap gap-2">
        <MetricPill icon={Rows}  label="Rows"    value={rowCount.toLocaleString()} color="text-accent" />
        <MetricPill icon={Clock} label="Time"    value={`${executionMs} ms`} color="text-emerald-400" />
        <MetricPill icon={Table2}label="Columns" value={cols.length} color="text-purple-400" />
        {totalPages > 1 && (
          <MetricPill icon={ChevronRight} label="Page" value={`${page+1}/${totalPages}`} color="text-amber-400" />
        )}
      </div>

      {/* Table */}
      <div className="rounded-2xl border border-white/8 overflow-hidden">
        <div className="overflow-x-auto overflow-y-auto" style={{ maxHeight: '420px' }}>
          <table className="w-full text-sm border-collapse">
            <thead className="sticky top-0 z-10">
              <tr className="bg-surface-700">
                <th className="px-4 py-2.5 text-left text-[10px] text-slate-500 uppercase tracking-wider w-10 border-b border-white/5">
                  #
                </th>
                {cols.map(col => (
                  <th
                    key={col}
                    className="px-4 py-2.5 text-left text-[10px] text-slate-400 uppercase tracking-wider
                               border-b border-white/5 font-medium whitespace-nowrap"
                  >
                    {col}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {pageData.map((row, i) => (
                <tr key={i} className="data-row border-b border-white/3 last:border-0">
                  <td className="px-4 py-2.5 text-xs text-slate-600 font-mono">
                    {page * PAGE_SIZE + i + 1}
                  </td>
                  {cols.map(col => (
                    <td key={col} className="px-4 py-2.5 text-slate-300 whitespace-nowrap max-w-xs truncate">
                      {formatCell(row[col])}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between px-4 py-2.5 bg-surface-700 border-t border-white/5">
            <button
              onClick={() => setPage(p => Math.max(0, p-1))}
              disabled={page === 0}
              id="prev-page-btn"
              className="flex items-center gap-1 text-xs text-slate-400 px-2.5 py-1 rounded-lg
                         hover:bg-white/8 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
            >
              <ChevronLeft size={14} /> Prev
            </button>
            <div className="flex gap-1">
              {Array.from({ length: Math.min(totalPages, 7) }, (_, i) => {
                const pn = totalPages <= 7 ? i : i === 0 ? 0 : i === 6 ? totalPages-1 : page - 2 + i
                return (
                  <button
                    key={i}
                    onClick={() => setPage(pn)}
                    className={`w-7 h-7 rounded-lg text-xs transition-all
                               ${page === pn ? 'bg-accent text-white' : 'text-slate-500 hover:bg-white/8'}`}
                  >
                    {pn + 1}
                  </button>
                )
              })}
            </div>
            <button
              onClick={() => setPage(p => Math.min(totalPages-1, p+1))}
              disabled={page === totalPages-1}
              id="next-page-btn"
              className="flex items-center gap-1 text-xs text-slate-400 px-2.5 py-1 rounded-lg
                         hover:bg-white/8 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
            >
              Next <ChevronRight size={14} />
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
