import { useState } from 'react'
import type { Option } from '../types/events'

interface Props {
  options: Option[]
}

export default function OptionsPanel({ options }: Props) {
  const [open, setOpen] = useState(true)
  if (!options.length) return null

  return (
    <div className="bg-brand-navy/5 border border-brand-navy/10 rounded-xl overflow-hidden">
      <button
        onClick={() => setOpen((v) => !v)}
        className="w-full flex items-center justify-between px-5 py-3 text-left"
      >
        <span className="text-brand-navy font-bold text-xs uppercase tracking-widest">
          {options.length} Options on the Table
        </span>
        <span className="text-brand-blue text-sm">{open ? '▲' : '▼'}</span>
      </button>

      {open && (
        <div className="px-5 pb-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {options.map((opt, i) => (
            <div key={opt.name} className="bg-white border border-brand-navy/10 rounded-lg p-3 space-y-1.5 shadow-sm">
              <div className="flex items-start gap-2">
                <span className="flex-shrink-0 w-5 h-5 rounded-full bg-brand-navy text-white text-[10px] font-bold flex items-center justify-center mt-0.5">
                  {i + 1}
                </span>
                <p className="font-bold text-brand-navy text-sm leading-tight">{opt.name}</p>
              </div>
              <p className="text-brand-navy/60 text-xs leading-relaxed pl-7">{opt.summary}</p>
              <div className="pl-7 pt-1 space-y-1">
                <p className="text-[11px] text-brand-navy/40">
                  <span className="font-semibold text-brand-navy/60">Assumes: </span>
                  {opt.key_assumption}
                </p>
                <p className="text-[11px] text-red-400/70">
                  <span className="font-semibold">Kill if: </span>
                  {opt.kill_condition}
                </p>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
