# ADR 0018 — Los bocetos viajan por OpenRouter

- **Fecha**: 2026-10-11
- **Estado**: aceptada
- **Contexto**: enmienda el [ADR 0016](0016-bocetos-con-claude.md) en un
  punto: por dónde sale la petición. Lo demás de aquel —qué sale, la salida
  estructurada, el dibujo en el cliente, cada intento guardado, siempre a
  petición— sigue igual.

## Problema

El ADR 0016 mandaba la petición a `api.anthropic.com` con una clave de la
consola de Anthropic. Johan va a pagar los bocetos con una cuenta de
OpenRouter, y la prueba con clave real de la Fase 9 seguía pendiente: se
decide antes de hacerla.

## Decisión

**La petición sale hacia OpenRouter, con el mismo SDK `anthropic`, y es el
único camino.**

- **El mismo SDK, otra dirección.** OpenRouter expone `/api/v1/messages` con
  el formato de la Messages API de Anthropic. El cliente se crea con
  `base_url="https://openrouter.ai/api"` y nada más del código de la petición
  cambia de forma: el streaming, los 64.000 tokens y la salida estructurada
  con `output_config` están en su esquema.
- **La clave**, `OPENROUTER_API_KEY`, solo en el `.env`. Viaja en
  `Authorization: Bearer` —`auth_token` en el SDK—, no en `x-api-key`.
  `ANTHROPIC_API_KEY` deja de existir.
- **El modelo**, `anthropic/claude-opus-5.5` por defecto, con el nombre que
  le da OpenRouter, en `BOCETOS_MODELO`.
- **Sin el respaldo ante una negativa.** `fallbacks="default"` y su cabecera
  beta son de la API de Anthropic. El `fallbacks` de OpenRouter es otra cosa:
  una lista de modelos que resuelve su enrutador. No se usa: si el modelo
  declina, el intento se guarda con su error, como cualquier otro fallido.
- **Un mensaje para el 402.** Una cuenta de prepago se queda sin saldo, y
  eso se dice con sus palabras, no como «falló».

## Alternativas descartadas

- **Los dos caminos, con la dirección en una variable.** Era la primera
  propuesta. Dos formas de autenticarse y una rama para el respaldo, por un
  camino que nadie va a usar; si hace falta volver, este ADR dice qué se
  quitó.
- **El SDK de OpenRouter o el de OpenAI.** Otra dependencia con sus
  transitivas ([ADR 0013](0013-transitivas-e-imagenes-fijadas.md)) y otra
  forma de respuesta, para llegar al mismo modelo.

## Consecuencias

- **Hay un intermediario.** El título, el cuadro, el tema, el copy y el guion
  pasan por OpenRouter antes de llegar al proveedor que sirva el modelo. Es
  contenido hecho para publicarse, y sigue sin salir nada del vault, del
  respaldo ni de los usuarios.
- **La app sale a `openrouter.ai`**, no a `api.anthropic.com`.
- **El precio lo pone OpenRouter.** Las cifras del ADR 0016 eran de
  `claude-opus-5` directo y ya no valen; los tokens de cada intento siguen en
  la tabla `boceto`.
- **Un `.env` de antes** con `ANTHROPIC_API_KEY` deja los bocetos sin
  configurar hasta que se cambie por `OPENROUTER_API_KEY`. El panel lo dice.
- **Sin probar con clave real**, igual que antes: que OpenRouter acepte la
  petición tal como la arma el SDK, y qué `stop_reason` y qué `usage`
  devuelve, lo dice la prueba de Johan en su PC.
