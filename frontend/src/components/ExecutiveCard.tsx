import type { ExecRole, ExecState } from '../types/events'
import MessageBubble from './MessageBubble'

interface Props {
  execState: ExecState
  isActive: boolean
}

const EXEC_META: Record<ExecRole, { archetypes: string; bg: string; initial: string }> = {
  CEO: { archetypes: 'Buffett · Cook · Doronin',   bg: 'bg-brand-ceo',  initial: 'CE' },
  CFO: { archetypes: 'Munger · Marks · Porat',      bg: 'bg-brand-cfo',  initial: 'CF' },
  COO: { archetypes: 'Bezos · Sandberg · Barra',    bg: 'bg-brand-coo',  initial: 'CO' },
  CMO: { archetypes: 'Godin · Jobs · Chesky',       bg: 'bg-brand-cmo',  initial: 'CM' },
  CTO: { archetypes: 'Vogels · Torvalds · Huang',   bg: 'bg-brand-cto',  initial: 'CT' },
}

export default function ExecutiveCard({ execState, isActive }: Props) {
  const { role, streamingText, statement, scores, isStreaming, isDone } = execState
  const meta = EXEC_META[role]

  const preferredOption = statement?.preferred_option
  const keyConcern = statement?.key_concern
  const vetoes = statement?.veto_options ?? []

  return (
    <div
      className={`fade-slide-in rounded-xl overflow-hidden transition-all duration-500 ${
        isActive ? 'active-speaker ring-2 ring-brand-blue' : isDone ? 'opacity-90' : 'opacity-60'
      }`}
    >
      {/* Card header */}
      <div className={`${meta.bg} px-5 py-4 flex items-center gap-4`}>
        <div className="w-10 h-10 rounded-full bg-white/15 flex items-center justify-center text-white font-extrabold text-xs tracking-wider flex-shrink-0">
          {meta.initial}
        </div>
        <div className="min-w-0">
          <p className="text-white font-extrabold text-sm uppercase tracking-widest">{role}</p>
          <p className="text-white/50 text-xs font-medium truncate">{meta.archetypes}</p>
        </div>
        {isActive && isStreaming && (
          <span className="ml-auto flex-shrink-0 flex items-center gap-1.5 text-white/70 text-xs">
            <span className="w-1.5 h-1.5 rounded-full bg-brand-blue animate-pulse" />
            Speaking
          </span>
        )}
        {isDone && (
          <span className="ml-auto flex-shrink-0 text-white/50 text-xs">✓</span>
        )}
      </div>

      {/* Card body */}
      <div className={`${meta.bg} bg-opacity-90 px-5 pb-5 space-y-3`}>
        {/* Streaming opening text */}
        {(streamingText || isStreaming) && (
          <MessageBubble text={streamingText} isStreaming={isStreaming && !statement} />
        )}

        {/* Structured statement */}
        {statement && (
          <div className="space-y-2 pt-1">
            {preferredOption && (
              <div className="flex items-start gap-2">
                <span className="text-brand-blue text-xs font-bold uppercase tracking-wider mt-0.5 flex-shrink-0">Endorses</span>
                <span className="text-white text-sm font-semibold">{preferredOption}</span>
              </div>
            )}
            {keyConcern && (
              <div className="flex items-start gap-2">
                <span className="text-white/40 text-xs font-bold uppercase tracking-wider mt-0.5 flex-shrink-0">Concern</span>
                <span className="text-white/80 text-sm">{keyConcern}</span>
              </div>
            )}
            {vetoes.length > 0 && (
              <div className="flex items-center gap-2 flex-wrap pt-1">
                <span className="text-red-300/70 text-xs font-bold uppercase tracking-wider flex-shrink-0">Vetoes</span>
                {vetoes.map((v) => (
                  <span key={v} className="px-2 py-0.5 bg-red-500/20 text-red-300 text-xs rounded-full font-medium">
                    {v}
                  </span>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Scores */}
        {scores.length > 0 && (
          <div className="pt-2 border-t border-white/10">
            <p className="text-white/30 text-xs font-semibold uppercase tracking-wider mb-2">Scores</p>
            <div className="space-y-1">
              {scores.map((s) => (
                <div key={s.option_name} className="flex items-center gap-2">
                  <span className="text-white/60 text-xs truncate flex-1 min-w-0">{s.option_name}</span>
                  <div className="flex items-center gap-1.5 flex-shrink-0">
                    <div className="w-16 h-1 bg-white/10 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-brand-blue rounded-full"
                        style={{ width: `${Math.min(100, (s.weighted_score / 100) * 100)}%` }}
                      />
                    </div>
                    <span className="text-white/70 text-xs w-8 text-right">
                      {s.weighted_score.toFixed(1)}
                    </span>
                    {s.vetoes.length > 0 && (
                      <span className="text-red-400 text-xs">✗</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
