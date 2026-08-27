# ADR 0002 — Autoalojado, con acceso por Tailscale

- **Fecha**: 2026-08-26
- **Estado**: aceptada

## Problema

Dos requisitos que parecían incompatibles: *todo local, sin nube y sin
suscripción mensual*, y *el editor entra desde otra máquina*.

## Decisión

Separar «local» en sus dos significados. El requisito real es **que el
proceso corra en hardware propio y los datos no vivan en el servidor de un
tercero** — no que nadie más pueda alcanzarlo.

El servidor corre por `docker compose` en la máquina de Johan; el editor
entra por **Tailscale**, red privada cifrada entre dispositivos. Plan
Personal gratuito, seis usuarios, dispositivos ilimitados. Sin puertos
abiertos en el router, sin factura, sin datos fuera de casa.

Tres variantes previstas, en orden de compromiso creciente:

| Variante | Coste | Disponibilidad | Cuándo |
|---|---|---|---|
| A. Servidor en el PC de Johan + Tailscale | $0 | Cuando ese PC esté encendido | Empezar aquí |
| B. Mini-PC o Raspberry Pi siempre encendido | ~$60–150 una vez | 24/7 | Si A molesta dos veces |
| C. Cloudflare Tunnel a un dominio propio | $0 + dominio | 24/7 público | Solo para la instancia de demostración |

## Consecuencias

- **Toda la configuración va en variables de entorno.** Pasar de A a B a C
  debe ser mudar el mismo contenedor, no refactorizar. Ninguna dirección de
  servidor escrita en el código.
- El coste aceptado de la variante A es la disponibilidad: si el PC está
  apagado, el editor no entra. Se acepta a sabiendas y se revisa pronto.
- **Coste para el portafolio**: un proyecto autoalojado no se abre en los
  ~15 segundos de un cribado. Se compensa con una instancia de demostración
  con datos sembrados (variante C) y un README como estudio de caso. Es
  trabajo presupuestado, no improvisado.
- La autenticación no se relaja por estar en red privada. Ver CLAUDE.md §2.3.
