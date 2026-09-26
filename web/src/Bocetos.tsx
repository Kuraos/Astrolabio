import { useCallback, useEffect, useState } from 'react'

import {
  ErrorDeApi,
  pedir,
  type Boceto,
  type ElementoDelBoceto,
  type EstadoDeLosBocetos,
  type LaminaDelBoceto,
  type Pieza,
} from './api'
import { anticuado, comoFormula, esHueco, palabraDelTipo, porPeso } from './boceto'
import { fechaYHora } from './fechas'
import { VistaPrevia } from './Guion'
import { Aviso, BOTON_DE_TEXTO, BOTON_SECUNDARIO, Estacion } from './ui'

/**
 * AV2: el peso se ve en el borde y en la letra. El 1, en tinta, grueso y con
 * la letra más grande; el 4, discontinuo y pequeño.
 */
const PESOS: Record<number, { caja: string; letra: string }> = {
  1: { caja: 'border-2 border-ink bg-raised', letra: 'text-[15px] leading-tight font-bold text-ink' },
  2: { caja: 'border border-ink-2', letra: 'text-[13px] leading-snug font-semibold text-ink' },
  3: { caja: 'border border-control', letra: 'text-xs leading-snug text-prose' },
  4: {
    caja: 'border border-dashed border-line-strong',
    letra: 'text-[11px] leading-snug text-ink-2',
  },
}

/**
 * Los bocetos de la pieza (Fase 9, AV), pedidos a Claude por la API. Siempre
 * con un botón: cada uno cuesta, y nada los pide solo (ADR 0016).
 */
export default function PanelBocetos({
  pieza,
  haySinGuardar,
}: {
  pieza: Pieza
  /** AV7: el boceto se hace con lo guardado, no con lo que se está escribiendo. */
  haySinGuardar: boolean
}) {
  const [estado, setEstado] = useState<EstadoDeLosBocetos | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [pidiendo, setPidiendo] = useState(false)
  // AV4: 0 es el más nuevo, porque la lista llega del más nuevo al más viejo.
  const [indice, setIndice] = useState(0)

  const ruta = `/api/piezas/${pieza.id}/bocetos`

  const consultar = useCallback(async () => {
    try {
      setEstado(await pedir<EstadoDeLosBocetos>(ruta))
    } catch (causa) {
      setError(causa instanceof ErrorDeApi ? causa.message : 'No se pudieron leer los bocetos')
    }
  }, [ruta])

  // Guardar el cuadro o el copy cambia la pieza, y con ella si se puede pedir.
  useEffect(() => {
    void consultar()
  }, [consultar, pieza])

  async function pedirUno() {
    setPidiendo(true)
    setError(null)
    try {
      await pedir<Boceto>(ruta, { method: 'POST' })
      setIndice(0)
    } catch (causa) {
      setError(causa instanceof ErrorDeApi ? causa.message : 'No se pudo pedir el boceto')
    }
    // Con éxito o sin él, la lista la dice el servidor.
    await consultar()
    setPidiendo(false)
  }

  const bocetos = estado?.bocetos ?? []
  const boceto = bocetos[Math.min(indice, bocetos.length - 1)]

  return (
    <Estacion titulo="Boceto" className="col-span-full border-t border-line pt-5 pb-4">
      <div className="flex flex-wrap items-center gap-x-5 gap-y-2.5">
        <button
          type="button"
          onClick={() => void pedirUno()}
          disabled={!estado?.disponible || pidiendo}
          className={BOTON_SECUNDARIO}
        >
          {pidiendo ? 'Pidiendo…' : bocetos.length > 0 ? 'Pedir otro boceto' : 'Pedir boceto'}
        </button>
        {pidiendo ? (
          <p role="status" className="mono-label text-ink-3">
            Claude está haciendo el boceto: suele tardar uno o dos minutos.
          </p>
        ) : estado && !estado.disponible ? (
          // Sin configurar o sin lo que hace falta: no es un error (§7).
          <p className="text-sm text-ink-2">{estado.motivo}</p>
        ) : (
          estado && (
            <p className="text-[13px] leading-snug text-ink-3">
              Lo hace Claude con el cuadro, el copy gráfico y el guion guardados. Cada boceto
              cuesta unos centavos de dólar.
            </p>
          )
        )}
      </div>

      {haySinGuardar && estado?.disponible && !pidiendo && (
        <p className="text-[13px] leading-snug text-alert">
          Hay cambios sin guardar: el boceto se hará con lo guardado.
        </p>
      )}

      {error && <Aviso mensaje={error} />}

      {estado === null
        ? !error && <p className="mono-label text-ink-3">Cargando…</p>
        : boceto
          ? (
            <VistaDelBoceto
              boceto={boceto}
              pieza={pieza}
              numero={bocetos.length - Math.min(indice, bocetos.length - 1)}
              total={bocetos.length}
              alMover={(paso) => setIndice((actual) => actual + paso)}
            />
          )
          : estado.disponible && (
            <p className="text-sm text-ink-2">Todavía no hay bocetos de esta pieza.</p>
          )}
    </Estacion>
  )
}

/** Un boceto: de cuándo y de quién, sus avisos y sus láminas. */
function VistaDelBoceto({
  boceto,
  pieza,
  numero,
  total,
  alMover,
}: {
  boceto: Boceto
  pieza: Pieza
  /** Contado desde el más viejo: el 1 es el primero que se pidió. */
  numero: number
  total: number
  /** +1 va a uno más viejo; −1, a uno más nuevo. */
  alMover: (paso: 1 | -1) => void
}) {
  const tokens = `${boceto.tokens_entrada.toLocaleString('es-CO')} + ${boceto.tokens_salida.toLocaleString('es-CO')} tokens`

  return (
    <div className="flex flex-col gap-4">
      <div className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
        <p className="mono-data text-ink-3">
          Boceto {numero} de {total} · {fechaYHora(boceto.creado_en)} · {boceto.creado_por} ·{' '}
          {boceto.modelo} · {tokens}
        </p>
        {total > 1 && (
          <span className="flex gap-5">
            <button
              type="button"
              onClick={() => alMover(1)}
              disabled={numero === 1}
              className={BOTON_DE_TEXTO}
            >
              ← Anterior
            </button>
            <button
              type="button"
              onClick={() => alMover(-1)}
              disabled={numero === total}
              className={BOTON_DE_TEXTO}
            >
              Siguiente →
            </button>
          </span>
        )}
      </div>

      {anticuado(boceto, pieza) && (
        <p className="text-[13px] leading-snug text-alert">
          El copy gráfico cambió después de este boceto: pide otro para que lo siga.
        </p>
      )}

      {/* AV6: la exactitud es de Johan (AGENTS §1). */}
      {boceto.avisos.length > 0 && (
        <div className="flex flex-col gap-1">
          <p className="text-[13px] leading-snug text-alert">
            Cifras que no están en el guion ni en el copy: compruébalas antes de usarlas.
          </p>
          <ul className="flex flex-col gap-0.5">
            {boceto.avisos.map((aviso) => (
              <li key={aviso} className="text-[13px] leading-snug text-alert">
                {aviso}
              </li>
            ))}
          </ul>
        </div>
      )}

      <ol className="grid gap-x-7 gap-y-8 sm:grid-cols-2 xl:grid-cols-3">
        {boceto.laminas.map((lamina) => (
          <li key={lamina.numero} className="min-w-0">
            <LaminaDeBoceto lamina={lamina} columnas={boceto.columnas} filas={boceto.filas} />
          </li>
        ))}
      </ol>
    </div>
  )
}

/**
 * AV2 y AV3: una lámina, dibujada desde los datos en su proporción, con la
 * rejilla a la vista y cada elemento en su zona. Rejilla de CSS y no SVG, para
 * que el texto se parta solo y las fórmulas salgan con el KaTeX del guion
 * (fase 9, §8.8).
 */
export function LaminaDeBoceto({
  lamina,
  columnas,
  filas,
}: {
  lamina: LaminaDelBoceto
  columnas: number
  filas: number
}) {
  return (
    <figure className="flex min-w-0 flex-col gap-2.5">
      <figcaption className="flex flex-col gap-1">
        <span className="mono-label text-ink-2">Lámina {lamina.numero}</span>
        <span className="text-sm leading-snug">{lamina.idea}</span>
      </figcaption>

      <div
        className="grid overflow-hidden border border-line-strong bg-surface"
        style={{
          aspectRatio: `${columnas} / ${filas}`,
          gridTemplateColumns: `repeat(${columnas}, minmax(0, 1fr))`,
          gridTemplateRows: `repeat(${filas}, minmax(0, 1fr))`,
          backgroundImage:
            'linear-gradient(to right, var(--color-line) 1px, transparent 1px), linear-gradient(to bottom, var(--color-line) 1px, transparent 1px)',
          backgroundSize: `calc(100% / ${columnas}) calc(100% / ${filas})`,
        }}
      >
        {porPeso(lamina.elementos).map((elemento, i) => (
          <ElementoDeBoceto key={i} elemento={elemento} />
        ))}
      </div>

      <p className="text-[13px] leading-snug text-ink-2">
        <span className="mono-label text-ink-3">Para la edición · </span>
        {lamina.nota_para_la_edicion}
      </p>
    </figure>
  )
}

/**
 * Un elemento en su zona. Lo que escribe el modelo se pinta como texto o como
 * markdown sin HTML, nunca como marcado propio (ADR 0016).
 */
function ElementoDeBoceto({ elemento }: { elemento: ElementoDelBoceto }) {
  const { zona, tipo, peso, contenido } = elemento
  const estilo = PESOS[peso] ?? PESOS[4]
  // En una fila no caben el rótulo encima y el texto debajo: van en línea, o
  // la nota de un crédito se quedaba en «Nota · 4» y nada más.
  const disposicion =
    zona.filas === 1 ? 'flex-row items-baseline gap-1.5 px-1.5 py-1' : 'flex-col gap-0.5 p-1.5'

  return (
    <div
      className={`relative flex min-h-0 min-w-0 overflow-hidden ${disposicion} ${estilo.caja}`}
      style={{
        gridColumn: `${zona.col} / span ${zona.cols}`,
        gridRow: `${zona.fila} / span ${zona.filas}`,
      }}
    >
      {esHueco(tipo) && <Aspa />}
      <span className="mono-data relative shrink-0 text-ink-3">
        {palabraDelTipo(tipo)} · {peso}
      </span>
      {esHueco(tipo) ? (
        <p className={`relative italic ${estilo.letra}`}>{contenido}</p>
      ) : (
        <div className="relative min-w-0">
          <VistaPrevia
            texto={tipo === 'formula' ? comoFormula(contenido) : contenido}
            letra={estilo.letra}
          />
        </div>
      )}
    </div>
  )
}

/** El aspa de los bocetos de siempre: aquí va una imagen. */
function Aspa() {
  return (
    <svg
      aria-hidden="true"
      viewBox="0 0 100 100"
      preserveAspectRatio="none"
      className="absolute inset-0 size-full text-line-strong"
    >
      <line x1="0" y1="0" x2="100" y2="100" stroke="currentColor" vectorEffect="non-scaling-stroke" />
      <line x1="100" y1="0" x2="0" y2="100" stroke="currentColor" vectorEffect="non-scaling-stroke" />
    </svg>
  )
}
