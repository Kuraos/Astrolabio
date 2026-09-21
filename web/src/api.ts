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
  // K4: los tres los decide el servidor. `transiciones` son las que puede dar
  // quien pregunta, y el cliente pinta esas y no otras (N2).
  estado: string
  de_quien_es: Rol | null
  transiciones: string[]
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

  return respuesta.json() as Promise<T>
}
