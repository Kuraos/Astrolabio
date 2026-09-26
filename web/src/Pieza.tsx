import { useCallback, useEffect, useRef, useState } from 'react'

import {
  ErrorDeApi,
  pedir,
  type Archivo,
  type Enlace,
  type EstadoDeLaCarpeta,
  type EstadoDelRespaldo,
  type Pieza,
  type Tarea,
  type Traspaso,
  type Usuario,
} from './api'
import PanelCuadro from './Cuadro'
import { esDeUnaLamina, faltaDelCuadro, resumen } from './cuadro'
import { aQuienLeToca, confirmacion, enPalabras, vuelveAtras } from './flujo'
import Guion from './Guion'
import { ESTADOS } from './tablero'
import ListaDeTareas, { quedan } from './Tareas'
import PanelTemas from './Temas'
import { Caption, CopyGrafico } from './Textos'
import {
  ANCHO,
  Aviso,
  BOTON,
  BOTON_DE_TEXTO,
  BOTON_SECUNDARIO,
  CONTROL,
  Campo,
  Estacion,
  Pestanas,
  idsDePestana,
} from './ui'

type Texto = 'guion' | 'copy' | 'caption'

const PESTANAS: { valor: Texto; rotulo: string }[] = [
  { valor: 'guion', rotulo: 'Guion' },
  { valor: 'copy', rotulo: 'Copy gráfico' },
  { valor: 'caption', rotulo: 'Caption' },
]

const mismasLaminas = (a: string[], b: string[]) =>
  a.length === b.length && a.every((lamina, i) => lamina === b[i])

/**
 * Vista de una pieza: arriba el traspaso (N2, N3), el cuadro de materiales
 * (AO), las fechas (AC3), las tareas (AD4), el material y el tema con sus
 * etiquetas, y debajo los textos: el guion con su barra y su vista previa (J1,
 * J2 y la Fase 4), el copy gráfico y el caption (AP). Desde la Fase 7, en
 * estaciones de dos columnas desde `lg` (AJ3).
 */
export default function VistaPieza({
  pieza: inicial,
  usuario,
  sugerencias,
  tareas,
  actualizarTareas,
  alVolver,
}: {
  pieza: Pieza
  usuario: Usuario
  /** Las etiquetas que ya existen en alguna pieza (Y5). */
  sugerencias: string[]
  /** Las de esta pieza; la lista entera vive en la pantalla principal (AD2). */
  tareas: Tarea[]
  actualizarTareas: (cambio: (todas: Tarea[]) => Tarea[]) => void
  alVolver: () => void
}) {
  const [pieza, setPieza] = useState(inicial)
  // Los tres textos se escriben aquí y se guardan juntos, con «Guardar» o
  // Ctrl+S; lo demás de la pieza se guarda solo, al elegirlo.
  const [guion, setGuion] = useState(inicial.guion)
  const [laminas, setLaminas] = useState(inicial.copy_grafico)
  const [caption, setCaption] = useState(inicial.caption)
  const [texto, setTexto] = useState<Texto>('guion')
  const [error, setError] = useState<string | null>(null)
  const [guardando, setGuardando] = useState(false)

  const sinGuardar =
    guion !== pieza.guion ||
    !mismasLaminas(laminas, pieza.copy_grafico) ||
    caption !== pieza.caption

  async function guardar() {
    setGuardando(true)
    setError(null)
    try {
      setPieza(
        await pedir<Pieza>(`/api/piezas/${pieza.id}`, {
          method: 'PATCH',
          body: JSON.stringify({ guion, copy_grafico: laminas, caption }),
        }),
      )
    } catch (causa) {
      setError(causa instanceof ErrorDeApi ? causa.message : 'No se pudo guardar')
    } finally {
      setGuardando(false)
    }
  }

  return (
    <main className="flex flex-col pb-16">
      {/* AJ1: volver, qué pieza es, y guardar o exportar. */}
      <div className="border-b border-line">
        <div
          className={`${ANCHO} relative flex min-h-13 flex-wrap items-center justify-between gap-x-3 gap-y-2 py-2`}
        >
          <div className="flex items-center gap-5 whitespace-nowrap">
            <button type="button" onClick={alVolver} className={BOTON_DE_TEXTO}>
              ← Piezas
            </button>
            <span className="mono-label text-ink-3">Pieza {pieza.id}</span>
          </div>
          <div className="ml-auto flex items-center gap-2.5 whitespace-nowrap">
            {sinGuardar && <span className="mono-label text-alert">Sin guardar</span>}
            <button
              type="button"
              onClick={() => void guardar()}
              disabled={guardando || !sinGuardar}
              className={BOTON}
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
      </div>

      <div className={`${ANCHO} flex flex-col`}>
        <header className="flex flex-col gap-3 pt-7 pb-6">
          <h2 className="text-[clamp(2rem,4vw,3.25rem)] leading-none font-bold tracking-[-0.01em] break-words font-stretch-semi-condensed">
            {pieza.titulo}
          </h2>
          <p className="mono-label text-ink-2">
            {resumen(pieza) || 'Sin tipo de pieza ni tema todavía'}
          </p>
        </header>

        <Pista pieza={pieza} usuario={usuario} />

        <div className="mt-8 grid lg:grid-cols-[minmax(0,7fr)_minmax(0,5fr)]">
          <PanelTraspaso
            pieza={pieza}
            haySinGuardar={sinGuardar}
            tareas={tareas}
            alMover={setPieza}
          />

          <div className="flex min-w-0 flex-col border-t border-line lg:border-l lg:pl-7">
            {/* AO: lo que pide el cuadro del editor, junto a su fecha. */}
            <PanelCuadro pieza={pieza} alCambiar={setPieza} />

            <PanelFechas pieza={pieza} alCambiar={setPieza} />

            {/* AD4: la checklist de la pieza. */}
            <Estacion titulo="Tareas" className="border-t border-line pt-5 pb-7">
              <ListaDeTareas tareas={tareas} piezaId={pieza.id} actualizar={actualizarTareas} />
            </Estacion>
          </div>

          <PanelMaterial pieza={pieza} />

          <div className="flex min-w-0 flex-col border-t border-line lg:border-l lg:pl-7">
            <PanelTemas pieza={pieza} sugerencias={sugerencias} alCambiar={setPieza} />

            {/* J2: solo para el investigador. El ADR 0001 le da `literature` a
                él, y la API ya devuelve 403 al editor — esto no lo esconde, lo
                acompaña. */}
            {usuario.rol === 'investigador' && (
              <PanelRespaldo pieza={pieza} alCambiar={setPieza} />
            )}
          </div>

          <Estacion
            titulo="Textos"
            extra={
              <span className="mono-data text-ink-3 max-md:hidden">
                {texto === 'guion' ? 'ctrl+s guarda · mk y dm abren una fórmula' : 'ctrl+s guarda'}
              </span>
            }
            className="col-span-full border-t border-line pt-5"
          >
            {/* AP1: el guion, el copy de cada lámina y el caption. */}
            <Pestanas
              grupo="textos"
              nombre="Textos de la pieza"
              pestanas={PESTANAS}
              actual={texto}
              alElegir={setTexto}
            />

            {error && <Aviso mensaje={error} />}

            {/* Los tres paneles siguen montados y solo se esconden: el guion
                conserva su pila de deshacer (U2), y Ctrl+S, que escucha el
                guion, guarda desde cualquier pestaña. */}
            <PanelDeTexto valor="guion" actual={texto}>
              {/* U4: Ctrl+S hace lo mismo que el botón, y nada si no hay
                  cambios o ya se está guardando. */}
              <Guion
                valor={guion}
                alCambiar={setGuion}
                alGuardar={() => {
                  if (sinGuardar && !guardando) void guardar()
                }}
              />
            </PanelDeTexto>
            <PanelDeTexto valor="copy" actual={texto}>
              <CopyGrafico
                laminas={laminas}
                deUnaLamina={esDeUnaLamina(pieza.formato)}
                alCambiar={setLaminas}
              />
            </PanelDeTexto>
            <PanelDeTexto valor="caption" actual={texto}>
              <Caption texto={caption} destinos={pieza.plataforma} alCambiar={setCaption} />
            </PanelDeTexto>
          </Estacion>
        </div>
      </div>
    </main>
  )
}

/** El panel de una pestaña de los textos: escondido, no desmontado. */
function PanelDeTexto({
  valor,
  actual,
  children,
}: {
  valor: Texto
  actual: Texto
  children: React.ReactNode
}) {
  const ids = idsDePestana('textos', valor)
  return (
    <div id={ids.panel} role="tabpanel" aria-labelledby={ids.pestana} hidden={valor !== actual}>
      {children}
    </div>
  )
}

/**
 * AJ2: los seis estados en fila. Los que ya pasaron, el actual —naranja si le
 * toca a quien mira, invertido si no— y los que faltan. Un estado que el
 * cliente no conoce se añade al final, como en el tablero (AB2).
 */
function Pista({ pieza, usuario }: { pieza: Pieza; usuario: Usuario }) {
  const estados = ESTADOS.includes(pieza.estado) ? ESTADOS : [...ESTADOS, pieza.estado]
  const actual = estados.indexOf(pieza.estado)
  const turno = aQuienLeToca(pieza, usuario)
  const tuya = pieza.de_quien_es === usuario.rol

  return (
    <ol aria-label="Dónde está la pieza" className="grid grid-cols-2 gap-0.5 sm:grid-cols-3 lg:grid-cols-6">
      {estados.map((estado, i) => (
        <li
          key={estado}
          aria-current={i === actual ? 'step' : undefined}
          className={`flex flex-col gap-1 border-t-[3px] px-3 pt-2.5 pb-3 ${
            i === actual
              ? tuya
                ? 'border-signal bg-signal text-page'
                : 'border-ink bg-ink text-page'
              : i < actual
                ? 'border-control text-ink-2'
                : 'border-line text-ink-3'
          }`}
        >
          <span className="mono-label">
            {String(i + 1).padStart(2, '0')}
            {i === actual && turno && ` · ${turno}`}
          </span>
          <span className={`text-sm ${i === actual ? 'font-bold' : 'font-medium'}`}>
            {enPalabras(estado)}
          </span>
        </li>
      ))}
    </ol>
  )
}

/** AJ5: «12 de sept, 16:30», en 24 h. */
function fechaYHora(iso: string): string {
  return new Date(iso).toLocaleString('es-CO', {
    day: 'numeric',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
    hourCycle: 'h23',
  })
}

/**
 * El traspaso: qué puede hacer quien mira y cómo llegó aquí (N2, N3). De quién
 * es la pieza ya lo dice la pista de arriba.
 *
 * Los botones son los que la API dice que el usuario puede dar ahora (K4), y
 * acompañan al 403 del servidor, nunca lo sustituyen (D3).
 */
function PanelTraspaso({
  pieza,
  haySinGuardar,
  tareas,
  alMover,
}: {
  pieza: Pieza
  haySinGuardar: boolean
  tareas: Tarea[]
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

  const botones = [...pieza.transiciones].sort(
    (a, b) => Number(vuelveAtras(a)) - Number(vuelveAtras(b)),
  )

  return (
    <Estacion titulo="Traspaso" className="border-t border-line pt-5 pb-8 lg:pr-7">
      {botones.length > 0 && (
        <div className="flex flex-col gap-4">
          <Campo rotulo="Nota para el traspaso · opcional">
            <textarea
              value={nota}
              onChange={(e) => setNota(e.target.value)}
              rows={3}
              placeholder={
                pieza.transiciones.includes('devolver')
                  ? 'Si la devuelves, di qué ajustar.'
                  : undefined
              }
              className={`${CONTROL} resize-y leading-normal`}
            />
          </Campo>
          <div className="flex flex-wrap gap-2.5">
            {botones.map((transicion) => (
              <button
                key={transicion}
                type="button"
                onClick={() => void mover(transicion)}
                disabled={moviendo || haySinGuardar}
                className={vuelveAtras(transicion) ? BOTON_SECUNDARIO : BOTON}
              >
                {enPalabras(transicion)}
              </button>
            ))}
          </div>
          {/* Mover la pieza con los textos a medias le pasaría al otro la
              versión anterior. */}
          {haySinGuardar && (
            <p className="text-[13px] leading-snug text-alert">
              Guarda los textos antes de moverla: el otro vería la versión anterior.
            </p>
          )}
          {/* AD7: la checklist informa y no bloquea (Fase 6, §7.2). Los
              botones siguen activos, y el servidor tampoco mira las tareas. */}
          {tareas.some((tarea) => !tarea.hecha) && (
            <p className="text-[13px] leading-snug text-alert">
              Checklist: {quedan(tareas)}. Se puede mover igual.
            </p>
          )}
          {/* AO2, donde se decide: al entregar la solicitud, que es cuando el
              editor recibe el cuadro. Tampoco bloquea. */}
          {pieza.transiciones.includes('entregar') && faltaDelCuadro(pieza).length > 0 && (
            <p className="text-[13px] leading-snug text-alert">
              Cuadro de materiales: falta {faltaDelCuadro(pieza).join(', ')}. Se puede entregar
              igual.
            </p>
          )}
        </div>
      )}

      {error && <Aviso mensaje={error} />}

      <div className="border-t border-line pt-3.5">
        <h3 className="mono-label text-ink-3">Historia</h3>
        {historia === null ? (
          <p className="mono-label mt-2 text-ink-3">Cargando…</p>
        ) : historia.length === 0 ? (
          <p className="mt-2 text-sm text-ink-2">Todavía no ha cambiado de manos.</p>
        ) : (
          // Lo último arriba: al abrir una pieza devuelta, lo primero que se
          // lee es la nota que dice qué ajustar.
          <ol className="mt-1 flex flex-col">
            {[...historia].reverse().map((paso) => (
              <li
                key={paso.id}
                className="grid grid-cols-[7.5rem_minmax(0,1fr)] gap-x-4 gap-y-1 border-b border-line-faint py-3 last:border-b-0 max-sm:grid-cols-1"
              >
                <span className="mono-data leading-[22px] text-ink-3">
                  {fechaYHora(paso.creado_en)}
                </span>
                <span className="flex min-w-0 flex-col gap-1">
                  <span className="flex flex-wrap items-baseline gap-x-2.5 gap-y-0.5">
                    <span className="text-[15px] font-semibold">{enPalabras(paso.transicion)}</span>
                    <span className="mono-data text-ink-3">
                      {enPalabras(paso.desde)} → {enPalabras(paso.hacia)} · {paso.creado_por}
                    </span>
                  </span>
                  {paso.nota && (
                    <span className="text-sm leading-snug whitespace-pre-wrap text-prose">
                      {paso.nota}
                    </span>
                  )}
                </span>
              </li>
            ))}
          </ol>
        )}
      </div>
    </Estacion>
  )
}

/**
 * Las fechas de la pieza (AC3): la entrega del diseño y la publicación
 * prevista. Se guardan solas, sin pasar por «Guardar», como el tema (Y5).
 */
function PanelFechas({
  pieza,
  alCambiar,
}: {
  pieza: Pieza
  alCambiar: (pieza: Pieza) => void
}) {
  const [error, setError] = useState<string | null>(null)

  async function guardar(cambios: {
    fecha_entrega?: string | null
    fecha_publicacion_prevista?: string | null
  }) {
    setError(null)
    try {
      alCambiar(
        await pedir<Pieza>(`/api/piezas/${pieza.id}`, {
          method: 'PATCH',
          body: JSON.stringify(cambios),
        }),
      )
    } catch (causa) {
      setError(causa instanceof ErrorDeApi ? causa.message : 'No se pudo guardar la fecha')
    }
  }

  return (
    <Estacion titulo="Fechas" className="border-t border-line pt-5 pb-6">
      <div className="grid gap-3 sm:grid-cols-2">
        {/* «Entrega del diseño» y no «Fecha de entrega», que es la palabra del
            editor: junto al botón «Entregar» de Johan, que es la otra
            entrega, se leería al revés (Fase 6, §7.7). */}
        <CampoFecha
          etiqueta="Entrega del diseño"
          valor={pieza.fecha_entrega}
          alGuardar={(valor) => void guardar({ fecha_entrega: valor })}
        />
        <CampoFecha
          etiqueta="Publicación prevista"
          valor={pieza.fecha_publicacion_prevista}
          alGuardar={(valor) => void guardar({ fecha_publicacion_prevista: valor })}
        />
      </div>

      {error && <Aviso mensaje={error} />}
    </Estacion>
  )
}

/**
 * Un campo de fecha del navegador que se guarda solo, pero no en cada cambio:
 * al teclear el año, el campo pasa por 0002, 0020 y 0202 antes de 2026, y cada
 * paso sería un PATCH que podría llegar después del bueno. Se guarda al salir
 * del campo, o tras un momento sin cambios, que es lo que cubre elegir el día
 * en el calendario: ahí el foco se queda en el campo.
 */
function CampoFecha({
  etiqueta,
  valor,
  alGuardar,
}: {
  etiqueta: string
  valor: string | null
  alGuardar: (valor: string | null) => void
}) {
  const [borrador, setBorrador] = useState(valor ?? '')
  const pendiente = useRef<number | undefined>(undefined)

  function guardar(nuevo: string) {
    window.clearTimeout(pendiente.current)
    if (nuevo !== (valor ?? '')) alGuardar(nuevo || null)
  }

  return (
    <Campo rotulo={etiqueta}>
      {/* El `color-scheme: dark` de la página pone claro el icono del
          calendario, que en negro no se vería sobre el campo. */}
      <input
        type="date"
        value={borrador}
        onChange={(e) => {
          const nuevo = e.target.value
          setBorrador(nuevo)
          window.clearTimeout(pendiente.current)
          pendiente.current = window.setTimeout(() => guardar(nuevo), 800)
        }}
        onBlur={() => guardar(borrador)}
        className={CONTROL}
      />
    </Campo>
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
    <Estacion titulo="Material" className="border-t border-line pt-5 pb-8 lg:pr-7">
      {enlaces === null ? (
        <p className="mono-label text-ink-3">Cargando…</p>
      ) : enlaces.length === 0 ? (
        <p className="text-sm text-ink-2">Todavía no hay enlaces.</p>
      ) : (
        <ul className="flex flex-col">
          {enlaces.map((enlace) => (
            <li
              key={enlace.id}
              className="flex items-start justify-between gap-4 border-b border-line-faint py-2.5"
            >
              <span className="flex min-w-0 flex-col gap-0.5">
                {/* S2: en otra pestaña, y sin darle a la página enlazada acceso
                    a esta ni saber de dónde viene la visita. */}
                <a
                  href={enlace.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-[15px] break-words underline decoration-control underline-offset-[3px] hover:decoration-ink"
                >
                  {enlace.nota || enlace.url}
                </a>
                <span className="mono-data text-ink-3">
                  {dominio(enlace.url)} · {enlace.creado_por}
                </span>
              </span>
              <button
                type="button"
                onClick={() => void quitar(enlace)}
                className={`${BOTON_DE_TEXTO} shrink-0`}
              >
                Quitar
              </button>
            </li>
          ))}
        </ul>
      )}

      <form
        onSubmit={anadir}
        className="grid items-end gap-2 md:grid-cols-[minmax(0,3fr)_minmax(0,2fr)_auto]"
      >
        <Campo rotulo="Enlace">
          <input
            type="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://… un pin, un vídeo, un artículo"
            className={CONTROL}
          />
        </Campo>
        <Campo rotulo="Para qué sirve · opcional">
          <input
            type="text"
            value={nota}
            onChange={(e) => setNota(e.target.value)}
            className={CONTROL}
          />
        </Campo>
        <button type="submit" disabled={enviando || !url.trim()} className={BOTON_SECUNDARIO}>
          {enviando ? 'Añadiendo…' : 'Añadir enlace'}
        </button>
      </form>

      {error && <Aviso mensaje={error} />}

      <Carpeta pieza={pieza} />
    </Estacion>
  )
}

/**
 * La carpeta de la pieza en Syncthing (Q3, S3, S4). Lo que se lista es la copia
 * de la máquina donde corre la app; cada uno abre los originales desde la
 * suya, y para encontrarlos está «Copiar ruta».
 */
function Carpeta({ pieza }: { pieza: Pieza }) {
  const [estado, setEstado] = useState<EstadoDeLaCarpeta | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [ocupado, setOcupado] = useState(false)
  const [copiada, setCopiada] = useState<string | null>(null)

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

  // S3: la ruta dentro de la carpeta compartida, que es la misma en las dos
  // máquinas. Si no se puede copiar, al menos se ve.
  async function copiarRuta(archivo: Archivo) {
    const ruta = `${estado?.carpeta}/${archivo.nombre}`
    setError(null)
    if (await copiar(ruta)) {
      setCopiada(archivo.nombre)
      setTimeout(() => setCopiada((actual) => (actual === archivo.nombre ? null : actual)), 2000)
    } else {
      setError(`No se pudo copiar. La ruta es: ${ruta}`)
    }
  }

  const botonCopiar = (archivo: Archivo) => (
    <button
      type="button"
      onClick={() => void copiarRuta(archivo)}
      className={`${BOTON_DE_TEXTO} shrink-0 self-start`}
    >
      {copiada === archivo.nombre ? 'Copiada' : 'Copiar ruta'}
    </button>
  )

  const imagenes = estado?.archivos.filter((a) => a.miniatura) ?? []
  const otros = estado?.archivos.filter((a) => !a.miniatura) ?? []

  return (
    <div className="flex flex-col gap-3.5 border-t border-line pt-3.5">
      <div className="flex items-baseline justify-between gap-3">
        <h3 className="mono-label min-w-0 break-words text-ink-3">
          Carpeta en Syncthing
          {estado?.carpeta && (
            <span className="font-sans text-[13px] tracking-normal normal-case text-ink font-stretch-normal">
              {' '}
              · {estado.carpeta}
            </span>
          )}
        </h3>
        {/* La app no se entera sola de lo que llega a la carpeta. */}
        {estado && (
          <button
            type="button"
            onClick={() => void pedirCarpeta()}
            disabled={ocupado}
            className={`${BOTON_DE_TEXTO} shrink-0`}
          >
            Actualizar
          </button>
        )}
      </div>

      {estado === null ? (
        !error && <p className="mono-label text-ink-3">Cargando…</p>
      ) : estado.motivo ? (
        <p className="text-sm text-ink-2">{estado.motivo}</p>
      ) : estado.carpeta === null ? (
        <button
          type="button"
          onClick={() => void pedirCarpeta({ method: 'POST' })}
          disabled={ocupado}
          className={`${BOTON_SECUNDARIO} self-start`}
        >
          {ocupado ? 'Creando…' : 'Crear la carpeta de la pieza'}
        </button>
      ) : estado.archivos.length === 0 ? (
        <p className="text-sm text-ink-2">
          Vacía. Lo que pongas en esta carpeta, dentro de tu carpeta de Syncthing, aparece
          aquí.
        </p>
      ) : (
        <>
          {/* S3: las imágenes, en miniatura. `contain` y no `cover`: de una
              referencia importa la imagen entera, no un recorte. Cinco por
              fila en la vista ancha, para que no crezcan con ella. */}
          {imagenes.length > 0 && (
            <ul className="grid grid-cols-3 gap-3 md:grid-cols-5">
              {imagenes.map((archivo) => (
                <li key={archivo.nombre} className="flex min-w-0 flex-col gap-1">
                  <img
                    src={archivo.miniatura ?? undefined}
                    alt={archivo.nombre}
                    loading="lazy"
                    className="aspect-square w-full border border-line bg-surface object-contain"
                  />
                  <p className="text-[12.5px] leading-snug break-all">{archivo.nombre}</p>
                  <p className="mono-data text-ink-3">{detalles(archivo)}</p>
                  {botonCopiar(archivo)}
                </li>
              ))}
            </ul>
          )}

          {/* R4: lo demás, sin miniatura. */}
          {otros.length > 0 && (
            <ul className="flex flex-col">
              {otros.map((archivo) => (
                <li
                  key={archivo.nombre}
                  className="flex items-baseline justify-between gap-3 border-t border-line-faint py-2"
                >
                  <span className="min-w-0 text-[13px] break-words">{archivo.nombre}</span>
                  <span className="flex shrink-0 items-baseline gap-4">
                    <span className="mono-data text-ink-3">{detalles(archivo)}</span>
                    {botonCopiar(archivo)}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </>
      )}

      {error && <Aviso mensaje={error} />}
    </div>
  )
}

/** Q3: el tamaño y la fecha, como los da el explorador; la hora, en 24 h (AJ5). */
function detalles(archivo: Archivo): string {
  return `${enBytes(archivo.tamano)} · ${fechaYHora(archivo.modificado)}`
}

/**
 * Copia al portapapeles también sin HTTPS. El editor entra por Tailscale en
 * HTTP, y ahí el navegador no ofrece `navigator.clipboard`: queda la vía
 * antigua, un campo de texto temporal y `execCommand('copy')`.
 */
async function copiar(texto: string): Promise<boolean> {
  if (window.isSecureContext && navigator.clipboard) {
    try {
      await navigator.clipboard.writeText(texto)
      return true
    } catch {
      // Sin permiso: se prueba la vía antigua.
    }
  }

  const anterior = document.activeElement
  const campo = document.createElement('textarea')
  campo.value = texto
  campo.setAttribute('readonly', '')
  campo.style.position = 'fixed'
  campo.style.opacity = '0'
  document.body.append(campo)
  campo.focus()
  campo.select()
  try {
    return document.execCommand('copy')
  } finally {
    campo.remove()
    // El foco vuelve al botón, para quien usa el teclado.
    if (anterior instanceof HTMLElement) anterior.focus()
  }
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
        className={BOTON_SECUNDARIO}
      >
        {enviando ? 'Exportando…' : 'Exportar al vault'}
      </button>

      {(resultado || error) && (
        <div className="absolute top-full right-4 left-4 z-10 mt-2 flex justify-end sm:right-6 lg:right-10">
          <div className="w-full max-w-xl bg-page">
            {error ? (
              <Aviso mensaje={error} />
            ) : (
              <p role="status" className="flex flex-col gap-1 border border-control px-3 py-2.5">
                <span className="mono-label text-ink-2">Escrito en</span>
                <span className="mono-data break-all text-ink">{resultado}</span>
              </p>
            )}
          </div>
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
  const [consultando, setConsultando] = useState(false)

  // Una nota que se crea en el vault con la pieza abierta no llega sola: se
  // vuelve a mirar con «Actualizar», como la carpeta de Syncthing.
  const consultar = useCallback(() => {
    setConsultando(true)
    setError(null)
    pedir<EstadoDelRespaldo>('/api/respaldo')
      .then(setEstado)
      .catch((causa: unknown) =>
        setError(causa instanceof ErrorDeApi ? causa.message : 'No se pudo consultar'),
      )
      .finally(() => setConsultando(false))
  }, [])

  useEffect(consultar, [consultar])

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
    <Estacion
      titulo="Respaldo científico"
      extra={
        <button type="button" onClick={consultar} disabled={consultando} className={BOTON_DE_TEXTO}>
          Actualizar
        </button>
      }
      className="border-t border-line pt-5 pb-7"
    >
      {error && <Aviso mensaje={error} />}

      {/* G4, la mitad de interfaz: si el vault no está montado la aplicación
          funciona igual y dice por qué, en vez de fingir que no hay notas. */}
      {estado && !estado.disponible && <p className="text-sm text-ink-2">{estado.motivo}</p>}

      {estado?.disponible &&
        (estado.notas.length === 0 ? (
          <p className="text-sm text-ink-2">No hay notas de respaldo en el vault todavía.</p>
        ) : (
          <ul className="flex flex-col gap-3.5">
            {estado.notas.map((nota) => (
              <li key={nota.archivo}>
                <label className="flex cursor-pointer items-start gap-2.5">
                  <input
                    type="checkbox"
                    checked={pieza.respaldo.includes(nota.archivo)}
                    onChange={() => void alternar(nota.archivo)}
                    className="mt-0.5 size-4 shrink-0 accent-ink"
                  />
                  <span className="flex min-w-0 flex-col gap-1">
                    <span className="text-sm leading-snug break-words">{nota.fuente_titulo}</span>
                    {(nota.autor || nota.fecha) && (
                      <span className="mono-data text-ink-3">
                        {[nota.autor, nota.fecha].filter(Boolean).join(' · ')}
                      </span>
                    )}
                  </span>
                </label>
              </li>
            ))}
          </ul>
        ))}

      {/* §2.1: el respaldo lo escribe el vault y aquí solo se enlaza. Dicho en
          pantalla, porque «no deja añadir» se lee como un fallo. */}
      {estado?.disponible && (
        <p className="text-[13px] leading-snug text-ink-3">
          Son las notas literature de Investigacion/Recursos, en el vault. Una nota nueva
          aparece aquí al actualizar.
        </p>
      )}
    </Estacion>
  )
}
