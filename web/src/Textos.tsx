import { useId } from 'react'

import { LIMITES_DEL_CAPTION, conCaption, palabraDe } from './cuadro'
import { VistaPrevia } from './Guion'
import { caracteres, formulas, hashtags, palabras, sinFormulas } from './recuento'
import { BOTON_DE_TEXTO, BOTON_SECUNDARIO, CONTROL, Campo } from './ui'

/** «1 lámina», «3 láminas», «2.200 caracteres»: en palabras y con el punto de los miles. */
export function contar(n: number, singular: string, plural: string): string {
  return `${n.toLocaleString('es-CO')} ${n === 1 ? singular : plural}`
}

/**
 * El copy gráfico (Fase 8, AP2): el texto de cada lámina, que el editor pone
 * en la pieza tal cual. Un campo por lámina, con su largo debajo, porque es
 * por lámina donde se sufre un copy «excesivamente largo» (estados §4). Sin
 * límite: se muestran los recuentos y el editor juzga (fase 8, §8.4).
 *
 * Un post individual o un póster son una lámina, así que empiezan con su
 * campo; se guarda en cuanto se escribe en él.
 */
export function CopyGrafico({
  laminas,
  deUnaLamina,
  alCambiar,
}: {
  laminas: string[]
  deUnaLamina: boolean
  alCambiar: (laminas: string[]) => void
}) {
  const grupo = useId()
  const id = (que: string, indice: number) => `${grupo}-${que}-${indice}`
  const visibles = laminas.length === 0 && deUnaLamina ? [''] : laminas
  const ultima = visibles.length - 1

  /** Después del render que trae el cambio: el elemento aún no existe o no está en su sitio. */
  const enfocar = (elemento: string) =>
    requestAnimationFrame(() => document.getElementById(elemento)?.focus())

  function mover(indice: number, hacia: -1 | 1) {
    const nuevas = [...visibles]
    const destino = indice + hacia
    ;[nuevas[indice], nuevas[destino]] = [nuevas[destino], nuevas[indice]]
    alCambiar(nuevas)
    // El foco sigue a la lámina que se movió, para poder seguir moviéndola; en
    // un extremo, al botón del otro sentido, que es el que sigue activo.
    const enElExtremo = destino === 0 || destino === ultima
    const boton = hacia === -1 ? (enElExtremo ? 'bajar' : 'subir') : enElExtremo ? 'subir' : 'bajar'
    enfocar(id(boton, destino))
  }

  function anadir() {
    alCambiar([...visibles, ''])
    enfocar(id('texto', visibles.length))
  }

  return (
    <div className="flex flex-col gap-5">
      {visibles.length === 0 ? (
        <p className="text-sm text-ink-2">
          Todavía no hay copy gráfico: el texto de cada lámina, tal cual va en la pieza.
        </p>
      ) : (
        <ol className="grid gap-x-7 gap-y-6 lg:grid-cols-2">
          {visibles.map((lamina, indice) => (
            <li key={indice} className="flex min-w-0 flex-col gap-2">
              <div className="flex items-baseline justify-between gap-3">
                <label htmlFor={id('texto', indice)} className="mono-label text-ink-2">
                  Lámina {indice + 1}
                </label>
                <span className="flex items-baseline gap-3.5">
                  <button
                    type="button"
                    id={id('subir', indice)}
                    aria-label={`Subir la lámina ${indice + 1}`}
                    onClick={() => mover(indice, -1)}
                    disabled={indice === 0}
                    className={BOTON_DE_TEXTO}
                  >
                    ↑
                  </button>
                  <button
                    type="button"
                    id={id('bajar', indice)}
                    aria-label={`Bajar la lámina ${indice + 1}`}
                    onClick={() => mover(indice, 1)}
                    disabled={indice === ultima}
                    className={BOTON_DE_TEXTO}
                  >
                    ↓
                  </button>
                  <button
                    type="button"
                    aria-label={`Quitar la lámina ${indice + 1}`}
                    onClick={() => alCambiar(visibles.filter((_, j) => j !== indice))}
                    className={BOTON_DE_TEXTO}
                  >
                    Quitar
                  </button>
                </span>
              </div>
              <textarea
                id={id('texto', indice)}
                value={lamina}
                onChange={(e) =>
                  alCambiar(visibles.map((texto, j) => (j === indice ? e.target.value : texto)))
                }
                rows={3}
                className={`${CONTROL} resize-y leading-normal`}
              />
              <RecuentoDeLamina texto={lamina} />
              {/* El editor pone la fórmula en la pieza, y la lee pintada, no
                  en LaTeX: la de la lámina, con el mismo KaTeX del guion. */}
              {lamina.includes('$') && (
                <div className="border-l border-line-strong pl-4">
                  <VistaPrevia texto={lamina} />
                </div>
              )}
            </li>
          ))}
        </ol>
      )}

      <button type="button" onClick={anadir} className={`${BOTON_SECUNDARIO} self-start`}>
        Añadir lámina
      </button>
    </div>
  )
}

/**
 * El largo de una lámina, sin contar el LaTeX de sus fórmulas, que no es lo
 * que se ve en la pieza: las fórmulas van aparte, y pintadas debajo.
 */
function RecuentoDeLamina({ texto }: { texto: string }) {
  const leido = sinFormulas(texto)
  const cuantas = formulas(texto)
  return (
    <span className="mono-data text-ink-3">
      {contar(caracteres(leido), 'carácter', 'caracteres')} ·{' '}
      {contar(palabras(leido), 'palabra', 'palabras')}
      {cuantas > 0 && ` · más ${contar(cuantas, 'fórmula', 'fórmulas')}`}
    </span>
  )
}

/**
 * El caption (Fase 8, AP3): el texto que acompaña la publicación. Cuenta
 * caracteres y hashtags y, por cada destino que lleva caption, los compara con
 * su límite. Pasarse lo dice en rosa y en palabras, pero no impide guardar:
 * quien decide es quien publica.
 */
export function Caption({
  texto,
  destinos,
  alCambiar,
}: {
  texto: string
  destinos: string[]
  alCambiar: (texto: string) => void
}) {
  const totalCaracteres = caracteres(texto)
  const totalHashtags = hashtags(texto)
  const redes = conCaption(destinos)

  return (
    <div className="grid gap-x-7 gap-y-6 lg:grid-cols-[minmax(0,3fr)_minmax(0,2fr)]">
      <div className="flex min-w-0 flex-col gap-2">
        <Campo rotulo="Caption">
          <textarea
            value={texto}
            onChange={(e) => alCambiar(e.target.value)}
            rows={10}
            placeholder="El texto que acompaña la publicación, con sus hashtags."
            className={`${CONTROL} resize-y leading-normal`}
          />
        </Campo>
        <span className="mono-data text-ink-3">
          {contar(totalCaracteres, 'carácter', 'caracteres')} ·{' '}
          {contar(totalHashtags, 'hashtag', 'hashtags')}
        </span>
      </div>

      <div className="flex min-w-0 flex-col gap-2">
        <h3 className="mono-label text-ink-3">Límites por destino</h3>
        {redes.length === 0 ? (
          <p className="text-sm text-ink-2">
            {destinos.length > 0
              ? 'Un impreso no lleva caption.'
              : 'Elige los destinos en el cuadro de materiales para ver sus límites.'}
          </p>
        ) : (
          <ul className="flex flex-col">
            {redes.map((destino) => {
              const limite = LIMITES_DEL_CAPTION[destino]
              return (
                <li
                  key={destino}
                  className="flex flex-col gap-1 border-b border-line-faint py-2.5 last:border-b-0"
                >
                  <span className="flex items-baseline gap-2.5">
                    <span className="text-sm font-medium">{palabraDe(destino)}</span>
                    {limite?.donde && (
                      <span className="mono-data text-ink-3">{limite.donde}</span>
                    )}
                  </span>
                  <span className="mono-data flex flex-col gap-0.5 text-ink-2">
                    <Medida
                      valor={totalCaracteres}
                      limite={limite?.caracteres ?? null}
                      singular="carácter"
                      plural="caracteres"
                    />
                    <Medida
                      valor={totalHashtags}
                      limite={limite?.hashtags ?? null}
                      singular="hashtag"
                      plural="hashtags"
                    />
                  </span>
                </li>
              )
            })}
          </ul>
        )}
        <p className="text-[13px] leading-snug text-ink-3">
          Límites comprobados el 26 de septiembre de 2026; las redes los cambian. Un emoji
          cuenta aquí como un carácter, y cada red lo cuenta a su manera: cerca del límite,
          el recuento es una guía.
        </p>
      </div>
    </div>
  )
}

/** Una medida contra su límite. Pasarse se dice en rosa y en palabras: el color solo no se oye. */
function Medida({
  valor,
  limite,
  singular,
  plural,
}: {
  valor: number
  limite: number | null
  singular: string
  plural: string
}) {
  if (limite === null) return <span>{contar(valor, singular, plural)}, sin límite comprobado</span>

  const sobran = valor - limite
  return (
    <span className={sobran > 0 ? 'text-alert' : undefined}>
      {valor.toLocaleString('es-CO')} de {contar(limite, singular, plural)}
      {sobran > 0 && `: ${sobran.toLocaleString('es-CO')} de más`}
    </span>
  )
}
