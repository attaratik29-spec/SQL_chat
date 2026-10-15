import React, { useState } from 'react'
import { HelpCircle, ChevronRight, CheckCircle2, Loader2 } from 'lucide-react'

function QuestionCard({ question, answer, onAnswer }) {
  return (
    <div className="space-y-2 animate-slide-up">
      <p className="text-sm font-medium text-slate-200 flex items-center gap-2">
        <HelpCircle size={14} className="text-accent flex-shrink-0" />
        {question.text}
      </p>

      {question.type === 'choice' ? (
        <div className="flex flex-wrap gap-2 pl-5">
          {question.options.map(opt => (
            <button
              key={opt}
              onClick={() => onAnswer(question.id, opt)}
              className={`choice-btn text-xs px-3 py-1.5 rounded-lg font-medium transition-all
                         ${answer === opt ? 'selected' : ''}`}
            >
              {answer === opt && <CheckCircle2 size={12} className="inline mr-1 text-accent" />}
              {opt}
            </button>
          ))}
        </div>
      ) : (
        <input
          type="text"
          placeholder="Type your answer…"
          value={answer || ''}
          onChange={e => onAnswer(question.id, e.target.value)}
          className="ml-5 bg-surface-700 border border-white/10 rounded-lg px-3 py-1.5
                     text-sm text-slate-200 placeholder-slate-600 outline-none w-full max-w-sm
                     focus:border-accent/50 transition-colors"
        />
      )}
    </div>
  )
}

export default function ClarificationWidget({
  message, questions, originalQuery, partialIntent, onResolved, loading,
}) {
  const [answers, setAnswers] = useState({})

  const setAnswer = (id, val) => setAnswers(p => ({ ...p, [id]: val }))

  const allAnswered = questions.every(q => answers[q.id])

  return (
    <div className="animate-fade-in rounded-2xl border border-accent/20 bg-accent/5 p-5 space-y-5">
      {/* Header */}
      <div className="flex items-start gap-3">
        <div className="p-2 rounded-xl bg-accent/15 flex-shrink-0 mt-0.5">
          <HelpCircle size={18} className="text-accent" />
        </div>
        <div>
          <h3 className="text-sm font-semibold text-white">Clarification Needed</h3>
          <p className="text-xs text-slate-400 mt-0.5">{message}</p>
        </div>
      </div>

      {/* Original query badge */}
      <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-surface-700 border border-white/5 w-fit">
        <span className="text-[10px] text-slate-500 uppercase tracking-wider">Query:</span>
        <span className="text-xs text-slate-300 font-mono">{originalQuery}</span>
      </div>

      {/* Questions */}
      <div className="space-y-4 pl-1">
        {questions.map(q => (
          <QuestionCard
            key={q.id}
            question={q}
            answer={answers[q.id]}
            onAnswer={setAnswer}
          />
        ))}
      </div>

      {/* Progress */}
      <div className="flex items-center justify-between pt-1">
        <div className="flex gap-1">
          {questions.map(q => (
            <div
              key={q.id}
              className={`h-1 w-8 rounded-full transition-colors duration-300 ${
                answers[q.id] ? 'bg-accent' : 'bg-surface-500'
              }`}
            />
          ))}
        </div>
        <span className="text-xs text-slate-500">
          {Object.keys(answers).length} / {questions.length} answered
        </span>
      </div>

      {/* Submit */}
      <button
        disabled={!allAnswered || loading}
        id="submit-clarification-btn"
        onClick={() => onResolved(originalQuery, answers, partialIntent)}
        className="flex items-center gap-2 px-5 py-2 rounded-xl text-sm font-semibold
                   bg-gradient-to-r from-accent to-purple-500 text-white
                   disabled:opacity-40 disabled:cursor-not-allowed
                   hover:from-accent-light hover:to-purple-400
                   active:scale-[0.98] transition-all duration-150 shadow-glow-accent"
      >
        {loading
          ? <><Loader2 size={14} className="animate-spin" /> Generating SQL…</>
          : <><ChevronRight size={14} /> Generate SQL</>
        }
      </button>
    </div>
  )
}
