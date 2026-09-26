/**
 * Lo que se repite en todas las pantallas (Fase 7, AG3): las clases de los
 * botones y de los campos, la estación, el campo con su rótulo y el aviso de
 * error. Cómo y cuándo se usa cada uno, en DESIGN_SYSTEM §6.
 */

/** El ancho de las pantallas: hasta 1440 px (AH6), con su margen. */
export const ANCHO = 'mx-auto w-full max-w-[1440px] px-4 sm:px-6 lg:px-10'

/** Lo que avanza la pieza o guarda: tinta sobre negro. */
export const BOTON =
  'mono-label bg-ink px-3.5 py-3 font-medium text-page disabled:opacity-40'

/** Lo que vuelve atrás o no mueve la pieza. */
export const BOTON_SECUNDARIO =
  'mono-label border border-control px-3.5 py-[11px] text-ink disabled:opacity-40'

/** Volver, quitar, actualizar, copiar: sin caja. */
export const BOTON_DE_TEXTO =
  'mono-label py-1 text-ink-2 hover:text-ink disabled:opacity-40'

/** Campo, selector y área de texto. El borde de 3,7:1 se ve como control (AG4). */
export const CONTROL =
  'w-full border border-control bg-transparent p-2.5 text-sm text-ink outline-none placeholder:text-ink-3 focus:border-ink disabled:opacity-40'

/** Una sección de pantalla: su título y, si hace falta, una acción a la derecha. */
export function Estacion({
  titulo,
  extra,
  className = '',
  children,
}: {
  titulo: string
  extra?: React.ReactNode
  className?: string
  children: React.ReactNode
}) {
  return (
    <section className={`flex min-w-0 flex-col gap-4 ${className}`}>
      <div className="flex items-baseline justify-between gap-3">
        <h2 className="heading-station">{titulo}</h2>
        {extra}
      </div>
      {children}
    </section>
  )
}

/** Un control con su rótulo visible encima (AJ4): el placeholder no basta. */
export function Campo({
  rotulo,
  className = '',
  children,
}: {
  rotulo: string
  className?: string
  children: React.ReactNode
}) {
  return (
    <label className={`flex min-w-0 flex-col gap-2 ${className}`}>
      <span className="mono-label text-ink-2">{rotulo}</span>
      {children}
    </label>
  )
}

/**
 * La pestaña a la que lleva una tecla, o `null` si la tecla no mueve: las
 * flechas pasan a la de al lado, dando la vuelta, e Inicio y Fin van a los
 * extremos, como pide el patrón de pestañas de ARIA.
 */
export function pestanaTrasTecla(actual: number, total: number, tecla: string): number | null {
  switch (tecla) {
    case 'ArrowRight':
      return (actual + 1) % total
    case 'ArrowLeft':
      return (actual - 1 + total) % total
    case 'Home':
      return 0
    case 'End':
      return total - 1
    default:
      return null
  }
}

/** Los `id` que unen cada pestaña con su panel. */
export const idsDePestana = (grupo: string, valor: string) => ({
  pestana: `${grupo}-pestana-${valor}`,
  panel: `${grupo}-panel-${valor}`,
})

/**
 * Pestañas (Fase 8, AP1): la elegida, invertida, como todo lo seleccionado
 * (DESIGN_SYSTEM §1). Con el teclado, Tab entra en la elegida y sale al
 * panel, y las flechas eligen otra. Los paneles los pone quien las usa, con
 * `role="tabpanel"` y los `id` de `idsDePestana`.
 */
export function Pestanas<T extends string>({
  grupo,
  nombre,
  pestanas,
  actual,
  alElegir,
}: {
  grupo: string
  nombre: string
  pestanas: { valor: T; rotulo: string }[]
  actual: T
  alElegir: (valor: T) => void
}) {
  const indice = pestanas.findIndex((p) => p.valor === actual)

  return (
    <div role="tablist" aria-label={nombre} className="flex self-start border border-line-strong">
      {pestanas.map((pestana) => {
        const elegida = pestana.valor === actual
        const ids = idsDePestana(grupo, pestana.valor)
        return (
          <button
            key={pestana.valor}
            id={ids.pestana}
            type="button"
            role="tab"
            aria-selected={elegida}
            aria-controls={ids.panel}
            tabIndex={elegida ? 0 : -1}
            onClick={() => alElegir(pestana.valor)}
            onKeyDown={(e) => {
              const destino = pestanaTrasTecla(indice, pestanas.length, e.key)
              if (destino === null) return
              e.preventDefault()
              alElegir(pestanas[destino].valor)
              document.getElementById(idsDePestana(grupo, pestanas[destino].valor).pestana)?.focus()
            }}
            className={`mono-label border-l border-line-strong px-3.5 py-2.5 first:border-l-0 ${
              elegida ? 'bg-ink font-medium text-page' : 'text-ink-2 hover:bg-raised hover:text-ink'
            }`}
          >
            {pestana.rotulo}
          </button>
        )
      })}
    </div>
  )
}

/** D4: los errores se ven, en su caja, y con `role="alert"` también se oyen. */
export function Aviso({ mensaje }: { mensaje: string }) {
  return (
    <p role="alert" className="flex flex-col gap-1 border border-alert bg-alert/8 px-3 py-2.5">
      <span className="mono-label font-medium text-alert">Error</span>
      <span className="text-sm leading-snug text-ink">{mensaje}</span>
    </p>
  )
}
