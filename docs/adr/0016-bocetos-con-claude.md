# ADR 0016 — Los bocetos, con Claude: el primer servicio externo

- **Fecha**: 2026-09-26
- **Estado**: aceptada
- **Contexto**: criterios AS–AW de `docs/fase-9-bocetos.md`. Toca el
  [ADR 0002](0002-autoalojado-con-tailscale.md), que deja la app en el PC de
  Johan, sin nube, y el [ADR 0013](0013-transitivas-e-imagenes-fijadas.md),
  por la dependencia nueva.

## Problema

El editor empieza cada pieza desde cero: lee el copy y el guion, decide qué
destaca y compone la lámina. Johan preguntó si una IA podía adelantarle un
boceto —qué elementos, de qué tamaño y dónde—, y el editor aprobó unos de
prueba hechos con Claude. Hacerlo dentro de Astrolabio significa, por
primera vez, que la app llama a un servicio de fuera de la casa.

## Decisión

**La API le pide el boceto a Claude con el SDK oficial, lo valida, lo guarda
y el cliente lo dibuja desde los datos. Todo es opcional: sin clave, la app
es la de siempre.**

- **Qué sale.** El título, el cuadro de materiales, el tema, el copy gráfico
  y el guion de la pieza, hacia la API de Anthropic. Nada del vault, del
  respaldo, de las notas del traspaso ni de los usuarios. Es contenido hecho
  para publicarse.
- **La clave**, `ANTHROPIC_API_KEY`, solo en el `.env` del PC donde corre la
  app (AGENTS §2.4). Sin ella, el panel lo dice y nada más cambia.
- **El modelo**, `claude-opus-5` por defecto, en `BOCETOS_MODELO`. Cambiarlo
  es cambiar calidad y coste sin tocar código.
- **Una salida estructurada** con el esquema de la fase: la respuesta es JSON
  que cumple el esquema, no texto que haya que interpretar. Lo que el esquema
  no puede exigir —un solo peso 1, zonas dentro de la rejilla y sin
  solaparse— lo comprueba la API antes de guardar nada.
- **El dibujo es del cliente.** El modelo devuelve datos —tipos, pesos,
  zonas y textos— y el cliente los pone en una rejilla. Ningún texto del
  modelo se interpreta como HTML.
- **Cada intento con respuesta se guarda**, con sus tokens, en la tabla
  `boceto`: el historial de la pieza y lo que ha costado.
- **Siempre a petición**, con un botón. Nunca al guardar ni al entregar.

## Alternativas descartadas

- **Generar la imagen del boceto.** No se puede validar qué dice, inventa
  texto y cifras, y no se deja rehacer en otro programa. Un boceto como datos
  sí.
- **Que el modelo devuelva HTML o SVG.** Habría que sanear marcado ajeno para
  pintarlo, y no se podría comprobar la rejilla.
- **Llamar a Claude desde el navegador.** La clave viajaría al cliente, y el
  editor la tendría.
- **Un modelo local.** El PC de Johan no tiene con qué moverlo a la calidad
  que aprobó el editor, y sería otra pieza que mantener.
- **Reintentar solo cuando la validación falla.** Duplicaría el gasto sin que
  nadie lo decida; mejor decir qué falló y que se vuelva a pedir.

## Consecuencias

- **La app sale a internet**, desde el contenedor de la api hacia
  `api.anthropic.com`, cuando alguien pide un boceto. El resto sigue sin salir
  de la red de la casa ni de Tailscale (ADR 0002).
- **Hay un proveedor y un precio.** Cada boceto cuesta, con el modelo por
  defecto, unos 0,08 USD, y hasta unos 0,20 con el razonamiento; el gasto está
  en la tabla `boceto`. Si Anthropic cambia modelos o precios, se cambia el
  `.env`.
- **Una dependencia nueva**, `anthropic`, con sus transitivas —entre ellas
  `httpx2`— fijadas en el lock (ADR 0013).
- **Desde la nube no se puede probar la llamada real**: no hay clave. Las
  pruebas simulan a Claude, y la prueba de verdad es la de Johan en su PC.
- **nginx espera más** a la API: hasta 10 minutos en lugar de 60 segundos.
