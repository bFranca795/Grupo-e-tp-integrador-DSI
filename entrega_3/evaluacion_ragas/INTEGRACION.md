# Integración y versiones de evaluación

Se instalaron RAGAS **0.2.15** y `langchain-community==0.3.31`, con el resto de versiones resueltas en `uv.lock`. `uv pip check` verifica compatibilidad del grafo instalado. La evaluación se ejecutó con CPython 3.14.8 en Windows 11 AMD64 y uv 0.13.1. Se verificó una instalación nueva desde el lockfile en `.venv-repro`; ver el resultado y los límites en el README. Las once pruebas del pipeline continúan pasando.

RAGAS 0.4.3 fue la primera versión intentada. En ese intento uv compiló desde fuente `scikit-network==0.33.5` y falló por ausencia de Microsoft Visual C++ 14. No se conserva un inventario de wheels ni esto demuestra incompatibilidad de RAGAS 0.4.3 con Python 3.14. Se eligió 0.2.15, que no requiere esa dependencia. Esta versión importa el módulo VertexAI de `langchain-community`, que no estaba disponible en la instalación observada de 0.4.2; por eso se fija 0.3.31 sin alterar `langchain-core` del pipeline.

RAGAS 0.2.15 aplica `nest_asyncio` al importar su executor. Ese parche de notebooks produjo `Timeout should be used inside a task` en Python 3.14, antes de llamar al proveedor. Los ocho errores se conservan en `../evidencias/ragas/smoke/`. En este CLI con un único event loop se impide exclusivamente esa aplicación durante el import y se restaura la función inmediatamente. No se edita RAGAS ni su fórmula; se utilizan los métodos oficiales `single_turn_ascore` sobre el event loop nativo. La prueba real corregida queda en `smoke_compatible/` y no se mezcla con la evaluación final.

Los fragmentos terminales disponibles, la procedencia y los límites de la evidencia se detallan en [README](../README.md#problema-de-instalación-evidencia-y-solución). No se guardó el log terminal completo original en el repositorio.

## Implementaciones exactas

| Nombre del trabajo | Implementación RAGAS 0.2.15 | Entrada relevante |
|---|---|---|
| Faithfulness | `ragas.metrics.Faithfulness` | pregunta, respuesta, contextos reales |
| Answer Relevancy | `ragas.metrics.ResponseRelevancy`, nombre interno `answer_relevancy`, strictness 3 | pregunta, respuesta; genera tres preguntas inversas |
| Context Precision con referencia | `ragas.metrics.LLMContextPrecisionWithReference` | pregunta, respuesta de referencia aprobada, contextos reales |
| Context Recall | `ragas.metrics.LLMContextRecall` | pregunta, referencia aprobada, contextos reales |

Se implementan únicamente adaptadores de proveedor que heredan de `BaseRagasLLM` y `BaseRagasEmbeddings`, interfaces oficiales. Las métricas y sus prompts son de RAGAS, sin sustituirlos por heurísticas propias. Se desactivan reparaciones automáticas de JSON en los prompts (`retries_left=0`); parsing fallido queda como error técnico. Los únicos reintentos son hasta tres intentos de llamadas con fallos transitorios (429/5xx/timeout/conexión); el SDK y RunConfig no agregan intentos. No se repite ningún resultado válido para mejorar su puntuación.

Evaluador explícito: `gemini-3.1-flash-lite`, temperatura 0, máximo de salida 8192, JSON, timeout HTTP 120 segundos, timeout por métrica 180 segundos. Embeddings explícitos: `gemini-embedding-001`, 768 dimensiones, `SEMANTIC_SIMILARITY` tanto para la pregunta como para las preguntas inversas de Answer Relevancy. Son llamadas evaluadoras, separadas de los embeddings de recuperación. No se regeneran embeddings del corpus. No se usa una clave de OpenAI aunque algunas dependencias de RAGAS incluyan su SDK.

## Documentación oficial consultada

- [Personalización de modelos 0.2.15 e interfaces de adaptadores](https://docs.ragas.io/en/v0.2.15/howtos/customizations/customize_models/).
- [Faithfulness 0.2.15](https://docs.ragas.io/en/v0.2.15/concepts/metrics/available_metrics/faithfulness/).
- [Response Relevancy 0.2.15](https://docs.ragas.io/en/v0.2.15/concepts/metrics/available_metrics/answer_relevance/).
- [Context Precision con referencia 0.2.15](https://docs.ragas.io/en/v0.2.15/concepts/metrics/available_metrics/context_precision/).
- [Código oficial etiquetado de Context Recall](https://github.com/explodinggradients/ragas/blob/v0.2.15/src/ragas/metrics/_context_recall.py).

También se inspeccionaron las implementaciones instaladas para corroborar entradas, fórmulas, strictness y tratamiento de NaN. Los prompts de evaluación permanecen en inglés, con entradas en español; se conserva esa configuración idéntica para ambas variantes. La aleatoriedad residual del proveedor puede existir aun con temperatura cero.

## Datos auditables

`configuracion.json` fija hashes del dataset, manifiesto, protocolo, lockfile y código del pipeline; modelos, versiones y prompt generador compartido. Cada generación conserva respuesta, candidatos, seleccionados, fuentes y payload reconstruido exactamente con la misma expresión utilizada por el pipeline. Un generador no invocado queda con payload null y contextos vacíos. Las llamadas evaluadoras guardan prompt, respuesta bruta del SDK, uso disponible, timestamps, intentos y tiempos en directorios `calls/` separados. Nunca se guardan claves ni cabeceras HTTP.
