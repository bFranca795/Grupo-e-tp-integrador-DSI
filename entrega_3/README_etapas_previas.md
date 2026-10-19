# Estados históricos de preparación de Parte C

Este anexo conserva las instrucciones de etapas anteriores; el estado vigente y la instalación están en [README.md](README.md). Las menciones de aprobación pendiente o plan no ejecutado son históricas.

## Parte C — dataset preparado; ejecución pendiente de aprobación

El [dataset](evaluacion_ragas/golden_dataset.json), el [manifiesto del corpus](evaluacion_ragas/corpus_manifest.json), las [validaciones](evaluacion_ragas/validacion.json) y la [revisión semántica](evaluacion_ragas/REVISION.md) pertenecen a `evaluacion_ragas/`. No se ejecutaron pipelines ni RAGAS en esta etapa. B.1–B.4 permanecen completos; las menciones de pendientes B.4 en instrucciones anteriores describen requisitos de preparación histórica, no el estado vigente.

Validar localmente, sin red ni modelos, desde la raíz:

```powershell
.\.venv\Scripts\python.exe entrega_3/evaluacion_ragas/validar.py
```

`corpus.py` lee SQLite exclusivamente en modo de solo lectura; no usa el cliente Chroma. `preparar.py` conserva la construcción editorial reproducible del dataset y manifiesto. No volver a ejecutarlo para aceptar silenciosamente cambios de corpus: revisar primero cualquier diferencia detectada por `validar.py`. Los hashes fijan contenido y metadatos, no demuestran el origen de los embeddings. Las conclusiones semánticas requieren revisión humana.

### Plan posterior acordado (no ejecutado)

1. Tras la aprobación del dataset y autorización de ejecución, generar diez respuestas con `basic` y diez con `rerank`, usando exactamente las mismas preguntas, referencias y corpus efectivo 17/35 del manifiesto. Validar su integridad antes y después. No usar `compare` sin adaptación: contiene ocho casos históricos y tres variantes, no este conjunto.
2. Mantener generador `gemini-3.1-flash-lite`, temperatura 0.0, prompt de generación compartido y parámetros comunes iguales, registrando configuración, versiones y hashes de código/prompt. Preservar avanzado: chunking 500/100, hasta ocho candidatos, sin corte previo por distancia, relevancia mínima 0.5 y hasta cuatro seleccionados. Conservar diferencias propias de recuperación del básico documentadas en B.
3. Guardar resultados del pipeline en `entrega_3/evidencias/ragas/`, separados de llamadas y resultados del evaluador. Registrar por caso pregunta, respuesta, referencias, contexto realmente enviado, variante, errores, estado, configuración y uso disponible. En rerank usar `sources` efectivamente suministradas al generador, no los ocho candidatos ni seleccionados descartados por un guardrail.
4. Evaluar Faithfulness, Answer Relevancy, Context Precision y Context Recall con RAGAS. Fijar y registrar versión, implementación de cada métrica, modelo evaluador, embeddings evaluadores y configuración idénticos en ambas variantes antes de ejecutar. Su elección concreta queda pendiente; no inventar resultados ni confundir juez de reranking con evaluador RAGAS.
5. Conservar errores y motivos de no aplicabilidad, especialmente escapes sin referencia factual y contextos vacíos. Mantener valores ausentes como null con motivo, sin reemplazarlos por cero o uno. Reportar todos los casos, incluidos los fallidos.
6. Conservar individuales, agregados, configuración y llamadas del evaluador. Para cada métrica, mostrar medias, cantidades válidas y delta `rerank - basic` sobre las mismas preguntas con valores válidos en ambas variantes; explicitar denominadores y casos no comparables. Si se presentan medias sobre todas las observaciones válidas de cada variante, distinguirlas del agregado pareado usado para los deltas.
7. Mantener preguntas y referencias congeladas y no descartar casos para fabricar una mejora. Si ninguna métrica mejora, mostrarlo y diagnosticarlo para decidir el siguiente paso. Identificar la peor métrica avanzada, documentar su soporte y proponer una mitigación técnica concreta, sin implementarla automáticamente. C1 requiere cinco chunks de respaldo para la referencia editorial completa frente al máximo de cuatro del avanzado: conservar y analizar esta limitación.

El informe de esta entrega es `entrega_3/informe.md`: C.3 contendrá solo comparación, deltas y explicación; C.4, diagnóstico y propuesta. No agregar C.1/C.2 ni modificar `informe.md` de la raíz.

## Parte C — evaluación autorizada y reanudable

El usuario aprobó el golden dataset el 18/10/2026. El protocolo de aplicabilidad se fijó antes de observar la comparación en [PROTOCOLO.md](evaluacion_ragas/PROTOCOLO.md). La selección de versión, adaptadores, compatibilidad con Python 3.14 y documentación oficial están en [INTEGRACION.md](evaluacion_ragas/INTEGRACION.md). Los párrafos anteriores que dicen «ejecución pendiente» describen la etapa de preparación.

Dependencias: `ragas==0.2.15` y `langchain-community==0.3.31`, resueltas junto con las dependencias existentes en `uv.lock`. Reconstruir con `uv sync --locked`; no usar una instalación de RAGAS sin fijar versión. Evaluador y generador usan explícitamente `gemini-3.1-flash-lite`; embeddings evaluadores `gemini-embedding-001`, 768 dimensiones y tarea `SEMANTIC_SIMILARITY`. Las métricas son las implementaciones oficiales `Faithfulness`, `ResponseRelevancy` (Answer Relevancy, strictness 3), `LLMContextPrecisionWithReference` y `LLMContextRecall`.

Desde la raíz, con `GEMINI_API_KEY` en `.env`:

```powershell
.\.venv\Scripts\python.exe entrega_3/evaluacion_ragas/validar.py
.\.venv\Scripts\python.exe entrega_3/evaluacion_ragas/ejecutar.py smoke
.\.venv\Scripts\python.exe entrega_3/evaluacion_ragas/ejecutar.py generate
.\.venv\Scripts\python.exe entrega_3/evaluacion_ragas/ejecutar.py evaluate
.\.venv\Scripts\python.exe entrega_3/evaluacion_ragas/resumir.py
.\.venv\Scripts\python.exe entrega_3/evaluacion_ragas/verificar_resultados.py
.\.venv\Scripts\python.exe entrega_3/evaluacion_ragas/test_evaluacion.py -v
```

`smoke` guarda dos casos de integración fuera del dataset final en `evidencias/ragas/smoke_compatible/`. `smoke/` conserva el primer fallo local de event loop, anterior a las llamadas al proveedor. Las veinte ejecuciones reales están en `generacion/`; las métricas individuales en `evaluacion/`, con prompts/respuestas brutas, intentos, tiempos y uso del evaluador en subdirectorios `calls/`. `resumen/` contiene JSON, CSV y un documento con las veinte respuestas completas, sus contextos y fuentes, métricas, agregados y exclusiones. `configuracion.json` fija el experimento. Los JSON no incluyen secretos ni bases binarias.

`generate` y `evaluate` reanudan por archivos existentes, incluidos errores terminales. No borrar resultados para repetir selectivamente una puntuación. Se verifica el corpus aprobado antes y después de cada fase; una diferencia de corpus, dataset o configuración detiene la corrida. Las dos métricas evaluadoras concurrentes usan los mismos parámetros en ambas variantes. El pipeline se ejecuta con su configuración vigente sin cambios y con telemetría LangSmith desactivada para esta evaluación local; se mantienen las evidencias previas de B.

Los contextos RAGAS son exclusivamente `generator_contexts`, derivados de `sources` que el pipeline entregó al generador. Los candidatos y chunks del golden no se sustituyen por contexto recuperado. Los estados `insufficient_context` son escapes funcionales; `judge_error` y `execution_error` son errores técnicos. Las métricas ausentes conservan null y su motivo. Los escapes funcionales se revisan además en `resumen/revision_escapes.json`; la igualdad literal es un dato separado de la corrección semántica.

### Resultado vigente de la corrida autorizada

Las veinte respuestas se generaron sin errores del pipeline. RAGAS terminó con 54 valores válidos, 18 errores evaluadores (17 respuestas 429 y un timeout) y 8 no aplicables. La Parte C **no está completa**. Los deltas pareados disponibles mejoran Faithfulness, Answer Relevancy y Context Recall; Precision empata. Consultar [C.3 y C.4](informe.md#c3--comparación-básico-vs-avanzado) para soportes, sesgos y diagnóstico provisional. No repetir resultados terminales para buscar mejores scores; los faltantes requieren resolver el límite del proveedor y acordar una continuación acotada.

Para indexar juicios y auditar intentos, sin llamadas externas:

```powershell
.\.venv\Scripts\python.exe entrega_3/evaluacion_ragas/extraer_juicios.py
.\.venv\Scripts\python.exe entrega_3/evaluacion_ragas/auditar_llamadas.py
```

La verificación final comprobó 335 condiciones de integridad de evidencias además de las 152 del dataset. Aprobar esos contratos no significa que se hayan obtenido las 18 puntuaciones ausentes ni que los juicios semánticos sean infalibles. La reanudación de la generación conservó los veinte registros sin llamadas nuevas. El resumen contiene `c_complete=false`.

La reanudación posterior de `evaluate` reutilizó los 80 estados terminales, incluidos los errores agotados, sin modificar archivos ni hacer llamadas nuevas: [evidencia](evidencias/ragas/resumen/reanudacion_evaluacion.json). Los snapshots `evidencias/ragas/codigo_ejecutado/` coinciden byte a byte con los hashes registrados de los dos módulos cargados al iniciar la corrida. La versión actual añade lectura tolerante a BOM y mensajes de error redactados, sin cambiar parámetros, métricas o entradas.
