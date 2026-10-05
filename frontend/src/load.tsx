import { useEffect, useState } from 'react'

export type Loaded<T> = { status: 'loading' } | { status: 'error'; message: string } | { status: 'ok'; data: T }

/** Carrega um recurso; `key` muda quando o recurso pedido muda. */
export function useLoad<T>(loader: () => Promise<T>, key: string): Loaded<T> {
  const [state, setState] = useState<Loaded<T>>({ status: 'loading' })
  useEffect(() => {
    let active = true
    setState({ status: 'loading' })
    Promise.resolve().then(loader).then(
      (data) => active && setState({ status: 'ok', data }),
      (error: unknown) => active && setState({ status: 'error', message: error instanceof Error ? error.message : 'erro' }),
    )
    return () => { active = false }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key])
  return state
}

export function Status({ state }: { state: Loaded<unknown> }) {
  if (state.status === 'loading') return <p role="status">Carregando…</p>
  if (state.status === 'error') return <p role="alert" className="error">Não foi possível carregar: {state.message}</p>
  return null
}
