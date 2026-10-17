# Auditoría B.4: contraste con la API de LangSmith

**La consulta API fue exitosa y acredita la ejecución real entregada.** La clave
local permite leer la traza y su proyecto. No se imprimieron ni exportaron claves.
No se generó una ejecución nueva para reemplazar a la del compañero.

**B.4 está cumplido según la consigna original:** se incorporaron las capturas
complementarias del juicio y de la selección final, contrastadas con la API. La observabilidad remota —etapas,
entradas/salidas, identidad, tiempos y tokens— sí quedó contrastada por API.
La Parte B queda completa en el alcance de la consigna y los casos documentados; no se afirma una mejora general.

La auditoría anterior, sin acceso API, se conserva en
[auditoria_previa_sin_api.md](auditoria_previa_sin_api.md). Sus restricciones de
lectura describen esa fase anterior; ahora se sustituyen por los datos siguientes.

## Identidad verificada por API

- Proyecto: **grupo-e-entrega-3-b4**.
- ID del proyecto: `ad56b0c4-866e-47a2-9145-0f218035ad61`.
- ID raíz: `01a14bff-94b8-7c73-a84d-da89091ad81a`.
- Inicio UTC: `2026-10-17T22:33:23.385031Z`.
- Fin UTC: `2026-10-17T22:33:38.084356Z`.
- Buenos Aires: 17/10/2026, **19:33:23.385031 a 19:33:38.084356**.
- Revisión registrada en metadata: `e6c90f5`.
- [Enlace de la traza en LangSmith](https://smith.langchain.com/o/4e1308b3-31f5-4580-ac80-b762ab74e4dc/projects/p/ad56b0c4-866e-47a2-9145-0f218035ad61/r/01a14bff-94b8-7c73-a84d-da89091ad81a?poll=true).

El enlace corresponde al workspace autenticado. No se comprobó acceso público ni
se publicó la traza: se presenta como enlace que requiere acceso al workspace.
Los IDs de juez y generador obtenidos por API coinciden exactamente con los del
JSON local entregado, vinculando ambos registros a esta raíz.

## Evidencia API conservada y controles reproducibles

- [traza_api.json](traza_api.json): exportación de campos de la traza y sus hijos,
  con inputs/outputs, metadata, tiempos y uso. No contiene claves.
- [contraste_api.json](contraste_api.json): resultados de controles, parámetros,
  fuentes, duraciones y tokens.
- [contrastar_api.py](contrastar_api.py): vuelve a comprobar la exportación frente
  al JSON local, sin llamadas al modelo ni creación de nuevas trazas.
- [verificacion_previa_sin_api.json](verificacion_previa_sin_api.json): fase anterior.

Pasaron los controles de identidad de trace_id para todos los nodos; igualdad de
las salidas remotas con el JSON local; ocho candidatos completos enviados al juez;
seleccionados pertenecientes a candidatos; correspondencia del juicio del modelo
con la salida del reranking; contexto exacto del generador; respuesta final;
fuentes; dos llamadas LLM distintas y suma de tokens consistente con la raíz.
Ningún nodo presenta error.

## Configuración de la ejecución, sin inferirla del código actual

La salida **remota** de la raíz contiene:

```json
{
  "variant": "rerank",
  "model": "gemini-3.1-flash-lite",
  "temperature": 0.0,
  "candidate_k": 8,
  "selected_k": 4,
  "min_judge_score": 0.5,
  "max_distance": 0.28
}
```

`max_distance` es un campo de configuración compartido. El comportamiento de
esta corrida está verificado con el input real del juez: recibe los ocho
candidatos recuperados, incluyendo seis con distancia mayor a 0.28. Por tanto,
no se aplicó ese corte duro antes del juez en esta ejecución. No se afirma que
la traza registre literalmente un parámetro efectivo `None`: no lo registra.

**Chunking 500/100:** el manifiesto local de indexación lo declara explícitamente,
pero la traza no contiene `chunk_size`, `chunk_overlap` ni el hash de esa
indexación. Se confirma el manifiesto como evidencia local, no como parámetro
remoto de la corrida. Para la consigna, se acepta el manifiesto local entregado como evidencia de
chunking 500/100. La ausencia de esos campos en LangSmith se declara expresamente;
no se afirma que provengan de la traza ni solo del código actual. Un hash enlazado
a la traza sería una mejora opcional de auditoría, no un requisito de cierre.

El corpus del compañero declara 18 documentos y 36 chunks e incluye DOC-00X;
no se confunde con el corpus anterior de 17/35.

## Candidatos, seleccionados y contexto efectivo

Los ocho candidatos remotos, con todos sus textos y metadatos, son exactamente
los del JSON local. El payload real de la llamada Gemini del juez contiene los
mismos ocho IDs y contenidos, en el mismo orden:

| Orden inicial | Padre/fragmento | Distancia | Score remoto |
|---|---|---:|---:|
| 1 | DOC-008/000 | 0.2673312426 | 1.0 |
| 2 | DOC-001/000 | 0.2738837600 | 1.0 |
| 3 | DOC-008/001 | 0.3024785519 | 0.8 |
| 4 | DOC-007/000 | 0.3230897188 | 1.0 |
| 5 | DOC-00X/000 | 0.3455745578 | 0.0 |
| 6 | DOC-001/001 | 0.3469077945 | 0.5 |
| 7 | DOC-003/000 | 0.3610868454 | 0.0 |
| 8 | DOC-004/000 | 0.3717386723 | 0.0 |

Los seleccionados remotos y el contexto **efectivamente enviado a Gemini**
coinciden en IDs, orden y texto exacto:

| Orden final | ID | Padre | Score |
|---|---|---|---:|
| 1 | DOC-008::chunk-000-989bdb5081187467 | DOC-008 | 1.0 |
| 2 | DOC-001::chunk-000-5d1a5023e0007962 | DOC-001 | 1.0 |
| 3 | DOC-007::chunk-000-bfbf474549da33fb | DOC-007 | 1.0 |
| 4 | DOC-008::chunk-001-92e73e8b1d8ef4e4 | DOC-008 | 0.8 |

El contenido bruto devuelto por la llamada al generador es idéntico a la respuesta
de la raíz y al JSON local. Las fuentes finales son exactamente los seleccionados,
incluidos textos, metadatos y orden. La respuesta confirma la cobertura local ya
validada de comprobantes, presentación/pago, aportes/contribuciones, altas/bajas
antes de liquidar e intereses/bloqueo del certificado por pago tardío.

## Tiempos obtenidos por API

| Nodo | Duración remota |
|---|---:|
| Raíz rag_rerank | 14.699325 s |
| recuperacion | 0.425542 s |
| reranking | 8.816276 s |
| Llamada Gemini juez, hija de reranking | 8.812468 s |
| Cadena generacion | 5.368333 s |
| Llamada Gemini generador, hija de generacion | 5.365554 s |

La interfaz muestra aproximadamente 14.70, 0.43, 8.82 y 5.37 segundos para raíz,
recuperación, reranking y generación. Es compatible con los valores API.
El ejecutor local declara 14.882544 s con otro intervalo de medición: no se
reemplaza la duración API por ese valor ni se suman padres con sus hijos.

## Tokens obtenidos por API, sin duplicación

| Llamada LLM | ID | Entrada | Salida | Total |
|---|---|---:|---:|---:|
| Juez | 01a14bff-96b9-7103-85e6-4455a3e303e8 | 1122 | 610 | 1732 |
| Generador | 01a14bff-b92b-7e12-afdc-a795bf901eca | 727 | 372 | 1099 |
| Suma de las dos llamadas distintas | — | 1849 | 982 | 2831 |

El agregado de la raíz API también es 1849/982/2831. **No se suma otra vez**.
Tampoco se suman reranking, juez_relevancia, RunnableBranch o generacion, que
repiten agregados de sus hijos. Los valores coinciden con el JSON local y con
los contadores visibles 1.732K y 1.099K de las capturas. No son estimaciones.
Los tokens de embeddings no figuran en esta traza.

## Capturas existentes

Principal: [langsmith_trace.png](../../langsmith_trace.png).
Complementarias: [recuperacion.png](recuperacion.png), [reranking.png](reranking.png)
y [juez_relevancia.png](juez_relevancia.png). Son copias byte idénticas de los
originales. No se fabricó ni modificó ninguna captura.

La API resolvió los faltantes de IDs, contenidos completos, respuesta y tokens
input/output que las capturas no mostraban. **Limitación de las capturas iniciales, resuelta con las nuevas vistas complementarias:**
`reranking.png` está en Input y apenas comienza Output; `selected [8 items]`
corresponde al estado previo al juez. No muestra visualmente la salida de cuatro.

Pantalla que se solicitó y ahora se complementa con juez1.png, juez2.png y select.png: abrir esta misma traza,
seleccionar **reranking → Output**, expandir **selected [4 items]** y **judge.items**
para leer cuatro IDs, puntuaciones y orden. Conservar el árbol con candidatos
`[8 items]` o acompañar con Output de recuperación. Si no cabe, tomar varias
capturas reales sin recortar la información necesaria.

## Matriz actualizada

| Requisito | Evidencia observada | Cumple / Pendiente |
|---|---|---|
| Proyecto, ID raíz, fecha y enlace | Leídos por API; llamadas hijas coinciden con el JSON entregado | Cumple |
| Variante avanzada, 8 candidatos, mínimo 0.5 y máximo 4 | Settings remotos y datos observados | Cumple |
| Ausencia de corte 0.28 antes del juez en esta corrida | Los ocho candidatos llegan completos al modelo, seis superan 0.28 | Cumple |
| Chunking 500/100 | Manifiesto local de indexación: 500/100 caracteres; no registrado en traza | Cumple |
| Recuperación, reranking y generación en misma traza | Todos los nodos comparten trace_id raíz | Cumple |
| Candidatos con IDs y contenidos | Input/output API completos e iguales al JSON | Cumple |
| Seleccionados, puntuaciones y orden | Salida API de reranking y respuesta bruta del juez | Cumple |
| Seleccionados pertenecen a candidatos | Igualdad de objetos y pertenencia comprobadas | Cumple |
| Contexto real del generador | Input de la llamada Gemini idéntico a seleccionados | Cumple |
| Respuesta final y fuentes | Salida Gemini, raíz, fuentes y JSON coinciden | Cumple |
| Duración total y etapas | Fechas de inicio/fin remotas por nodo | Cumple |
| Tokens entrada/salida sin doble conteo | Dos llamadas distintas; agregado raíz coincide sin sumarlo de nuevo | Cumple |
| Captura principal y complementarias legibles e intactas | PNG conservados y hashes comprobados | Cumple |
| Diferencia visual candidatos frente a seleccionados | Recuperación muestra ocho; juez1/juez2/select muestran el juicio y selected con cuatro entradas; API confirma IDs y orden | Cumple |

**Conclusión:** la ejecución real y su observabilidad están verificadas por API.
Las capturas nuevas completan el entregable visual solicitado. El manifiesto local
satisface la documentación del chunking; no se exige un hash de indexación. Se marca B.1–B.4 cumplido en el alcance documentado. No se implementa Parte C ni se hace commit/push/merge/PR.


## Cierre según la consigna original y el pedido final

B.1–B.3 están implementados y validados en los casos documentados. B.4 tiene
identidad, etapas, tiempos, tokens y selección 8→4 verificados por API y evidencia
local del chunking. La configuración final queda documentada como 500/100
caracteres, hasta ocho candidatos, sin corte 0.28 antes del juez, mínimo 0.5 y
hasta cuatro seleccionados. No se asume una mejora general ni hay resultados RAGAS.

El pendiente obligatorio del entregable visual quedó resuelto con las capturas
complementarias juez1.png, juez2.png y select.png, sin generar otra ejecución. Las capturas actuales ya muestran
los tiempos, tokens y ocho candidatos; las nuevas vistas completan el contraste
visual con los cuatro seleccionados. No se necesita generar otra ejecución.

Opcionales, no bloqueantes: añadir en futuras trazas chunk_size/chunk_overlap,
hash de indexación y mayor metadata de procedencia. No se exigen para cerrar la
consigna original y no se han implementado en este paso.


## Incorporación final de capturas y cierre B.4

Nuevas evidencias aportadas, conservadas sin modificar sus bytes:

- [juez1.png](juez1.png): elementos 0–2 del juicio; IDs y scores 1.0, 1.0 y 0.8.
- [juez2.png](juez2.png): elementos 3–5; IDs y scores 1.0, 0.5 y 0.0.
- [select.png](select.png): elementos 6–7 con score 0.0 y lista selected con
  cuatro entradas de índices 0, 1, 2 y 3.

Las tres son legibles y sus IDs/scores coinciden con la exportación API de la
traza existente. La lista selected está expandida al nivel de sus cuatro
entradas, pero cada objeto interno sigue colapsado: `{6 items}` indica seis
campos, no seis seleccionados. No se atribuyen a esta imagen los IDs/textos
internos ni el orden final: esos datos se verificaron por API y constan arriba.
Algunas razones se ven abreviadas en la interfaz; los motivos completos están
en la exportación API. Estas limitaciones de encuadre no se ocultan ni se
confunden con datos faltantes de la ejecución.

El conjunto conserva la captura principal con tiempos/tokens, recuperación con
ocho candidatos y las nuevas vistas de juicio/selección con cuatro entradas.
Los datos remotos acreditan los contenidos completos y el envío efectivo al
generador. Así queda satisfecho el entregable solicitado según la consigna
original, sin exigir como condición adicional un hash de indexación.

**B.4: cumplido. Pendientes obligatorios de B.1–B.4: ninguno.**
La revisión visual y hashes se guardan en
[revision_capturas_finales.json](revision_capturas_finales.json).
No se ejecutaron nuevas pruebas ni llamadas al pipeline/API, no se implementó C
y no se hizo commit ni push.
