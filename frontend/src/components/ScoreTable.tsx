import type { ExecRole, ExecState, Option } from '../types/events'

const EXEC_ORDER: ExecRole[] = ['CEO', 'CFO', 'COO', 'CMO', 'CTO']

const EXEC_COLOR: Record<ExecRole, string> = {
  CEO: 'bg-brand-ceo',
  CFO: 'bg-brand-cfo',
  COO: 'bg-brand-coo',
  CMO: 'bg-brand-cmo',
  CTO: 'bg-brand-cto',
}

interface Props {
  options: Option[]
  execs: Partial<Record<ExecRole, ExecState>>
}

export default function ScoreTable({ options, execs }: Props) {
  const roles = EXEC_ORDER.filter((r) => execs[r]?.scores.length)
  if (!roles.length || !options.length) return null

  return (
    <div className="bg-white border border-brand-navy/10 rounded-xl overflow-hidden shadow-sm">
      <div className="px-5 py-3 border-b border-brand-navy/10">
        <p className="text-brand-navy font-bold text-xs uppercase tracking-widest">Weighted Scores by Exec</p>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b border-brand-navy/10">
              <th className="text-left px-4 py-2 text-brand-navy/50 font-semibold uppercase tracking-wider w-48">Option</th>
              {roles.map((r) => (
                <th key={r} className="px-3 py-2 text-center">
                  <span className={`px-2 py-0.5 rounded-full text-white font-bold ${EXEC_COLOR[r]}`}>{r}</span>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {options.map((opt) => (
              <tr key={opt.name} className="border-b border-brand-navy/5 last:border-0">
                <td className="px-4 py-2.5 font-medium text-brand-navy">{opt.name}</td>
                {roles.map((r) => {
                  const score = execs[r]?.scores.find((s) => s.option_name === opt.name)
                  const isVetoed = score && score.vetoes.length > 0
                  return (
                    <td key={r} className="px-3 py-2.5 text-center">
                      {score ? (
                        <span className={`font-bold ${isVetoed ? 'text-red-400 line-through' : 'text-brand-navy'}`}>
                          {score.weighted_score.toFixed(1)}
                          {isVetoed && <span className="ml-1 text-red-400 no-underline not-italic">✗</span>}
                        </span>
                      ) : (
                        <span className="text-brand-navy/20">—</span>
                      )}
                    </td>
                  )
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
