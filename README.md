# Astrolabio

Taller de producción de contenido para **Voz del Cosmos**, un proyecto de
divulgación astronómica de dos personas.

El problema que resuelve no es «gestionar contenido»: es **el traspaso**. Cómo
pasa una pieza de las manos del investigador a las del editor y vuelve, sin que
ninguno tenga que preguntarle al otro en qué estado va.

La prueba de que funciona es que **dejen de mandarse mensajes** sobre el estado
de las piezas. Todo lo demás es infraestructura alrededor de eso.

| Rol | Quién | Qué hace |
|---|---|---|
| `investigador` | Johan | Investigación, guion, grabación. Responsable de la exactitud científica |
| `editor` | Su hermano | Edición y piezas gráficas |

---

## Estado

Las fases 0 a 2 están cerradas. De la 3 a la 6 el código está terminado y
falta su prueba en el uso.

- **Fase 0, el esqueleto**: sesión con cookie, dos roles y autorización
  comprobada en el servidor.
- **Fase 1, la fuente de verdad dividida**: el guion en markdown con LaTeX,
  el respaldo científico leído del vault de Obsidian y la pieza exportada a
  él.
- **Fase 2, el traspaso**: seis estados con las palabras del editor, reglas
  de quién mueve la pieza y una historia que no se puede reescribir.
- **Fase 3, el material**: enlaces de referencia y la carpeta de cada pieza
  en Syncthing, con las miniaturas de sus imágenes. Falta probarla con el
  editor desde su máquina.
- **Fase 4, escribir con herramientas**: una barra y atajos para el guion,
  tablas en la vista previa y más espacio para escribir. Falta escribir un
  guion de verdad con ella y compararlo en Obsidian.
- **Fase 5, temas y etiquetas**: cuatro temas fijos, y etiquetas libres con
  un catálogo de qué se ha hablado, que llegan a Obsidian como tags
  anidados. Falta usarla con piezas de verdad y verlas en Obsidian.
- **Fase 6, tablero, tareas y fechas**: un tablero por estado en lugar de
  la lista, tareas por pieza y sueltas, fechas de entrega y de publicación,
  y lo pendiente por semanas. Falta que el editor lo use desde su máquina.

La [hoja de ruta](docs/hoja-de-ruta.md) terminaba en la Fase 6: lo que venga
después saldrá del uso.

- **Fase 7, identidad «Control»**, abierta: la interfaz gana una identidad
  propia sin cambiar lo que hace. Su alcance está en
  [`docs/fase-7-identidad.md`](docs/fase-7-identidad.md).

---

## Cómo está hecho

React y FastAPI sobre Postgres, con Docker Compose, en el PC de Johan. Un
nginx sirve el cliente y hace de proxy de la API en el mismo origen; el editor
entra por Tailscale, sin nube y sin puertos abiertos, y los archivos pesados
viajan por Syncthing, nunca por la API.

El diagrama, el camino de una petición y dónde vive cada dato están en
[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

---

## Cómo levantarlo

Requiere Docker y Docker Compose. Desde un clon limpio:

```bash
cp .env.example .env
```

```bash
docker compose up --build
```

Los tres servicios quedan arriba sin ningún paso manual adicional, y la
aplicación queda en `http://localhost:8080`.

El esquema lo crean **las migraciones**: el contenedor de `api` corre
`alembic upgrade head` antes de servir. No hay `create_all` en ninguna parte, y
una prueba lo vigila — dos mecanismos para crear el mismo esquema derivan, y
cuál gana depende del orden de arranque.

Los valores de `.env.example` son marcadores de desarrollo, no credenciales de
nada real. **En cualquier despliegue que no sea el portátil de quien programa,
cámbialos.**

Para crear los dos usuarios:

```bash
docker compose run --rm api python -m app.seed
```

Las contraseñas salen del entorno (`SEED_*`), nunca del código.

El respaldo científico y la carpeta de material leen dos carpetas del host:
`VAULT_HOST_PATH` y `SYNCTHING_HOST_PATH`, en `.env`. Sin ellas la aplicación
arranca igual y cada panel dice qué falta.

Los demás comandos —pruebas, `check` del cliente, migraciones— están en
[`AGENTS.md`](AGENTS.md) §5.

---

## Documentos

| | |
|---|---|
| [`docs/PRD.md`](docs/PRD.md) | Qué se construye, para quién y qué no entra |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | Cómo se conecta: servicios, datos, seguridad y despliegue |
| [`docs/DESIGN_SYSTEM.md`](docs/DESIGN_SYSTEM.md) | Cómo se ve la interfaz, con el contraste medido |
| [`AGENTS.md`](AGENTS.md) | Cómo trabaja un agente de código aquí: invariantes, convenciones y comandos |
| [`docs/estados-del-flujo.md`](docs/estados-del-flujo.md) | Los estados del flujo, en palabras del editor |
| [`docs/hoja-de-ruta.md`](docs/hoja-de-ruta.md) | Las fases 3 a 6 |

---

## Decisiones

Los registros de decisión están en [`docs/adr/`](docs/adr/). Son parte del
producto, no documentación de relleno: explican por qué el sistema es como es y
qué alternativas se descartaron.

| | |
|---|---|
| [0001](docs/adr/0001-fuente-de-verdad-por-type.md) | Fuente de verdad dividida por `type`, sin sincronización bidireccional |
| [0002](docs/adr/0002-autoalojado-con-tailscale.md) | Autoalojado, con acceso por Tailscale |
| [0003](docs/adr/0003-binarios-fuera-de-la-app.md) | Los binarios pesados viven fuera de la aplicación |
| [0004](docs/adr/0004-sin-rankings-bajo-umbral.md) | Sin rankings de tema bajo el umbral estadístico |
| [0005](docs/adr/0005-mismo-origen-tras-proxy.md) | Un solo origen: la web sirve el frontend y hace de proxy |
| [0006](docs/adr/0006-sesiones-con-estado-en-postgres.md) | La sesión vive en Postgres, no en una cookie firmada |
| [0007](docs/adr/0007-como-escribe-astrolabio-en-el-vault.md) | Cómo escribe Astrolabio en el vault |
| [0008](docs/adr/0008-traspaso-append-only-en-la-base.md) | `traspaso` es de solo inserción en la base, no por disciplina |
| [0009](docs/adr/0009-el-estado-viaja-al-vault.md) | El estado viaja al vault en `status` |
| [0010](docs/adr/0010-la-carpeta-de-cada-pieza.md) | La carpeta de cada pieza en Syncthing |
| [0011](docs/adr/0011-las-etiquetas-viajan-al-vault.md) | Las etiquetas viajan al vault como tags anidados |
| [0012](docs/adr/0012-la-fecha-de-publicacion-viaja-al-vault.md) | La fecha de publicación viaja al vault: la prevista y, al publicar, la real |
| [0013](docs/adr/0013-transitivas-e-imagenes-fijadas.md) | Las transitivas y las imágenes base también se fijan |
| [0014](docs/adr/0014-identidad-con-tokens-y-fuentes-propias.md) | La identidad trae sus colores y sus fuentes, servidas por la app |
