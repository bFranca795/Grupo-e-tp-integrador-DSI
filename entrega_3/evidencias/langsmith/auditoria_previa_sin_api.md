# Auditoría de B.4: capturas y registro del compañero

**Resultado: B.4 permanece pendiente de verificación completa.** Hay capturas
legibles de una ejecución remota y un JSON local compatible con ellas, pero no
se dispone del proyecto, ID raíz, fecha remota verificable ni enlace de la traza.
La clave local de LangSmith es un marcador de ejemplo; no se envió como credencial
ni se intentó consultar la API. No se conocen sus permisos de lectura.

Esta auditoría no ejecuta de nuevo el pipeline, no modifica su configuración ni
crea una traza distinta para sustituir a la entregada. No implementa Parte C ni
realiza evaluaciones RAGAS.

## Fuentes examinadas y alcance

- Captura principal: [`../../langsmith_trace.png`](../../langsmith_trace.png), copia
  exacta de `entrega_3/Generacion.png`.
- Complementarias: [`recuperacion.png`](recuperacion.png),
  [`reranking.png`](reranking.png), [`juez_relevancia.png`](juez_relevancia.png).
- Registro local: [`../b4_companero/resultado_langsmith.json`](../b4_companero/resultado_langsmith.json).
- Manifiesto local de indexación: [`../b4_companero/indexacion.json`](../b4_companero/indexacion.json).
- Verificaciones reproducibles: [`verificacion_b4.json`](verificacion_b4.json) y
  [`auditar_evidencias.py`](auditar_evidencias.py).

Las cuatro copias PNG son byte a byte iguales a los originales; sus SHA-256 están
registrados. No se retocaron, recortaron, recompusieron ni alteraron valores.
Las capturas son legibles a resolución original. Su limitación es el área visible:
las listas están colapsadas o los payloads continúan fuera del encuadre.

## Identidad y enlace

**Proyecto remoto:** no visible en las capturas ni declarado en el JSON de salida.
El nombre `grupo-e-entrega-3-b4` es el indicado por la guía, no un valor confirmado
para esta ejecución. No se toma el `.env` actual como prueba de esa identidad.

**ID raíz de la traza:** no aportado. Los botones «ID» de las capturas no muestran
el UUID. El JSON local sí registra estos IDs de llamadas hijas:

- Juez: `01a14bff-96b9-7103-85e6-4455a3e303e8`.
- Generador: `01a14bff-b92b-7e12-afdc-a795bf901eca`.

Estos UUID no se presentan como ID raíz ni bastan para construir un enlace privado
verificado sin conocer proyecto/workspace o leer la API.

**Fecha:** el JSON local registra finalización `2026-10-17T22:33:38.088354+00:00`
(17/10/2026, 19:33:38.088354 de Buenos Aires). Las capturas muestran «10:33 PM»,
sin fecha ni zona horaria. La fecha remota de la traza queda sin confirmar.

**Enlace real de la traza: pendiente de aportar o recuperar mediante API.**
No se inventó una URL ni se reemplazó por un enlace al portal como si fuera la
traza. Solicitar «Copy link» de la ejecución raíz en LangSmith. Debe tratarse como
un enlace que requiere acceso al workspace salvo comprobación expresa de acceso
público; no se ha verificado que sea público.

La pregunta, árbol de etapas, tiempos y contadores de tokens son compatibles entre
las cuatro capturas y el JSON. Esto permite contrastar contenido, pero no reemplaza
la identificación inequívoca por ID remoto.

## Configuración: qué se puede comprobar

| Parámetro | Evidencia disponible | Alcance de la confirmación |
|---|---|---|
| Chunking 500/100, caracteres | Manifiesto local: `chunk_size=500`, `chunk_overlap=100`, `length_unit=characters` | Documentado localmente; no aparece en la traza visible ni hay vínculo remoto con la indexación |
| Variante avanzada | Árbol `rag_rerank` con juez y generación; JSON `variant=rerank` | Observable en capturas y registro local |
| Hasta 8 candidatos | Recuperación muestra `candidates [8 items]`; JSON contiene 8 y `candidate_k=8` | Conteo observado; límite configurado solo en JSON local |
| Sin corte previo de distancia | El juez visible recibe DOC-008/001; JSON lo sitúa a 0.3024785519 y registra otros candidatos mayores que 0.28 evaluados | Compatible y comprobable en los datos locales para este caso; falta ver configuración/entrada remota completa |
| Relevancia mínima 0.5 | JSON `min_judge_score=0.5`; orden de selección consistente | Solo registro local; los scores seleccionados no demuestran por sí solos ese umbral exacto |
| Hasta 4 seleccionados | JSON `selected_k=4` y cuatro seleccionados | Confirmado localmente; salida remota completa no visible |
| Modelo/temperatura | JSON `gemini-3.1-flash-lite`, temperatura 0.0; modelo truncado en árbol visible | Valores exactos locales; falta Attributes remoto legible |

`settings.max_distance=0.28` figura en el JSON, pero ese campo es compartido con el
básico: no prueba que se haya aplicado a la variante avanzada. Tampoco se utiliza
el código actual, por sí solo, para certificar una configuración de una corrida
anterior. En esta auditoría no se ha afirmado una configuración remota que no
aparezca en evidencia de esa ejecución.

El manifiesto del compañero declara **18 documentos y 36 chunks**, con igual hash
original antes/después. Diferencias respecto al JSON limpio: DOC-003 y DOC-00X.
Las pruebas previas tenían 17/35. Se conservan ambas evidencias; no se describe el
corpus del compañero como idéntico al anterior. DOC-00X aparece entre los candidatos
y recibe score 0.0 en el registro local.

## Etapas, candidatos y seleccionados

Las cuatro capturas muestran un árbol compatible de `rag_rerank` que contiene:
`recuperacion` → `reranking` / `juez_relevancia` → rama de generación →
`generacion` → `respuesta_y_fuentes`. El último nodo está en el árbol, pero su
salida no está abierta.

En `recuperacion.png`, `selected [8 items]` es el estado **anterior al juez**,
con `judge=null`. En `reranking.png` también se ve ese estado en **Input**; el
área Output solo alcanza a mostrar su comienzo. No se interpreta ese ocho como
la cantidad seleccionada al terminar el reranking.

### Ocho candidatos del JSON local, en orden

| Orden | ID | Padre | Distancia | Score local |
|---|---|---|---:|---:|
| 1 | DOC-008::chunk-000-989bdb5081187467 | DOC-008 | 0.2673312426 | 1.0 |
| 2 | DOC-001::chunk-000-5d1a5023e0007962 | DOC-001 | 0.2738837600 | 1.0 |
| 3 | DOC-008::chunk-001-92e73e8b1d8ef4e4 | DOC-008 | 0.3024785519 | 0.8 |
| 4 | DOC-007::chunk-000-bfbf474549da33fb | DOC-007 | 0.3230897188 | 1.0 |
| 5 | DOC-00X::chunk-000-56a9a072654fa42c | DOC-00X | 0.3455745578 | 0.0 |
| 6 | DOC-001::chunk-001-619740ed81062fb1 | DOC-001 | 0.3469077945 | 0.5 |
| 7 | DOC-003::chunk-000-42f59d263c71dc15 | DOC-003 | 0.3610868454 | 0.0 |
| 8 | DOC-004::chunk-000-e141194203030764 | DOC-004 | 0.3717386723 | 0.0 |

El JSON conserva IDs, textos completos, metadatos, distancias y motivos. La captura
del juez muestra el comienzo del payload y varios IDs/contenidos, pero no todos.

### Seleccionados del JSON local, en orden final

| Orden | ID | Padre | Score |
|---|---|---|---:|
| 1 | DOC-008::chunk-000-989bdb5081187467 | DOC-008 | 1.0 |
| 2 | DOC-001::chunk-000-5d1a5023e0007962 | DOC-001 | 1.0 |
| 3 | DOC-007::chunk-000-bfbf474549da33fb | DOC-007 | 1.0 |
| 4 | DOC-008::chunk-001-92e73e8b1d8ef4e4 | DOC-008 | 0.8 |

Verificación local ejecutada: pertenencia a candidatos; IDs únicos; igualdad de
contenido y metadatos con el candidato correspondiente; orden igual a scores
ordenados establemente, mínimo 0.5 y límite 4; `sources` exactamente igual a
`selected` incluyendo textos y orden. Todos esos controles pasan.

La captura principal permite leer los primeros tres IDs enviados al generador y
sus contenidos visibles, compatibles con el JSON. El cuarto continúa fuera del
encuadre. No se puede certificar visualmente toda la entrada del generador, ni
la salida final y fuentes remotas. No se sustituye esa comprobación por una
inferencia a partir del código.

La respuesta local completa figura en `resultado_langsmith.json` y cubre
comprobantes de IVA, presentación/pago, aportes/contribuciones, altas/bajas antes
de liquidar e intereses/bloqueo del certificado por pago tardío. Ninguna captura
abre la respuesta final completa: su correspondencia remota queda pendiente.

## Duraciones: LangSmith visible frente a registro local

| Medida | Capturas de LangSmith | JSON local |
|---|---:|---:|
| Duración raíz | 14.70 s, redondeada | `total_seconds=14.882544` del ejecutor local |
| Recuperación | 0.43 s | 0.4248662 s |
| Reranking | 8.82 s | 8.8156950 s |
| Cadena del juez | 8.81 s | No hay medición separada de esa cadena en el JSON |
| Generación | 5.37 s | 5.3688674 s |

Son límites de medición distintos: no se equipara la duración raíz de LangSmith
con el total del ejecutor local. El juez es hijo del reranking; no se suman ambas
duraciones como etapas independientes. No se estima la precisión no visible en
la interfaz ni se interpreta la diferencia como un error del pipeline.

## Tokens: no duplicar padres e hijos

| Rol | Total visible en captura | Entrada en JSON local | Salida en JSON local | Total exacto en JSON local |
|---|---:|---:|---:|---:|
| Juez, llamada Gemini | 1.732K | 1122 | 610 | 1732 |
| Generador, llamada Gemini | 1.099K | 727 | 372 | 1099 |

Los contadores visibles están en los nodos de las llamadas al modelo. Los tokens
input/output exactos de la tabla provienen del SDK guardado en el JSON local,
**no de una lectura de la API de LangSmith ni de campos expandidos en las capturas**.
Los totales son compatibles con la interfaz. El total local deduplicado de las
dos llamadas hijas es 1849 de entrada + 982 de salida = **2831 tokens**.
No se añaden agregados del padre, prompt/parser ni otras copias de `provider_usage`.
No hay registro de tokens de embeddings en estas evidencias. La confirmación remota
del desglose input/output queda pendiente.

## Matriz de cumplimiento

| Requisito | Evidencia observada | Cumple / Pendiente |
|---|---|---|
| Identidad: proyecto, ID raíz, fecha y enlace | Solo IDs hijos y fecha en JSON local; capturas sin proyecto/UUID/URL | Pendiente |
| Configuración final vinculada a esta traza | Manifiesto 500/100 y settings locales; falta Attributes/procedencia remota | Pendiente |
| Recuperación, reranking y generación identificables | Árbol rag_rerank legible con las tres etapas | Cumple |
| Ocho candidatos con IDs y contenido remotos completos | Conteo visible, payload parcial; JSON local completo | Pendiente |
| Seleccionados, puntuaciones y orden remotos | Cuatro y scores comprobados en JSON; Output remoto no expandido | Pendiente |
| Consistencia local candidatos → seleccionados → fuentes | Pertenencia, igualdad de contenidos y orden verificados | Cumple |
| Contexto efectivamente enviado al generador | Tres IDs visibles; cuarto/contexto total fuera de encuadre | Pendiente |
| Respuesta final y fuentes remotas | JSON completo, Output remoto no abierto | Pendiente |
| Duración total y etapas | 14.70 / 0.43 / 8.82 / 5.37 s legibles en interfaz | Cumple |
| Totales de tokens por llamada sin doble conteo | 1.732K juez y 1.099K generador en nodos Gemini | Cumple |
| Desglose remoto de tokens input/output | Solo JSON local: 1122/610 y 727/372 | Pendiente |
| Captura principal y complementarias conservadas | Copias byte idénticas en las rutas pedidas | Cumple |
| Evidencia visual completa de candidatos frente a seleccionados | Capturas legibles pero listas colapsadas/recortadas | Pendiente |

## Qué pantalla falta capturar o recuperar por API

1. **Raíz `rag_rerank` → Attributes/Details:** proyecto, ID raíz, fecha con zona,
   configuración/metadata y «Copy link». Aportar el enlace privado y aclarar el
   acceso requerido al workspace.
2. **`recuperacion` → Output:** expandir `candidates` y mostrar los ocho IDs y
   contenidos. Usar varias capturas si no caben; no recortar valores necesarios.
3. **`reranking` → Output (no Input):** expandir `selected` y `judge.items` para
   mostrar cuatro seleccionados, scores, motivos y orden.
4. **`generacion` o su llamada Gemini → Input:** desplegar el payload para poder
   leer los cuatro IDs y textos suministrados. Contrastar con el punto anterior.
5. **`respuesta_y_fuentes` o raíz → Output:** respuesta final y `sources` completos.
6. **Cada llamada Gemini → Attributes/metadata de uso:** entrada, salida y total
   de tokens, junto al nombre/ID del nodo. No sumar el total agregado del padre.
7. **Configuración e indexación de esta corrida:** si 500/100 o la política de
   selección no están en la traza, registrar ese faltante y aportar el manifiesto
   de indexación vinculado al corpus/colección de esa ejecución. El valor actual
   del código no sustituye la procedencia de la corrida.

Una lectura API autorizada que confirme esos mismos campos puede complementar
las capturas. Configurar un PAT con lectura directamente en `.env`; no compartir
la clave en el chat ni en archivos de evidencias. Si solo hay clave Tracing Only,
la consulta API de lectura no será suficiente y hará falta la verificación visual.

**Conclusión:** hay evidencia parcial real de observabilidad y consistencia local,
pero no alcanza para cerrar B.4 con los requisitos de esta auditoría. No se marca
toda la Parte B como completa. No se hizo commit, push, merge ni PR.
