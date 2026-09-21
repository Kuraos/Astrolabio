# ADR 0008 — `traspaso` es append-only en la base, no por disciplina

- **Fecha**: 2026-09-21
- **Estado**: aceptada
- **Contexto**: criterio M2 de `docs/fase-2-traspaso.md`, invariante §2.6.

## Problema

El §2.6 dice que `traspaso` se inserta y nunca se actualiza ni se borra: de
esa tabla sale la métrica que ninguna herramienta comprada puede dar, cuánto
tarda una pieza en cada etapa. Una historia que se puede reescribir no mide
nada.

La pregunta es quién hace cumplir la regla. Si la cumple el código, la cumple
el código que existe el día que se escribe la prueba. La vigilancia no alcanza
a un script de corrección de datos, a una migración futura, a un endpoint que
alguien añade con prisa ni a una sesión de `psql` a mano, y todos esos caminos
llegan a la tabla sin pasar por la aplicación.

## Decisión

Un trigger de Postgres rechaza `UPDATE`, `DELETE` y `TRUNCATE` sobre
`traspaso`. Se crea en la misma migración que la tabla, y su `downgrade` lo
retira.

`TRUNCATE` entra por lo mismo que `DELETE`: es un borrado sin `WHERE`, y un
trigger por fila no lo ve.

La prueba de M2 no comprueba que el código evite el `UPDATE`: lo ejecuta por
SQL y espera que la base lo rechace. Así vigila lo que de verdad garantiza el
invariante, y falla si una migración posterior retira el trigger.

## Alternativas descartadas

- **Solo una prueba sobre el código.** Vigila las rutas que existen hoy, y el
  invariante tiene que valer también para las que todavía no existen.
- **Un evento del ORM** (`before_update` y `before_delete` en SQLAlchemy).
  Cubre el mismo terreno que la prueba y ni uno más: el SQL directo no pasa por
  el ORM.
- **Quitarle los permisos al usuario de la aplicación.** La aplicación y
  Alembic usan el mismo usuario, que es dueño de las tablas, y un dueño puede
  devolverse los permisos que se quita. Cerrarlo de verdad pide separar el
  usuario que migra del que usa la aplicación: dos credenciales y dos cadenas
  de conexión para lo que un trigger resuelve en una migración.

## Consecuencias

- **Un error se corrige con otra fila, no editando la mala.** Si alguna vez
  hace falta reescribir la historia, desactivar el trigger es un acto explícito
  del dueño de la base (`ALTER TABLE … DISABLE TRIGGER`), no un descuido.
- **Una pieza con historia no se puede borrar**: sus traspasos la referencian
  y no se pueden borrar con ella. Hoy no existe forma de borrar piezas, así
  que no cambia nada.
- `alembic downgrade` sigue funcionando: `DROP TABLE` no dispara triggers de
  `DELETE` ni de `TRUNCATE`.
- Las pruebas no lo notan: cada una corre en una transacción que se revierte,
  y revertir no es borrar.
- La comparación de modelos contra migraciones (F2) no ve triggers, así que no
  hay deriva que detectar. Lo que vigila que el trigger siga ahí es la prueba
  de M2.
- Cuando lleguen `snapshot` y `version_pieza`, las otras dos tablas del §2.6,
  su migración engancha la misma función.
