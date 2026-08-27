import { useEffect, useState } from 'react'

/** Respuesta de `GET /api/health`. */
type Salud = {
  status: 'ok' | 'degraded'
  database: { connected: boolean; error: string | null }
}

type Estado =
  | { fase: 'cargando' }
  | { fase: 'listo'; salud: Salud }
  | { fase: 'error'; mensaje: string }

/**
 * Fase 0: la pantalla no tiene dominio. Lo único que hace es recorrer la
 * cadena entera —navegador → proxy → api → Postgres— y enseñar el resultado.
 * El login llega en el criterio D1, después de probar Tailscale (A4).
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
    <main className="min-h-screen bg-slate-950 text-slate-100 flex items-center justify-center p-6">
      <div className="w-full max-w-md space-y-6">
        <header className="space-y-1">
          <h1 className="text-2xl font-semibold tracking-tight">Astrolabio</h1>
          <p className="text-sm text-slate-400">
            Esqueleto de la Fase 0 — sin dominio todavía.
          </p>
        </header>

        <section className="rounded-lg border border-slate-800 bg-slate-900/60 p-4">
          <h2 className="text-xs font-medium uppercase tracking-wider text-slate-500">
            Estado del sistema
          </h2>

          <div className="mt-3">
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
          </div>
        </section>
      </div>
    </main>
  )
}

function Indicador({ ok, etiqueta }: { ok: boolean; etiqueta: string }) {
  return (
    <p className="flex items-center gap-2 text-sm">
      <span
        aria-hidden
        className={`size-2 rounded-full ${ok ? 'bg-emerald-400' : 'bg-rose-400'}`}
      />
      <span className={ok ? 'text-slate-200' : 'text-rose-300'}>{etiqueta}</span>
    </p>
  )
}
