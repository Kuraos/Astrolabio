# Guía para la conversación sobre los estados

Insumo para cumplir el §2.8 del `CLAUDE.md`. **No es el resultado**: el
resultado es lo que diga tu hermano, escrito en `docs/`, y de ahí sale la
migración que añade la columna `estado`.

## Para qué es, y para qué no

**Sirve para** que los estados del flujo salgan de sus palabras, describiendo
su propio trabajo.

**No sirve para** enseñarle una lista y que la apruebe. Eso es inventar los
estados con testigo: dirá que sí a casi cualquier cosa razonable, porque
todavía no ha trabajado con ellos y porque la lista la traes tú.

La diferencia se nota en el resultado. Yo puedo escribir
`borrador → revisión → aprobado → publicado` en dos minutos: suena bien y
probablemente no describe el trabajo de nadie. Si él dice «cuando me pasas el
guion lo dejo *en cola* hasta que tengo el material», eso es un estado real
con un nombre que ya usa — y `en_cola` no se le ocurre a nadie desde fuera.

## Cómo conducirla

- **Veinte minutos bastan.** Es una conversación, no una entrevista de
  requisitos.
- **Pregunta por lo que pasó, no por lo que debería pasar.** «Cuéntame la
  última pieza» saca hechos; «¿qué estados te parecen bien?» saca opiniones
  sobre un vocabulario que no es suyo.
- **No propongas nombres.** Si te quedas callado tres segundos, él los llena.
- **Anota sus palabras literales**, aunque suenen informales. `atascado`,
  `sin material`, `pendiente de que me pases` son mejores nombres de estado
  que cualquier sinónimo más técnico.
- **Si dice «depende», eso es oro.** Un «depende» marca una bifurcación real
  del flujo, que es justo lo que una máquina de estados tiene que modelar.

## Las preguntas

### El recorrido real

1. Cuéntame la última pieza que editaste, desde que te llegó hasta que quedó
   lista. ¿Qué hiciste primero?
2. ¿En qué te fijas para saber que puedes empezar?
3. ¿Qué es lo primero que haces cuando abres una pieza nueva?

### Los traspasos — el núcleo

4. ¿En qué momento exacto una pieza deja de ser mía y pasa a ser tuya?
5. ¿Y cuándo te la quitas de encima y vuelve a mí?
6. ¿Alguna vez te llega algo que técnicamente está «listo» pero no puedes
   empezar? ¿Qué le falta?

### Los atascos

7. ¿Dónde se te queda parada una pieza más tiempo del que quisieras?
8. Cuando no puedes avanzar, ¿es por algo que falta de mi lado, o por algo
   tuyo? ¿Cómo lo distingues hoy?
9. ¿Ha pasado que una pieza vuelva atrás? ¿Por qué?

### El final

10. ¿Cuándo consideras que tu parte está terminada?
11. ¿Y quién decide que la pieza se publica?

### La pregunta que mide el producto

12. **¿Qué me preguntas por mensaje sobre una pieza?**

Esta última es la más importante y conviene dejarla para el final. El §1 dice
que la prueba de que Astrolabio funciona es que **dejen de mandarse mensajes**
sobre el estado de las piezas. Cada pregunta que hoy se hacen por chat es un
estado que la aplicación debería mostrar sola.

Si la respuesta es «te pregunto si ya está el guion» → hay un estado sobre el
guion. Si es «te pregunto si ya viste mi corte» → hay un estado sobre la
revisión. Los estados están escondidos en el historial de WhatsApp.

## Qué anotar

Un documento corto en `docs/`, con:

- **La lista de estados con sus nombres**, tal como él los dijo.
- **Quién puede mover cada uno.** No siempre es simétrico: puede que él marque
  «listo para revisión» pero solo tú marques «publicada».
- **Las transiciones que existen**, incluidas las que van hacia atrás. Un flujo
  que solo avanza casi nunca es el real.
- **Qué tiene que ser cierto para pasar de uno al siguiente.** De aquí sale la
  checklist de traspaso.
- **Lo que quedó en duda.** Vale más un hueco declarado que un estado
  inventado para tapar el hueco.

## Trampas

**No hagas la lista «completa».** Si salen tres estados, son tres. Un flujo de
ocho etapas en un proyecto de dos personas se abandona en un mes, y entonces
la aplicación miente sobre dónde está cada pieza.

**No modeles lo que quieres que pase.** Si hoy la revisión no existe como paso,
no la inventes porque «debería haberla». El estado se añade cuando el hábito
exista, con su propia migración.

**Cuidado con los estados que son de una persona sola.** Si algo solo lo mira
él y nunca cambia lo que tú haces, quizá sea una nota suya y no un estado del
flujo compartido.

## Después

Con ese documento en `docs/` se puede escribir el alcance de la fase
siguiente: la columna `estado`, su migración, las reglas de quién mueve qué
—cada una con su prueba de 403, como manda el §2.3— y la tabla `traspaso`
append-only del §2.6, que es de donde sale la métrica de cuánto tarda una
pieza y en qué etapa se atasca.
