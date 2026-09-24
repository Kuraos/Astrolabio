import { useCallback, useEffect, useState } from 'react'
import Markdown from 'react-markdown'
import rehypeKatex from 'rehype-katex'
import remarkMath from 'remark-math'

import 'katex/dist/katex.min.css'

import {
  ErrorDeApi,
  pedir,
  type Enlace,
  type EstadoDeLaCarpeta,
  type EstadoDelRespaldo,
  type Pieza,
  type Traspaso,
  type Usuario,
} from './api'
import { aQuienLeToca, confirmacion, enPalabras, vuelveAtras } from './flujo'

/**
 * Vista de una pieza: arriba el traspaso (N2, N3), y debajo el guion a la
 * izquierda y lo que se verá a la derecha (criterios J1 y J2).
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

      <PanelTraspaso
        pieza={pieza}
        usuario={usuario}
        haySinGuardar={sinGuardar}
        alMover={setPieza}
      />

      <PanelMaterial pieza={pieza} />

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

/**
 * El traspaso: de quién es la pieza, qué puede hacer quien mira y cómo llegó
 * aquí (N2, N3).
 *
 * Los botones son los que la API dice que el usuario puede dar ahora (K4), y
 * acompañan al 403 del servidor, nunca lo sustituyen (D3).
 */
function PanelTraspaso({
  pieza,
  usuario,
  haySinGuardar,
  alMover,
}: {
  pieza: Pieza
  usuario: Usuario
  haySinGuardar: boolean
  alMover: (p: Pieza) => void
}) {
  const [historia, setHistoria] = useState<Traspaso[] | null>(null)
  const [nota, setNota] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [moviendo, setMoviendo] = useState(false)

  useEffect(() => {
    pedir<Traspaso[]>(`/api/piezas/${pieza.id}/traspasos`)
      .then(setHistoria)
      .catch((causa: unknown) =>
        setError(causa instanceof ErrorDeApi ? causa.message : 'No se pudo leer la historia'),
      )
  }, [pieza.id])

  async function mover(transicion: string) {
    const pregunta = confirmacion(transicion)
    if (pregunta && !window.confirm(pregunta)) return

    setMoviendo(true)
    setError(null)
    try {
      await pedir(`/api/piezas/${pieza.id}/traspasos`, {
        method: 'POST',
        body: JSON.stringify({ transicion, desde: pieza.estado, nota: nota.trim() || null }),
      })
      setNota('')
    } catch (causa) {
      setError(causa instanceof ErrorDeApi ? causa.message : 'No se pudo mover la pieza')
    }

    // Con éxito o sin él se vuelve a leer: el estado lo dice el servidor, no lo
    // que el cliente cree que pasó. Tras un 409 (L4), esto pone la pantalla al
    // día y el aviso de arriba explica por qué cambió.
    try {
      const [fresca, pasos] = await Promise.all([
        pedir<Pieza>(`/api/piezas/${pieza.id}`),
        pedir<Traspaso[]>(`/api/piezas/${pieza.id}/traspasos`),
      ])
      alMover(fresca)
      setHistoria(pasos)
    } catch (causa) {
      setError(causa instanceof ErrorDeApi ? causa.message : 'No se pudo actualizar')
    } finally {
      setMoviendo(false)
    }
  }

  const turno = aQuienLeToca(pieza, usuario)
  const botones = [...pieza.transiciones].sort(
    (a, b) => Number(vuelveAtras(a)) - Number(vuelveAtras(b)),
  )

  return (
    <section className="rounded-lg border border-slate-800 bg-slate-900/60 p-4">
      <h3 className="text-xs font-medium uppercase tracking-wider text-slate-500">
        Traspaso
      </h3>

      <div className="mt-3 space-y-3">
        <p className="text-sm">
          <span className="text-slate-100">{enPalabras(pieza.estado)}</span>
          {turno && (
            <span
              className={
                pieza.de_quien_es === usuario.rol ? 'text-amber-200' : 'text-slate-500'
              }
            >
              {' '}
              · {turno}
            </span>
          )}
        </p>

        {botones.length > 0 && (
          <div className="space-y-2">
            <textarea
              value={nota}
              onChange={(e) => setNota(e.target.value)}
              rows={2}
              placeholder={
                pieza.transiciones.includes('devolver')
                  ? 'Nota opcional. Si la devuelves, di qué ajustar.'
                  : 'Nota opcional.'
              }
              className="w-full resize-y rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-xs text-slate-100 outline-none focus:border-slate-500"
            />
            <div className="flex flex-wrap gap-2">
              {botones.map((transicion) => (
                <button
                  key={transicion}
                  type="button"
                  onClick={() => void mover(transicion)}
                  disabled={moviendo || haySinGuardar}
                  className={
                    vuelveAtras(transicion)
                      ? 'rounded-md border border-slate-700 px-3 py-1.5 text-xs text-slate-300 disabled:opacity-40'
                      : 'rounded-md bg-slate-100 px-3 py-1.5 text-xs font-medium text-slate-900 disabled:opacity-40'
                  }
                >
                  {enPalabras(transicion)}
                </button>
              ))}
            </div>
            {/* Mover la pieza con el guion a medias le pasaría al otro la
                versión anterior. */}
            {haySinGuardar && (
              <p className="text-xs text-amber-300/80">
                Guarda el guion antes de moverla: el otro vería la versión anterior.
              </p>
            )}
          </div>
        )}

        {error && (
          <p
            role="alert"
            className="rounded-md border border-rose-900/60 bg-rose-950/40 px-3 py-2 text-xs text-rose-200"
          >
            {error}
          </p>
        )}

        <div className="border-t border-slate-800 pt-3">
          <h4 className="text-xs text-slate-500">Historia</h4>
          {historia === null ? (
            <p className="mt-2 text-xs text-slate-600">Cargando…</p>
          ) : historia.length === 0 ? (
            <p className="mt-2 text-xs text-slate-600">Todavía no ha cambiado de manos.</p>
          ) : (
            // Lo último arriba: al abrir una pieza devuelta, lo primero que se
            // lee es la nota que dice qué ajustar.
            <ol className="mt-2 space-y-2">
              {[...historia].reverse().map((paso) => (
                <li key={paso.id} className="text-xs">
                  <span className="text-slate-200">{enPalabras(paso.transicion)}</span>
                  <span className="text-slate-500">
                    {' '}
                    · {enPalabras(paso.desde)} → {enPalabras(paso.hacia)}
                  </span>
                  <span className="block text-slate-500">
                    {paso.creado_por} ·{' '}
                    {new Date(paso.creado_en).toLocaleString('es-CO', {
                      day: 'numeric',
                      month: 'short',
                      hour: 'numeric',
                      minute: '2-digit',
                    })}
                  </span>
                  {paso.nota && (
                    <span className="mt-1 block whitespace-pre-wrap text-slate-300">
                      {paso.nota}
                    </span>
                  )}
                </li>
              ))}
            </ol>
          )}
        </div>
      </div>
    </section>
  )
}

/**
 * El material de la pieza (S1, S2): lo que Johan le pasa al editor para
 * hacerla, y que antes iba por chat. Es para los dos roles, a diferencia del
 * respaldo. Debajo de los enlaces, la carpeta de la pieza en Syncthing (S4).
 */
function PanelMaterial({ pieza }: { pieza: Pieza }) {
  const [enlaces, setEnlaces] = useState<Enlace[] | null>(null)
  const [url, setUrl] = useState('')
  const [nota, setNota] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [enviando, setEnviando] = useState(false)

  const ruta = `/api/piezas/${pieza.id}/enlaces`

  useEffect(() => {
    pedir<Enlace[]>(ruta)
      .then(setEnlaces)
      .catch((causa: unknown) =>
        setError(causa instanceof ErrorDeApi ? causa.message : 'No se pudo leer el material'),
      )
  }, [ruta])

  async function anadir(evento: React.FormEvent) {
    evento.preventDefault()
    setEnviando(true)
    setError(null)
    try {
      const nuevo = await pedir<Enlace>(ruta, {
        method: 'POST',
        body: JSON.stringify({ url: url.trim(), nota: nota.trim() || null }),
      })
      setEnlaces((actuales) => [...(actuales ?? []), nuevo])
      setUrl('')
      setNota('')
    } catch (causa) {
      // P3: el 422 trae el motivo de Pydantic, en inglés y en forma de lista.
      // Aquí basta con decir qué se acepta.
      setError(
        causa instanceof ErrorDeApi && causa.estado === 422
          ? 'Solo se aceptan enlaces http o https.'
          : causa instanceof ErrorDeApi
            ? causa.message
            : 'No se pudo añadir el enlace',
      )
    } finally {
      setEnviando(false)
    }
  }

  async function quitar(enlace: Enlace) {
    setError(null)
    try {
      await pedir(`${ruta}/${enlace.id}`, { method: 'DELETE' })
      setEnlaces((actuales) => (actuales ?? []).filter((e) => e.id !== enlace.id))
    } catch (causa) {
      setError(causa instanceof ErrorDeApi ? causa.message : 'No se pudo quitar el enlace')
    }
  }

  return (
    <section className="rounded-lg border border-slate-800 bg-slate-900/60 p-4">
      <h3 className="text-xs font-medium uppercase tracking-wider text-slate-500">
        Material
      </h3>

      <div className="mt-3 space-y-3">
        {enlaces === null ? (
          <p className="text-xs text-slate-600">Cargando…</p>
        ) : enlaces.length === 0 ? (
          <p className="text-xs text-slate-600">Todavía no hay enlaces.</p>
        ) : (
          <ul className="space-y-2">
            {enlaces.map((enlace) => (
              <li key={enlace.id} className="flex items-start justify-between gap-3 text-xs">
                <span className="min-w-0">
                  {/* S2: en otra pestaña, y sin darle a la página enlazada acceso
                      a esta ni saber de dónde viene la visita. */}
                  <a
                    href={enlace.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="break-words text-slate-100 underline decoration-slate-600 underline-offset-2 hover:decoration-slate-300"
                  >
                    {enlace.nota || enlace.url}
                  </a>
                  <span className="block text-slate-500">
                    {dominio(enlace.url)} · {enlace.creado_por}
                  </span>
                </span>
                <button
                  type="button"
                  onClick={() => void quitar(enlace)}
                  className="shrink-0 text-slate-500 hover:text-slate-300"
                >
                  Quitar
                </button>
              </li>
            ))}
          </ul>
        )}

        <form onSubmit={anadir} className="space-y-2">
          <input
            type="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://… un pin, un vídeo, un artículo"
            className="w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-xs text-slate-100 outline-none focus:border-slate-500"
          />
          <input
            type="text"
            value={nota}
            onChange={(e) => setNota(e.target.value)}
            placeholder="Nota opcional: para qué sirve"
            className="w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-xs text-slate-100 outline-none focus:border-slate-500"
          />
          <button
            type="submit"
            disabled={enviando || !url.trim()}
            className="rounded-md border border-slate-700 px-3 py-1.5 text-xs text-slate-300 disabled:opacity-40"
          >
            {enviando ? 'Añadiendo…' : 'Añadir enlace'}
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

        <Carpeta pieza={pieza} />
      </div>
    </section>
  )
}

/**
 * La carpeta de la pieza en Syncthing (Q3, S4). Lo que se lista es la copia de
 * la máquina donde corre la app; cada uno abre los archivos desde la suya.
 */
function Carpeta({ pieza }: { pieza: Pieza }) {
  const [estado, setEstado] = useState<EstadoDeLaCarpeta | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [ocupado, setOcupado] = useState(false)

  const ruta = `/api/piezas/${pieza.id}/carpeta`

  // El mismo camino para mirar, volver a mirar y crear: las dos rutas
  // responden con el estado de la carpeta.
  const pedirCarpeta = useCallback(
    async (init?: RequestInit) => {
      setOcupado(true)
      setError(null)
      try {
        setEstado(await pedir<EstadoDeLaCarpeta>(ruta, init))
      } catch (causa) {
        setError(causa instanceof ErrorDeApi ? causa.message : 'No se pudo leer la carpeta')
      } finally {
        setOcupado(false)
      }
    },
    [ruta],
  )

  useEffect(() => {
    void pedirCarpeta()
  }, [pedirCarpeta])

  return (
    <div className="space-y-2 border-t border-slate-800 pt-3">
      <div className="flex items-baseline justify-between gap-3">
        <h4 className="min-w-0 break-words text-xs text-slate-400">
          Carpeta en Syncthing
          {estado?.carpeta && <span className="text-slate-200"> · {estado.carpeta}</span>}
        </h4>
        {/* La app no se entera sola de lo que llega a la carpeta. */}
        {estado && (
          <button
            type="button"
            onClick={() => void pedirCarpeta()}
            disabled={ocupado}
            className="shrink-0 text-xs text-slate-500 hover:text-slate-300 disabled:opacity-40"
          >
            Actualizar
          </button>
        )}
      </div>

      {estado === null ? (
        !error && <p className="text-xs text-slate-600">Cargando…</p>
      ) : estado.motivo ? (
        <p className="text-xs text-slate-500">{estado.motivo}</p>
      ) : estado.carpeta === null ? (
        <button
          type="button"
          onClick={() => void pedirCarpeta({ method: 'POST' })}
          disabled={ocupado}
          className="rounded-md border border-slate-700 px-3 py-1.5 text-xs text-slate-300 disabled:opacity-40"
        >
          {ocupado ? 'Creando…' : 'Crear la carpeta de la pieza'}
        </button>
      ) : estado.archivos.length === 0 ? (
        <p className="text-xs text-slate-600">
          Vacía. Lo que pongas en esta carpeta, dentro de tu carpeta de Syncthing, aparece
          aquí.
        </p>
      ) : (
        <ul className="space-y-1">
          {estado.archivos.map((archivo) => (
            <li key={archivo.nombre} className="flex items-baseline justify-between gap-3 text-xs">
              <span className="min-w-0 break-words text-slate-200">{archivo.nombre}</span>
              <span className="shrink-0 text-slate-500">
                {enBytes(archivo.tamano)} ·{' '}
                {new Date(archivo.modificado).toLocaleString('es-CO', {
                  day: 'numeric',
                  month: 'short',
                  hour: 'numeric',
                  minute: '2-digit',
                })}
              </span>
            </li>
          ))}
        </ul>
      )}

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

/** En las unidades del explorador de Windows, que cuenta de 1024 en 1024. */
function enBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 ** 2) return `${Math.round(bytes / 1024)} KB`
  return `${(bytes / 1024 ** 2).toLocaleString('es-CO', { maximumFractionDigits: 1 })} MB`
}

/** `pinterest.com` en vez de la URL entera: basta para saber qué se va a abrir. */
function dominio(url: string): string {
  try {
    return new URL(url).hostname.replace(/^www\./, '')
  } catch {
    return url
  }
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
