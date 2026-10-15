import React, { useRef, useEffect, useState } from 'react'
import { Send, Zap, Loader2, ChevronDown, ChevronUp } from 'lucide-react'

const EXAMPLE_QUERIES = [
  "Show top 10 customers by revenue",
  "List all delivered orders this year",
  "Which products are low in stock?",
  "Show total sales by payment method",
  "Find orders with status cancelled",
  "Show recent transactions",
  "List products in Electronics category",
  "Top 5 selling products",
]

export default function QueryInput({ onSubmit, loading }) {
  const [query, setQuery]         = React.useState('')
  const [showExamples, setShowEx] = useState(false)
  const textareaRef           = useRef(null)

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 120) + 'px'
    }
  }, [query])

  const handleSubmit = (e) => {
    e && e.preventDefault()
    if (!query.trim() || loading) return
    onSubmit(query.trim())
    setQuery('')
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) handleSubmit()
  }

  const useExample = (q) => {
    setQuery(q)
    textareaRef.current?.focus()
  }

  return (
    <div className="space-y-3">
      {/* Example chips toggle */}
      <div>
        <button
          onClick={() => setShowEx(p => !p)}
          className="flex items-center gap-1.5 text-xs text-slate-500 hover:text-accent transition-colors mb-2"
        >
          <Zap size={11} className="text-accent" />
          Example queries — click to try
          {showExamples ? <ChevronUp size={11} /> : <ChevronDown size={11} />}
        </button>
        {showExamples && (
          <div className="flex flex-wrap gap-2 animate-fade-in">
            {EXAMPLE_QUERIES.map(q => (
              <button
                key={q}
                onClick={() => useExample(q)}
                className="text-xs px-3 py-1.5 rounded-full border border-white/10 text-slate-400
                           hover:border-accent/40 hover:text-accent hover:bg-accent/5
                           transition-all duration-150 font-mono"
              >
                {q}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Input area */}
      <form onSubmit={handleSubmit} className="relative gradient-border rounded-2xl">
        <div className="glass rounded-2xl overflow-hidden">
          <textarea
            ref={textareaRef}
            id="nl-query-input"
            value={query}
            onChange={e => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask anything about your data… e.g., 'Show me top 10 customers by total spend this year'"
            rows={2}
            className="w-full bg-transparent px-5 pt-3 pb-12 text-sm text-slate-200
                       placeholder-slate-600 resize-none outline-none leading-relaxed"
          />
          {/* Footer bar */}
          <div className="absolute bottom-0 left-0 right-0 flex items-center justify-between
                          px-4 py-2.5 border-t border-white/5">
            <span className="text-[10px] text-slate-600">Ctrl+Enter to submit</span>
            <button
              type="submit"
              disabled={!query.trim() || loading}
              id="submit-query-btn"
              className="flex items-center gap-2 px-4 py-1.5 rounded-xl text-sm font-medium
                         bg-accent text-white disabled:opacity-40 disabled:cursor-not-allowed
                         hover:bg-accent-light active:scale-95 transition-all duration-150
                         shadow-glow-sm neon-pulse"
            >
              {loading
                ? <><Loader2 size={14} className="animate-spin" /> Thinking…</>
                : <><Send size={14} /> Ask SQL</>
              }
            </button>
          </div>
        </div>
      </form>
    </div>
  )
}
