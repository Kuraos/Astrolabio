import { useCallback, useEffect, useState } from 'react'

import {
  ErrorDeApi,
  pedir,
  type EstadoDelRespaldo,
  type NotaDeRespaldo,
  type Pieza,
} from './api'
import { repartir } from './fuente'
import { Aviso, BOTON, BOTON_DE_TEXTO, BOTON_SECUNDARIO, CONTROL, Campo, Estacion } from './ui'

/**
 * J2 y la Fase 12: el respaldo científico de la pieza. Arriba, las fuentes
 * que son de esta pieza (BC1); debajo, las demás del vault, con su buscador
 * (BC2), y el formulario que crea una nueva (BB). Solo lo ve Johan.
 */
export default function PanelRespaldo({
  pieza,
  alCambiar,
}: {
  pieza: Pieza
  alCambiar: (p: Pieza) => void
}) {
  const [estado, setEstado] = useState<EstadoDelRespaldo | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [consultando, setConsultando] = useState(false)
  const [busqueda, setBusqueda] = useState('')
  const [creando, setCreando] = useState(false)

  // Una nota que se crea en Obsidian con la pieza abierta no llega sola: se
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

  // BB4: la API ya la dejó enlazada; aquí solo se vuelve a leer la pieza y el vault.
  async function alCrearFuente() {
    setCreando(false)
    consultar()
    try {
      alCambiar(await pedir<Pieza>(`/api/piezas/${pieza.id}`))
    } catch (causa) {
      setError(causa instanceof ErrorDeApi ? causa.message : 'No se pudo consultar')
    }
  }

  const reparto = repartir(estado?.notas ?? [], pieza.respaldo, busqueda)
  const hayDisponibles = (estado?.notas.length ?? 0) > reparto.enlazadas.length

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

      {estado?.disponible && (
        <>
          <section aria-labelledby="respaldo-de-la-pieza" className="flex flex-col gap-3">
            <h3 id="respaldo-de-la-pieza" className="mono-label text-ink-2">
              En esta pieza · {pieza.respaldo.length}
            </h3>
            {pieza.respaldo.length === 0 ? (
              <p className="text-sm text-ink-2">
                Todavía no tiene fuentes. Marca las que la respaldan, o crea una.
              </p>
            ) : (
              <ul className="flex flex-col gap-3.5">
                {reparto.enlazadas.map((nota) => (
                  <Fuente key={nota.archivo} nota={nota} marcada alAlternar={alternar} />
                ))}
                {/* Renombrada o borrada en Obsidian: el enlace sigue en la
                    pieza y saldría roto al exportar. Se dice, y se puede quitar. */}
                {reparto.perdidas.map((archivo) => (
                  <li key={archivo} className="flex items-start justify-between gap-4">
                    <span className="flex min-w-0 flex-col gap-1">
                      <span className="text-sm leading-snug break-words">{archivo}</span>
                      <span className="text-[13px] text-alert">Ya no está en el vault</span>
                    </span>
                    <button
                      type="button"
                      onClick={() => void alternar(archivo)}
                      aria-label={`Quitar ${archivo}`}
                      className={`${BOTON_DE_TEXTO} shrink-0`}
                    >
                      Quitar
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </section>

          {hayDisponibles && (
            <section aria-labelledby="respaldo-del-vault" className="flex flex-col gap-3">
              <h3 id="respaldo-del-vault" className="mono-label text-ink-2">
                Disponibles en el vault
              </h3>
              <Campo rotulo="Buscar por título o autor">
                <input
                  type="search"
                  value={busqueda}
                  onChange={(e) => setBusqueda(e.target.value)}
                  className={CONTROL}
                />
              </Campo>
              {reparto.disponibles.length === 0 ? (
                <p className="text-sm text-ink-2">Ninguna fuente coincide con la búsqueda.</p>
              ) : (
                <ul className="flex flex-col gap-3.5">
                  {reparto.disponibles.map((nota) => (
                    <Fuente key={nota.archivo} nota={nota} marcada={false} alAlternar={alternar} />
                  ))}
                </ul>
              )}
            </section>
          )}

          {creando ? (
            <NuevaFuente
              piezaId={pieza.id}
              alCrear={alCrearFuente}
              alCancelar={() => setCreando(false)}
            />
          ) : (
            <button
              type="button"
              onClick={() => setCreando(true)}
              className={`${BOTON_SECUNDARIO} self-start`}
            >
              Nueva fuente
            </button>
          )}

          {/* ADR 0019: Astrolabio crea la nota y no la vuelve a tocar. Dicho en
              pantalla, porque «no deja editarla» se lee como un fallo. */}
          <p className="text-[13px] leading-snug text-ink-3">
            Son las notas literature de Investigacion/Recursos, en el vault. Una fuente nueva se
            crea aquí o en Obsidian; después, solo se edita en Obsidian.
          </p>
        </>
      )}
    </Estacion>
  )
}

function Fuente({
  nota,
  marcada,
  alAlternar,
}: {
  nota: NotaDeRespaldo
  marcada: boolean
  alAlternar: (archivo: string) => Promise<void>
}) {
  return (
    <li>
      <label className="flex cursor-pointer items-start gap-2.5">
        <input
          type="checkbox"
          checked={marcada}
          onChange={() => void alAlternar(nota.archivo)}
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
  )
}

const VACIA = {
  fuente_titulo: '',
  nombre: '',
  fuente_tipo: 'paper',
  autor: '',
  url: '',
  resumen: '',
  confianza: '',
}

/**
 * BB: la nota literature nace aquí, con lo que pide el vault, y queda enlazada
 * a la pieza. Los valores que acepta son los de `FuenteNueva`, en
 * `api/app/fuentes.py`.
 */
function NuevaFuente({
  piezaId,
  alCrear,
  alCancelar,
}: {
  piezaId: number
  alCrear: () => Promise<void>
  alCancelar: () => void
}) {
  const [fuente, setFuente] = useState(VACIA)
  const [error, setError] = useState<string | null>(null)
  const [enviando, setEnviando] = useState(false)

  const campo =
    (nombre: keyof typeof VACIA) =>
    (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) =>
      setFuente((actual) => ({ ...actual, [nombre]: e.target.value }))

  async function crear(evento: React.FormEvent) {
    evento.preventDefault()
    setEnviando(true)
    setError(null)

    try {
      await pedir<NotaDeRespaldo>('/api/fuentes', {
        method: 'POST',
        body: JSON.stringify({ ...fuente, pieza_id: piezaId }),
      })
      await alCrear()
    } catch (causa) {
      setError(
        !(causa instanceof ErrorDeApi)
          ? 'No se pudo conectar'
          : // Un 422 trae la lista de Pydantic, no una frase. Lo único que el
            // formulario no comprueba antes es la forma del enlace.
            causa.estado === 422
            ? 'Revisa el enlace: tiene que ser una dirección http(s) o un DOI, y cada campo, de una línea.'
            : causa.message,
      )
    } finally {
      setEnviando(false)
    }
  }

  const completa = fuente.fuente_titulo.trim() && fuente.url.trim() && fuente.confianza

  return (
    <form onSubmit={crear} className="flex flex-col gap-3 border border-control p-3.5">
      <h3 className="mono-label text-ink">Nueva fuente</h3>
      <Campo rotulo="Título original de la fuente">
        <input value={fuente.fuente_titulo} onChange={campo('fuente_titulo')} className={CONTROL} />
      </Campo>
      <Campo rotulo="Nombre de la nota · opcional">
        <input
          value={fuente.nombre}
          onChange={campo('nombre')}
          placeholder="Si lo dejas vacío, el título"
          className={CONTROL}
        />
      </Campo>
      <div className="grid gap-3 sm:grid-cols-2">
        <Campo rotulo="Tipo">
          <select value={fuente.fuente_tipo} onChange={campo('fuente_tipo')} className={CONTROL}>
            <option value="paper">Paper</option>
            <option value="articulo">Artículo</option>
          </select>
        </Campo>
        <Campo rotulo="Autor · opcional">
          <input value={fuente.autor} onChange={campo('autor')} className={CONTROL} />
        </Campo>
      </div>
      <Campo rotulo="Enlace o DOI">
        <input
          value={fuente.url}
          onChange={campo('url')}
          placeholder="https://arxiv.org/abs/… o 10.3847/…"
          className={CONTROL}
        />
      </Campo>
      <Campo rotulo="Nivel de confianza científica">
        <select value={fuente.confianza} onChange={campo('confianza')} className={CONTROL}>
          <option value="">Sin decidir</option>
          <option value="consenso">Consenso establecido</option>
          <option value="hipotesis">Hipótesis activa</option>
          <option value="preliminar">Resultado preliminar</option>
        </select>
      </Campo>
      <Campo rotulo="Resumen, con tus palabras · opcional">
        <textarea
          value={fuente.resumen}
          onChange={campo('resumen')}
          rows={5}
          placeholder="Markdown y LaTeX. Sin resumen, la nota queda «por leer»."
          className={CONTROL}
        />
      </Campo>

      {error && <Aviso mensaje={error} />}

      <div className="flex flex-wrap items-center gap-3">
        <button type="submit" disabled={enviando || !completa} className={BOTON}>
          {enviando ? 'Creando…' : 'Crear en el vault'}
        </button>
        <button type="button" onClick={alCancelar} className={BOTON_DE_TEXTO}>
          Cancelar
        </button>
      </div>
    </form>
  )
}
