# Fase 7 — Identidad «Control»

**Código terminado el 2026-09-25**, con las decisiones de §7; queda su prueba
de terminado (§5): que el editor la vea en su máquina. Es alcance nuevo: la
[hoja de ruta](hoja-de-ruta.md) terminó en la Fase 6, y esta nace de pedirle
personalidad a la interfaz, no de un problema de uso.

## 1. Objetivo

Que Astrolabio tenga una identidad propia sin cambiar lo que hace: las mismas
pantallas, las mismas palabras del flujo y las mismas reglas, con otra forma.

La forma se eligió entre tres direcciones dibujadas sobre el mismo tablero
—«Latón», «Bitácora» y «Control»— en el canvas de diseño de Johan
(<https://claude.ai/artifact/A4DA99VQMEt3MYqSndZhym>, privado). Ganó
**Control**: negro, una grotesca con eje de anchura, una mono para los
rótulos y un solo color de señal. Sus referentes son el manual gráfico de la
NASA de 1975 (Danne y Blackburn) y las consolas de Mission Control.

La identidad sirve al traspaso, no lo adorna. Lo que más pesa en pantalla es
lo que te toca: un bloque naranja con el número, y una línea de tiempo donde
lo atrasado no se puede no ver.

## 2. Fuera de alcance — no implementar

Tema claro · animaciones · iconos de biblioteca · cambiar estados,
transiciones o sus palabras (§2.8 de `AGENTS.md`) · tocar la API · arrastrar
tarjetas (fase 6, §7.4) · el panel de métricas · notificaciones de ningún
tipo · cambiar lo que se exporta al vault.

## 3. El terreno, verificado

Mirado en el código y con Node, el 2026-09-25:

- **Las clases se copian panel a panel.** `Panel`, `Campo` y `Aviso` viven en
  `App.tsx` sin exportarse, y `Pieza.tsx`, `Temas.tsx` y `Tareas.tsx` repiten
  su marcado (DESIGN_SYSTEM §11.5).
- **Lo que DESIGN_SYSTEM §9 deja pendiente**: `slate-500` da 4,0:1 y
  `slate-600` 2,5:1 en texto que se lee; los bordes de campo, 1,8:1; la nota
  del traspaso, el enlace y el guion solo tienen `placeholder`.
- **De quién es cada estado lo sabe el servidor** (`DE_QUIEN_ES`, en
  `models.py`), y el cliente solo lo ve pieza a pieza. La franja del tablero
  lo necesita también en las columnas vacías, así que el cliente lo copia,
  como ya copia los estados (`tablero.ts`) y los temas (`api.ts`).
- **Las fuentes**, en `@fontsource-variable/archivo` y
  `@fontsource-variable/martian-mono` 5.3.0: OFL-1.1, sin dependencias, con
  los ejes de anchura que usa la identidad (Archivo de 62 a 125 %, Martian
  Mono de 75 a 112,5 %). En latín pesan 90 KB, 102 KB la cursiva de Archivo,
  y 38 KB.
- **Tailwind 4.3** trae `font-stretch-*` y deja vaciar la paleta por defecto
  desde `@theme`.
- **El naranja y el rosa del canvas tenían casi la misma luminancia** (0,317
  y 0,339): se distinguían solo por el tono. El rosa pasa de `#ff6b93` a
  `#ffa3bd`, que difiere en luminosidad (ΔL\* = 13,6) y, con tritanopía
  simulada (Machado 2009), pasa de ΔE = 13,7 a 42.
- **nginx cachea para siempre lo que hay en `/assets/`**, que es donde Vite
  deja las fuentes empaquetadas.
- **La tarjeta sin flecha ya falló una vez**: el comentario del tablero en
  `App.tsx` cuenta que la lista de antes «parecía de solo lectura, y pasó de
  verdad». La flecha se queda.

## 4. Criterios de aceptación

Las letras siguen después de la AF de la Fase 6.

### AG. La base

- **AG1** Los colores, las dos familias y los tres estilos de texto que se
  repiten —título de estación, rótulo y dato— se definen una sola vez en
  `index.css`, con `@theme` y `@utility`. La paleta por defecto de Tailwind se
  vacía: una clase `slate-*` olvidada no pinta nada, y una prueba en vitest
  falla si queda alguna en `src/`.
- **AG2** Archivo y Martian Mono las sirve la propia app, empaquetadas por Vite
  ([ADR 0014](adr/0014-identidad-con-tokens-y-fuentes-propias.md)): el
  navegador no pide nada fuera del origen.
- **AG3** La estación, el campo con rótulo, el aviso de error y las clases de
  los botones viven en `ui.tsx`, y ninguna pantalla vuelve a copiarlas.
- **AG4** Todo texto que se lee da al menos 4,5:1 sobre su fondo; los bordes de
  los controles, 3:1; el foco se ve, con un contorno de 2 px. Los números de
  DESIGN_SYSTEM salen de un cálculo, no de memoria.

### AH. El tablero

- **AH1** Una barra arriba con la marca, la fecha, quién entró y con qué rol
  (D2), y «Salir».
- **AH2** Una franja con una celda por estado: su número, su nombre (N4),
  cuántas piezas tiene y de quién es, dicho desde quien mira: «tú», o el otro.
  El editor nunca lee ahí «editor» ([estados §6.6](estados-del-flujo.md)). A la
  izquierda, en naranja, cuántas piezas le tocan a quien mira, de cuántas.
- **AH3** Una columna a la izquierda con la pieza nueva —solo para el
  investigador (D3)— y el catálogo de etiquetas, que filtra como hasta ahora
  (Z2, AB4). La etiqueta que filtra se ve invertida.
- **AH4** Las tarjetas dicen lo mismo que en la Fase 6 (AB3, AC4, AD6), con la
  flecha de que se abren. Una entrega o una publicación ya vencidas salen en
  rosa, y las piezas publicadas quedan en segundo plano.
- **AH5** Las tareas sueltas, debajo de las semanas (AD5).
- **AH6** El tablero crece hasta 1440 px. En pantalla estrecha, las columnas se
  apilan en el orden del flujo (AB5).

### AI. Las semanas, en una línea de tiempo

- **AI1** Una función pura, con sus pruebas en vitest, coloca cada entrada de
  `semanas()` en su día y en un carril, para que las etiquetas no se pisen. Las
  semanas sin nada entre dos que sí tienen se dibujan como un salto, no como
  días vacíos.
- **AI2** Desde `md`, las semanas son una línea de días: hoy, invertido; lo
  atrasado, en rosa; y cada entrada abre su pieza. En pantalla estrecha sigue
  la lista de AE2.
- **AI3** No cambia qué entra: la misma `semanas()` y el mismo filtro (AB4).

### AJ. La pieza

- **AJ1** Una barra con la vuelta al tablero, el número de la pieza, «sin
  guardar», «Guardar» y «Exportar al vault» (J3, solo Johan).
- **AJ2** El título grande y, debajo, los seis estados en fila: los que ya
  pasaron, el actual —naranja si te toca, invertido si no— y los que faltan.
- **AJ3** Desde `lg`, dos columnas de estaciones: el traspaso junto a las
  fechas y las tareas; el material junto al tema, las etiquetas y el
  respaldo; y el guion, a todo el ancho. En pantalla estrecha, una debajo de
  otra.
- **AJ4** Todo campo tiene nombre. La nota del traspaso, el enlace y su nota, y
  el guion llevan rótulo visible (cierra DESIGN_SYSTEM §9).
- **AJ5** La historia y las fechas de los archivos, con la hora en 24 h.

### AK. El guion

- **AK1** La barra agrupa sus diez botones en cuatro grupos, con los mismos
  atajos y los mismos títulos (T1).
- **AK2** «Markdown» y «Vista previa» rotulan las dos mitades.
- **AK3** La vista previa, en la identidad nueva: Archivo a 15/1,65, títulos en
  mayúsculas anchas, viñetas cuadradas. KaTeX no se toca.

### AL. La entrada

- **AL1** La pantalla de entrar en la identidad nueva, con el error en su caja
  (D4).

### AM. Los documentos

- **AM1** `DESIGN_SYSTEM.md` se reescribe con esta identidad y con los
  contrastes calculados.
- **AM2** `ARCHITECTURE.md`, `AGENTS.md` §7 y el PRD, al día.

## 5. Definición de terminado

**Johan y el editor abren Astrolabio y, antes de leer nada, saben qué les
toca: el bloque naranja lo dice, y lo atrasado sale en rosa en la línea de
tiempo.** El editor lo ha visto en su máquina y no le estorba. En el código:
`npm --prefix web run check` en verde, y cada pantalla comparada con el canvas
a 1280 y a 375 px, mirándola, porque una prueba verde no dice cómo se ve.

## 6. Orden sugerido

Cada paso sirve por sí solo: si la fase se detiene a la mitad, lo hecho se usa.

1. La base (AG). Sin ella, lo demás repetiría clases.
2. El tablero (AH).
3. La línea de tiempo (AI).
4. La pieza y el guion (AJ, AK).
5. La entrada (AL).
6. Los documentos (AM).

## 7. Decisiones — acordadas el 2026-09-25

1. **Control**, entre las tres direcciones del canvas.
2. **Las fuentes llegan por `@fontsource-variable`**, fijadas en el lockfile
   como el resto:
   [ADR 0014](adr/0014-identidad-con-tokens-y-fuentes-propias.md).
3. **En escritorio, la línea de tiempo sustituye a la lista de semanas.**
   Revisa lo que la Fase 6 dejó fuera en su §2, «la línea de tiempo es una
   lista por semanas». No es un calendario ni un Gantt: cada entrada es un día,
   sin duración.
4. **La tarjeta marca en rosa la entrega y la publicación vencidas**, con el
   criterio de la línea de tiempo: anteriores a hoy, por día (§8). Revisa
   también la Fase 6, §2, que dejaba fuera «los avisos de fechas vencidas».
   Es un color en lo que ya se ve, no un aviso: nada salta ni se notifica.

Y cinco que no hizo falta preguntar, y que se cambian si no convencen:

5. **El rosa es `#ffa3bd`**, no el del canvas (§3).
6. **La franja dice «tú»** y no el nombre de quien mira.
7. **La flecha de la tarjeta se queda** (§3).
8. **La hora, en 24 h.**
9. **1440 px como máximo**, en vez de 1024: las seis columnas y el guion con
   su vista previa lo agradecen, y más allá las líneas se hacen demasiado
   largas.

## 8. Lo que apareció por el camino

- **Los subíndices de las fórmulas no se pintaban, desde la Fase 1.**
  `rehype-katex` pinta con KaTeX 0.16 y el CSS venía de `katex` 0.18, que
  renombró sus clases de tamaño: $m_1$ se leía «m1». Se vio al ampliar la
  vista previa para compararla con el canvas. `katex` queda en la versión de
  `rehype-katex`, con una prueba que vigila que no se separen.
- **La tarjeta y la línea de tiempo decían «tarde» con criterios distintos.**
  La tarjeta comparaba la entrega con hoy; la línea, la semana con la de hoy.
  Una entrega del martes, vista el viernes, salía en rosa en la tarjeta y sin
  rosa en la línea, y ninguna prueba tenía un atraso dentro de la semana en
  curso. Johan eligió el día: cada entrada vencida va en rosa y dice
  «atrasada», también en la lista del teléfono, y el rótulo de la semana lo
  sigue diciendo solo de las semanas pasadas. La publicación vencida también va en rosa, en la
  línea y ahora en la tarjeta (decisión 4). Lo calcula `semanas()`, con su
  prueba.
- **El exportador usa el título tal cual como nombre de archivo**, y un título
  con `?` o `:` no se puede escribir en el vault de Windows. No es de esta
  fase: va en su propia rama.
