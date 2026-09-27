import { useCallback, useEffect, useLayoutEffect, useRef, useState } from 'react'

import { ErrorDeApi, pedir, type Pieza, type Tarea, type Usuario } from './api'
import { catalogo, type Entrada } from './catalogo'
import {
  diaDeHoy,
  diaDeLaSemana,
  diaYMes,
  entregaPendiente,
  lineaDeTiempo,
  semanas,
  type Semana,
} from './fechas'
import { aQuienLeToca, duenoDelEstado, enPalabras } from './flujo'
import VistaPieza from './Pieza'
import { ESTADOS, tablero } from './tablero'
import ListaDeTareas, { quedan } from './Tareas'
import { ANCHO, Aviso, BOTON, BOTON_DE_TEXTO, CONTROL, Campo, Estacion } from './ui'

/**
 * Fase 0, criterios D1–D4; el tablero de la Fase 6 (AB), que reemplazó a la
 * lista de N1; y la identidad «Control» de la Fase 7 (AH, AL).
 *
 * Dos pantallas y ningún enrutador: entrar o estar dentro. Una biblioteca de
 * rutas para dos estados sería infraestructura sin beneficio.
 */
export default function App() {
  const [usuario, setUsuario] = useState<Usuario | null>(null)
  const [comprobando, setComprobando] = useState(true)

  useEffect(() => {
    // Se pregunta a la API si hay sesión en vez de recordarlo en el cliente:
    // así recargar la página mantiene la sesión y el cliente nunca se cree
    // autenticado por su cuenta (D1).
    pedir<Usuario>('/api/auth/me')
      .then(setUsuario)
      // Un 401 aquí es lo normal —todavía no ha entrado nadie—, no un error
      // que enseñar. Los errores de D4 son los de las acciones del usuario.
      .catch(() => setUsuario(null))
      .finally(() => setComprobando(false))
  }, [])

  if (comprobando) {
    return <p className={`${ANCHO} mono-label py-6 text-ink-3`}>Comprobando sesión…</p>
  }

  return usuario ? (
    <Taller usuario={usuario} alSalir={() => setUsuario(null)} />
  ) : (
    <Entrar alEntrar={setUsuario} />
  )
}

/** D1 y AL1: contra el endpoint real. No hay ningún usuario simulado en el cliente. */
function Entrar({ alEntrar }: { alEntrar: (u: Usuario) => void }) {
  const [usuario, setUsuario] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [enviando, setEnviando] = useState(false)

  async function entrar(evento: React.FormEvent) {
    evento.preventDefault()
    setEnviando(true)
    setError(null)

    try {
      alEntrar(
        await pedir<Usuario>('/api/auth/login', {
          method: 'POST',
          body: JSON.stringify({ usuario, password }),
        }),
      )
    } catch (causa) {
      // D4: el error de la API se ve en pantalla, no en la consola.
      setError(causa instanceof ErrorDeApi ? causa.message : 'No se pudo conectar')
    } finally {
      setEnviando(false)
    }
  }

  return (
    <main className={`${ANCHO} flex min-h-screen flex-col`}>
      <p className="mono-label flex h-14 shrink-0 items-center border-b border-line text-ink-3">
        Voz del Cosmos / Taller
      </p>

      <h1 className="mt-16 text-[clamp(2rem,10vw,8rem)] leading-[0.85] font-black tracking-[-0.01em] uppercase font-stretch-expanded">
        Astrolabio
      </h1>
      <p className="mono-label mt-4 text-ink-2">Taller de Voz del Cosmos</p>

      <form onSubmit={entrar} className="mt-14 flex w-full max-w-[360px] flex-col gap-4">
        <Campo rotulo="Usuario">
          <input
            value={usuario}
            onChange={(e) => setUsuario(e.target.value)}
            autoComplete="username"
            className={CONTROL}
          />
        </Campo>
        <Campo rotulo="Contraseña">
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="current-password"
            className={CONTROL}
          />
        </Campo>

        {error && <Aviso mensaje={error} />}

        <button type="submit" disabled={enviando || !usuario || !password} className={`${BOTON} mt-1`}>
          {enviando ? 'Entrando…' : 'Entrar'}
        </button>
      </form>

      {/* El flujo que se viene a mover, como adorno: por eso `aria-hidden`. */}
      <ol
        aria-hidden
        className="mono-label mt-auto mb-10 grid grid-cols-6 gap-0.5 pt-16 text-ink-3 max-md:hidden"
      >
        {ESTADOS.map((estado, i) => (
          <li key={estado} className="border-t-[3px] border-line pt-2.5">
            {String(i + 1).padStart(2, '0')} {enPalabras(estado)}
          </li>
        ))}
      </ol>
    </main>
  )
}

function Taller({ usuario, alSalir }: { usuario: Usuario; alSalir: () => void }) {
  const [piezas, setPiezas] = useState<Pieza[] | null>(null)
  const [abierta, setAbierta] = useState<Pieza | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [filtro, setFiltro] = useState<string | null>(null)
  const [tareas, setTareas] = useState<Tarea[]>([])
  // Dónde estaba el tablero al abrir la pieza, para devolverlo al volver.
  const desplazamiento = useRef(0)

  function abrir(pieza: Pieza) {
    desplazamiento.current = window.scrollY
    setAbierta(pieza)
  }

  // Sin enrutador, el navegador no se entera de que cambió la pantalla y
  // conserva el desplazamiento del tablero: la pieza se abría a media altura,
  // con la barra, el título y los estados (AJ1, AJ2) fuera de la vista. Se
  // abre arriba, y al volver el tablero recupera el suyo, como con «atrás».
  // `useLayoutEffect` para que el salto ocurra antes de pintar.
  useLayoutEffect(() => {
    window.scrollTo(0, abierta ? 0 : desplazamiento.current)
  }, [abierta])

  const cargar = useCallback(async () => {
    try {
      // AD2: las tareas, todas de una vez. El tablero cuenta las de cada
      // pieza, la pieza abierta recibe las suyas y las sueltas tienen panel.
      const [nuevas, todas] = await Promise.all([
        pedir<Pieza[]>('/api/piezas'),
        pedir<Tarea[]>('/api/tareas'),
      ])
      setPiezas(nuevas)
      setTareas(todas)
      setError(null)
    } catch (causa) {
      setError(causa instanceof ErrorDeApi ? causa.message : 'No se pudo conectar')
    }
  }, [])

  useEffect(() => {
    void cargar()
  }, [cargar])

  // Z1: el catálogo sale de la lista que ya está cargada.
  const entradas = catalogo(piezas ?? [])
  // Una etiqueta que ya no está en ninguna pieza deja de filtrar: si no, la
  // lista se quedaría vacía sin que su etiqueta apareciera en el catálogo.
  const activo = entradas.some((e) => e.etiqueta === filtro) ? filtro : null
  // AB4: el filtro vale para el tablero y para las semanas.
  const visibles = (piezas ?? []).filter(
    (pieza) => activo === null || pieza.etiquetas.includes(activo),
  )
  const alternarFiltro = (etiqueta: string) =>
    setFiltro(activo === etiqueta ? null : etiqueta)

  async function salir() {
    try {
      await pedir('/api/auth/logout', { method: 'POST' })
    } finally {
      // Aunque el logout falle, en este cliente ya no hay sesión utilizable.
      alSalir()
    }
  }

  return (
    <>
      {/* AH1 y D2: nombre y rol de quien entró, en la barra de arriba. */}
      <header className="border-b border-line">
        <div className={`${ANCHO} flex h-14 items-center justify-between gap-4`}>
          <div className="flex items-baseline gap-4">
            <h1 className="text-lg font-extrabold tracking-[0.02em] uppercase font-stretch-expanded sm:text-xl">
              Astrolabio
            </h1>
            <span className="mono-label text-ink-3 max-md:hidden">Voz del Cosmos / Taller</span>
          </div>
          <div className="mono-label flex items-center gap-3 text-right text-ink-2 sm:gap-6">
            <span className="max-md:hidden">{diaDeHoy().split('-').reverse().join('.')}</span>
            <span>
              {usuario.usuario} / {usuario.rol}
            </span>
            <button
              type="button"
              onClick={() => void salir()}
              className="mono-label border border-control px-3 py-2 text-ink"
            >
              Salir
            </button>
          </div>
        </div>
      </header>

      {abierta ? (
        <VistaPieza
          pieza={abierta}
          usuario={usuario}
          sugerencias={entradas.map((e) => e.etiqueta)}
          tareas={tareas.filter((tarea) => tarea.pieza_id === abierta.id)}
          actualizarTareas={setTareas}
          alVolver={() => {
            setAbierta(null)
            void cargar()
          }}
        />
      ) : (
        <main className={`${ANCHO} flex flex-col gap-12 pt-6 pb-16`}>
          {error ? (
            <Aviso mensaje={error} />
          ) : piezas === null ? (
            <p className="mono-label text-ink-3">Cargando…</p>
          ) : (
            <section aria-label="Tablero" className="flex flex-col gap-3">
              {piezas.length === 0 && (
                <p className="text-sm text-ink-2">
                  Todavía no hay piezas.
                  {usuario.rol === 'editor' && ' Johan crea la primera.'}
                </p>
              )}
              {activo && <SoloLasDe etiqueta={activo} alQuitar={() => setFiltro(null)} />}
              <div className="grid md:grid-cols-3 lg:grid-cols-[200px_repeat(6,minmax(0,1fr))]">
                <div className="flex flex-col gap-8 pb-8 max-lg:col-span-full lg:pr-4">
                  <TeToca
                    cuantas={piezas.filter((p) => p.de_quien_es === usuario.rol).length}
                    total={piezas.length}
                  />
                  {/*
                    D3: al editor no se le enseña el formulario. Es **además**
                    del 403 del servidor, nunca en su lugar: §2.3 dice que
                    ocultar un botón no es autorización, es decoración.
                  */}
                  {usuario.rol === 'investigador' && <NuevaPieza alCrear={cargar} />}
                  <Etiquetas entradas={entradas} activo={activo} alElegir={alternarFiltro} />
                </div>
                <Tablero piezas={visibles} usuario={usuario} tareas={tareas} alAbrir={abrir} />
              </div>
            </section>
          )}

          {/* AE2: para cuándo, por semanas. */}
          <Estacion
            titulo="Semanas"
            extra={<span className="mono-label text-ink-3">Entregas y publicaciones</span>}
          >
            {activo && <SoloLasDe etiqueta={activo} alQuitar={() => setFiltro(null)} />}
            <Semanas piezas={visibles} alAbrir={abrir} />
          </Estacion>

          {/* AD5 y AH5: lo que no es de ninguna pieza. */}
          <Estacion
            titulo="Tareas sueltas"
            extra={<span className="mono-label text-ink-3">De ninguna pieza</span>}
            className="max-w-xl"
          >
            <ListaDeTareas
              tareas={tareas.filter((tarea) => tarea.pieza_id === null)}
              piezaId={null}
              actualizar={setTareas}
            />
          </Estacion>
        </main>
      )}
    </>
  )
}

/** AH2: cuántas piezas le tocan a quien mira, de cuántas. Lo único en naranja. */
function TeToca({ cuantas, total }: { cuantas: number; total: number }) {
  return (
    <p className="flex h-44 flex-col justify-between bg-signal p-4 text-page max-lg:h-auto max-lg:flex-row max-lg:items-baseline max-lg:justify-start max-lg:gap-4">
      <span className="mono-label font-medium">Te toca</span>
      <span className="text-[120px] leading-[0.82] font-black font-stretch-extra-condensed max-lg:text-6xl">
        {cuantas}
      </span>
      <span className="mono-label">
        de {total} {total === 1 ? 'pieza' : 'piezas'}
      </span>
    </p>
  )
}

/**
 * AB1–AB3 y AH2–AH4: una columna por estado, con su celda en la franja —su
 * número, cuántas piezas tiene y de quién es— y debajo sus tarjetas. Mover la
 * pieza no se hace aquí: la tarjeta la abre, y ahí están sus botones, la nota
 * de «Devolver» y las confirmaciones (Fase 6, §7.4).
 *
 * En pantalla estrecha, las columnas se apilan en el mismo orden (AB5).
 */
function Tablero({
  piezas,
  usuario,
  tareas,
  alAbrir,
}: {
  piezas: Pieza[]
  usuario: Usuario
  tareas: Tarea[]
  alAbrir: (pieza: Pieza) => void
}) {
  const hoy = diaDeHoy()
  return (
    <>
      {tablero(piezas).map((columna, i) => {
        const dueno = duenoDelEstado(columna.estado, usuario)
        return (
      <section
        key={columna.estado}
        className={`flex min-w-0 flex-col border-line ${i > 0 ? 'lg:border-l' : ''}`}
      >
        <header className="flex flex-col gap-1.5 border-b border-line px-3 pt-4 pb-3.5 max-lg:flex-row max-lg:items-baseline max-lg:gap-3 max-lg:px-0 lg:h-44">
          <span className="mono-label text-ink-3">{String(i + 1).padStart(2, '0')}</span>
          <h3 className="text-[15px] leading-tight font-semibold">{enPalabras(columna.estado)}</h3>
          <span
            className={`text-[76px] leading-[0.9] font-extrabold font-stretch-extra-condensed max-lg:ml-auto max-lg:text-3xl lg:mt-auto ${
              columna.estado === 'publicada' ? 'text-ink-3' : ''
            }`}
          >
            {columna.piezas.length}
          </span>
          <span className="mono-label text-ink-3 max-lg:hidden">{dueno ?? '—'}</span>
        </header>
        <ul className="flex flex-col px-3 max-lg:px-0">
          {columna.piezas.map((pieza) => (
            <li key={pieza.id}>
              <Tarjeta
                pieza={pieza}
                usuario={usuario}
                tareas={tareas.filter((tarea) => tarea.pieza_id === pieza.id)}
                hoy={hoy}
                alAbrir={() => alAbrir(pieza)}
              />
            </li>
          ))}
        </ul>
      </section>
        )
      })}
    </>
  )
}

/**
 * Que se vea que se abre: fondo al pasar por encima y una flecha. Sin ellos, la
 * lista de antes parecía de solo lectura, y pasó de verdad. `gap` y no
 * `space-y`: la línea de fechas se oculta cuando queda vacía, y un hueco hecho
 * con margen se quedaría.
 */
function Tarjeta({
  pieza,
  usuario,
  tareas,
  hoy,
  alAbrir,
}: {
  pieza: Pieza
  usuario: Usuario
  tareas: Tarea[]
  hoy: string
  alAbrir: () => void
}) {
  const turno = aQuienLeToca(pieza, usuario)

  return (
    <button
      type="button"
      onClick={alAbrir}
      className="group -mx-2 flex w-[calc(100%+1rem)] flex-col gap-2 border-b border-line px-2 py-3.5 text-left hover:bg-raised"
    >
      {turno &&
        (pieza.de_quien_es === usuario.rol ? (
          <span className="mono-label flex items-center gap-1.5 font-medium text-signal">
            <span aria-hidden className="size-2 bg-signal" />
            {turno}
          </span>
        ) : (
          <span className="mono-label text-ink-3">{turno}</span>
        ))}
      <span className="flex items-baseline justify-between gap-2">
        <span
          className={`min-w-0 text-base leading-tight break-words ${
            pieza.estado === 'publicada' ? 'text-ink-2' : 'font-medium'
          }`}
        >
          {pieza.titulo}
        </span>
        <span aria-hidden className="text-sm leading-none text-ink-3 group-hover:text-ink">
          →
        </span>
      </span>
      <span className="mono-data flex flex-col text-ink-2 empty:hidden">
        {/* AC4: para cuándo, mientras siga pendiente. Entregado el diseño, su
            fecha ya no dice nada; publicada la pieza, la prevista se leería
            como la real, que es otra (ADR 0012). Vencidas, en rosa (§7.4):
            anteriores a hoy, con el mismo criterio que las semanas. */}
        {pieza.fecha_entrega && entregaPendiente(pieza) && (
          <span className={pieza.fecha_entrega < hoy ? 'text-alert' : ''}>
            Entrega <span className="whitespace-nowrap">{diaYMes(pieza.fecha_entrega)}</span>
          </span>
        )}
        {pieza.fecha_publicacion_prevista && pieza.estado !== 'publicada' && (
          <span className={pieza.fecha_publicacion_prevista < hoy ? 'text-alert' : ''}>
            Publicación{' '}
            <span className="whitespace-nowrap">{diaYMes(pieza.fecha_publicacion_prevista)}</span>
          </span>
        )}
        <Pendientes tareas={tareas} />
        {pieza.guion.trim() === '' && <span>Sin guion</span>}
      </span>
    </button>
  )
}

/**
 * AH3 y Z2: de qué se ha hablado. Pulsar una etiqueta filtra el tablero y las
 * semanas; pulsarla otra vez los devuelve enteros. La que filtra, invertida.
 */
function Etiquetas({
  entradas,
  activo,
  alElegir,
}: {
  entradas: Entrada[]
  activo: string | null
  alElegir: (etiqueta: string) => void
}) {
  return (
    <section aria-label="Etiquetas" className="flex flex-col gap-2">
      <h2 className="flex flex-col gap-0.5">
        <span className="heading-station text-[13px]">Etiquetas</span>
        <span className="mono-data font-normal text-ink-3">De qué hemos hablado</span>
      </h2>
      {entradas.length === 0 ? (
        <p className="text-sm text-ink-2">Todavía no hay etiquetas: se ponen en cada pieza.</p>
      ) : (
        <ul className="flex flex-col max-lg:flex-row max-lg:flex-wrap max-lg:gap-x-6">
          {entradas.map((entrada) => {
            const elegida = activo === entrada.etiqueta
            return (
              <li key={entrada.etiqueta}>
                <button
                  type="button"
                  aria-pressed={elegida}
                  onClick={() => alElegir(entrada.etiqueta)}
                  className={`flex flex-col gap-0.5 border-t border-line-faint px-2.5 py-2 text-left lg:-mx-2.5 lg:w-[calc(100%+1.25rem)] ${
                    elegida ? 'bg-ink text-page' : 'hover:bg-raised'
                  }`}
                >
                  <span className={`text-sm break-words ${elegida ? 'font-semibold' : ''}`}>
                    {entrada.etiqueta}
                  </span>
                  <span className={`mono-data ${elegida ? 'text-line' : 'text-ink-3'}`}>
                    {entrada.publicadas} {entrada.publicadas === 1 ? 'publicada' : 'publicadas'} ·{' '}
                    {entrada.enCurso} en curso
                  </span>
                </button>
              </li>
            )
          })}
        </ul>
      )}
    </section>
  )
}

/**
 * La nota de un panel filtrado por etiqueta (AB4), con la salida del filtro.
 * Sin ella, unas semanas vacías dirían que no hay nada pendiente.
 */
function SoloLasDe({ etiqueta, alQuitar }: { etiqueta: string; alQuitar: () => void }) {
  return (
    <p className="mono-label flex items-baseline justify-between gap-3 text-ink-2">
      <span>
        Solo las de{' '}
        <span className="font-sans text-sm tracking-normal normal-case text-ink font-stretch-normal">
          {etiqueta}
        </span>
      </span>
      <button type="button" onClick={alQuitar} className={BOTON_DE_TEXTO}>
        Ver todas
      </button>
    </p>
  )
}

/**
 * AE2: lo pendiente con fecha, por semanas, porque el editor trabaja «por
 * bloques semanales, quincenales o mensuales» (P1). Lo atrasado sale primero,
 * y cada entrada abre su pieza. Desde `md`, en una línea de días (AI2); en
 * pantalla estrecha, en lista.
 */
function Semanas({ piezas, alAbrir }: { piezas: Pieza[]; alAbrir: (pieza: Pieza) => void }) {
  const hoy = diaDeHoy()
  const lista = semanas(piezas, hoy)

  if (lista.length === 0) {
    return (
      <p className="text-sm text-ink-2">
        Nada pendiente con fecha. Las fechas se ponen en cada pieza.
      </p>
    )
  }

  return (
    <>
      <LineaDeTiempo lista={lista} hoy={hoy} alAbrir={alAbrir} />
      <ListaDeSemanas lista={lista} alAbrir={alAbrir} />
    </>
  )
}

/**
 * AI2: una columna por día, con hoy invertido y lo atrasado en rosa: cada
 * entrada vencida, aunque sea de esta semana, y el rótulo de las semanas ya
 * pasadas. Cada etiqueta cuelga de su día —o, al final de la línea, acaba en
 * él— y va en el carril que le dio `lineaDeTiempo`. Los números de los días
 * son andamio: el lector de pantalla lee las semanas y las entradas, no 28
 * números.
 */
function LineaDeTiempo({
  lista,
  hoy,
  alAbrir,
}: {
  lista: Semana[]
  hoy: string
  alAbrir: (pieza: Pieza) => void
}) {
  const linea = lineaDeTiempo(lista, hoy)
  const columnas = linea.celdas
    .map((celda) => (celda.tipo === 'dia' ? 'minmax(0,1fr)' : '1.5rem'))
    .join(' ')
  const lunes = new Set(linea.semanas.map((s) => s.desde))

  return (
    <div className="grid border-t border-line max-md:hidden" style={{ gridTemplateColumns: columnas }}>
      {linea.semanas.map((semana) => (
        <span
          key={semana.lunes}
          className={`mono-label border-l border-line-strong px-2 py-2 ${
            semana.cuando === 'pasada'
              ? 'text-alert'
              : semana.cuando === 'esta'
                ? 'text-ink'
                : 'text-ink-2'
          }`}
          style={{ gridColumn: `${semana.desde} / span 7`, gridRow: 1 }}
        >
          Semana del {diaYMes(semana.lunes)}
          {semana.cuando === 'pasada' && ' · atrasada'}
          {semana.cuando === 'esta' && ' · esta semana'}
        </span>
      ))}

      {linea.celdas.map((celda, i) =>
        celda.tipo === 'salto' ? (
          <span
            key={`salto-${i}`}
            aria-hidden
            className="mono-data flex items-center justify-center border-b border-line text-ink-3"
            style={{ gridColumn: i + 1, gridRow: '1 / span 2' }}
          >
            …
          </span>
        ) : (
          <span
            key={celda.fecha}
            aria-hidden
            className={`mono-data border-b border-l py-1 pl-1.5 ${
              lunes.has(i + 1) ? 'border-l-line-strong' : 'border-l-line-faint'
            } ${celda.hoy ? 'border-b-ink bg-ink font-medium text-page' : 'border-b-line text-ink-3'}`}
            style={{ gridColumn: i + 1, gridRow: 2 }}
          >
            {Number(celda.fecha.slice(8))}
          </span>
        ),
      )}

      {linea.marcas.map(({ entrada, cuando, desde, hasta, ancla, carril }) => (
        <button
          key={`${entrada.tipo}-${entrada.pieza.id}`}
          type="button"
          onClick={() => alAbrir(entrada.pieza)}
          className={`mt-3 flex min-w-0 flex-col gap-1 px-2 pt-0.5 pb-1 hover:bg-raised ${
            ancla === 'inicio' ? 'border-l-2 text-left' : 'items-end border-r-2 text-right'
          } ${
            entrada.vencida
              ? 'border-alert'
              : cuando === 'esta'
                ? 'border-ink'
                : 'border-control'
          }`}
          style={{ gridColumn: `${desde} / ${hasta + 1}`, gridRow: carril + 3 }}
        >
          <span className={`mono-label ${entrada.vencida ? 'text-alert' : 'text-ink-2'}`}>
            {diaDeLaSemana(entrada.fecha)} · {entrada.tipo === 'entrega' ? 'Entrega' : 'Publicación'}
            {entrada.vencida && ' · atrasada'}
          </span>
          <span className="text-sm leading-tight font-medium break-words">{entrada.pieza.titulo}</span>
        </button>
      ))}
    </div>
  )
}

/** AE2 tal cual, para pantallas estrechas: una línea de días no cabe en un teléfono. */
function ListaDeSemanas({ lista, alAbrir }: { lista: Semana[]; alAbrir: (pieza: Pieza) => void }) {
  return (
    <div className="flex flex-col gap-5 md:hidden">
      {lista.map((semana) => (
        <section key={semana.lunes} className="flex flex-col">
          <h3
            className={`mono-label border-b border-line pb-2 ${
              semana.cuando === 'pasada'
                ? 'text-alert'
                : semana.cuando === 'esta'
                  ? 'text-ink'
                  : 'text-ink-2'
            }`}
          >
            Semana del {diaYMes(semana.lunes)}
            {semana.cuando === 'esta' && ' · esta semana'}
            {semana.cuando === 'pasada' && ' · atrasada'}
          </h3>
          <ul>
            {semana.entradas.map((entrada) => (
              <li key={`${entrada.tipo}-${entrada.pieza.id}`}>
                <button
                  type="button"
                  onClick={() => alAbrir(entrada.pieza)}
                  className="-mx-2 grid w-[calc(100%+1rem)] grid-cols-[3.5rem_6.5rem_minmax(0,1fr)] items-baseline gap-2 border-b border-line-faint px-2 py-2.5 text-left hover:bg-raised"
                >
                  <span className={`mono-data ${entrada.vencida ? 'text-alert' : 'text-ink-2'}`}>
                    {diaDeLaSemana(entrada.fecha)}
                  </span>
                  <span className={`mono-data ${entrada.vencida ? 'text-alert' : 'text-ink-2'}`}>
                    {entrada.tipo === 'entrega' ? 'Entrega' : 'Publicación'}
                    {entrada.vencida && ' · atrasada'}
                  </span>
                  <span className="text-sm break-words">{entrada.pieza.titulo}</span>
                </button>
              </li>
            ))}
          </ul>
        </section>
      ))}
    </div>
  )
}

/**
 * AD6: qué le falta a la pieza. Nada, y no un elemento vacío, si no tiene
 * tareas: así la línea de la tarjeta se sigue ocultando cuando queda vacía.
 */
function Pendientes({ tareas }: { tareas: Tarea[] }) {
  const texto = quedan(tareas)
  // `quedan` va en minúscula porque el traspaso lo usa a media frase; aquí
  // abre la línea.
  return texto ? <span>{texto[0].toUpperCase() + texto.slice(1)}</span> : null
}

/** AH3: la pieza nueva, en la columna de la izquierda. Solo la ve Johan (D3). */
function NuevaPieza({ alCrear }: { alCrear: () => Promise<void> }) {
  const [titulo, setTitulo] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [enviando, setEnviando] = useState(false)

  async function crear(evento: React.FormEvent) {
    evento.preventDefault()
    setEnviando(true)
    setError(null)

    try {
      await pedir<Pieza>('/api/piezas', {
        method: 'POST',
        body: JSON.stringify({ titulo }),
      })
      setTitulo('')
      await alCrear()
    } catch (causa) {
      setError(causa instanceof ErrorDeApi ? causa.message : 'No se pudo conectar')
    } finally {
      setEnviando(false)
    }
  }

  return (
    <form onSubmit={crear} className="flex flex-col gap-2.5">
      <Campo rotulo="Nueva pieza">
        <input
          value={titulo}
          onChange={(e) => setTitulo(e.target.value)}
          placeholder="Título"
          className={CONTROL}
        />
      </Campo>

      {error && <Aviso mensaje={error} />}

      <button type="submit" disabled={enviando || !titulo.trim()} className={BOTON}>
        {enviando ? 'Creando…' : 'Crear pieza'}
      </button>
    </form>
  )
}
