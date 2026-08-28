import { useCallback, useEffect, useState } from 'react'
import Markdown from 'react-markdown'
import rehypeKatex from 'rehype-katex'
import remarkMath from 'remark-math'

import 'katex/dist/katex.min.css'

import {
  ErrorDeApi,
  pedir,
  type EstadoDelRespaldo,
  type Pieza,
  type Usuario,
} from './api'

/**
 * Vista de una pieza: guion a la izquierda, lo que se verá a la derecha
 * (criterios J1 y J2).
 *
 * `react-markdown` construye elementos de React en vez de inyectar HTML, así
 * que no hace falta sanitizador ni `dangerouslySetInnerHTML`. Con dos usuarios
 * de confianza el riesgo sería bajo igualmente, pero no cuesta nada.
 */
export default function VistaPieza({
  pieza: inicial,
  usuario,
  alVolver,
}: {
  pieza: Pieza
  usuario: Usuario
  alVolver: () => void
}) {
  const [pieza, setPieza] = useState(inicial)
  const [guion, setGuion] = useState(inicial.guion)
  const [error, setError] = useState<string | null>(null)
  const [guardando, setGuardando] = useState(false)

  const sinGuardar = guion !== pieza.guion

  async function guardar() {
    setGuardando(true)
    setError(null)
    try {
      setPieza(
        await pedir<Pieza>(`/api/piezas/${pieza.id}`, {
          method: 'PATCH',
          body: JSON.stringify({ guion }),
        }),
      )
    } catch (causa) {
      setError(causa instanceof ErrorDeApi ? causa.message : 'No se pudo guardar')
    } finally {
      setGuardando(false)
    }
  }

  return (
    <div className="space-y-4">
      <div className="relative flex items-center justify-between gap-3">
        <button
          type="button"
          onClick={alVolver}
          className="text-xs text-slate-400 hover:text-slate-200"
        >
          ← Piezas
        </button>
        <div className="flex items-center gap-2">
          {sinGuardar && (
            <span className="text-xs text-amber-300/80">sin guardar</span>
          )}
          <button
            type="button"
            onClick={() => void guardar()}
            disabled={guardando || !sinGuardar}
            className="rounded-md bg-slate-100 px-3 py-1.5 text-xs font-medium text-slate-900 disabled:opacity-40"
          >
            {guardando ? 'Guardando…' : 'Guardar'}
          </button>
          {/* J3: exportar es acción explícita, nunca automática al guardar —
              escribiría en el vault de Johan sin que lo haya pedido. Solo él
              exporta, acompañando al 403 del servidor. */}
          {usuario.rol === 'investigador' && (
            <Exportar pieza={pieza} haySinGuardar={sinGuardar} />
          )}
        </div>
      </div>

      <header>
        <h2 className="text-lg font-semibold">{pieza.titulo}</h2>
        <p className="text-xs text-slate-500">
          {[pieza.formato, pieza.tema, pieza.plataforma].filter(Boolean).join(' · ') ||
            'sin formato ni tema todavía'}
        </p>
      </header>

      {error && (
        <p
          role="alert"
          className="rounded-md border border-rose-900/60 bg-rose-950/40 px-3 py-2 text-xs text-rose-200"
        >
          {error}
        </p>
      )}

      {/* J1: se escribe a la izquierda y se ve a la derecha. Sin alternar
          pestañas: la fórmula hay que mirarla mientras se escribe, que para
          eso el §2 del CLAUDE.md global insiste en LaTeX real. */}
      <div className="grid gap-3 md:grid-cols-2">
        <textarea
          value={guion}
          onChange={(e) => setGuion(e.target.value)}
          spellCheck={false}
          placeholder="El guion, en markdown. Las fórmulas van entre $…$ o $$…$$."
          className="min-h-80 w-full resize-y rounded-lg border border-slate-800 bg-slate-900/60 p-3 font-mono text-xs leading-relaxed text-slate-100 outline-none focus:border-slate-600"
        />

        <div className="min-h-80 overflow-x-auto rounded-lg border border-slate-800 bg-slate-900/30 p-3">
          {guion.trim() ? (
            <div className="prosa text-sm text-slate-200">
              <Markdown remarkPlugins={[remarkMath]} rehypePlugins={[rehypeKatex]}>
                {guion}
              </Markdown>
            </div>
          ) : (
            <p className="text-xs text-slate-600">La vista previa aparece aquí.</p>
          )}
        </div>
      </div>

      {/* J2: solo para el investigador. El ADR 0001 le da `literature` a él, y
          la API ya devuelve 403 al editor — esto no lo esconde, lo acompaña. */}
      {usuario.rol === 'investigador' && (
        <PanelRespaldo pieza={pieza} alCambiar={setPieza} />
      )}
    </div>
  )
}

/** J3: la acción dice qué archivo escribió y dónde, no solo «exportado». */
function Exportar({ pieza, haySinGuardar }: { pieza: Pieza; haySinGuardar: boolean }) {
  const [resultado, setResultado] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [enviando, setEnviando] = useState(false)

  async function exportar() {
    setEnviando(true)
    setError(null)
    setResultado(null)
    try {
      const r = await pedir<{ archivo: string }>(
        `/api/piezas/${pieza.id}/exportar`,
        { method: 'POST' },
      )
      setResultado(r.archivo)
    } catch (causa) {
      setError(causa instanceof ErrorDeApi ? causa.message : 'No se pudo exportar')
    } finally {
      setEnviando(false)
    }
  }

  return (
    <>
      <button
        type="button"
        onClick={() => void exportar()}
        disabled={enviando}
        title={
          haySinGuardar
            ? 'Se exportará lo último guardado, no lo que tienes sin guardar'
            : undefined
        }
        className="rounded-md border border-slate-700 px-3 py-1.5 text-xs text-slate-300 disabled:opacity-40"
      >
        {enviando ? 'Exportando…' : 'Exportar al vault'}
      </button>

      {(resultado || error) && (
        <div className="absolute inset-x-0 top-full z-10 mt-2">
          <p
            role="status"
            className={`rounded-md border px-3 py-2 font-mono text-[11px] break-all ${
              error
                ? 'border-rose-900/60 bg-rose-950/40 text-rose-200'
                : 'border-emerald-900/60 bg-emerald-950/30 text-emerald-200'
            }`}
          >
            {error ?? `Escrito en ${resultado}`}
          </p>
        </div>
      )}
    </>
  )
}

function PanelRespaldo({
  pieza,
  alCambiar,
}: {
  pieza: Pieza
  alCambiar: (p: Pieza) => void
}) {
  const [estado, setEstado] = useState<EstadoDelRespaldo | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    pedir<EstadoDelRespaldo>('/api/respaldo')
      .then(setEstado)
      .catch((causa: unknown) =>
        setError(causa instanceof ErrorDeApi ? causa.message : 'No se pudo consultar'),
      )
  }, [])

  const alternar = useCallback(
    async (archivo: string) => {
      const respaldo = pieza.respaldo.includes(archivo)
        ? pieza.respaldo.filter((a) => a !== archivo)
        : [...pieza.respaldo, archivo]

      try {
        alCambiar(
          await pedir<Pieza>(`/api/piezas/${pieza.id}`, {
            method: 'PATCH',
            body: JSON.stringify({ respaldo }),
          }),
        )
      } catch (causa) {
        setError(causa instanceof ErrorDeApi ? causa.message : 'No se pudo enlazar')
      }
    },
    [pieza, alCambiar],
  )

  return (
    <section className="rounded-lg border border-slate-800 bg-slate-900/60 p-4">
      <h3 className="text-xs font-medium uppercase tracking-wider text-slate-500">
        Respaldo científico
      </h3>

      <div className="mt-3 space-y-2">
        {error && <p className="text-xs text-rose-300/80">{error}</p>}

        {/* G4, la mitad de interfaz: si el vault no está montado la aplicación
            funciona igual y dice por qué, en vez de fingir que no hay notas. */}
        {estado && !estado.disponible && (
          <p className="text-xs text-slate-500">{estado.motivo}</p>
        )}

        {estado?.disponible &&
          (estado.notas.length === 0 ? (
            <p className="text-xs text-slate-500">
              No hay notas de respaldo en el vault todavía.
            </p>
          ) : (
            estado.notas.map((nota) => (
              <label
                key={nota.archivo}
                className="flex cursor-pointer items-start gap-2 text-xs"
              >
                <input
                  type="checkbox"
                  checked={pieza.respaldo.includes(nota.archivo)}
                  onChange={() => void alternar(nota.archivo)}
                  className="mt-0.5 accent-slate-300"
                />
                <span>
                  <span className="text-slate-200">{nota.fuente_titulo}</span>
                  {(nota.autor || nota.fecha) && (
                    <span className="block text-slate-500">
                      {[nota.autor, nota.fecha].filter(Boolean).join(' · ')}
                    </span>
                  )}
                </span>
              </label>
            ))
          ))}
      </div>
    </section>
  )
}
