# ADR 0005 — Un solo origen: la web sirve el frontend y hace de proxy a la API

- **Fecha**: 2026-08-26
- **Estado**: aceptada
- **Contexto**: criterio A4 de `docs/fase-0-esqueleto.md`.

## Problema

El editor entra desde otra máquina de la tailnet y la sesión viaja en una
cookie (CLAUDE.md §3). La pregunta de la Fase 0 no es si la cookie se
emite, sino **si sobrevive el viaje**.

Si el frontend y la API son orígenes distintos —dos puertos del mismo
host lo son— la cookie pasa a ser *cross-site*. Entonces el navegador
exige `SameSite=None`, que solo acepta acompañado de `Secure`, que solo
viaja por HTTPS. Y la variante A del ADR 0002 es HTTP plano sobre
Tailscale. El resultado es que **el login no funcionaría y la causa
estaría a tres capas de distancia** del síntoma.

## Decisión

Un solo origen. El servicio `web` sirve el build estático y hace de
proxy inverso de `/api` hacia el contenedor `api`. El navegador solo
conoce una dirección y un puerto.

Con eso la cookie es *same-site*: basta `SameSite=Lax`, no hace falta
CORS con credenciales y no hace falta TLS para iniciar sesión.

La decisión ya estaba implícita en `.env.example`, donde `VITE_API_BASE`
viene vacío y anotado como «vacío = mismo origen». Este ADR la hace
explícita y deja escrito el porqué.

## Alternativas descartadas

- **Orígenes separados con CORS y `SameSite=None`.** Obliga a montar
  HTTPS sobre la tailnet (Tailscale Serve o certificados propios) antes
  de poder probar un login. Mete TLS en el camino crítico de la Fase 0
  para no ganar nada: nadie necesita que la API viva aparte.
- **Exponer el servidor de desarrollo de Vite directamente.** Exige
  declarar el nombre Tailscale en `allowedHosts` y convierte un servidor
  de desarrollo en el camino de producción.
- **Token en `localStorage` en vez de cookie.** Esquiva el problema de
  origen, pero contradice §3 y le entrega a cualquier XSS un token
  legible. La cookie `HttpOnly` existe justamente para eso.

## Consecuencias

- El frontend llama rutas relativas (`/api/...`). `VITE_API_BASE` se
  queda vacío y solo se rellenaría si algún día se separan, que es
  precisamente lo que este ADR desaconseja.
- Las tres variantes de despliegue del ADR 0002 siguen siendo un cambio
  de entorno y no de código: siempre es un puerto.
- Cuando llegue HTTPS (variante C), la única línea que cambia es
  `COOKIE_SECURE=true`.
- **Coste**: el build del frontend queda dentro de la imagen, así que
  iterar en React por `docker compose` es lento. Se itera con
  `npm --prefix web run dev` en local; `compose` es el camino
  reproducible, no el de desarrollo.
- La dirección de la API no se escribe en el código: la plantilla de
  nginx la recibe por entorno (`API_HOST`, `API_PORT`), que es lo que
  exige el criterio A3.
