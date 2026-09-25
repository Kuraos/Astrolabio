import { useCallback, useEffect, useState } from 'react'

import { ErrorDeApi, pedir, type Pieza, type Tarea, type Usuario } from './api'
import { catalogo } from './catalogo'
import { diaDeHoy, diaDeLaSemana, diaYMes, semanas } from './fechas'
import { aQuienLeToca, enPalabras } from './flujo'
import VistaPieza from './Pieza'
import { tablero } from './tablero'
import ListaDeTareas, { quedan } from './Tareas'

/**
 * Fase 0, criterios D1–D4, y el tablero de la Fase 6 (AB), que reemplazó a
 * la lista de N1.
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

  return (
    <main className="min-h-screen bg-slate-950 p-6 text-slate-100">
      {/* Con sesión, la columna pasa de 512 a 1024 px: el tablero necesita
          sus seis columnas (AB5), y la pieza, el guion con la vista previa al
          lado (X1). La entrada se queda estrecha. */}
      <div className={`mx-auto w-full space-y-6 ${usuario ? 'max-w-5xl' : 'max-w-lg'}`}>
        <header className="space-y-1">
          <h1 className="text-2xl font-semibold tracking-tight">Astrolabio</h1>
          <p className="text-sm text-slate-400">Taller de Voz del Cosmos</p>
        </header>

        {comprobando ? (
          <p className="text-sm text-slate-400">Comprobando sesión…</p>
        ) : usuario ? (
          <Taller usuario={usuario} alSalir={() => setUsuario(null)} />
        ) : (
          <Login alEntrar={setUsuario} />
        )}
      </div>
    </main>
  )
}

/** D1: contra el endpoint real. No hay ningún usuario simulado en el cliente. */
function Login({ alEntrar }: { alEntrar: (u: Usuario) => void }) {
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
    <Panel titulo="Entrar">
      <form onSubmit={entrar} className="space-y-3">
        <Campo
          etiqueta="Usuario"
          valor={usuario}
          alCambiar={setUsuario}
          autoComplete="username"
        />
        <Campo
          etiqueta="Contraseña"
          valor={password}
          alCambiar={setPassword}
          tipo="password"
          autoComplete="current-password"
        />

        {error && <Aviso mensaje={error} />}

        <button
          type="submit"
          disabled={enviando || !usuario || !password}
          className="w-full rounded-md bg-slate-100 px-3 py-2.5 text-sm font-medium text-slate-900 disabled:opacity-50"
        >
          {enviando ? 'Entrando…' : 'Entrar'}
        </button>
      </form>
    </Panel>
  )
}

function Taller({ usuario, alSalir }: { usuario: Usuario; alSalir: () => void }) {
  const [piezas, setPiezas] = useState<Pieza[] | null>(null)
  const [abierta, setAbierta] = useState<Pieza | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [filtro, setFiltro] = useState<string | null>(null)
  const [tareas, setTareas] = useState<Tarea[]>([])

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

  async function salir() {
    try {
      await pedir('/api/auth/logout', { method: 'POST' })
    } finally {
      // Aunque el logout falle, en este cliente ya no hay sesión utilizable.
      alSalir()
    }
  }

  return (
    <div className="space-y-6">
      {/* D2: nombre y rol del usuario que entró. */}
      <Panel titulo="Sesión">
        <div className="flex items-center justify-between gap-3">
          <p className="text-sm">
            <span className="font-medium">{usuario.usuario}</span>
            <span className="ml-2 rounded bg-slate-800 px-2 py-0.5 text-xs text-slate-300">
              {usuario.rol}
            </span>
          </p>
          <button
            type="button"
            onClick={() => void salir()}
            className="rounded-md border border-slate-700 px-3 py-1.5 text-xs text-slate-300"
          >
            Salir
          </button>
        </div>
      </Panel>

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
        <>
      {/*
        D3: al editor no se le enseña el botón. Es **además** del 403 del
        servidor, nunca en su lugar: §2.3 dice que ocultar un botón no es
        autorización, es decoración.
      */}
      {usuario.rol === 'investigador' && <NuevaPieza alCrear={cargar} />}

      <Panel titulo="Piezas · abre una para escribir el guion">
        {error ? (
          <Aviso mensaje={error} />
        ) : piezas === null ? (
          <p className="text-sm text-slate-400">Cargando…</p>
        ) : piezas.length === 0 ? (
          <p className="text-sm text-slate-400">
            Todavía no hay piezas.
            {usuario.rol === 'editor' && ' Johan crea la primera.'}
          </p>
        ) : (
          <>
          {activo && (
            <p className="mb-2 flex items-baseline justify-between gap-3 text-xs text-slate-400">
              <span>
                Solo las de <span className="text-slate-100">{activo}</span>
              </span>
              <button
                type="button"
                onClick={() => setFiltro(null)}
                className="shrink-0 text-slate-400 hover:text-slate-200"
              >
                Ver todas
              </button>
            </p>
          )}
          <Tablero
            piezas={piezas.filter(
              (pieza) => activo === null || pieza.etiquetas.includes(activo),
            )}
            usuario={usuario}
            tareas={tareas}
            alAbrir={setAbierta}
          />
          </>
        )}
      </Panel>

      {/* AE2: para cuándo, por semanas. */}
      <Panel titulo="Semanas · entregas y publicaciones pendientes">
        <Semanas piezas={piezas ?? []} alAbrir={setAbierta} />
      </Panel>

      {/* AD5: lo que no es de ninguna pieza. */}
      <Panel titulo="Tareas sueltas · las que no son de ninguna pieza">
        <ListaDeTareas
          tareas={tareas.filter((tarea) => tarea.pieza_id === null)}
          piezaId={null}
          actualizar={setTareas}
        />
      </Panel>

      {/* Z2: de qué se ha hablado. Pulsar una etiqueta filtra la lista de
          arriba; pulsarla otra vez la devuelve entera. */}
      <Panel titulo="Etiquetas · de qué hemos hablado">
        {entradas.length === 0 ? (
          <p className="text-sm text-slate-400">
            Todavía no hay etiquetas: se ponen en cada pieza.
          </p>
        ) : (
          <ul className="divide-y divide-slate-800">
            {entradas.map((entrada) => (
              <li key={entrada.etiqueta}>
                <button
                  type="button"
                  aria-pressed={activo === entrada.etiqueta}
                  onClick={() =>
                    setFiltro(activo === entrada.etiqueta ? null : entrada.etiqueta)
                  }
                  className={`-mx-2 flex w-[calc(100%+1rem)] items-baseline justify-between gap-3 rounded-md px-2 py-2 text-left hover:bg-slate-800/60 ${
                    activo === entrada.etiqueta ? 'bg-slate-800/60' : ''
                  }`}
                >
                  <span className="min-w-0 break-words text-sm text-slate-100">
                    {entrada.etiqueta}
                  </span>
                  <span className="shrink-0 text-xs text-slate-400">
                    {entrada.publicadas} {entrada.publicadas === 1 ? 'publicada' : 'publicadas'}{' '}
                    · {entrada.enCurso} en curso
                  </span>
                </button>
              </li>
            ))}
          </ul>
        )}
      </Panel>
        </>
      )}
    </div>
  )
}

/**
 * AB1–AB3: una columna por estado, y en cada tarjeta de quién es y qué le
 * falta. Mover la pieza no se hace aquí: la tarjeta la abre, y ahí están sus
 * botones, la nota de «Devolver» y las confirmaciones (Fase 6, §7.4). Los dos
 * roles abren cualquier pieza; lo que el editor no ve dentro es el respaldo.
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
  return (
    <div className="grid gap-4 md:grid-cols-3 lg:grid-cols-6">
      {tablero(piezas).map((columna) => (
        <section key={columna.estado} className="min-w-0 space-y-2">
          <h3 className="flex items-baseline justify-between gap-2 text-xs font-medium uppercase tracking-wider text-slate-400">
            <span className="min-w-0 break-words">{enPalabras(columna.estado)}</span>
            <span>{columna.piezas.length}</span>
          </h3>
          <ul className="space-y-2">
            {columna.piezas.map((pieza) => (
              <li key={pieza.id}>
                {/* Que se vea que se abre: fondo al pasar por encima y una
                    flecha. Sin ellos, la lista de antes parecía de solo
                    lectura, y pasó de verdad. `gap` y no `space-y`: la línea
                    de abajo se oculta cuando queda vacía, y un hueco hecho
                    con margen se quedaría. */}
                <button
                  type="button"
                  onClick={() => alAbrir(pieza)}
                  className="group flex w-full flex-col gap-1.5 rounded-md border border-slate-800 px-2 py-2 text-left hover:bg-slate-800/60"
                >
                  <span className="flex items-baseline justify-between gap-2">
                    <span className="min-w-0 break-words text-sm text-slate-100">
                      {pieza.titulo}
                    </span>
                    <span
                      aria-hidden
                      className="shrink-0 text-slate-600 group-hover:text-slate-300"
                    >
                      →
                    </span>
                  </span>
                  <span className="flex flex-wrap items-center gap-x-2 gap-y-1 text-xs text-slate-400 empty:hidden">
                    <Turno pieza={pieza} usuario={usuario} />
                    {/* AC4: para cuándo. */}
                    {pieza.fecha_entrega && (
                      <span>entrega {diaYMes(pieza.fecha_entrega)}</span>
                    )}
                    {pieza.fecha_publicacion_prevista && (
                      <span>publicación {diaYMes(pieza.fecha_publicacion_prevista)}</span>
                    )}
                    <Pendientes
                      tareas={tareas.filter((tarea) => tarea.pieza_id === pieza.id)}
                    />
                    {pieza.guion.trim() === '' && <span>sin guion</span>}
                  </span>
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
 * AE2: lo pendiente con fecha, por semanas, porque el editor trabaja «por
 * bloques semanales, quincenales o mensuales» (P1). Lo atrasado sale primero,
 * y cada entrada abre su pieza.
 */
function Semanas({ piezas, alAbrir }: { piezas: Pieza[]; alAbrir: (pieza: Pieza) => void }) {
  const lista = semanas(piezas, diaDeHoy())

  if (lista.length === 0) {
    return (
      <p className="text-sm text-slate-400">
        Nada pendiente con fecha. Las fechas se ponen en cada pieza.
      </p>
    )
  }

  return (
    <div className="space-y-4">
      {lista.map((semana) => (
        <section key={semana.lunes} className="space-y-1">
          <h3 className="text-xs font-medium text-slate-300">
            Semana del {diaYMes(semana.lunes)}
            {semana.cuando === 'esta' && <span className="text-slate-400"> · esta semana</span>}
            {semana.cuando === 'pasada' && (
              <span className="text-amber-300/80"> · atrasada</span>
            )}
          </h3>
          <ul>
            {semana.entradas.map((entrada) => (
              <li key={`${entrada.tipo}-${entrada.pieza.id}`}>
                <button
                  type="button"
                  onClick={() => alAbrir(entrada.pieza)}
                  className="-mx-2 flex w-[calc(100%+1rem)] items-baseline gap-3 rounded-md px-2 py-1.5 text-left text-xs hover:bg-slate-800/60"
                >
                  <span className="w-12 shrink-0 text-slate-400">
                    {diaDeLaSemana(entrada.fecha)}
                  </span>
                  <span className="w-20 shrink-0 text-slate-400">
                    {entrada.tipo === 'entrega' ? 'entrega' : 'publicación'}
                  </span>
                  <span className="min-w-0 break-words text-slate-100">
                    {entrada.pieza.titulo}
                  </span>
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
  return texto ? <span>{texto}</span> : null
}

/** El turno de cada pieza, resaltado cuando le toca a quien mira. */
function Turno({ pieza, usuario }: { pieza: Pieza; usuario: Usuario }) {
  const texto = aQuienLeToca(pieza, usuario)
  if (texto === null) return null

  return (
    <span
      className={`shrink-0 rounded px-2 py-0.5 text-[11px] ${
        pieza.de_quien_es === usuario.rol
          ? 'bg-amber-400/15 text-amber-200'
          : 'text-slate-400'
      }`}
    >
      {texto}
    </span>
  )
}

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
    <Panel titulo="Nueva pieza">
      <form onSubmit={crear} className="space-y-3">
        <Campo etiqueta="Título" valor={titulo} alCambiar={setTitulo} />

        {error && <Aviso mensaje={error} />}

        {/* Sin `w-full`, a diferencia de «Entrar»: con el tablero la columna
            mide 1024 px (AB5), y a ese ancho el botón pesaría más que él. */}
        <button
          type="submit"
          disabled={enviando || !titulo.trim()}
          className="rounded-md bg-slate-100 px-3 py-2.5 text-sm font-medium text-slate-900 disabled:opacity-40"
        >
          {enviando ? 'Creando…' : 'Crear pieza'}
        </button>
      </form>
    </Panel>
  )
}

function Campo({
  etiqueta,
  valor,
  alCambiar,
  tipo = 'text',
  autoComplete,
}: {
  etiqueta: string
  valor: string
  alCambiar: (v: string) => void
  tipo?: string
  autoComplete?: string
}) {
  return (
    <label className="block space-y-1.5">
      <span className="text-xs text-slate-400">{etiqueta}</span>
      <input
        type={tipo}
        value={valor}
        autoComplete={autoComplete}
        onChange={(e) => alCambiar(e.target.value)}
        className="w-full rounded-md border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100 outline-none focus:border-slate-500"
      />
    </label>
  )
}

/** D4: los errores se ven, con `role="alert"` para que también se oigan. */
function Aviso({ mensaje }: { mensaje: string }) {
  return (
    <p
      role="alert"
      className="rounded-md border border-rose-900/60 bg-rose-950/40 px-3 py-2 text-xs text-rose-200"
    >
      {mensaje}
    </p>
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
