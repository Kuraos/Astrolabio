# CLAUDE.md — Astrolabio

Instrucciones raíz del proyecto. Léelo antes de escribir código, proponer
arquitectura o crear archivos.

Si algo de este documento choca con lo que te pide el usuario en el momento,
gana el usuario — pero **dilo en voz alta antes de hacerlo**: «esto contradice
la regla §2.3 de CLAUDE.md, que existe por X; ¿la derogamos?». Las reglas de
§2 se tomaron con razones escritas en `docs/adr/`; cambiarlas es legítimo,
cambiarlas sin darse cuenta no.

---

## 1. Qué es Astrolabio

Taller de producción de contenido para **Voz del Cosmos**, un proyecto de
divulgación astronómica de dos personas.

- **Johan** (rol `investigador`): investigación, guion, grabación y
  recopilación de material. Responsable de la exactitud científica.
- **Su hermano** (rol `editor`): editor de contenido principal. Realiza y
  edita las piezas gráficas.

El problema que resuelve **no es «gestionar contenido»**: es **el traspaso**.
Cómo pasa una pieza de las manos de uno a las del otro y vuelve, sin que
ninguno tenga que preguntarle al otro en qué estado va. Todo lo demás es
infraestructura alrededor de eso.

La prueba de que el producto funciona es que **dejen de mandarse mensajes**
sobre el estado de las piezas. Cualquier función que no contribuya a eso es
secundaria, por vistosa que sea.

Contexto completo, con el análisis y las alternativas descartadas: la nota
`Propuesta-Astrolabio` del vault personal de Johan (no está en este repo).

---

## 2. Invariantes — no se rompen sin derogar el ADR correspondiente

### 2.1 Una sola dirección entre la app y el vault

Las piezas (`type: contenido`) se editan **solo aquí**. El vault de Obsidian
recibe una copia exportada, marcada como generada, que nunca se edita a mano.
El respaldo científico (`type: literature`) va al revés: se **lee** del vault
y se muestra en solo lectura; Astrolabio nunca lo escribe.

Nunca propongas sincronización bidireccional de texto. Exige resolución de
conflictos real y es la complejidad que hunde este tipo de proyecto.
→ `docs/adr/0001-fuente-de-verdad-por-type.md`

### 2.2 Los binarios pesados no entran a la aplicación

Vídeo, proyectos de edición e imágenes en capas **no** van a la base de
datos ni suben por HTTP a través de la API. Se sincronizan por fuera
(Syncthing) y la app guarda **la ruta**, no el archivo.

Única excepción: una miniatura comprimida de menos de 200 KB por versión,
para que la interfaz muestre de qué se habla.
→ `docs/adr/0003-binarios-fuera-de-la-app.md`

### 2.3 La autorización se verifica en el servidor, siempre

Cada endpoint comprueba el rol. Ocultar un botón en el frontend **no es
autorización**; es decoración. Que la app viva en una red privada no cambia
esto: los roles de §1 necesitan identidad para funcionar y el historial de
quién cambió qué es la mitad del valor del producto.

### 2.4 Ninguna credencial en el repositorio

Ni tokens, ni `client_secret`, ni contraseñas, ni cadenas de conexión con
usuario real. Todo por variables de entorno, con `.env.example` documentando
las claves y ningún valor. El repositorio es candidato a ser público.

### 2.5 Nunca acceso al vault personal completo

El vault `the-wild-hunt-vault` contiene el diario y la vida personal de
Johan. El editor **no** debe tener acceso a ese repositorio, ni la app debe
leer nada fuera de `03-Negocios/Voz-del-Cosmos/`. `git clone` no tiene
granularidad de carpeta: por eso Astrolabio es un repositorio separado.

### 2.6 Los registros de historia son append-only

`traspaso`, `snapshot` y `version_pieza` se insertan, nunca se actualizan ni
se borran. De ahí sale la métrica que ninguna herramienta comprada puede
dar: cuánto tarda una pieza entre «guion cerrado» y «publicada», y en qué
etapa se atasca.

### 2.7 Sin rankings de tema bajo el umbral estadístico

El panel de métricas muestra conteos y curvas individuales. **No** muestra
rankings ni comparativas de temas mientras haya menos de ~5 piezas por
combinación de tema × formato × plataforma. Con `n` pequeño el ranking mide
la varianza del algoritmo de recomendación, no el rendimiento del tema.
→ `docs/adr/0004-sin-rankings-bajo-umbral.md`

### 2.8 La máquina de estados no se inventa

Los estados del flujo salen de una conversación con el editor, usando **sus**
palabras para su propio trabajo. Hasta que esa conversación ocurra y quede
escrita en `docs/`, no se modela el dominio.

Si te pido estados y esa conversación no ha pasado, recuérdamelo antes de
escribir el código. Es la parte divertida y por eso es la que se hace
demasiado pronto.

---

## 3. Stack

| Capa | Elección | Por qué |
|---|---|---|
| Frontend | React 18 + TypeScript + Vite + Tailwind | Mismo que Grimoire, el otro proyecto del autor: no se vuelve a pagar la curva |
| Backend | Python 3.12 + FastAPI + SQLAlchemy 2.0 | Mismo que Grimoire; la ingesta de APIs de plataforma es Python natural |
| Base de datos | **Postgres** | Dos usuarios escribiendo a la vez. SQLite serializa escrituras y aquí hay concurrencia real |
| Empaquetado | Docker Compose | Hace reproducible el «todo local» y permite mudar el despliegue sin tocar código |
| Red | Tailscale | El editor entra por red privada cifrada, sin nube y sin abrir puertos |
| Auth | Sesión en cookie `HttpOnly` + Argon2 | Dos usuarios; un proveedor OAuth externo sería infraestructura sin beneficio |
| Guion | Markdown + KaTeX | El contenido lleva fórmulas y deben conservarse en LaTeX real |

**Tauri no se usa**, a diferencia de Grimoire, y es deliberado: el cliente
del editor tiene que ser un navegador. Si más adelante hace falta una
ventana nativa, Tauri puede envolver la misma web sin tocar el backend.

---

## 4. Convenciones

- **Idioma**: los nombres del **dominio** van en español, porque son las
  palabras que usan los dos usuarios y las mismas del vault — `pieza`,
  `traspaso`, `guion`, `respaldo`, `version_pieza`, `snapshot`. Todo lo
  demás (variables locales, utilidades, tipos técnicos, mensajes de commit)
  en inglés. No traduzcas «pieza» a «piece» en el modelo de datos.
- **Configuración**: todo por variables de entorno, sin valores por defecto
  que apunten a producción. Nada de rutas absolutas escritas en el código
  — la app debe correr igual en el PC de Johan, en un mini-servidor y en la
  instancia de demostración.
- **Migraciones**: Alembic desde la Fase 1. El esqueleto puede usar
  `create_all`, pero en cuanto haya un modelo de dominio real, migraciones.
  Dejarlo para después significa no hacerlo.
- **Tests**: cada regla de autorización de §2.3 tiene un test que comprueba
  el 403. Es la parte del código donde un fallo no se nota mirando la
  pantalla.
- **Commits**: pequeños y con el porqué en el cuerpo cuando la decisión no
  sea obvia. El repositorio es parte del portafolio; el historial se lee.

---

## 5. Comandos

```bash
docker compose up --build     # levanta web + api + db
docker compose run api pytest # pruebas del backend
npm --prefix web run check    # tsc + vitest + build
```

(Ajustar cuando el esqueleto exista; mantener este bloque al día es parte
del trabajo, no un extra.)

---

## 6. Cómo debes comportarte por defecto

- **No añadas dependencias sin decirlo.** Cada una es superficie de
  mantenimiento en un proyecto de dos personas sin equipo de plataforma.
- **No construyas la fase siguiente.** El alcance vigente está en `docs/`.
  Si ves algo que falta, propónlo; no lo implementes de paso.
- **Prefiere lo aburrido.** Este proyecto es infraestructura de dos
  usuarios, no un laboratorio. La novedad técnica se paga en depuración.
- **Cuando una decisión tenga consecuencias**, escribe un ADR corto en
  `docs/adr/` antes de implementarla. Son la mitad del valor de portafolio
  del repositorio.
- **Si algo no se puede probar, dilo.** No des por funcionando lo que no
  ejecutaste.

---

## 7. Registros de decisión

- `docs/adr/0001-fuente-de-verdad-por-type.md`
- `docs/adr/0002-autoalojado-con-tailscale.md`
- `docs/adr/0003-binarios-fuera-de-la-app.md`
- `docs/adr/0004-sin-rankings-bajo-umbral.md`

Alcance vigente: `docs/fase-0-esqueleto.md`.
