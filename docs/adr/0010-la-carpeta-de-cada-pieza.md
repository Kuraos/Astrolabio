# ADR 0010 — La carpeta de cada pieza en Syncthing

- **Fecha**: 2026-09-21
- **Estado**: aceptada
- **Contexto**: criterios Q y R de `docs/fase-3-material.md`. Amplía el ADR
  0003, que decidió Syncthing sin decir cómo se organiza la carpeta ni cómo la
  usa la app.

## Problema

El ADR 0003 dejó los binarios fuera de la aplicación: viajan por Syncthing y la
app guarda la ruta, con una miniatura de menos de 200 KB. La Fase 3 lo pone en
uso para las imágenes de referencia, que el editor necesita en su calidad
original para sus programas de diseño.

Faltaba decidir tres cosas: cómo se llama la carpeta de cada pieza, quién la
crea y de dónde salen las miniaturas.

## Decisión

### Una carpeta por pieza: `<id> - <título>`

Dentro de la carpeta compartida, cada pieza tiene la suya:
`12 - Prueba de traspaso`. La app la busca por el número —el prefijo `12 - `—,
así que la encuentra aunque la pieza cambie de título.

No la renombra. Renombrar una carpeta mientras Syncthing la sincroniza con otra
máquina es buscar conflictos, y un nombre viejo solo afea.

### La crea la app, y es lo único que escribe

Cuando la carpeta de una pieza no existe, el panel ofrece crearla, a cualquiera
de los dos. Para eso la carpeta compartida se monta en escritura, pero el único
código que escribe es ese `mkdir`: la app no crea, mueve, renombra ni borra
archivos. Una prueba lo vigila, como G2 vigila que nada escriba en el vault
fuera de `Contenido/`.

### Miniaturas al vuelo

Pillow genera la miniatura cuando se pide —de `jpg`, `png` y `webp`—, por debajo
de los 200 KB de la excepción del §2.2, y no se guarda. La URL de la miniatura
lleva la fecha de modificación del archivo, así que el navegador puede
guardarla sin volver a preguntar mientras la imagen no cambie.

### Fuera del vault

La carpeta compartida vive fuera del vault. El vault es un repositorio git
(obsidian-git), y cada imagen lo haría crecer en cada commit; además, el §2.5
mantiene al editor fuera del vault.

## Alternativas descartadas

- **`pieza-12`.** Estable y fea. La carpeta es para personas antes que para la
  app; el ADR 0007 descartó lo mismo para las notas del vault.
- **Renombrar la carpeta al cambiar el título**, como hace el exportador con su
  nota (ADR 0007). Esa nota la escribe solo Astrolabio; esta carpeta la tocan
  dos personas y un proceso de sincronización.
- **Montaje de solo lectura, con la carpeta creada a mano.** Un paso manual por
  pieza, con un nombre que hay que escribir exacto.
- **Guardar las miniaturas.** Con decenas de imágenes por pieza, generarlas
  cuesta menos que mantener una caché y saber cuándo invalidarla.
- **Subir las imágenes a la app**, enmendando el §2.2. El editor necesita el
  archivo original en su programa de diseño, no una copia comprimida en una
  pantalla.

## Consecuencias

- La app solo ve la copia de la máquina donde corre: no sabe si al otro ya le
  llegó un archivo (estados §4).
- Si alguien crea a mano otra carpeta con el mismo número, la app no adivina
  cuál es la buena: el panel dice que hay dos.
- Al crear la carpeta, el título pierde los caracteres que Windows no admite en
  un nombre (`\ : * ? " < > |`). La `/` pasa a `-` desde el 2026-09-25, para
  que «1/3» no se lea «13»; las carpetas de antes conservan su nombre.
- Pillow es una dependencia nueva, fijada como las demás.
- Cada navegador genera la miniatura la primera vez que la ve. Si algún día eso
  pesa, se guardan, y este ADR se revisa.
