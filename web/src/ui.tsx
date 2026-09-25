/**
 * Lo que se repite en todas las pantallas (Fase 7, AG3): las clases de los
 * botones y de los campos, la estación, el campo con su rótulo y el aviso de
 * error. Cómo y cuándo se usa cada uno, en DESIGN_SYSTEM §6.
 */

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

/** D4: los errores se ven, en su caja, y con `role="alert"` también se oyen. */
export function Aviso({ mensaje }: { mensaje: string }) {
  return (
    <p role="alert" className="flex flex-col gap-1 border border-alert bg-alert/8 px-3 py-2.5">
      <span className="mono-label font-medium text-alert">Error</span>
      <span className="text-sm leading-snug text-ink">{mensaje}</span>
    </p>
  )
}
