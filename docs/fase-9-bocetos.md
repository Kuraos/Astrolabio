# Fase 9 — Bocetos con Claude

**Código terminado el 2026-09-26**, con las decisiones de §7 acordadas con
Johan; queda su prueba de terminado (§5), que necesita su clave. Nace de su
prueba del 2026-09-25, como la Fase 8, y la necesita: el boceto sale del tipo
de pieza, el destino y el copy gráfico que trajo.

## 1. Objetivo

Que el editor empiece cada pieza con la composición resuelta: qué elementos
lleva cada lámina, cuál pesa más y dónde va cada uno. Un boceto no es el
diseño: es el punto de partida, en la rejilla de la pieza, hecho con el copy
y el guion de Johan.

La API se lo pide a Claude con una salida estructurada, la valida, la guarda,
y el cliente la dibuja desde los datos. El editor aprobó los bocetos de
prueba que se hicieron así antes de esta fase.

Es el primer servicio externo de Astrolabio
([ADR 0016](adr/0016-bocetos-con-claude.md)): la única parte de la app que
sale de la red de la casa, y solo si hay clave.

## 2. Fuera de alcance — no implementar

Bocetos de short y de video largo, que son guion gráfico y no lámina (§7.1) ·
generar imágenes · editar el boceto a mano en la app · pedirlo solo, al
guardar o al entregar: siempre es un botón · exportarlo al vault · que el
modelo escriba HTML o SVG · corregir el copy o el guion · otro proveedor.

## 3. El terreno, verificado

Mirado el 2026-09-26:

- **El SDK de Python es `anthropic` 1.8.0.** Trae `httpx2`, `httpcore2` y
  `truststore`, que la api no tenía. Admite salidas estructuradas en
  `output_config` y en streaming, y `anthropic.transform_schema` convierte un
  modelo de Pydantic en el esquema que acepta la API: lo que la API no admite
  —mínimos y máximos— lo deja como pista en la descripción.
- **El esquema de la API no admite `minimum`, `maximum` ni restricciones de
  longitud de listas.** Que las zonas caigan en la rejilla y que haya un solo
  peso 1 lo tiene que comprobar la app.
- **El modelo por defecto es `claude-opus-5`**: 5 USD por millón de tokens de
  entrada y 25 de salida (documentación de Anthropic, junio de 2026). Piensa
  por defecto, y lo pensado se cobra como salida.
- **nginx corta a los 60 s** lo que la API tarda en responder: no fija
  `proxy_read_timeout`. Un boceto de varias láminas, con razonamiento, puede
  pasar de ahí.
- **La pieza ya lo tiene todo** desde la Fase 8: `formato`, `plataforma`,
  `proposito`, `nivel`, `copy_grafico` y el guion.
- **De las cuatro imágenes base, solo `python:3.12-slim` tiene un digest
  nuevo.** Se leyó del registro de Docker Hub, que es lo que consulta
  `docker buildx imagetools inspect`.

## 4. Criterios de aceptación

Las letras siguen después de la AR de la Fase 8.

### AS. La petición

- **AS1** `POST /api/piezas/{id}/bocetos` pide un boceto. Los dos roles pueden
  (§7.2), con sesión; sin ella, 401.
- **AS2** Sale hacia Claude el título, el cuadro —tipo, destinos, propósito,
  nivel—, el tema, el copy gráfico y el guion (§7.3). Nada del vault, del
  respaldo, de las notas del traspaso ni de los usuarios. Una prueba mira el
  mensaje que se envía.
- **AS3** La respuesta llega con una salida estructurada: por lámina, su
  número, su idea en una frase, sus elementos —tipo, peso, contenido y zona—
  y una nota para la edición. El esquema sale del mismo modelo de Pydantic
  con el que se valida.
- **AS4** El modelo se elige en el `.env` (`BOCETOS_MODELO`), y por defecto es
  `claude-opus-5`.
- **AS5** Sin `ANTHROPIC_API_KEY`, la app funciona igual: el panel dice que
  los bocetos no están configurados y el `POST` responde 409 con ese motivo,
  como el exportador sin vault.
- **AS6** Solo se pide para lo que tiene rejilla (§7.1) y copy: sin tipo, con
  un short o un video largo, sin copy gráfico, o con más de una lámina en un
  post individual o un póster, 409 con el motivo en español.
- **AS7** Un fallo de Anthropic —clave inválida, sin conexión, límite de
  peticiones, error del servidor— y un boceto que Claude no termina o
  declina, 502 con la causa en español. La app no reintenta sola: cada
  intento cuesta.

### AT. La validación

- **AT1** Tantas láminas como el copy gráfico, numeradas desde 1.
- **AT2** Cada lámina, con al menos un elemento y exactamente uno de peso 1.
- **AT3** Cada zona, dentro de la rejilla de la pieza.
- **AT4** Ninguna zona se solapa con otra de su lámina.
- **AT5** Una cifra del boceto que no está en el guion ni en el copy no lo
  invalida, pero queda como aviso junto al boceto: la exactitud es de Johan
  (AGENTS §1), y un boceto con una cifra inventada no se puede dar por bueno
  sin mirarla.
- **AT6** Lo que no pasa AT1–AT4 es un 502 que dice qué falló, y no se dibuja.

### AU. Lo que se guarda

- **AU1** Cada intento que llega a tener respuesta de Claude se guarda en la
  tabla `boceto`: quién lo pidió, cuándo, el modelo, la rejilla, el copy con
  que se hizo, los tokens de entrada y de salida, y el boceto o el error. Así
  se sabe cuánto ha costado, también lo que falló.
- **AU2** `GET /api/piezas/{id}/bocetos` devuelve si se puede pedir uno y por
  qué no, y los bocetos válidos, del más nuevo al más viejo.

### AV. El dibujo

- **AV1** Una estación «Boceto» en la pieza, debajo de los textos, con
  «Pedir boceto». Mientras Claude trabaja, lo dice, y cuánto suele tardar.
- **AV2** Cada lámina se dibuja desde los datos, en su proporción, con la
  rejilla a la vista y cada elemento en su zona. El peso se ve en el borde y
  en el tamaño de la letra; las figuras y las gráficas, con el aspa de un
  hueco para imagen. Las fórmulas, con el KaTeX del guion. Nada de lo que
  escribe el modelo se interpreta como HTML.
- **AV3** Encima de cada lámina, su idea; debajo, la nota para la edición.
- **AV4** Los bocetos anteriores se pueden volver a ver.
- **AV5** Si el copy gráfico cambió después del boceto, se dice.
- **AV6** Los avisos de AT5, en rosa y en palabras.
- **AV7** Si hay copy sin guardar, se avisa de que el boceto se hará con el
  guardado.

### AW. La infraestructura y los documentos

- **AW1** `anthropic` en `requirements.txt`, con su porqué, y el lock
  regenerado con los digests al día (ADR 0013).
- **AW2** nginx espera a la API hasta 10 minutos.
- **AW3** `.env.example` documenta `ANTHROPIC_API_KEY` sin valor y
  `BOCETOS_MODELO`; compose los pasa a la api con valores por defecto, para
  que un `.env` viejo siga arrancando.
- **AW4** Pytest con Claude simulado: la forma de la petición, cada regla de
  AT, cada error de AS6 y AS7, y el 401. Vitest: el dibujo sale de los datos
  y escapa lo que escribe el modelo.
- **AW5** El PRD, `ARCHITECTURE.md`, `DESIGN_SYSTEM.md`, `AGENTS.md` y el
  README, al día.

## 5. Definición de terminado

**El editor pide el boceto de una pieza real en Astrolabio y empieza el
diseño desde él, sin preguntarle a Johan qué va en cada lámina.** Johan ha
puesto su clave en el `.env` de su PC y ha visto lo que cuesta. En el código:
`npm --prefix web run check` y `docker compose run api pytest` en verde, y el
boceto mirado a 1280 y a 375 px.

Desde la sesión en la nube no hay clave: la llamada real a Claude la prueba
Johan en su máquina, y hasta entonces la fase no está terminada.

## 6. Orden sugerido

1. Las dependencias (AW1): el SDK, el lock y los digests.
2. La API (AS, AT, AU), con sus pruebas.
3. El dibujo (AV).
4. La configuración y los documentos (AW2–AW5).

## 7. Decisiones — acordadas con Johan el 2026-09-25 y 26

1. **Solo las piezas estáticas**: carrusel y post individual en 4:5, con una
   rejilla de 12 columnas por 15 filas (1080 × 1350 px, celdas de 90 px), y
   póster en proporción A, con 12 × 17 (12 × √2 ≈ 16,97). El short y el video
   largo, en otra fase.
2. **Los dos roles piden bocetos.** El editor es quien los usa, y cada
   petición queda registrada (AU1).
3. **A Claude le llegan el cuadro, el copy y el guion.** El guion da el
   contexto para elegir qué dato destacar, y es contenido que se va a
   publicar.
4. **El esquema de cada lámina**: número, idea, elementos —tipo `titulo`,
   `dato`, `texto`, `formula`, `figura`, `grafica` o `nota`; peso de 1 a 4,
   con un solo 1; contenido del guion, sin inventar cifras, y fórmulas en
   LaTeX; zona con `fila`, `col`, `filas` y `cols`— y nota para la edición.
5. **La app valida y el cliente dibuja desde los datos**, nunca con marcado
   del modelo. Se guarda como JSON en la base.
6. **`claude-opus-5` por defecto**, cambiable en el `.env`. Con unos 2.100
   tokens de entrada y 2.800 de salida, un boceto cuesta unos 0,08 USD, y con
   el razonamiento hasta unos 0,20.
7. **La clave solo en el `.env`**, nunca en el repositorio ni en el chat. Sin
   clave, la app funciona igual.

Y las que no hizo falta preguntar, que se cambian si no convencen:

8. **Rejilla de CSS y no SVG.** El texto de un elemento se parte solo en
   líneas, y las fórmulas se pintan con el mismo componente del guion. El
   aspa de las figuras sí es un SVG. Lo que importa de la decisión del 25
   —dibujar desde los datos, nunca con marcado del modelo— se cumple igual.
9. **Se guardan también los intentos fallidos que costaron** (AU1), sin
   dibujo: si no, el gasto que se ve sería menor que el real.
10. **Las cifras sin fuente avisan y no rechazan** (AT5): una cifra puede
    estar bien escrita de otra forma, y rechazar el boceto la escondería.
11. **Streaming, con hasta 64.000 tokens de salida.** Un carrusel de 20
    láminas, el máximo de Instagram, con razonamiento, no cabe en los 16.000
    de una petición sin streaming. Se piden 20 láminas como mucho.
12. **El respaldo del servidor de Anthropic ante una negativa**
    (`fallbacks: "default"`), que la documentación recomienda para
    `claude-opus-5`: si el modelo declina, la API reintenta con otro dentro de
    la misma petición. Para bocetos de astronomía no debería pasar nunca.
13. **nginx espera hasta 10 minutos** a toda la API, no solo a los bocetos: el
    resto responde en milisegundos, y una regla aparte para una ruta sería
    más configuración que beneficio.

## 8. Lo que apareció por el camino

- **La petición real, contra un Anthropic de mentira.** Sin clave no se puede
  llamar a Claude, pero sí al SDK de verdad: con `ANTHROPIC_BASE_URL`
  apuntando a un servidor local que responde con los eventos de streaming de
  la API, el boceto se pidió, se validó, se guardó y se dibujó desde la
  pantalla. El servidor anotó lo que armó el SDK: el modelo, el streaming con
  64.000 tokens, la salida estructurada, el respaldo ante una negativa con su
  cabecera beta y la clave en su cabecera. Lo que queda sin probar es lo que
  solo sabe la API real: que acepte esa combinación y lo que responda Claude.
- **Sin configurar es 409, no 503.** El exportador ya respondía 409 cuando
  falta el vault; los bocetos siguen esa regla (AS5).
- **En una zona de una fila no cabían el rótulo y el texto.** La nota de un
  crédito se quedaba en «Nota · 4»; se vio en la captura del teléfono. Ahora
  van en línea.
- **El digest de la imagen de Python había cambiado** y los otros tres no. Se
  leyeron del registro de Docker Hub, porque en la sesión de la nube no hay
  Docker; el lock se regeneró repitiendo la etapa `lock` en un entorno limpio
  de Python 3.12, y la CI lo comprueba con la imagen.
- **Con `httpx2` instalado, el `TestClient` deja de avisar** de que usaba
  `httpx`, en desuso: lo trajo el SDK.
