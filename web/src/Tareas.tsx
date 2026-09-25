import { useState } from 'react'

import { ErrorDeApi, pedir, type Tarea } from './api'

/**
 * Cuántas le quedan, de cuántas (AD6, AD7): «quedan 2 de 5 tareas», o «5
 * tareas hechas» cuando no queda ninguna. `null` si no tiene tareas.
 */
export function quedan(tareas: Tarea[]): string | null {
  const total = tareas.length
  if (total === 0) return null

  const pendientes = tareas.filter((tarea) => !tarea.hecha).length
  if (pendientes === 0) return total === 1 ? '1 tarea hecha' : `${total} tareas hechas`

  return `${pendientes === 1 ? 'queda' : 'quedan'} ${pendientes} de ${total} ${
    total === 1 ? 'tarea' : 'tareas'
  }`
}

/**
 * Las tareas y el campo para añadir otra (AD4, AD5): la checklist de una
 * pieza, o las sueltas si `piezaId` es `null`. El panel lo pone quien la usa.
 *
 * Las tareas viven en el estado de la pantalla principal, que las carga todas
 * de una vez (AD2): así el tablero cuenta las de cada pieza sin pedirlas otra
 * vez. Cada cambio llega como una función sobre la lista entera.
 */
export default function ListaDeTareas({
  tareas,
  piezaId,
  actualizar,
}: {
  tareas: Tarea[]
  piezaId: number | null
  actualizar: (cambio: (todas: Tarea[]) => Tarea[]) => void
}) {
  const [nueva, setNueva] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [guardando, setGuardando] = useState(false)

  async function hacer(accion: () => Promise<(todas: Tarea[]) => Tarea[]>) {
    setGuardando(true)
    setError(null)
    try {
      actualizar(await accion())
      return true
    } catch (causa) {
      setError(causa instanceof ErrorDeApi ? causa.message : 'No se pudo guardar la tarea')
      return false
    } finally {
      setGuardando(false)
    }
  }

  async function anadir(evento: React.FormEvent) {
    evento.preventDefault()
    const hecho = await hacer(async () => {
      const creada = await pedir<Tarea>('/api/tareas', {
        method: 'POST',
        body: JSON.stringify({ texto: nueva, pieza_id: piezaId }),
      })
      return (todas) => [...todas, creada]
    })
    if (hecho) setNueva('')
  }

  const marcar = (tarea: Tarea) =>
    void hacer(async () => {
      const marcada = await pedir<Tarea>(`/api/tareas/${tarea.id}`, {
        method: 'PATCH',
        body: JSON.stringify({ hecha: !tarea.hecha }),
      })
      return (todas) => todas.map((t) => (t.id === marcada.id ? marcada : t))
    })

  const quitar = (tarea: Tarea) =>
    void hacer(async () => {
      await pedir(`/api/tareas/${tarea.id}`, { method: 'DELETE' })
      return (todas) => todas.filter((t) => t.id !== tarea.id)
    })

  return (
    <div className="space-y-3">
      {tareas.length === 0 ? (
        <p className="text-xs text-slate-400">Todavía no hay tareas.</p>
      ) : (
        <ul className="space-y-2">
          {tareas.map((tarea) => (
            <li key={tarea.id} className="flex items-start gap-2 text-xs">
              <label className="flex min-w-0 flex-1 cursor-pointer items-start gap-2">
                <input
                  type="checkbox"
                  checked={tarea.hecha}
                  onChange={() => marcar(tarea)}
                  disabled={guardando}
                  className="mt-0.5 accent-slate-300"
                />
                <span className="min-w-0 break-words">
                  <span className={tarea.hecha ? 'text-slate-400 line-through' : 'text-slate-200'}>
                    {tarea.texto}
                  </span>
                  {/* AD4: quién la marcó, para no tener que preguntarlo. */}
                  {tarea.hecha && (
                    <span className="block text-[11px] text-slate-400">
                      hecha por {tarea.marcada_por}
                    </span>
                  )}
                </span>
              </label>
              <button
                type="button"
                aria-label={`Quitar la tarea ${tarea.texto}`}
                onClick={() => quitar(tarea)}
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
        <input
          value={nueva}
          onChange={(e) => setNueva(e.target.value)}
          aria-label="Nueva tarea"
          placeholder={piezaId === null ? 'Comprar el micrófono' : 'Buscar la imagen del Hubble'}
          className="min-w-0 flex-1 rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-xs text-slate-100 outline-none focus:border-slate-500"
        />
        <button
          type="submit"
          disabled={guardando || !nueva.trim()}
          className="rounded-md border border-slate-700 px-3 py-1.5 text-xs text-slate-300 disabled:opacity-40"
        >
          Añadir
        </button>
      </form>

      {error && (
        <p
          role="alert"
          className="rounded-md border border-rose-900/60 bg-rose-950/40 px-3 py-2 text-xs text-rose-200"
        >
          {error}
        </p>
      )}
    </div>
  )
}
