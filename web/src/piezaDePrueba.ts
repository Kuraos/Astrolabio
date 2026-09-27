import type { Pieza } from './api'

/**
 * Una pieza para las pruebas: recién creada, con todo vacío salvo lo que cada
 * prueba cambie. Un solo sitio que crece cuando la pieza crece, en vez de un
 * literal completo copiado en cada archivo de pruebas.
 */
export function piezaDePrueba(cambios: Partial<Pieza> = {}): Pieza {
  return {
    id: 1,
    titulo: 'Una pieza',
    creada_en: '2026-09-24T00:00:00Z',
    creada_por: 'johan',
    guion: '',
    formato: null,
    tema: null,
    proposito: null,
    nivel: null,
    plataforma: [],
    copy_grafico: [],
    caption: '',
    respaldo: [],
    etiquetas: [],
    fecha_entrega: null,
    fecha_publicacion_prevista: null,
    estado: 'investigacion',
    de_quien_es: 'investigador',
    transiciones: [],
    ...cambios,
  }
}
