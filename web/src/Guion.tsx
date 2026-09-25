import { useEffect, useRef } from 'react'
import Markdown, { type Components } from 'react-markdown'
import rehypeKatex from 'rehype-katex'
import remarkGfm from 'remark-gfm'
import remarkMath from 'remark-math'

import 'katex/dist/katex.min.css'

import {
  cita,
  cursiva,
  disparador,
  enlace,
  formulaEnBloque,
  formulaEnLinea,
  imagen,
  lista,
  negrita,
  tabla,
  titulo,
  type Cambio,
  type Seleccion,
} from './barra'

type Accion = (texto: string, seleccion: Seleccion) => Cambio

type Boton = {
  etiqueta: string
  accion: Accion
  titulo?: string
  atajo?: string
  estilo?: string
}

/**
 * T1: los diez botones, en cuatro grupos desde la Fase 7 (AK1): el énfasis,
 * los bloques, lo que trae algo de fuera y las fórmulas. `titulo` es la ayuda
 * al pasar el ratón: repite el nombre, porque hay herramientas que la leen
 * como tal, y añade el atajo.
 */
const GRUPOS: Boton[][] = [
  [
    { etiqueta: 'Negrita', accion: negrita, titulo: 'Negrita (Ctrl+B)', atajo: 'Control+B', estilo: 'font-bold' },
    { etiqueta: 'Cursiva', accion: cursiva, titulo: 'Cursiva (Ctrl+I)', atajo: 'Control+I', estilo: 'italic' },
  ],
  [
    { etiqueta: 'Título', accion: titulo, titulo: 'Título de nivel 3' },
    { etiqueta: 'Lista', accion: lista },
    { etiqueta: 'Cita', accion: cita },
  ],
  [
    { etiqueta: 'Enlace', accion: enlace, titulo: 'Enlace (Ctrl+K)', atajo: 'Control+K' },
    { etiqueta: 'Imagen', accion: imagen, titulo: 'Imagen por URL' },
    { etiqueta: 'Tabla', accion: tabla },
  ],
  [
    { etiqueta: 'Fórmula', accion: formulaEnLinea, titulo: 'Fórmula en línea (o escribe mk)' },
    { etiqueta: 'Fórmula en bloque', accion: formulaEnBloque, titulo: 'Fórmula en bloque (o escribe dm)' },
  ],
]

/** U1: solo con el foco en el guion. */
const ATAJOS: Record<string, Accion> = { b: negrita, i: cursiva, k: enlace }

/**
 * La tecla de un Ctrl+tecla, o de un Cmd+tecla en Mac; `null` si no lo es.
 * Sin Alt: en Windows, AltGr es Ctrl+Alt, y en un teclado español escribe la
 * @ y la barra invertida.
 */
function conControl(e: Pick<KeyboardEvent, 'ctrlKey' | 'metaKey' | 'altKey' | 'shiftKey' | 'key'>) {
  return (e.ctrlKey || e.metaKey) && !e.altKey && !e.shiftKey ? e.key.toLowerCase() : null
}

/**
 * V2: un enlace de la vista previa se abre en otra pestaña, que en esta
 * dejaría el guion sin guardar. Las anclas de la propia página —las notas al
 * pie— se quedan en ella.
 */
const COMPONENTES: Components = {
  a: ({ node: _node, ...props }) =>
    props.href?.startsWith('#') ? (
      <a {...props} />
    ) : (
      <a {...props} target="_blank" rel="noopener noreferrer" />
    ),
}

/**
 * Las notas al pie, en español: por defecto salen rotuladas «Footnotes». El
 * rótulo queda oculto a la vista, como en GitHub, y la flecha de vuelta lleva
 * el selector de texto (U+FE0E) para que Windows no la pinte como emoji.
 */
const NOTAS_AL_PIE = {
  footnoteLabel: 'Notas',
  footnoteBackLabel: 'Volver al texto',
  footnoteBackContent: '↩︎',
}

/**
 * El guion renderizado, como se verá (V1). `remark-gfm` pone las tablas, el
 * tachado, las listas de tareas y las notas al pie que también pinta
 * Obsidian. El tachado, solo con dos virgulillas, que es como lo documenta
 * Obsidian: en un guion de física, `~10` es «aproximadamente diez».
 */
export function VistaPrevia({ texto }: { texto: string }) {
  return (
    <div className="prosa text-[15px] leading-[1.65] text-prose">
      <Markdown
        remarkPlugins={[[remarkGfm, { singleTilde: false }], remarkMath]}
        rehypePlugins={[rehypeKatex]}
        remarkRehypeOptions={NOTAS_AL_PIE}
        components={COMPONENTES}
      >
        {texto}
      </Markdown>
    </div>
  )
}

/**
 * El guion: la barra, el campo y la vista previa (J1, y T y U de la Fase 4).
 *
 * Todo lo que cambia la barra pasa por `ejecutar`, que lo inserta como si se
 * tecleara para que Ctrl+Z lo deshaga (U2). La vista previa usa
 * `react-markdown`, que construye elementos de React en vez de inyectar HTML:
 * no hace falta sanitizador ni `dangerouslySetInnerHTML`.
 */
export default function Guion({
  valor,
  alCambiar,
  alGuardar,
}: {
  valor: string
  alCambiar: (valor: string) => void
  alGuardar: () => void
}) {
  const campo = useRef<HTMLTextAreaElement>(null)
  // Mientras la barra inserta, `mk` y `dm` no se miran: eso no se tecleó.
  const insertando = useRef(false)
  const guardar = useRef(alGuardar)

  useEffect(() => {
    guardar.current = alGuardar
  })

  // U4: desde cualquier parte de la pieza, no solo desde el guion. Si no, con
  // el foco en otro sitio, el navegador abriría su «Guardar como».
  useEffect(() => {
    function alTeclear(e: KeyboardEvent) {
      if (conControl(e) !== 's') return
      e.preventDefault()
      guardar.current()
    }
    window.addEventListener('keydown', alTeclear)
    return () => window.removeEventListener('keydown', alTeclear)
  }, [])

  /**
   * U2: `execCommand` está en desuso, pero es la única vía que conserva la
   * pila de deshacer del navegador: asignar el valor desde React la rompe
   * (§3 del alcance). El `input` que dispara pone al día el estado.
   */
  function ejecutar({ desde, hasta, texto, seleccion }: Cambio) {
    const el = campo.current
    if (!el) return
    el.focus() // U3: se sigue escribiendo sin tocar el ratón.
    el.setSelectionRange(desde, hasta)
    insertando.current = true
    if (texto) document.execCommand('insertText', false, texto)
    else if (desde < hasta) document.execCommand('delete')
    insertando.current = false
    el.setSelectionRange(seleccion.inicio, seleccion.fin)
  }

  function pulsar(accion: Accion) {
    const el = campo.current
    if (el) ejecutar(accion(el.value, { inicio: el.selectionStart, fin: el.selectionEnd }))
  }

  return (
    <div className="flex flex-col gap-3.5">
      {/* `preventDefault` en el `mousedown`: al hacer clic en un botón, el
          foco y la selección se quedan en el guion. */}
      <div
        role="toolbar"
        aria-label="Formato del guion"
        className="flex flex-wrap items-center gap-2.5"
      >
        {GRUPOS.map((grupo) => (
          <div key={grupo[0].etiqueta} className="flex border border-line-strong">
            {grupo.map((boton) => (
              <button
                key={boton.etiqueta}
                type="button"
                title={boton.titulo}
                aria-keyshortcuts={boton.atajo}
                onMouseDown={(e) => e.preventDefault()}
                onClick={() => pulsar(boton.accion)}
                className={`border-l border-line-strong px-3 py-1.5 text-[13px] text-prose first:border-l-0 hover:bg-raised hover:text-ink ${boton.estilo ?? ''}`}
              >
                {boton.etiqueta}
              </button>
            ))}
          </div>
        ))}
      </div>

      {/* J1: se escribe a la izquierda y se ve a la derecha. Sin alternar
          pestañas: la fórmula hay que mirarla mientras se escribe. AK2: cada
          mitad con su rótulo, que además da nombre al campo. */}
      <div className="grid border border-line md:grid-cols-2">
        <label className="flex min-w-0 flex-col md:border-r md:border-line">
          <span className="mono-label border-b border-line px-4 py-2.5 text-ink-2">Markdown</span>
          <textarea
            ref={campo}
            value={valor}
            onChange={(e) => {
              alCambiar(e.target.value)
              // U5: solo lo tecleado. Ni lo pegado, ni lo que inserta la barra,
              // ni un Ctrl+Z, que tiene que poder devolver el `mk` escrito.
              const tecleado = (e.nativeEvent as InputEvent).inputType === 'insertText'
              if (insertando.current || !tecleado) return
              const cambio = disparador(e.target.value, e.target.selectionStart)
              // Después del evento en curso, para no anidar otro `input` dentro.
              if (cambio) queueMicrotask(() => ejecutar(cambio))
            }}
            onKeyDown={(e) => {
              const accion = ATAJOS[conControl(e) ?? '']
              if (!accion) return
              e.preventDefault()
              pulsar(accion)
            }}
            spellCheck={false}
            placeholder="El guion, en markdown. Las fórmulas van entre $…$ o $$…$$."
            className="min-h-[29rem] w-full resize-y bg-surface p-4 font-mono text-[12.5px] leading-[1.75] text-ink outline-offset-[-2px] font-stretch-condensed placeholder:text-ink-3"
          />
        </label>

        <div className="flex min-w-0 flex-col max-md:border-t max-md:border-line">
          <span className="mono-label border-b border-line px-4 py-2.5 text-ink-2">Vista previa</span>
          <div className="min-h-[29rem] overflow-x-auto px-7 pt-5 pb-7">
            {valor.trim() ? (
              <VistaPrevia texto={valor} />
            ) : (
              <p className="text-sm text-ink-2">La vista previa aparece aquí.</p>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
