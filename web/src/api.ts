/**
 * Cliente HTTP mínimo.
 *
 * Rutas relativas: el frontend se sirve desde el mismo origen que la API
 * (ADR 0005), así que no hay ninguna dirección escrita aquí (criterio A3).
 */

/** Error con el mensaje que mandó la API, para poder enseñarlo (criterio D4). */
export class ErrorDeApi extends Error {
  constructor(
    mensaje: string,
    readonly estado: number,
  ) {
    super(mensaje)
  }
}

export type Rol = 'investigador' | 'editor'

/**
 * Y1: los mismos cuatro temas que acepta la API (`Tema`, en
 * `api/app/piezas.py`). Si cambian allí, cambian aquí; si no, la API
 * responde 422 y lo delata.
 */
export const TEMAS = ['Sistema Solar', 'Estrellas', 'Galaxias y cosmología', 'Exploración espacial']

export type Usuario = { usuario: string; rol: Rol }

export type Pieza = {
  id: number
  titulo: string
  creada_en: string
  creada_por: string
  guion: string
  formato: string | null
  tema: string | null
  plataforma: string | null
  respaldo: string[]
  // Y2 y Y3: ya normalizadas por el servidor.
  etiquetas: string[]
  // K4: los tres los decide el servidor. `transiciones` son las que puede dar
  // quien pregunta, y el cliente pinta esas y no otras (N2).
  estado: string
  de_quien_es: Rol | null
  transiciones: string[]
}

/** Un enlace de referencia de la pieza (criterio P1). */
export type Enlace = {
  id: number
  url: string
  nota: string | null
  creado_por: string
  creado_en: string
}

/**
 * Un archivo de la carpeta de la pieza en Syncthing (Q3). `miniatura` es la
 * URL de la suya si es una imagen, y `null` si no (R4).
 */
export type Archivo = {
  nombre: string
  tamano: number
  modificado: string
  miniatura: string | null
}

/**
 * La carpeta de la pieza. Que falte no es un error (Q1): sin `motivo` y sin
 * `carpeta`, la pieza aún no tiene la suya y se puede crear (S4).
 */
export type EstadoDeLaCarpeta = {
  motivo: string | null
  carpeta: string | null
  archivos: Archivo[]
}

/** Un paso de la historia de la pieza (M1, M3). */
export type Traspaso = {
  id: number
  transicion: string
  desde: string
  hacia: string
  creado_por: string
  creado_en: string
  nota: string | null
}

export type NotaDeRespaldo = {
  archivo: string
  fuente_titulo: string
  fuente_tipo: string | null
  autor: string | null
  fecha: string | null
}

/** El vault puede no estar montado, y eso no es un error (criterio G4). */
export type EstadoDelRespaldo = {
  disponible: boolean
  motivo: string | null
  notas: NotaDeRespaldo[]
}

export async function pedir<T>(ruta: string, init?: RequestInit): Promise<T> {
  const respuesta = await fetch(ruta, {
    ...init,
    // Por defecto ya sería `same-origin`; explícito porque es justo lo que el
    // ADR 0005 compra: la cookie viaja sin CORS ni SameSite=None.
    credentials: 'same-origin',
    headers: { 'Content-Type': 'application/json', ...init?.headers },
  })

  if (!respuesta.ok) {
    // FastAPI manda el motivo en `detail`. Si no viene, el código ya dice algo.
    const cuerpo = await respuesta.json().catch(() => null)
    throw new ErrorDeApi(
      cuerpo?.detail ?? `La API respondió ${respuesta.status}`,
      respuesta.status,
    )
  }

  // 204: no hay cuerpo que leer, y `json()` fallaría con una respuesta correcta.
  if (respuesta.status === 204) return undefined as T

  return respuesta.json() as Promise<T>
}
