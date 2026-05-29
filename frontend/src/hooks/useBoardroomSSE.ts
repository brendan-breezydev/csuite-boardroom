import { useReducer, useEffect, useRef, useCallback } from 'react'
import type {
  BoardroomEvent,
  BoardroomUIState,
  ExecRole,
  ExecState,
} from '../types/events'

const EXEC_ORDER: ExecRole[] = ['CEO', 'CFO', 'COO', 'CMO', 'CTO']

const initialState: BoardroomUIState = {
  phase: null,
  isRunning: false,
  options: [],
  execs: {},
  synthesis: null,
  error: null,
  activeRole: null,
}

function emptyExecState(role: ExecRole): ExecState {
  return { role, streamingText: '', statement: null, scores: [], isStreaming: false, isDone: false }
}

type Action =
  | { type: 'START' }
  | { type: 'RESET' }
  | { type: 'EVENT'; event: BoardroomEvent }

function reducer(state: BoardroomUIState, action: Action): BoardroomUIState {
  switch (action.type) {
    case 'START':
      return { ...initialState, isRunning: true }
    case 'RESET':
      return initialState

    case 'EVENT': {
      const ev = action.event
      switch (ev.type) {
        case 'phase_start':
          return { ...state, phase: ev.phase }

        case 'node_start': {
          const role = ev.role
          const existing = state.execs[role] ?? emptyExecState(role)
          return {
            ...state,
            activeRole: role,
            execs: {
              ...state.execs,
              [role]: { ...existing, isStreaming: true },
            },
          }
        }

        case 'token_stream': {
          const role = ev.role
          const existing = state.execs[role] ?? emptyExecState(role)
          return {
            ...state,
            execs: {
              ...state.execs,
              [role]: {
                ...existing,
                streamingText: existing.streamingText + ev.delta,
                isStreaming: true,
              },
            },
          }
        }

        case 'options_ready':
          return { ...state, options: ev.options }

        case 'exec_statement': {
          const role = ev.role
          const existing = state.execs[role] ?? emptyExecState(role)
          return {
            ...state,
            execs: {
              ...state.execs,
              [role]: { ...existing, statement: ev, isStreaming: false },
            },
          }
        }

        case 'scores_ready': {
          const role = ev.role
          const existing = state.execs[role] ?? emptyExecState(role)
          return {
            ...state,
            execs: {
              ...state.execs,
              [role]: { ...existing, scores: ev.option_scores, isDone: true },
            },
          }
        }

        case 'synthesis_complete':
          return { ...state, synthesis: ev, isRunning: false, activeRole: null }

        case 'error':
          return { ...state, error: ev.message, isRunning: false, activeRole: null }

        case 'done':
          return { ...state, isRunning: false, activeRole: null }

        default:
          return state
      }
    }
  }
}

export function useBoardroomSSE() {
  const [state, dispatch] = useReducer(reducer, initialState)
  const esRef = useRef<EventSource | null>(null)

  const closeStream = useCallback(() => {
    esRef.current?.close()
    esRef.current = null
  }, [])

  const submit = useCallback(async (situation: string) => {
    closeStream()
    dispatch({ type: 'START' })

    try {
      const res = await fetch('/api/boardroom', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ situation }),
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: 'Unknown error' }))
        dispatch({ type: 'EVENT', event: { type: 'error', message: err.detail ?? 'Failed to start session', session_id: '' } })
        return
      }
      const { session_id } = await res.json()

      const es = new EventSource(`/api/boardroom/${session_id}/stream`)
      esRef.current = es

      es.onmessage = (e) => {
        try {
          const event = JSON.parse(e.data) as BoardroomEvent
          dispatch({ type: 'EVENT', event })
          if (event.type === 'done' || event.type === 'error') {
            closeStream()
          }
        } catch {
          // ignore malformed events
        }
      }

      es.onerror = () => {
        dispatch({ type: 'EVENT', event: { type: 'error', message: 'Connection lost.', session_id } })
        closeStream()
      }
    } catch (err) {
      dispatch({ type: 'EVENT', event: { type: 'error', message: String(err), session_id: '' } })
    }
  }, [closeStream])

  const reset = useCallback(() => {
    closeStream()
    dispatch({ type: 'RESET' })
  }, [closeStream])

  useEffect(() => () => { closeStream() }, [closeStream])

  return { state, submit, reset, EXEC_ORDER }
}
