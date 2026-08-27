# Fase 0 — Esqueleto que camina

**Alcance vigente.** Ninguna otra funcionalidad entra hasta que esto esté
terminado según §4.

## 1. Objetivo

Atravesar el sistema entero de punta a punta con la funcionalidad más
delgada posible: navegador del editor → Tailscale → React → FastAPI →
Postgres → una fila → y de vuelta.

Todo el riesgo real de este proyecto está en la **integración**, no en las
funciones: la red privada, las cookies a través de ella, el rol verificado
en el servidor, el despliegue reproducible. Construir funciones antes de
resolver eso es acumular trabajo sobre cimientos sin probar.

Por eso el esqueleto **no tiene dominio**. No es un descuido: los estados
del flujo salen de la conversación con el editor (CLAUDE.md §2.8), y
modelarlos antes sería inventarlos.

## 2. Fuera de alcance — no implementar

Estados y máquina de estados · guion y editor markdown · KaTeX · checklist
de traspaso · comentarios · versiones de pieza · miniaturas · Syncthing ·
exportador al vault · importador de respaldo · métricas y APIs de
plataforma · Alembic (aquí basta `create_all`).

Si alguna parece necesaria, propónla; no la implementes de paso.

## 3. Criterios de aceptación

Verificables. Cada uno se comprueba ejecutando algo, no leyendo el código.

### A. Infraestructura

- **A1** Desde un clon limpio: copiar `.env.example` a `.env`,
  `docker compose up --build`, y los tres servicios (`db`, `api`, `web`)
  quedan arriba sin ningún paso manual adicional.
- **A2** `GET /api/health` → 200 con el estado de la conexión real a
  Postgres, no un `{"ok": true}` fijo.
- **A3** Ninguna dirección de host, puerto ni ruta absoluta escrita en el
  código. Todo por variables de entorno (CLAUDE.md §4).
- **A4** Un segundo dispositivo de la tailnet abre la web por la dirección
  Tailscale del host y funciona igual, **cookies de sesión incluidas**.
  Este es el criterio que más probablemente falle primero; es justo por eso
  que está en la Fase 0 y no en la 3.

### B. Autenticación

- **B1** Script de siembra que crea dos usuarios, uno `investigador` y uno
  `editor`, con contraseñas leídas del entorno.
- **B2** `POST /api/auth/login` válido → 200 y cookie de sesión `HttpOnly`,
  `SameSite=Lax`, y `Secure` cuando el despliegue sea HTTPS.
- **B3** Credenciales inválidas → 401 con **el mismo mensaje y el mismo
  coste temporal** tanto si el usuario existe como si no. No filtrar la
  existencia de cuentas.
- **B4** Contraseñas con Argon2id. Ningún hash aparece en ninguna respuesta
  de la API, en ningún endpoint, nunca.
- **B5** `POST /api/auth/logout` invalida la sesión. `GET /api/auth/me`
  responde 401 sin sesión y 200 con ella.

### C. Autorización — el corazón de la fase

- **C1** Entidad mínima `pieza`: `id`, `titulo`, `creada_en`, `creada_por`.
  **Sin campo `estado`.**
- **C2** `POST /api/piezas` solo para `investigador`. Un `editor`
  autenticado recibe **403** — no 401, no 404, no un 200 silencioso.
- **C3** `GET /api/piezas` accesible a ambos roles.
- **C4** Un test hace la petición de C2 con la cookie del `editor`
  **directamente contra la API**, sin pasar por el frontend, y espera 403.
- **C5** Sin cookie de sesión: 401 en todo salvo `health` y `login`.

### D. Frontend

- **D1** Pantalla de login contra el endpoint real. Ningún usuario simulado
  en el cliente.
- **D2** Tras entrar se ven el nombre y el rol del usuario, y la lista de
  piezas.
- **D3** El botón de crear pieza no se le muestra al `editor` — **además**
  del 403 del servidor, nunca en su lugar.
- **D4** Un error de la API se le muestra al usuario. No se traga en la
  consola.

### E. Calidad

- **E1** `docker compose run api pytest` en verde, cubriendo B2, B3, C2, C4
  y C5.
- **E2** `npm --prefix web run check` en verde (tsc + build).
- **E3** GitHub Actions ejecuta E1 y E2 en cada push.
- **E4** `.env.example` lista todas las variables, sin un solo valor real.
  `.gitignore` excluye `.env`, `tokens/` y `client_secret*`.
- **E5** README con qué es el proyecto, cómo levantarlo, y el diagrama de
  despliegue.

## 4. Definición de terminado

**El editor, desde su propia máquina, entra con su usuario, ve la lista de
piezas y comprueba que no puede crear una.**

No cuenta como terminado en la máquina de quien lo programó. La prueba es
que funcione en la otra punta de la tailnet, con la persona real.

Grabar ese recorrido en un GIF de veinte segundos al conseguirlo: sirve para
el README y es la imagen que se ve en los primeros segundos de una revisión
de portafolio (ADR 0002).

## 5. Orden sugerido de trabajo

1. **Primer commit: solo este brief.** `CLAUDE.md` y `docs/`, sin código.
   El historial empieza mostrando que las decisiones existían antes que la
   implementación.
2. `docker compose` con los tres servicios y `health` (A1, A2, A3).
3. Tailscale y A4 — **antes** de la auth. Si las cookies no cruzan la red
   privada, cambia el diseño de sesión, y es mejor descubrirlo con cero
   código de auth escrito.
4. Auth (B) con sus tests.
5. `pieza` y autorización (C) con sus tests.
6. Frontend (D).
7. CI y README (E).

## 6. Primer mensaje sugerido para la sesión de Claude Code

> Lee `CLAUDE.md` y todo `docs/`. No escribas código todavía: dime qué vas
> a hacer para los criterios A1–A3 de `docs/fase-0-esqueleto.md`, qué
> dependencias necesitas y por qué. Luego lo implementamos por pasos, y
> paramos en A4 para probar Tailscale antes de seguir.

Pedir el plan antes que el código evita la sesión típica en la que aparecen
cuarenta archivos de golpe y ninguno se ha ejecutado.
