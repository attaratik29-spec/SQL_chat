import React, { useState, useRef, useEffect } from 'react'
import {
  Sparkles, Database, MessageSquare, ChevronLeft,
  ChevronRight, RotateCcw, AlertCircle, CheckCircle2,
  Terminal, PanelLeftClose, PanelLeft, Info,
} from 'lucide-react'

import SchemaViewer       from './components/SchemaViewer'
import QueryInput         from './components/QueryInput'
import ClarificationWidget from './components/ClarificationWidget'
import SqlBlock           from './components/SqlBlock'
import ResultsPanel       from './components/ResultsPanel'
import { submitQuery, submitClarified } from './api/client'

// ─── History item types ────────────────────────────────────────
//  { type:'user',          text }
//  { type:'clarification', data: { message, questions, originalQuery, partialIntent } }
//  { type:'success',       data: { sql, data, columns, rowCount, ms } }
//  { type:'error',         text }

function HistoryUserBubble({ text }) {
  return (
    <div className="flex justify-end animate-fade-in">
      <div className="max-w-[75%] px-4 py-2.5 rounded-2xl rounded-br-sm
                      bg-gradient-to-br from-accent to-purple-600 text-white text-sm shadow-glow-sm">
        {text}
      </div>
    </div>
  )
}

function HistorySuccessBlock({ data }) {
  return (
    <div className="space-y-3 animate-slide-up">
      <div className="flex items-center gap-2 text-emerald-400 text-xs font-medium">
        <CheckCircle2 size={14} />
        <span>Query resolved successfully</span>
      </div>
      <SqlBlock sql={data.sql} />
      <ResultsPanel
        data={data.data}
        columns={data.columns}
        rowCount={data.rowCount}
        executionMs={data.ms}
      />
    </div>
  )
}

function HistoryErrorBlock({ text }) {
  return (
    <div className="flex items-start gap-3 px-4 py-3 rounded-xl bg-red-500/8 border border-red-500/20 animate-fade-in">
      <AlertCircle size={16} className="text-red-400 flex-shrink-0 mt-0.5" />
      <p className="text-sm text-red-300">{text}</p>
    </div>
  )
}

export default function App() {
  const [history,        setHistory]   = useState([])
  const [loading,        setLoading]   = useState(false)
  const [sidebarOpen,    setSidebar]   = useState(true)
  const bottomRef                      = useRef(null)

  // Auto-scroll on new history items
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [history])

  // ── Push a history item ──────────────────────────────────────
  const push = (item) => setHistory(h => [...h, item])

  // ── Handle NL query submission ───────────────────────────────
  const handleQuery = async (query) => {
    push({ type: 'user', text: query })
    setLoading(true)
    try {
      const { data } = await submitQuery(query)
      if (data.status === 'clarification_needed') {
        push({
          type: 'clarification',
          data: {
            message:       data.message,
            questions:     data.questions,
            originalQuery: data.original_query,
            partialIntent: data.partial_intent,
          },
        })
      } else {
        push({
          type: 'success',
          data: {
            sql:      data.sql,
            data:     data.data,
            columns:  data.columns,
            rowCount: data.row_count,
            ms:       data.execution_ms,
          },
        })
      }
    } catch (err) {
      const msg = err?.response?.data?.detail || err.message || 'Unknown error'
      push({ type: 'error', text: `Backend error: ${msg}` })
    } finally {
      setLoading(false)
    }
  }

  // ── Handle clarification submission ─────────────────────────
  const handleClarified = async (originalQuery, answers, partialIntent) => {
    setLoading(true)
    try {
      const { data } = await submitClarified(originalQuery, answers, partialIntent)
      push({
        type: 'success',
        data: {
          sql:      data.sql,
          data:     data.data,
          columns:  data.columns,
          rowCount: data.row_count,
          ms:       data.execution_ms,
        },
      })
    } catch (err) {
      const msg = err?.response?.data?.detail || err.message || 'Unknown error'
      push({ type: 'error', text: `Backend error: ${msg}` })
    } finally {
      setLoading(false)
    }
  }

  const clearHistory = () => setHistory([])

  return (
    <div className="h-screen flex flex-col overflow-hidden bg-surface-900">
      {/* ── Top Bar ─────────────────────────────────────────── */}
      <header className="flex-shrink-0 flex items-center justify-between px-5 py-3
                         border-b border-white/5 glass z-10">
        <div className="flex items-center gap-3">
          <div className="p-2 rounded-xl bg-accent/15 neon-pulse">
            <Sparkles size={18} className="text-accent" />
          </div>
          <div>
            <h1 className="text-base font-bold gradient-text leading-none">SQL Whisperer</h1>
            <p className="text-[10px] text-slate-500 mt-0.5">Text-to-SQL Engine with Clarification Loop</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {/* DB status pill */}
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-surface-700 border border-white/5 text-xs">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse-slow" />
            <Database size={12} className="text-slate-400" />
            <span className="text-slate-400">E-Commerce SQLite</span>
          </div>

          {history.length > 0 && (
            <button
              onClick={clearHistory}
              id="clear-history-btn"
              className="flex items-center gap-1.5 text-xs text-slate-500 hover:text-slate-300
                         px-3 py-1.5 rounded-xl hover:bg-white/5 transition-all"
            >
              <RotateCcw size={12} /> Clear
            </button>
          )}

          <button
            onClick={() => setSidebar(p => !p)}
            id="toggle-sidebar-btn"
            className="p-2 rounded-xl hover:bg-white/5 text-slate-400 hover:text-slate-200 transition-all"
            title="Toggle schema sidebar"
          >
            {sidebarOpen ? <PanelLeftClose size={16} /> : <PanelLeft size={16} />}
          </button>
        </div>
      </header>

      {/* ── Main Layout ──────────────────────────────────────── */}
      <div className="flex flex-1 overflow-hidden">

        {/* ── Schema Sidebar ──────────────────────────────── */}
        <aside
          className={`flex-shrink-0 border-r border-white/5 glass transition-all duration-300 overflow-hidden ${
            sidebarOpen ? 'w-72' : 'w-0'
          }`}
        >
          {sidebarOpen && <SchemaViewer />}
        </aside>

        {/* ── Main Panel ──────────────────────────────────── */}
        <main className="flex-1 flex flex-col overflow-hidden">

          {/* Conversation area */}
          <div className="flex-1 overflow-y-auto px-6 py-6 space-y-6">
            {/* Empty state */}
            {history.length === 0 && (
              <div className="flex flex-col items-center justify-center h-full text-center gap-5 animate-fade-in">
                <div className="relative">
                  <div className="absolute inset-0 rounded-full bg-accent/20 blur-2xl scale-150" />
                  <div className="relative p-5 rounded-2xl bg-accent/10 border border-accent/20">
                    <MessageSquare size={40} className="text-accent" />
                  </div>
                </div>
                <div>
                  <h2 className="text-xl font-bold text-white mb-2">Ask your database anything</h2>
                  <p className="text-sm text-slate-500 max-w-sm leading-relaxed">
                    Type a natural language question below. The engine will clarify any ambiguities
                    before generating safe, executable SQL.
                  </p>
                </div>
                <div className="flex items-center gap-2 px-4 py-2 rounded-xl bg-surface-700 border border-white/5 text-xs text-slate-500">
                  <Info size={12} className="text-accent" />
                  Only safe <span className="text-accent font-mono mx-1">SELECT</span> statements are executed — your data is read-only.
                </div>
              </div>
            )}

            {/* History items */}
            {history.map((item, idx) => (
              <div key={idx}>
                {item.type === 'user' && (
                  <HistoryUserBubble text={item.text} />
                )}
                {item.type === 'clarification' && (
                  <ClarificationWidget
                    {...item.data}
                    onResolved={handleClarified}
                    loading={loading && idx === history.length - 1}
                  />
                )}
                {item.type === 'success' && (
                  <HistorySuccessBlock data={item.data} />
                )}
                {item.type === 'error' && (
                  <HistoryErrorBlock text={item.text} />
                )}
              </div>
            ))}

            <div ref={bottomRef} />
          </div>

          {/* Input bar */}
          <div className="flex-shrink-0 px-6 pb-6 pt-3 border-t border-white/5 bg-surface-900/80 backdrop-blur-sm">
            <QueryInput onSubmit={handleQuery} loading={loading} />
          </div>
        </main>
      </div>
    </div>
  )
}
