import { useState } from 'react'

import { ErrorDeApi, pedir, type Pieza } from './api'
import {
  DESTINOS,
  NIVELES,
  PROPOSITOS,
  TIPOS_DE_PIEZA,
  faltaDelCuadro,
  type Opcion,
} from './cuadro'
import { Aviso, CONTROL, Campo, Estacion } from './ui'

type Cambios = {
  formato?: string | null
  proposito?: string | null
  nivel?: string | null
  plataforma?: string[]
}

/**
 * El cuadro de materiales del editor (Fase 8, AO1 y AO2): tipo de pieza,
 * propósito, nivel y destino, con sus palabras. Se guarda al elegir, sin pasar
 * por «Guardar», como el tema (Y5): no tiene por qué esperar al guion.
 *
 * Debajo, lo que falta del cuadro. Informa y no bloquea, como la checklist
 * (AD7): el traspaso no mira el cuadro, ni aquí ni en el servidor.
 */
export default function PanelCuadro({
  pieza,
  alCambiar,
}: {
  pieza: Pieza
  alCambiar: (pieza: Pieza) => void
}) {
  const [error, setError] = useState<string | null>(null)
  const [guardando, setGuardando] = useState(false)

  async function guardar(cambios: Cambios) {
    setGuardando(true)
    setError(null)
    try {
      alCambiar(
        await pedir<Pieza>(`/api/piezas/${pieza.id}`, {
          method: 'PATCH',
          body: JSON.stringify(cambios),
        }),
      )
    } catch (causa) {
      setError(causa instanceof ErrorDeApi ? causa.message : 'No se pudo guardar el cuadro')
    } finally {
      setGuardando(false)
    }
  }

  // El servidor los ordena como la lista, así que da igual dónde se añada.
  const alternarDestino = (destino: string) =>
    void guardar({
      plataforma: pieza.plataforma.includes(destino)
        ? pieza.plataforma.filter((d) => d !== destino)
        : [...pieza.plataforma, destino],
    })

  const falta = faltaDelCuadro(pieza)

  return (
    <Estacion titulo="Cuadro de materiales" className="pt-5 pb-6">
      <div className="grid gap-3 sm:grid-cols-3">
        <Selector
          rotulo="Tipo de pieza"
          vacio="Sin tipo"
          opciones={TIPOS_DE_PIEZA}
          valor={pieza.formato}
          deshabilitado={guardando}
          alElegir={(formato) => void guardar({ formato })}
        />
        <Selector
          rotulo="Propósito"
          vacio="Sin propósito"
          opciones={PROPOSITOS}
          valor={pieza.proposito}
          deshabilitado={guardando}
          alElegir={(proposito) => void guardar({ proposito })}
        />
        <Selector
          rotulo="Nivel"
          vacio="Sin nivel"
          opciones={NIVELES}
          valor={pieza.nivel}
          deshabilitado={guardando}
          alElegir={(nivel) => void guardar({ nivel })}
        />
      </div>

      {/* Casillas y no un selector: una pieza puede ir a varios destinos. */}
      <fieldset className="flex min-w-0 flex-col gap-2">
        <legend className="mono-label mb-2 text-ink-2">Destino</legend>
        <div className="flex flex-wrap gap-x-6 gap-y-2.5">
          {DESTINOS.map((destino) => (
            <label key={destino.valor} className="flex cursor-pointer items-center gap-2.5 text-sm">
              <input
                type="checkbox"
                checked={pieza.plataforma.includes(destino.valor)}
                onChange={() => alternarDestino(destino.valor)}
                disabled={guardando}
                className="size-4 shrink-0 accent-ink"
              />
              {destino.palabra}
            </label>
          ))}
        </div>
      </fieldset>

      {falta.length > 0 && (
        <p className="text-[13px] leading-snug text-alert">Falta: {falta.join(', ')}.</p>
      )}

      {error && <Aviso mensaje={error} />}
    </Estacion>
  )
}

/** Un selector del cuadro, con «Sin …» para lo que aún no se ha decidido. */
function Selector({
  rotulo,
  vacio,
  opciones,
  valor,
  deshabilitado,
  alElegir,
}: {
  rotulo: string
  vacio: string
  opciones: Opcion[]
  valor: string | null
  deshabilitado: boolean
  alElegir: (valor: string | null) => void
}) {
  return (
    <Campo rotulo={rotulo}>
      <select
        value={valor ?? ''}
        onChange={(e) => alElegir(e.target.value || null)}
        disabled={deshabilitado}
        className={CONTROL}
      >
        <option value="">{vacio}</option>
        {opciones.map((opcion) => (
          <option key={opcion.valor} value={opcion.valor}>
            {opcion.palabra}
          </option>
        ))}
      </select>
    </Campo>
  )
}
