import { useState } from 'react'

import { ErrorDeApi, pedir, TEMAS, type Pieza } from './api'

/**
 * El tema y las etiquetas de la pieza (Y5).
 *
 * Se guardan al elegirlos, sin pasar por «Guardar», como los enlaces del
 * material: el guion puede estar a medias y esto no tiene por qué esperarlo.
 * La normalización de las etiquetas es del servidor (Y3); aquí se enseña la
 * que devuelve.
 */
export default function PanelTemas({
  pieza,
  sugerencias,
  alCambiar,
}: {
  pieza: Pieza
  sugerencias: string[]
  alCambiar: (pieza: Pieza) => void
}) {
  const [nueva, setNueva] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [guardando, setGuardando] = useState(false)

  async function guardar(cambios: { tema?: string | null; etiquetas?: string[] }) {
    setGuardando(true)
    setError(null)
    try {
      alCambiar(
        await pedir<Pieza>(`/api/piezas/${pieza.id}`, {
          method: 'PATCH',
          body: JSON.stringify(cambios),
        }),
      )
      return true
    } catch (causa) {
      // El 422 de una etiqueta trae el detalle de Pydantic, en inglés: basta
      // con decir qué le falta.
      setError(
        causa instanceof ErrorDeApi && causa.estado === 422
          ? 'Esa etiqueta no vale: cada una necesita al menos una letra.'
          : causa instanceof ErrorDeApi
            ? causa.message
            : 'No se pudo guardar',
      )
      return false
    } finally {
      setGuardando(false)
    }
  }

  async function anadir(evento: React.FormEvent) {
    evento.preventDefault()
    // Varias de una vez, separadas por comas: si no, la coma se borraría al
    // normalizar y «agujeros negros, m31» sería una sola etiqueta.
    const nuevas = nueva.split(',').map((e) => e.trim()).filter(Boolean)
    if (nuevas.length === 0) return
    if (await guardar({ etiquetas: [...pieza.etiquetas, ...nuevas] })) setNueva('')
  }

  const quitar = (etiqueta: string) =>
    void guardar({ etiquetas: pieza.etiquetas.filter((e) => e !== etiqueta) })

  return (
    <section className="rounded-lg border border-slate-800 bg-slate-900/60 p-4">
      <h3 className="text-xs font-medium uppercase tracking-wider text-slate-500">
        Tema y etiquetas
      </h3>

      <div className="mt-3 space-y-3">
        <label className="block space-y-1.5">
          <span className="text-xs text-slate-400">Tema</span>
          <select
            value={pieza.tema ?? ''}
            onChange={(e) => void guardar({ tema: e.target.value || null })}
            disabled={guardando}
            className="w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-xs text-slate-100 outline-none focus:border-slate-500 disabled:opacity-40"
          >
            <option value="">Sin tema</option>
            {TEMAS.map((tema) => (
              <option key={tema} value={tema}>
                {tema}
              </option>
            ))}
          </select>
        </label>

        <div className="space-y-1.5">
          <span className="block text-xs text-slate-400">Etiquetas</span>
          {pieza.etiquetas.length === 0 ? (
            <p className="text-xs text-slate-400">Todavía no tiene etiquetas.</p>
          ) : (
            <ul className="flex flex-wrap gap-1.5">
              {pieza.etiquetas.map((etiqueta) => (
                <li
                  key={etiqueta}
                  className="flex items-center gap-1 rounded bg-slate-800 py-0.5 pl-2 pr-1 text-xs text-slate-200"
                >
                  {etiqueta}
                  <button
                    type="button"
                    aria-label={`Quitar la etiqueta ${etiqueta}`}
                    onClick={() => quitar(etiqueta)}
                    disabled={guardando}
                    className="px-1 text-slate-400 hover:text-slate-100 disabled:opacity-40"
                  >
                    ×
                  </button>
                </li>
              ))}
            </ul>
          )}

          <form onSubmit={anadir} className="flex gap-2">
            {/* Las que ya existen en otras piezas, para no inventar una
                variante de la misma (Y5). `datalist` es del navegador. */}
            <input
              list="etiquetas-existentes"
              value={nueva}
              onChange={(e) => setNueva(e.target.value)}
              aria-label="Nuevas etiquetas, separadas por comas"
              placeholder="agujeros negros, m31"
              className="min-w-0 flex-1 rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-xs text-slate-100 outline-none focus:border-slate-500"
            />
            <datalist id="etiquetas-existentes">
              {sugerencias
                .filter((e) => !pieza.etiquetas.includes(e))
                .map((e) => (
                  <option key={e} value={e} />
                ))}
            </datalist>
            <button
              type="submit"
              disabled={guardando || !nueva.trim()}
              className="rounded-md border border-slate-700 px-3 py-1.5 text-xs text-slate-300 disabled:opacity-40"
            >
              Añadir
            </button>
          </form>
        </div>

        {error && (
          <p
            role="alert"
            className="rounded-md border border-rose-900/60 bg-rose-950/40 px-3 py-2 text-xs text-rose-200"
          >
            {error}
          </p>
        )}
      </div>
    </section>
  )
}
