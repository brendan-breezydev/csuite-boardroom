interface Props {
  phase: 1 | 2 | 3 | null
}

const phases = [
  { n: 1, label: 'Problem Analysis' },
  { n: 2, label: 'Board Deliberation' },
  { n: 3, label: 'Board Resolution' },
]

export default function PhaseIndicator({ phase }: Props) {
  if (!phase) return null
  return (
    <div className="flex items-center gap-2 px-6 py-3 bg-brand-navy/5 border-b border-brand-navy/10">
      {phases.map((p, i) => (
        <div key={p.n} className="flex items-center gap-2">
          <div
            className={`flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider px-3 py-1 rounded-full transition-all ${
              phase === p.n
                ? 'bg-brand-navy text-white'
                : phase > p.n
                ? 'bg-brand-blue/20 text-brand-blue'
                : 'text-brand-navy/30'
            }`}
          >
            <span
              className={`w-4 h-4 rounded-full flex items-center justify-center text-[10px] font-bold ${
                phase === p.n ? 'bg-brand-blue text-white' : phase > p.n ? 'bg-brand-blue/40 text-white' : 'bg-brand-navy/10'
              }`}
            >
              {phase > p.n ? '✓' : p.n}
            </span>
            {p.label}
          </div>
          {i < phases.length - 1 && (
            <span className={`text-brand-navy/20 text-xs ${phase > p.n ? 'text-brand-blue/40' : ''}`}>›</span>
          )}
        </div>
      ))}
    </div>
  )
}
