import React, { useState, useEffect } from 'react'
import {
  Database, ChevronDown, ChevronRight, Key, Link,
  Columns, Hash, Type, ToggleLeft
} from 'lucide-react'
import { getSchema } from '../api/client'

const TYPE_ICONS = {
  INTEGER: <Hash size={11} className="text-orange-400" />,
  REAL:    <Hash size={11} className="text-yellow-400" />,
  TEXT:    <Type size={11} className="text-emerald-400" />,
  BOOLEAN: <ToggleLeft size={11} className="text-blue-400" />,
}

const getTypeIcon = (type = '') => {
  const t = type.toUpperCase().split('(')[0]
  return TYPE_ICONS[t] || <Type size={11} className="text-slate-400" />
}

const TABLE_COLORS = {
  users:        'bg-blue-500/20 text-blue-300 border-blue-500/30',
  products:     'bg-emerald-500/20 text-emerald-300 border-emerald-500/30',
  orders:       'bg-purple-500/20 text-purple-300 border-purple-500/30',
  order_items:  'bg-amber-500/20 text-amber-300 border-amber-500/30',
  categories:   'bg-pink-500/20 text-pink-300 border-pink-500/30',
  transactions: 'bg-cyan-500/20 text-cyan-300 border-cyan-500/30',
}

function TableCard({ name, info, isOpen, onToggle }) {
  const color = TABLE_COLORS[name] || 'bg-slate-500/20 text-slate-300 border-slate-500/30'
  const fkCols = new Set(info.foreign_keys.map(fk => fk.from_col))

  return (
    <div className="mb-2 rounded-xl overflow-hidden border border-white/5 transition-all duration-200">
      {/* Header */}
      <button
        onClick={onToggle}
        className="w-full flex items-center gap-3 px-3 py-2.5 hover:bg-white/5 transition-colors text-left group"
      >
        <span className={`flex-shrink-0 px-2 py-0.5 rounded-md text-xs font-mono border ${color}`}>
          {name}
        </span>
        <span className="text-xs text-slate-500 ml-auto">
          {info.row_count} rows
        </span>
        {isOpen
          ? <ChevronDown size={14} className="text-slate-500 flex-shrink-0 transition-transform group-hover:text-slate-300" />
          : <ChevronRight size={14} className="text-slate-500 flex-shrink-0 transition-transform group-hover:text-slate-300" />
        }
      </button>

      {/* Columns */}
      {isOpen && (
        <div className="border-t border-white/5 bg-surface-900/50">
          {info.columns.map(col => (
            <div
              key={col.name}
              className="flex items-center gap-2 px-4 py-1.5 hover:bg-white/3 transition-colors"
            >
              {col.pk
                ? <Key size={11} className="text-yellow-400 flex-shrink-0" title="Primary Key" />
                : fkCols.has(col.name)
                ? <Link size={11} className="text-sky-400 flex-shrink-0" title="Foreign Key" />
                : <span className="w-[11px] flex-shrink-0" />
              }
              <span className="text-xs text-slate-300 font-mono flex-1 truncate">{col.name}</span>
              <span className="flex items-center gap-1">
                {getTypeIcon(col.type)}
                <span className="text-[10px] text-slate-600 font-mono">{col.type?.split('(')[0]}</span>
              </span>
            </div>
          ))}

          {/* Foreign Keys */}
          {info.foreign_keys.length > 0 && (
            <div className="border-t border-white/5 px-4 py-2">
              <p className="text-[10px] text-slate-600 uppercase tracking-wider mb-1">FK Relations</p>
              {info.foreign_keys.map((fk, i) => (
                <div key={i} className="flex items-center gap-1 text-[10px] text-slate-500 font-mono py-0.5">
                  <span className="text-sky-500">{fk.from_col}</span>
                  <span className="text-slate-600">→</span>
                  <span className="text-emerald-500">{fk.to_table}.{fk.to_col}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default function SchemaViewer({ onTableClick }) {
  const [schema, setSchema]       = useState(null)
  const [openTables, setOpen]     = useState({ orders: true })
  const [loading, setLoading]     = useState(true)
  const [error, setError]         = useState(null)

  useEffect(() => {
    getSchema()
      .then(r => setSchema(r.data.schema))
      .catch(() => setError('Could not load schema. Is the backend running?'))
      .finally(() => setLoading(false))
  }, [])

  const toggle = name => setOpen(p => ({ ...p, [name]: !p[name] }))

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center gap-2 px-4 py-3 border-b border-white/5">
        <div className="p-1.5 rounded-lg bg-accent/10">
          <Database size={16} className="text-accent" />
        </div>
        <div>
          <h2 className="text-sm font-semibold text-white">Database Schema</h2>
          <p className="text-[10px] text-slate-500">E-Commerce Sample DB</p>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto px-3 py-3">
        {loading && (
          <div className="flex flex-col items-center justify-center h-32 gap-3">
            <div className="spinner" />
            <p className="text-xs text-slate-500">Loading schema…</p>
          </div>
        )}

        {error && (
          <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-xs text-red-400">
            {error}
          </div>
        )}

        {schema && Object.entries(schema).map(([name, info]) => (
          <TableCard
            key={name}
            name={name}
            info={info}
            isOpen={!!openTables[name]}
            onToggle={() => toggle(name)}
          />
        ))}
      </div>

      {/* Footer legend */}
      <div className="px-4 py-2 border-t border-white/5 flex gap-3 text-[10px] text-slate-600">
        <span className="flex items-center gap-1"><Key size={9} className="text-yellow-400" /> PK</span>
        <span className="flex items-center gap-1"><Link size={9} className="text-sky-400" /> FK</span>
        <span className="flex items-center gap-1"><Columns size={9} className="text-slate-500" /> Column</span>
      </div>
    </div>
  )
}
