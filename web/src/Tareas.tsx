import { useState } from 'react'

import { ErrorDeApi, pedir, type Tarea } from './api'
import { Aviso, BOTON_SECUNDARIO, CONTROL } from './ui'

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
    <div className="flex flex-col gap-3.5">
      {tareas.length === 0 ? (
        <p className="text-sm text-ink-2">Todavía no hay tareas.</p>
      ) : (
        <ul className="flex flex-col">
          {tareas.map((tarea) => (
            <li
              key={tarea.id}
              className="flex items-start gap-2.5 border-b border-line-faint py-2.5"
            >
              <label className="flex min-w-0 flex-1 cursor-pointer items-start gap-2.5">
                <input
                  type="checkbox"
                  checked={tarea.hecha}
                  onChange={() => marcar(tarea)}
                  disabled={guardando}
                  className="mt-0.5 size-4 shrink-0 accent-ink"
                />
                <span className="flex min-w-0 flex-col gap-0.5 break-words">
                  <span className={tarea.hecha ? 'text-sm text-ink-2 line-through' : 'text-sm'}>
                    {tarea.texto}
                  </span>
                  {/* AD4: quién la marcó, para no tener que preguntarlo. */}
                  {tarea.hecha && (
                    <span className="mono-data text-ink-3">hecha por {tarea.marcada_por}</span>
                  )}
                </span>
              </label>
              <button
                type="button"
                aria-label={`Quitar la tarea ${tarea.texto}`}
                onClick={() => quitar(tarea)}
                disabled={guardando}
                className="px-1 text-base leading-none text-ink-2 hover:text-ink disabled:opacity-40"
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
          className={`${CONTROL} min-w-0 flex-1`}
        />
        <button type="submit" disabled={guardando || !nueva.trim()} className={BOTON_SECUNDARIO}>
          Añadir
        </button>
      </form>

      {error && <Aviso mensaje={error} />}
    </div>
  )
}
