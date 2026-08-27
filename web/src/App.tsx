import { useCallback, useEffect, useState } from 'react'

/** Respuesta de `GET /api/health`. */
type Salud = {
  status: 'ok' | 'degraded'
  database: { connected: boolean; error: string | null }
}

/** Respuesta de `GET /api/_probe/cookie`. */
type Sonda = { present: boolean; value: string | null }

type Estado =
  | { fase: 'cargando' }
  | { fase: 'listo'; salud: Salud }
  | { fase: 'error'; mensaje: string }

/**
 * Fase 0: la pantalla no tiene dominio. Recorre la cadena entera —navegador →
 * proxy → api → Postgres— y sirve de banco de pruebas para el criterio A4.
 * El login llega en D1, después de comprobar que la cookie cruza la tailnet.
 */
export default function App() {
  const [estado, setEstado] = useState<Estado>({ fase: 'cargando' })

  useEffect(() => {
    const control = new AbortController()

    // Ruta relativa: el frontend se sirve desde el mismo origen que la API
    // (ADR 0005), así que aquí no hay ninguna dirección escrita (A3).
    fetch('/api/health', { signal: control.signal })
      .then(async (respuesta) => {
        const salud = (await respuesta.json()) as Salud
        setEstado({ fase: 'listo', salud })
      })
      .catch((causa: unknown) => {
        if (control.signal.aborted) return
        // El error se le muestra al usuario, no se queda en la consola.
        setEstado({
          fase: 'error',
          mensaje:
            causa instanceof Error ? causa.message : 'No se pudo contactar la API',
        })
      })

    return () => control.abort()
  }, [])

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100 p-6">
      <div className="mx-auto w-full max-w-md space-y-6">
        <header className="space-y-1">
          <h1 className="text-2xl font-semibold tracking-tight">Astrolabio</h1>
          <p className="text-sm text-slate-400">
            Esqueleto de la Fase 0 — sin dominio todavía.
          </p>
        </header>

        <Panel titulo="Estado del sistema">
          {estado.fase === 'cargando' && (
            <p className="text-sm text-slate-400">Consultando la API…</p>
          )}

          {estado.fase === 'error' && (
            <div className="space-y-1">
              <Indicador ok={false} etiqueta="API inalcanzable" />
              <p className="text-xs text-rose-300/80">{estado.mensaje}</p>
            </div>
          )}

          {estado.fase === 'listo' && (
            <div className="space-y-2">
              <Indicador ok etiqueta="API respondiendo" />
              <Indicador
                ok={estado.salud.database.connected}
                etiqueta={
                  estado.salud.database.connected
                    ? 'Postgres conectado'
                    : `Postgres sin responder (${estado.salud.database.error})`
                }
              />
            </div>
          )}
        </Panel>

        <SondaCookie />
      </div>
    </main>
  )
}

/**
 * Banco de pruebas del criterio A4, pensado para usarse desde el teléfono sin
 * una terminal al lado. Se retira junto con el módulo `probe` en la Fase B.
 */
function SondaCookie() {
  const [sonda, setSonda] = useState<Sonda | null>(null)
  const [fallo, setFallo] = useState<string | null>(null)
  const [ocupado, setOcupado] = useState(false)

  // `same-origin` es el valor por defecto para peticiones al mismo origen;
  // va explícito porque es exactamente lo que el ADR 0005 compra.
  const consultar = useCallback(async () => {
    try {
      const respuesta = await fetch('/api/_probe/cookie', {
        credentials: 'same-origin',
      })
      setSonda((await respuesta.json()) as Sonda)
      setFallo(null)
    } catch (causa: unknown) {
      setFallo(causa instanceof Error ? causa.message : 'No se pudo consultar')
    }
  }, [])

  const enviar = useCallback(
    async (metodo: 'POST' | 'DELETE') => {
      setOcupado(true)
      try {
        await fetch('/api/_probe/cookie', {
          method: metodo,
          credentials: 'same-origin',
        })
        await consultar()
      } catch (causa: unknown) {
        setFallo(causa instanceof Error ? causa.message : 'No se pudo escribir')
      } finally {
        setOcupado(false)
      }
    },
    [consultar],
  )

  useEffect(() => {
    void consultar()
  }, [consultar])

  return (
    <Panel titulo="Sonda de cookie (criterio A4)">
      <div className="space-y-4">
        {fallo ? (
          <p className="text-xs text-rose-300/80">{fallo}</p>
        ) : sonda === null ? (
          <p className="text-sm text-slate-400">Consultando…</p>
        ) : (
          <div className="space-y-1">
            <Indicador
              ok={sonda.present}
              etiqueta={
                sonda.present
                  ? 'El navegador devolvió la cookie'
                  : 'No hay cookie en esta petición'
              }
            />
            {sonda.value && (
              <p className="font-mono text-xs text-slate-500 break-all">
                {sonda.value}
              </p>
            )}
          </div>
        )}

        <div className="flex gap-2">
          <button
            type="button"
            disabled={ocupado}
            onClick={() => void enviar('POST')}
            className="flex-1 rounded-md bg-slate-100 px-3 py-2.5 text-sm font-medium text-slate-900 disabled:opacity-50"
          >
            Emitir cookie
          </button>
          <button
            type="button"
            disabled={ocupado}
            onClick={() => void enviar('DELETE')}
            className="rounded-md border border-slate-700 px-3 py-2.5 text-sm text-slate-300 disabled:opacity-50"
          >
            Borrar
          </button>
        </div>

        <p className="text-xs leading-relaxed text-slate-500">
          La prueba de verdad es <strong className="text-slate-400">recargar</strong>{' '}
          después de emitir. Que el servidor sepa escribirla no demuestra nada; lo
          que se mide es si el navegador la guarda y la reenvía al volver.
        </p>
      </div>
    </Panel>
  )
}

function Panel({ titulo, children }: { titulo: string; children: React.ReactNode }) {
  return (
    <section className="rounded-lg border border-slate-800 bg-slate-900/60 p-4">
      <h2 className="text-xs font-medium uppercase tracking-wider text-slate-500">
        {titulo}
      </h2>
      <div className="mt-3">{children}</div>
    </section>
  )
}

function Indicador({ ok, etiqueta }: { ok: boolean; etiqueta: string }) {
  return (
    <p className="flex items-center gap-2 text-sm">
      <span
        aria-hidden
        className={`size-2 shrink-0 rounded-full ${ok ? 'bg-emerald-400' : 'bg-rose-400'}`}
      />
      <span className={ok ? 'text-slate-200' : 'text-rose-300'}>{etiqueta}</span>
    </p>
  )
}
