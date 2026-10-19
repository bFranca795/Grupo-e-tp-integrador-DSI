# Protocolo fijado antes de observar la comparación

Autorización: dataset aprobado por el usuario el 18/10/2026. No cambiar corpus, referencias, preguntas, hechos ni pipelines. Validar manifiesto 17/35 antes de toda fase y después de generación.

## Aplicabilidad

- Conservar todo score finito devuelto por RAGAS, incluso bajo o cero ante abstención correcta. No recortar valores desfavorables.
- Faithfulness: intentar para toda respuesta técnicamente válida, incluidos escapes y contextos vacíos. Si RAGAS no identifica afirmaciones y devuelve NaN, registrar `not_applicable` con valor null y motivo `no_claims`; no convertirlo en uno. Un fallo de API, parsing o timeout es `evaluation_error`, no ausencia semántica.
- Answer Relevancy: intentar para toda respuesta técnicamente válida, incluidos escapes y contextos vacíos. Conservar cero si lo determina RAGAS; una abstención puede ser correcta funcionalmente y poco relevante según esta métrica.
- Context Precision con referencia: no aplicable para E1/E2 porque carecen de una referencia factual positiva; no aplicable con lista de contextos vacía (no existe ranking cuya precisión medir). Fuera de eso ejecutar y conservar resultado bruto.
- Context Recall: no aplicable para E1/E2 porque no hay hechos positivos que recuperar. Para las otras preguntas ejecutar incluso con contextos vacíos: la referencia factual permite medir falta de cobertura, conservando el valor que devuelve RAGAS.
- `judge_error`, `execution_error` y cualquier guardrail técnico se distinguen de `insufficient_context`. No evaluar como respuesta exitosa una ejecución fallida; registrar cuatro estados `pipeline_error` con valores null y el motivo.
- Los resultados no finitos de otras métricas se registran como `evaluation_undefined`, con valor null y representación bruta, sin inventar su causa. Todos los resultados quedan en evidencias.
- Escapes E1/E2: auditar aparte estado técnico, texto completo y si coincide con la frase de abstención prevista, sin respuesta sustantiva inventada. Esta comprobación funcional no sustituye ninguna métrica RAGAS.

## Reintentos y reanudación

Máximo tres intentos por operación fallida únicamente ante errores transitorios identificables (429, 5xx, timeout, conexión), con esperas acotadas. Guardar cada intento fallido. No reintentar puntuaciones válidas, NaN, parsing ni puntuaciones bajas. Guardar por caso/variante y por métrica. Una reanudación reutiliza resultados terminales (también errores agotados), nunca vuelve a llamar para mejorar un score. Adaptadores sin reintentos internos adicionales. Contextos, prompts y respuestas de llamadas evaluadoras se guardan separados del pipeline, sin credenciales ni cabeceras.

## Comparación

Medias descriptivas por variante: solo valores finitos con estado `ok`, mostrando n. Deltas: calcular ambas medias sobre la intersección de IDs válidos para cada métrica y `rerank - basic`; mostrar pares e IDs excluidos con motivos. No comparar medias sobre conjuntos distintos. Determinar peor métrica avanzada con medias válidas, indicar empates y soporte. Una corrida de diez preguntas reutilizadas parcialmente y corpus simulado no acredita significancia ni generalización.

## Prueba mínima previa

Ejecutar las cuatro implementaciones con un caso factual mínimo y con una abstención/contextos vacíos, sin mezclar esos datos con la corrida final. Probar directamente las métricas incluso cuando el protocolo final determine no aplicabilidad, para registrar el comportamiento bruto de la integración.
