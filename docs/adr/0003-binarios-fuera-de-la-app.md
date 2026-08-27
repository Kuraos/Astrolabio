# ADR 0003 — Los binarios pesados viven fuera de la aplicación

- **Fecha**: 2026-08-26
- **Estado**: aceptada

## Problema

El editor trabaja con proyectos de edición, cortes de vídeo e imágenes en
capas: cientos de MB por archivo, decenas de GB acumulados. Guardarlos en la
base de datos o subirlos por HTTP a través de la API produce respaldos
inmanejables, migraciones lentas y una API que se cae en cada subida.

## Decisión

Los archivos se sincronizan por fuera con **Syncthing** —peer-to-peer,
cifrado, sin servidor central, usado en producción con volúmenes del orden
del terabyte— y la aplicación guarda **la ruta**, no el archivo.

| Qué | Dónde | Quién manda |
|---|---|---|
| Material crudo, cortes, proyectos de edición | Carpeta Syncthing compartida | El sistema de archivos |
| Ruta, versión, autor, notas del corte | Tabla `version_pieza` | Astrolabio |
| Miniatura de vista previa (< 200 KB) | Astrolabio | Astrolabio |

La miniatura es la **única** excepción: existe para que la interfaz muestre
de qué se está hablando sin mover el archivo grande.

## Consecuencias

- La app puede mostrar una ruta que apunte a un archivo que aún no ha
  llegado a la otra máquina. Hay que **detectar y mostrar ese estado**, no
  asumir que el archivo existe.
- Syncthing exige que ambos equipos estén encendidos a la vez, la misma
  restricción que la variante A del ADR 0002 — no añade una nueva.
- La base de datos se mantiene pequeña, respaldable con un `pg_dump` y
  migrable en segundos.
