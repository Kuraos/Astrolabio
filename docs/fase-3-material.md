# Fase 3 — El material viaja con la pieza

**Código terminado el 2026-09-23**, con las decisiones de §7; queda la prueba
con el editor (§5), que se hace en el uso. Resuelve el problema 1 de la
[hoja de ruta](hoja-de-ruta.md). El alcance vigente está en
[`AGENTS.md`](../AGENTS.md) §7.

## 1. Objetivo

Que lo que Johan le pasa al editor para hacer la pieza —enlaces de referencia e
imágenes— viva en la pieza y no en el chat.

Los enlaces, en Astrolabio. Las imágenes, en la carpeta de la pieza en
Syncthing y en su calidad original: el editor las necesita para meterlas en sus
programas de diseño, no para verlas en una pantalla (decisión de Johan,
2026-09-21). Astrolabio guarda dónde están y muestra una miniatura, que es
exactamente lo que el ADR 0003 decidió: el §2.2 no se toca.

## 2. Fuera de alcance — no implementar

Exportar el material al vault (decisión de Johan: no hace falta) · vistas
previas de enlaces: traer la página desde el servidor abre la puerta a SSRF y
pide otra dependencia · saber si al editor ya le llegó cada archivo, o si a
Johan le llegó el diseño finalizado: la app solo ve la copia de la máquina donde
corre, y la API REST de Syncthing lo diría a cambio de su clave y su red ·
miniaturas de archivos de diseño (PSD, AI), que se listan por nombre · subir
archivos desde el navegador (§2.2) · mover, renombrar o borrar archivos desde la
app · imágenes dentro del guion (fase 4).

## 3. El terreno, verificado

No son suposiciones; están mirados en la máquina de Johan y en el código:

- **Syncthing no estaba instalado en la máquina de Johan** el 2026-09-21: ni
  proceso, ni ejecutable en el `PATH`, ni carpetas en los sitios habituales.
  Desde el 2026-09-23 corre en las dos máquinas, con la carpeta compartida
  fuera del vault (§6, paso 1).
- El ADR 0003 decidió Syncthing, con la ruta en la app y una miniatura, pero
  nada de eso está implementado: no hay montaje, ni variable, ni tabla.
- El vault ya resolvió el mismo problema de otra carpeta montada:
  `VAULT_VOZ_DEL_COSMOS_PATH` es opcional, y sin ella la app arranca y lo dice
  (G4). `respaldo.dentro_de` ya impide salirse con `../` (G3): se reutiliza.
- La vista de la pieza tiene un panel de respaldo, solo para Johan (ADR 0001).
  El de material es para los dos.
- **La carpeta de Syncthing vive fuera del vault.** El vault es un repositorio
  git (obsidian-git), y las imágenes lo inflarían en cada commit; además, el
  §2.5 mantiene al editor fuera del vault.
- El editor trabaja hoy con Drive: Syncthing es un paso nuevo para él
  (estados §4).

## 4. Criterios de aceptación

### P. Enlaces de referencia

- **P1** `enlace` entra en su propia migración: la pieza, la URL, una nota
  opcional («la paleta de este pin»), quién lo añadió y cuándo. Quién sale de
  la sesión, nunca del cuerpo de la petición.
- **P2** Los dos roles añaden y quitan enlaces (§7). Con sesión, sin
  distinción de rol; sin ella, 401, como todo.
- **P3** Solo `http` y `https`, validado en el servidor: cualquier otra cosa es
  422, con su prueba. Un `javascript:` en un enlace es un XSS esperando el
  clic, y el cliente no es quien lo impide.
- **P4** La API devuelve los enlaces de una pieza en orden de llegada.

### Q. La carpeta de la pieza

- **Q1** Una variable apunta a la carpeta compartida montada en el contenedor.
  Es opcional: sin ella la app arranca, todo lo demás funciona y el panel dice
  por qué no hay imágenes, como G4.
- **Q2** Cada pieza tiene su carpeta dentro de la compartida, llamada
  `<id> - <título>` ([ADR 0010](adr/0010-la-carpeta-de-cada-pieza.md)), y la
  app la encuentra por el número aunque la pieza cambie de título.
- **Q3** La app lista los archivos de esa carpeta: nombre, tamaño y fecha. Si
  la carpeta no existe, el panel ofrece crearla.
- **Q4** Nada se lee fuera de la carpeta de la pieza: un nombre con `../` o un
  enlace simbólico que se salga falla, con su prueba, como G3.
- **Q5** Crear la carpeta de la pieza es lo único que la app escribe en la
  carpeta compartida: no crea, mueve, renombra ni borra archivos. Una prueba lo
  vigila (ADR 0010).

### R. Miniaturas

- **R1** De cada imagen `jpg`, `png` o `webp`, una miniatura de menos de
  200 KB, la excepción del §2.2. La genera el servidor con **Pillow**:
  dependencia nueva, dicha aquí (§6 del `CLAUDE.md`).
- **R2** Se generan cuando se piden y no se guardan (ADR 0010); el navegador
  las guarda en caché mientras el archivo no cambie.
- **R3** Una prueba afirma el tope de 200 KB con una imagen grande de verdad,
  no con una que ya fuera pequeña.
- **R4** Los demás archivos se listan sin miniatura.

### S. Interfaz

- **S1** Un panel «Material» en la pieza, para los dos roles.
- **S2** Añadir y quitar enlaces. Se abren en otra pestaña, con
  `rel="noopener noreferrer"`.
- **S3** Las imágenes, en miniatura con su nombre, y un botón que copia su ruta
  dentro de la carpeta de la pieza. Un navegador no abre archivos locales desde
  una página web; con la ruta, el editor la encuentra en su copia de Syncthing
  y la arrastra a su programa de diseño.
- **S4** Si falta la carpeta de la pieza, el panel ofrece crearla; si
  Syncthing no está configurado, lo dice. Los enlaces funcionan en los dos
  casos.

## 5. Definición de terminado

**Johan añade a una pieza un pin de Pinterest, un vídeo y una imagen suya en la
carpeta de la pieza. El editor, desde su sesión, ve los enlaces y la miniatura,
y abre la imagen original en su programa de diseño desde su propia carpeta de
Syncthing, sin que nadie haya mandado un mensaje.**

Como en las fases anteriores, la prueba es el editor desde su máquina.

## 6. Orden sugerido

1. **Syncthing, fuera del código.** Instalarlo en las dos máquinas, crear la
   carpeta compartida fuera del vault, compartirla entre los dos equipos y, en
   la máquina de Johan, apuntar a ella la variable del `.env`.
2. Enlaces (P): no dependen de Syncthing, y ya quitan del chat la mitad del
   problema.
3. La carpeta (Q), con su prueba de `../`.
4. Miniaturas (R).
5. Interfaz (S).

## 7. Decisiones — acordadas el 2026-09-21

1. **Las imágenes viven en Syncthing**, en su calidad original: el editor las
   necesita en sus programas de diseño, no solo en el guion.
2. **El material lo añaden los dos.**
3. **El material no va al vault.**
4. **La carpeta de cada pieza se llama `<id> - <título>`**, y la app no la
   renombra ([ADR 0010](adr/0010-la-carpeta-de-cada-pieza.md)).
5. **La carpeta la crea la app**, con un botón del panel, y es lo único que
   escribe en la carpeta compartida (ADR 0010).
6. **Un enlace lo quita cualquiera de los dos**, igual que lo añade.
7. **Las miniaturas se generan al vuelo** y no se guardan (ADR 0010).
