# ADR 0011 — Las transitivas y las imágenes base también se fijan

- **Fecha**: 2026-09-21
- **Estado**: aceptada
- **Contexto**: la reproducibilidad que `api/requirements.txt` promete desde la
  Fase 0 y que solo cumplía para las dependencias directas.

## Problema

`requirements.txt` fija con `==` diez paquetes, pero la imagen de la api instala
treinta y nueve. Las otras veintinueve —todo el extra `standard` de uvicorn,
`pydantic_core`, `greenlet`— se resuelven de nuevo cada vez que se invalida la
capa de pip. Al reconstruir tras fijar PyYAML (9e0d816), `watchfiles` pasó de
1.2.0 a 1.3.0 sin que nadie lo pidiera.

Pip no es la única capa que se mueve. `python:3.12-slim` y `postgres:18-alpine`
son tags que se reconstruyen cada pocas semanas. Compose solo baja una imagen si
no la tiene y la caché congela la capa de pip; la CI, en cambio, construye desde
cero en cada push. Así se junta lo peor de los dos lados: ni reproducible ni al
día, y distinto en los dos sitios donde corren las pruebas. El 2026-09-21, el
`postgres:18-alpine` de la máquina de Johan era un build del 13 de agosto y la CI
bajaba otro.

## Decisión

### Un lock generado, junto a lo que edita una persona

`requirements.txt` sigue siendo lo que se edita: las dependencias directas, con
su porqué. `constraints.txt` es lo que se instala de verdad: el `pip freeze` de
una instalación limpia de `requirements.txt`, transitivas incluidas. El
Dockerfile instala el primero con el segundo como restricción:

    pip install -r requirements.txt -c constraints.txt

Se regenera con una etapa `lock` del mismo Dockerfile, por la que la imagen de
la api no pasa:

    docker build --no-cache --target lock --output api api

Parte del mismo `FROM`, así que el lock lo resuelven el intérprete y la pip que
luego lo instalan. No monta nada ni depende del lock anterior. Si una directa
sube y choca con el lock viejo, el build de la api falla, y un comando que
necesitara esa imagen no podría arreglarlo.

### Una prueba ata los dos archivos

Subir una directa sin regenerar ya falla solo: pip rechaza la restricción
contradictoria. Añadir una no falla: entraría suelta. Por eso una prueba compara
el `pip freeze` de la imagen con `constraints.txt` y, si difieren, da el comando
de regeneración, igual que la de F2 compara modelos y migraciones.

### Las imágenes base, por digest

Las cuatro —`python:3.12-slim`, `postgres:18-alpine`, `node:24-alpine` y
`nginx:alpine`— se escriben como `tag@sha256:…`. El tag dice qué línea se sigue
y el digest, en qué punto de ella se está; Docker solo usa el digest. Es el del
índice multiarquitectura y no el de la imagen amd64, para que la variante B del
ADR 0002 —una Raspberry Pi— pueda construir lo mismo.

### Cuándo se actualiza

Sin bots ni calendario. Dependabot o Renovate abrirían PRs cada semana, y para
dos personas ese es el trámite que acaba con la regla.

1. **Cuando cambia `requirements.txt`.** La prueba obliga a regenerar en el
   mismo commit.
2. **Al abrir cada fase**, un commit de mantenimiento: digests nuevos, lock
   regenerado, build y pruebas.
3. **Ante un aviso de seguridad**, se edita esa línea del lock a mano. Pip
   comprueba la coherencia al instalar, y la prueba, que el lock siga siendo
   la imagen.

Regenerar resuelve siempre todo de cero: al añadir un paquete sube también lo
que haya salido desde la última vez. Es deliberado: un comando, un significado.

## Alternativas descartadas

- **pip-tools.** Sus anotaciones `# via` habrían mostrado de dónde llegaba
  PyYAML. Pero es una dependencia más, construida sobre las internas de pip, y
  resuelve con los marcadores del sistema donde corre: en Windows dejaría fuera
  `uvloop`, que uvicorn solo pide fuera de `win32`. Tendría que correr en un
  contenedor, igual que esto, a cambio de una comodidad.
- **Hashes (`--require-hashes`).** Con `==` ya no entra una versión nueva; los
  hashes cubren además bytes distintos bajo la misma versión. Pero los wheels
  son por plataforma: las treinta y nueve versiones sumaban 943 archivos en
  PyPI, y un lock que construya también en arm64 los necesita todos. Un diff de
  mil líneas de hash no lo lee nadie, y para un servidor en una red privada la
  amenaza no lo justifica.
- **uv**, con su lock universal: otra herramienta y otro ecosistema para
  treinta y nueve paquetes.
- **`pip lock`** (PEP 751): no existe en la pip de la imagen, la 25.0.1.

## Consecuencias

- La imagen es la misma en la máquina de Johan, en la CI y en el servidor que
  venga. Los parches de seguridad llegan al subir el digest y no solos, aunque
  a la máquina de Johan tampoco llegaban antes.
- Pillow, en la Fase 3, es la primera dependencia que entra por este camino.
- Dentro de la 18, las versiones menores de Postgres no cambian el formato en
  disco, así que subir su digest no toca el volumen. Pasar a la 19 sigue siendo
  cambiar el tag, con su migración de datos.
- El lock se genera en linux/amd64 y solo fija versiones. En arm64 instala los
  mismos treinta y nueve paquetes: comprobado el 2026-09-21 con emulación, no
  en una Raspberry real.
