import { useEffect, useRef } from 'react'
import { useBoardroomSSE } from '../hooks/useBoardroomSSE'
import type { ExecRole } from '../types/events'
import ExecutiveCard from './ExecutiveCard'
import InputForm from './InputForm'
import OptionsPanel from './OptionsPanel'
import PhaseIndicator from './PhaseIndicator'
import ScoreTable from './ScoreTable'
import SynthesisCard from './SynthesisCard'

const EXEC_ORDER: ExecRole[] = ['CEO', 'CFO', 'COO', 'CMO', 'CTO']

export default function BoardroomChat() {
  const { state, submit, reset } = useBoardroomSSE()
  const bottomRef = useRef<HTMLDivElement>(null)

  // Auto-scroll as content arrives
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [state.execs, state.synthesis, state.options])

  const visibleExecs = EXEC_ORDER.filter((r) => state.execs[r])
  const hasResults = visibleExecs.length > 0 || !!state.synthesis
  const allExecsDone = EXEC_ORDER.every((r) => state.execs[r]?.isDone)

  return (
    <div className="flex flex-col h-full">
      {/* Phase indicator bar */}
      <PhaseIndicator phase={state.phase} />

      {/* Scrollable content */}
      <div className="flex-1 overflow-y-auto scrollbar-hide">
        <div className="max-w-3xl mx-auto px-4 py-6 space-y-5">

          {/* Error */}
          {state.error && (
            <div className="bg-red-50 border border-red-200 rounded-xl px-5 py-4 text-red-700 text-sm">
              <strong>Error: </strong>{state.error}
            </div>
          )}

          {/* Options panel */}
          {state.options.length > 0 && (
            <OptionsPanel options={state.options} />
          )}

          {/* Executive cards */}
          {visibleExecs.map((role) => {
            const execState = state.execs[role]!
            return (
              <ExecutiveCard
                key={role}
                execState={execState}
                isActive={state.activeRole === role}
              />
            )
          })}

          {/* Score table — appears once all execs have scores */}
          {allExecsDone && state.options.length > 0 && (
            <ScoreTable options={state.options} execs={state.execs} />
          )}

          {/* Synthesis */}
          {state.synthesis && (
            <SynthesisCard synthesis={state.synthesis} />
          )}

          <div ref={bottomRef} />
        </div>
      </div>

      {/* Input form — pinned to bottom */}
      <div className="border-t border-brand-navy/10 bg-brand-white px-4 py-4">
        <div className="max-w-3xl mx-auto">
          <InputForm
            onSubmit={submit}
            isRunning={state.isRunning}
            onReset={reset}
            hasResults={hasResults}
          />
        </div>
      </div>
    </div>
  )
}
