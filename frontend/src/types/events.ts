// SSE event types — mirror the backend sse_events.py schema

export type ExecRole = 'CEO' | 'CFO' | 'COO' | 'CMO' | 'CTO'

export interface PhaseStartEvent {
  type: 'phase_start'
  phase: 1 | 2 | 3
  label: string
}

export interface NodeStartEvent {
  type: 'node_start'
  role: ExecRole
  node: string
  label: string
}

export interface TokenStreamEvent {
  type: 'token_stream'
  role: ExecRole
  delta: string
}

export interface NodeCompleteEvent {
  type: 'node_complete'
  role: ExecRole
  node: string
  payload: Record<string, unknown>
}

export interface Option {
  name: string
  summary: string
  mechanism: string
  key_assumption: string
  kill_condition: string
  archetype_lean: string
}

export interface OptionsReadyEvent {
  type: 'options_ready'
  options: Option[]
}

export interface ExecStatementEvent {
  type: 'exec_statement'
  role: ExecRole
  opening_statement: string
  preferred_option: string
  key_concern: string
  veto_options: string[]
}

export interface OptionScore {
  option_name: string
  weighted_score: number
  vetoes: string[]
}

export interface ScoresReadyEvent {
  type: 'scores_ready'
  role: ExecRole
  option_scores: OptionScore[]
}

export interface SynthesisStartEvent {
  type: 'synthesis_start'
}

export interface ConsensusItem {
  option_name: string
  agreeing_roles: string[]
  basis: string
}

export interface DissentItem {
  option_name: string
  dissenting_role: string
  concern: string
  resolution: string
}

export interface SynthesisCompleteEvent {
  type: 'synthesis_complete'
  final_recommendation: string
  consensus_items: ConsensusItem[]
  dissent_items: DissentItem[]
  conditions: string[]
  synthesis_narrative: string
}

export interface ErrorEvent {
  type: 'error'
  message: string
  session_id: string
}

export interface DoneEvent {
  type: 'done'
  session_id: string
}

export type BoardroomEvent =
  | PhaseStartEvent
  | NodeStartEvent
  | TokenStreamEvent
  | NodeCompleteEvent
  | OptionsReadyEvent
  | ExecStatementEvent
  | ScoresReadyEvent
  | SynthesisStartEvent
  | SynthesisCompleteEvent
  | ErrorEvent
  | DoneEvent

// UI state shape
export interface ExecState {
  role: ExecRole
  streamingText: string
  statement: ExecStatementEvent | null
  scores: OptionScore[]
  isStreaming: boolean
  isDone: boolean
}

export interface BoardroomUIState {
  phase: 1 | 2 | 3 | null
  isRunning: boolean
  options: Option[]
  execs: Partial<Record<ExecRole, ExecState>>
  synthesis: SynthesisCompleteEvent | null
  error: string | null
  activeRole: ExecRole | null
}
