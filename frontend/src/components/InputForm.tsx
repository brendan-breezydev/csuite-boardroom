import { useState, useRef } from 'react'

interface Props {
  onSubmit: (situation: string) => void
  isRunning: boolean
  onReset: () => void
  hasResults: boolean
}

const EXAMPLE = "We are a Series B SaaS company with 18 months of runway. A competitor just raised $200M and is undercutting our pricing by 40%. The board wants us to match their price or raise a bridge round. Our gross margin is already tight at 58%."

export default function InputForm({ onSubmit, isRunning, onReset, hasResults }: Props) {
  const [value, setValue] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const trimmed = value.trim()
    if (!trimmed || isRunning) return
    onSubmit(trimmed)
  }

  const fillExample = () => {
    setValue(EXAMPLE)
    textareaRef.current?.focus()
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-3">
      <div className="relative">
        <textarea
          ref={textareaRef}
          value={value}
          onChange={(e) => setValue(e.target.value)}
          disabled={isRunning}
          rows={5}
          placeholder="Describe your business situation, challenge, or decision…"
          className="w-full resize-none rounded-xl border border-brand-navy/15 bg-white px-4 py-3.5 text-sm text-brand-navy placeholder-brand-navy/30 focus:outline-none focus:ring-2 focus:ring-brand-blue/40 focus:border-brand-blue/40 disabled:opacity-50 disabled:cursor-not-allowed transition"
        />
        {!value && !isRunning && (
          <button
            type="button"
            onClick={fillExample}
            className="absolute bottom-3 right-3 text-[11px] text-brand-blue/60 hover:text-brand-blue underline underline-offset-2"
          >
            Try an example
          </button>
        )}
      </div>

      <div className="flex gap-2">
        <button
          type="submit"
          disabled={!value.trim() || isRunning}
          className="flex-1 bg-brand-navy hover:bg-brand-navy/90 disabled:opacity-40 disabled:cursor-not-allowed text-white font-bold text-sm uppercase tracking-widest py-3 px-6 rounded-xl transition-all"
        >
          {isRunning ? (
            <span className="flex items-center justify-center gap-2">
              <span className="w-3 h-3 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              Boardroom in session…
            </span>
          ) : (
            'Bring to the Board'
          )}
        </button>

        {hasResults && !isRunning && (
          <button
            type="button"
            onClick={onReset}
            className="px-4 py-3 rounded-xl border border-brand-navy/15 text-brand-navy/50 hover:text-brand-navy hover:border-brand-navy/30 text-sm font-medium transition"
          >
            New Session
          </button>
        )}
      </div>
    </form>
  )
}
