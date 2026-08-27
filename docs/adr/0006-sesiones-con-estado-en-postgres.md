# ADR 0006 — La sesión vive en Postgres, no en una cookie firmada

- **Fecha**: 2026-08-26
- **Estado**: aceptada
- **Contexto**: criterio B5 de `docs/fase-0-esqueleto.md`.

## Problema

Hay dos formas habituales de sostener una sesión en cookie:

1. **Cookie firmada sin estado.** La cookie *contiene* la identidad, firmada
   con una clave. El servidor no guarda nada: valida la firma y confía.
2. **Identificador opaco con estado.** La cookie contiene un número
   aleatorio sin significado; la sesión real es una fila en la base.

La primera es más simple y escala mejor, y para dos usuarios en una red
privada esa ventaja es irrelevante.

Lo que decide es **B5: «logout invalida la sesión»**. Una cookie firmada no
se puede invalidar: sigue siendo criptográficamente válida hasta que
expire, la tenga quien la tenga. La única manera de revocarla es una lista
de revocación consultada en cada petición — que es exactamente un almacén
de sesiones, pero construido al revés y con peor nombre.

## Decisión

Sesión con estado. La cookie lleva un identificador opaco y aleatorio; la
tabla `sesion` guarda a quién pertenece y cuándo expira. `logout` borra la
fila, y desde ese instante la cookie no vale nada.

Atributos de la cookie, ya validados contra la tailnet por la sonda del
criterio A4: `HttpOnly`, `SameSite=Lax`, `Path=/`, y `Secure` gobernado por
`COOKIE_SECURE` — hoy en false porque la variante A del ADR 0002 es HTTP
plano.

El identificador se genera con `secrets.token_urlsafe`, no con `uuid4`:
un UUID no está pensado para ser impredecible, y este valor es la
credencial entera.

## Alternativas descartadas

- **JWT.** Es la cookie firmada del caso 1 con más ceremonia: mismo problema
  de revocación, más superficie (algoritmos, `alg: none`, expiración mal
  interpretada) y ningún beneficio para dos usuarios que comparten servidor.
- **Sesión en memoria del proceso.** Se pierde en cada `docker compose up`,
  y el editor tendría que volver a entrar cada vez que se toca el backend.
- **Lista de revocación sobre cookie firmada.** Es este ADR, implementado de
  la forma más complicada posible.

## Consecuencias

- Cada petición autenticada hace una consulta a Postgres. Con dos usuarios
  eso no es un coste, es ruido estadístico.
- Se puede responder «¿quién tiene sesión abierta ahora?» y cerrar sesiones
  a distancia, que en un sistema de dos personas con roles distintos es una
  propiedad útil y no un lujo.
- La tabla `sesion` **no** es un registro de historia del §2.6: las filas se
  borran al cerrar sesión. La auditoría de quién cambió qué es otra cosa y
  vive en `traspaso`, que sí es append-only.
- **`SESSION_SECRET` desaparece.** No se firma nada, así que no hay clave que
  guardar: el identificador opaco necesita una fuente de aleatoriedad, y esa
  la da el sistema operativo a través de `secrets`, no una variable de
  entorno.

  Una primera versión de este ADR la dejaba «reservada por si algún día se
  firma algo distinto». Eso es andamiaje preventivo, que este proyecto no
  admite, y además una variable que nadie lee es una pregunta sin respuesta
  para quien abra la configuración dentro de seis meses. Se retiró.
