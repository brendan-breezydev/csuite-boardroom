import type { SynthesisCompleteEvent } from '../types/events'

interface Props {
  synthesis: SynthesisCompleteEvent
}

export default function SynthesisCard({ synthesis }: Props) {
  const {
    final_recommendation,
    consensus_items,
    dissent_items,
    conditions,
    synthesis_narrative,
  } = synthesis

  return (
    <div className="fade-slide-in bg-brand-navy rounded-2xl overflow-hidden shadow-xl">
      {/* Header */}
      <div className="px-6 py-5 border-b border-white/10">
        <p className="text-brand-blue text-xs font-bold uppercase tracking-widest mb-1">Board Resolution</p>
        <h2 className="text-white text-xl font-extrabold leading-tight">{final_recommendation}</h2>
      </div>

      <div className="px-6 py-5 space-y-5">
        {/* Narrative */}
        <p className="text-white/80 text-sm leading-relaxed italic">{synthesis_narrative}</p>

        {/* Consensus */}
        {consensus_items.length > 0 && (
          <div>
            <p className="text-brand-blue text-xs font-bold uppercase tracking-widest mb-2">Consensus</p>
            <div className="space-y-2">
              {consensus_items.map((c, i) => (
                <div key={i} className="bg-white/5 rounded-lg px-4 py-2.5 space-y-1">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-white font-semibold text-sm">{c.option_name}</span>
                    <div className="flex gap-1 flex-wrap">
                      {c.agreeing_roles.map((r) => (
                        <span key={r} className="px-1.5 py-0.5 bg-brand-blue/30 text-brand-blue text-[10px] font-bold rounded">
                          {r}
                        </span>
                      ))}
                    </div>
                  </div>
                  <p className="text-white/60 text-xs">{c.basis}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Dissent */}
        {dissent_items.length > 0 && (
          <div>
            <p className="text-white/40 text-xs font-bold uppercase tracking-widest mb-2">Dissent & Resolution</p>
            <div className="space-y-2">
              {dissent_items.map((d, i) => (
                <div key={i} className="bg-white/5 rounded-lg px-4 py-2.5 space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="px-1.5 py-0.5 bg-red-500/20 text-red-300 text-[10px] font-bold rounded">
                      {d.dissenting_role}
                    </span>
                    <span className="text-white/60 text-xs">{d.concern}</span>
                  </div>
                  <p className="text-white/40 text-xs">
                    <span className="text-brand-blue/70 font-semibold">Resolution: </span>
                    {d.resolution}
                  </p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Conditions */}
        {conditions.length > 0 && (
          <div>
            <p className="text-white/40 text-xs font-bold uppercase tracking-widest mb-2">Conditions</p>
            <ul className="space-y-1">
              {conditions.map((c, i) => (
                <li key={i} className="flex items-start gap-2 text-white/70 text-sm">
                  <span className="text-brand-blue mt-1 flex-shrink-0">›</span>
                  {c}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  )
}
