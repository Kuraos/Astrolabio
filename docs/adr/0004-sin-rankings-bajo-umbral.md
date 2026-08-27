# ADR 0004 — Sin rankings de tema bajo el umbral estadístico

- **Fecha**: 2026-08-26
- **Estado**: aceptada

## Problema

El objetivo declarado del módulo de métricas es responder *¿qué temas de
astronomía y en qué formato sostienen la atención?*. La tentación es
construir cuanto antes la vista que ordena los temas por rendimiento: es la
más vistosa y la más fácil de demostrar.

## Análisis

La unidad de análisis útil no es la pieza, es la celda
`tema × formato × plataforma`. Con `T` temas, `F` formatos y `P` plataformas,
las piezas por celda tras `N` publicaciones son:

    n = N / (T · F · P)

Con 6 temas, 3 formatos y 3 plataformas hay 54 celdas: con N = 30 piezas
queda n ≈ 0,6 y la mayoría de celdas está vacía.

Peor: la distribución de vistas por pieza en plataformas con recomendación
algorítmica es de cola pesada. La varianza **entre piezas del mismo tema**
domina a la diferencia **entre temas**. Un ranking alimentado con n ≲ 5 no
mide temas — mide ruido, y lo presenta con la autoridad visual de un gráfico.

## Decisión

1. El panel muestra conteos y curvas individuales por pieza. **No** muestra
   rankings ni comparativas agregadas de temas mientras n < 5 en las celdas
   comparadas.
2. Cuando el umbral se alcance, la vista comparativa debe mostrar el `n` de
   cada celda junto al valor. Un número sin su tamaño de muestra es una
   afirmación sin respaldo, y este es un proyecto de divulgación científica.
3. **Consecuencia de producto:** fijar 3–4 temas y 2 formatos desde el
   inicio. Multiplica por siete las piezas por celda con el mismo esfuerzo
   de producción.

## Consecuencias

- La vista más atractiva del proyecto es la última en construirse. Es
  deliberado.
- Coherente con el rol de responsable de exactitud científica del proyecto:
  sería incoherente exigir respaldo a cada afirmación de un guion y aceptar
  un ranking con n = 2 en el propio panel.
