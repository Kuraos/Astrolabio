import { useCallback, useEffect, useState } from 'react'

import { ErrorDeApi, pedir, type Pieza, type Usuario } from './api'
import VistaPieza from './Pieza'

/**
 * Fase 0, criterios D1–D4.
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
      <div className="mx-auto w-full max-w-lg space-y-6">
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

  const cargar = useCallback(async () => {
    try {
      setPiezas(await pedir<Pieza[]>('/api/piezas'))
      setError(null)
    } catch (causa) {
      setError(causa instanceof ErrorDeApi ? causa.message : 'No se pudo conectar')
    }
  }, [])

  useEffect(() => {
    void cargar()
  }, [cargar])

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

      <Panel titulo="Piezas">
        {error ? (
          <Aviso mensaje={error} />
        ) : piezas === null ? (
          <p className="text-sm text-slate-400">Cargando…</p>
        ) : piezas.length === 0 ? (
          <p className="text-sm text-slate-500">
            Todavía no hay piezas.
            {usuario.rol === 'editor' && ' Johan crea la primera.'}
          </p>
        ) : (
          <ul className="divide-y divide-slate-800">
            {piezas.map((pieza) => (
              <li key={pieza.id}>
                {/* Los dos roles abren la pieza: el editor lee el guion y
                    puede corregirlo; lo que no ve es el respaldo. */}
                <button
                  type="button"
                  onClick={() => setAbierta(pieza)}
                  className="w-full py-2.5 text-left first:pt-0 last:pb-0 hover:opacity-80"
                >
                  <span className="block text-sm text-slate-100">
                    {pieza.titulo}
                  </span>
                  <span className="block text-xs text-slate-500">
                    {pieza.creada_por} ·{' '}
                    {new Date(pieza.creada_en).toLocaleDateString('es-CO', {
                      day: 'numeric',
                      month: 'short',
                      year: 'numeric',
                    })}
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

        <button
          type="submit"
          disabled={enviando || !titulo.trim()}
          className="w-full rounded-md bg-slate-100 px-3 py-2.5 text-sm font-medium text-slate-900 disabled:opacity-50"
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
