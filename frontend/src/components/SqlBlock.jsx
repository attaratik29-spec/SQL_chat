import React, { useState } from 'react'
import { Code2, Copy, Check } from 'lucide-react'

// ── Very lightweight SQL tokenizer for syntax highlighting ──────
function tokenize(sql) {
  const KEYWORDS = /\b(SELECT|FROM|WHERE|JOIN|LEFT|RIGHT|INNER|OUTER|ON|GROUP\s+BY|ORDER\s+BY|HAVING|LIMIT|OFFSET|DISTINCT|AS|AND|OR|NOT|IN|LIKE|BETWEEN|IS|NULL|ASC|DESC|CASE|WHEN|THEN|ELSE|END|WITH|UNION|ALL|EXISTS)\b/gi
  const FUNCTIONS= /\b(COUNT|SUM|AVG|MIN|MAX|COALESCE|IFNULL|ROUND|DATE|STRFTIME|SUBSTR|LOWER|UPPER|TRIM|LENGTH|CAST|TYPEOF)\b/gi
  const STRINGS  = /'([^']*)'/g
  const NUMBERS  = /\b(\d+(\.\d+)?)\b/g
  const OPERATORS= /([=<>!]+|[\+\-\*\/]|\bBETWEEN\b|\bLIKE\b)/gi

  let result = sql
    .replace(KEYWORDS,  m => `<span class="sql-keyword">${m}</span>`)
    .replace(FUNCTIONS, m => `<span class="sql-function">${m}</span>`)
    .replace(STRINGS,   m => `<span class="sql-string">${m}</span>`)
    .replace(NUMBERS,   m => `<span class="sql-number">${m}</span>`)

  return result
}

export default function SqlBlock({ sql }) {
  const [copied, setCopied] = useState(false)

  const copy = async () => {
    await navigator.clipboard.writeText(sql)
    setCopied(true)
    setTimeout(() => setCopied(false), 1500)
  }

  const highlighted = tokenize(sql)

  return (
    <div className="rounded-2xl overflow-hidden border border-white/8 animate-fade-in">
      {/* Header bar */}
      <div className="flex items-center justify-between px-4 py-2.5
                      bg-surface-700 border-b border-white/5">
        <div className="flex items-center gap-2">
          {/* Traffic-light dots */}
          <div className="flex gap-1.5">
            <div className="w-2.5 h-2.5 rounded-full bg-red-500/70" />
            <div className="w-2.5 h-2.5 rounded-full bg-yellow-500/70" />
            <div className="w-2.5 h-2.5 rounded-full bg-emerald-500/70" />
          </div>
          <Code2 size={13} className="text-accent ml-1" />
          <span className="text-xs text-slate-400 font-mono">Generated SQL</span>
        </div>
        <button
          onClick={copy}
          id="copy-sql-btn"
          className="flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-lg
                     text-slate-400 hover:text-white hover:bg-white/8 transition-all"
        >
          {copied
            ? <><Check size={12} className="text-emerald-400" /> Copied!</>
            : <><Copy size={12} /> Copy</>
          }
        </button>
      </div>

      {/* Code */}
      <div className="bg-surface-900 overflow-x-auto">
        <pre className="px-5 py-4 text-sm font-mono leading-relaxed text-slate-300 whitespace-pre-wrap">
          <code dangerouslySetInnerHTML={{ __html: highlighted }} />
        </pre>
      </div>
    </div>
  )
}
