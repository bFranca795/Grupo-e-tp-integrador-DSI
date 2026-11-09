# Ficha técnica — Agente inteligente contable

## Identificación

| Campo | Descripción |
| --- | --- |
| Proyecto | TP Final Integrador DSI — Agente contable |
| Equipo | Grupo E |
| Integrantes | Franca Bruno, Franzoni Clara, Rodrigo Martinez, Nicolas Lucas Grassi. |
| Objetivo | Consultar documentación del estudio y registrar o consultar solicitudes administrativas ficticias con continuidad conversacional. |
| Estado | Implementado y probado para demostración local. No preparado para exposición pública. |
| Alcance excluido | Pagos, declaraciones fiscales, comunicaciones externas y operaciones contables reales. |

Fuentes: [README](README.md), [informe técnico](informe.md), [dependencias](requirements.txt), módulos de `src/grupo_e_tp_integrador_dsi/` y pruebas de `tests/`. Esta ficha sintetiza la implementación; los procedimientos de instalación y ejecución están en el README.

## Stack tecnológico

Versiones fijadas en `requirements.txt` y contrastadas con el entorno `.tools/env-agente`. El grafo completo de dependencias se conserva en `uv.lock`.

| Tecnología | Versión o identificación | Función |
| --- | --- | --- |
| Python | Declarado ≥3.14; probado 3.14.8 | Runtime de la aplicación y tests. |
| FastAPI | 0.162.2 | API REST, modelos HTTP y lifespan. |
| Uvicorn | 0.54.0 | Servidor ASGI, ejecución local con un worker. |
| LangGraph | 1.2.20 | Grafo ReAct y estado conversacional. |
| langgraph-checkpoint | 4.3.1 | Infraestructura de checkpoints. |
| langgraph-checkpoint-sqlite | 3.1.3 | `AsyncSqliteSaver` para memoria persistente. |
| LangChain Core | 1.6.12 | Mensajes, `StructuredTool`, esquemas y callbacks. |
| langchain-community | 0.3.31 | Dependencia existente del proyecto; no define el ciclo ReAct. |
| langchain-text-splitters | 1.1.3 | División documental en componentes del proyecto. |
| Gemini | `gemini-3.1-flash-lite` | Modelo predeterminado del agente y del RAG. Es un identificador de modelo, no una versión de paquete. |
| google-genai | 2.24.0 | SDK de Gemini y llamadas a funciones. |
| SQLite | 3.53.1 en el intérprete verificado | Persistencia local; la versión depende del runtime, no de un pin pip. |
| aiosqlite | 0.22.1 | Acceso asíncrono a SQLite. |
| ChromaDB | 1.5.9 | Base vectorial existente del RAG. |
| LangSmith | 0.14.11, SDK | Trazas opcionales y metadatos de consumo. |
| Pydantic | 2.13.5 | Contratos HTTP y argumentos de herramientas. |
| python-dotenv | 1.2.3 | Carga de configuración local compartida con el RAG. |
| pytest | 9.2.0, grupo de desarrollo `dev` | Evaluación del entregable `security_tests.py` y suite conjunta; no es dependencia de producción. |

Otras dependencias existentes: NumPy 2.5.3, tiktoken 0.14.0, faiss-cpu 1.15.1 y RAGAS 0.2.15. FAISS y RAGAS pertenecen a componentes o evaluaciones del proyecto; no reemplazan ChromaDB ni participan como herramientas del agente.

## Arquitectura

**Flujo:** cliente HTTP → FastAPI → validadores → LangGraph ReAct → Gemini y herramientas → filtro de salida HTTP.

- **API:** `api.crear_app()` mantiene una instancia de `AgenteContable` en `app.state.agente`. El lifespan abre y cierra recursos; importar el módulo no abre SQLite ni inicializa modelos externos.
- **Agente:** `agente.AgenteContable` alterna nodos `modelo` y `herramientas`. El modelo propone las llamadas y el grafo las ejecuta secuencialmente.
- **Tool calling:** `modelo_agente.GeminiAgente` registra declaraciones de funciones. El SDK no ejecuta funciones automáticamente; LangGraph controla sus efectos.
- **RAG:** reutiliza `entrega_3.rag_pipeline.pipeline.build_pipeline()` con variante `rerank`. El pipeline síncrono se ejecuta en un hilo, sin bloquear el event loop, y se inicializa una vez por instancia de herramienta.
- **Estado:** checkpoints, solicitudes y conocimiento vectorial permanecen separados.
- **Controles:** logs JSON, métricas por aplicación y trazas opt-in; validación previa al agente y enmascaramiento posterior.

Límites por consulta: **6 invocaciones del modelo y 8 llamadas a herramientas**, configurables en el constructor entre 1 y 50. Cada llamada de un lote cuenta individualmente. El agotamiento devuelve `limite`; no revierte acciones previas. El prompting del agente y de generación RAG es zero-shot, sin ejemplos demostrativos incorporados como few-shot.

## Endpoints

| Método | Ruta | Propósito | Respuesta o comportamiento |
| --- | --- | --- | --- |
| GET | `/health` | Salud HTTP de la aplicación. | 200: `status="ok"`, `service="agente-contable"`. No comprueba disponibilidad de Gemini o ChromaDB. |
| POST | `/consultar` | Ejecutar una consulta en un hilo. | Recibe `thread_id`, `pregunta`; devuelve `thread_id`, `resultado`, `respuesta`. 422 por entrada rechazada; 500 genérico ante fallo inesperado. |
| GET | `/estado/{thread_id}` | Leer resumen persistido sin ejecutar modelo ni herramientas. | 200: `thread_id`, `existe`, `cantidad_mensajes`, `ultimo_resultado`. Hilo inexistente: `false`, 0 y `null`; ID inválido: 422. |
| GET | `/metricas` | Consultar snapshot consistente del registro. | 200 con métricas agregadas; 503 genérico si el registro falla. No cambia contadores. |

`thread_id`: cadena obligatoria, no vacía, hasta 128 caracteres. `pregunta`: cadena obligatoria, no vacía, hasta 2000 caracteres. El modelo de solicitud prohíbe campos adicionales y tipos incorrectos.

Los resultados públicos del agente son `finalizada`, `sin_evidencia`, `requiere_vinculacion`, `limite` y `error`. Un `error` controlado puede llegar con HTTP 200. Los rechazos usan `detail.motivo`, sin reflejar el contenido recibido. `/estado` cuenta también mensajes internos de herramientas y devuelve `ultimo_resultado=null` si no existe un resultado público persistido confiable.

## Herramientas del agente

Son herramientas nativas `StructuredTool`, con esquema Pydantic y ejecución asíncrona mediante `.ainvoke()`. Las rutas de pruebas no se exponen al modelo.

| Nombre exacto | Tipo y entrada | Resultado y alcance |
| --- | --- | --- |
| `consultar_rag` | Retriever documental; `pregunta` no vacía de hasta 4000 caracteres en su esquema interno. La API limita la pregunta del usuario a 2000. | `respondida`, `sin_evidencia`, `requiere_vinculacion` o `error`, texto y hasta cuatro referencias. No devuelve chunks completos. |
| `consultar_solicitud_interna` | Sensor; `identificador`. | `encontrada` o `no_encontrada`, con datos públicos o ausencia controlada. SQLite en modo de solo lectura. |
| `crear_solicitud_interna` | Actuador; `categoria`, `descripcion`, `clave_idempotencia`, `id_documental` opcional. | `creada`, `existente` o `conflicto`; guarda exclusivamente tareas ficticias. |

El RAG conserva recuperación, embeddings, juez, generación y guardrails de Entrega 3. Usa `estudio_contable_chunks` dentro de `chroma_db/`, que debe estar preparada. La inicialización no reconstruye embeddings. Las abstenciones del RAG terminan la ejecución de forma controlada; no se completan con conocimiento libre del agente.

## Memoria y persistencia

| Recurso | Ruta | Uso |
| --- | --- | --- |
| Memoria del grafo | `data/agente/checkpoints.sqlite` | `AsyncSqliteSaver`, historial y estado por `thread_id`; recuperación después de cerrar y reabrir. |
| Solicitudes | `data/agente/solicitudes.sqlite` | UUID, categoría, descripción, clave de idempotencia, referencia opcional, fecha UTC y estado inicial `pendiente`. |
| Conocimiento | `chroma_db/` | Índice vectorial existente del RAG, separado de SQLite. |

Las rutas se resuelven desde la raíz. El almacenamiento administrativo admite `IVA`, `MONOTRIBUTO` y `TRAMITES`, descripción de hasta 200 caracteres y consultas SQL parametrizadas. La restricción única sobre la clave evita duplicados con el mismo contenido; reutilizarla con otro contenido devuelve conflicto.

No hay transacción común entre solicitud y checkpoint. Si la acción se confirma y luego falla la memoria, un reintento con otra clave puede duplicarla. No existe garantía de ejecución exactamente una vez. El bloqueo por `thread_id` coordina lectura y escritura dentro de un proceso; no proporciona autorización ni coordinación multiproceso.

## Observabilidad

| Recurso | Información disponible |
| --- | --- |
| Logs JSON | Timestamp UTC, nivel, evento, ID de hilo enmascarado cuando corresponde, duración y resultado público. Eventos de aplicación, consultas aceptadas, herramientas, errores y límites. |
| Métricas HTTP | `consultas_recibidas`, `consultas_completadas`, `errores`, `consultas_por_resultado`, `latencia_promedio_ms`, `latencia_p95_ms`, `ejecuciones_herramientas`, `herramientas_por_nombre`, `bloqueos_seguridad`. |
| Latencias | Reloj monotónico; promedio aritmético y p95 por rango más próximo: `sorted(muestras)[ceil(0.95*n)-1]`. Sin muestras: cero. Excluyen rechazos anteriores al agente. |
| LangSmith | Trazas acotadas de consulta, modelo, herramientas y etapas internas del RAG; tokens de entrada, salida y total solo cuando el proveedor los informa. |

Cada POST cuenta como recibido, incluso con 422. Las respuestas 200 con resultado público cuentan como completadas. HTTP 5xx o resultado público `error` incrementan errores una vez. Las herramientas se contabilizan individualmente; los bloqueos de seguridad no incrementan errores ni completadas. Las lecturas de `/metricas` no alteran el registro.

`LANGSMITH_TRACING=true` habilita trazas; `false` las desactiva. Se admiten proyecto y endpoint configurables, y el alias `LANGCHAIN_TRACING_V2` si la primera variable no existe. Durante la consulta del agente se suprime el tracing automático de payloads y se propaga un contexto acotado al RAG. Ejecutar el RAG directamente no garantiza esas protecciones ni su asociación con el agente. Los logs propios no publican preguntas, respuestas completas, argumentos ni errores crudos; los logs de terceros requieren revisión independiente.

## Seguridad

| Control | Comportamiento |
| --- | --- |
| `validar_entrada()` | Rechaza texto vacío, más de 2000 puntos de código o Unicode inválido. Se conservan las restricciones Pydantic. |
| `detectar_prompt_injection()` | Reconoce patrones explícitos en español e inglés con normalización de mayúsculas, acentos y espacios. No usa modelos ni bloquea solo palabras aisladas. |
| Rechazo HTTP | 422 con motivo controlado, antes de invocar al agente o modificar checkpoints. Defectos estructurales tienen prioridad si coinciden con contenido inválido. |
| `enmascarar_pii()` | Oculta email, teléfono argentino y CUIT/CUIL reconocibles en `respuesta` HTTP, incluidos estados controlados. Prioriza CUIT sobre teléfono y no exige checksum válido. |
| Fallo del filtro | 500 genérico; no se publica el texto sin filtrar y se contabiliza el error. |
| Bloqueos | Cada rechazo de seguridad suma exactamente uno a `bloqueos_seguridad`; JSON inválido o campos estructurales incorrectos no lo incrementan. |

El filtro conserva `thread_id` y `resultado`; deben usarse IDs opacos sin PII. No modifica checkpoints ni datos internos de herramientas. La protección de salida no equivale a protección del almacenamiento.

## Pruebas y resultados

La última ejecución de esta etapa aprobó **228 tests automatizados: PASS, cero FAIL**, en 36,583 segundos. Se ejecutó `python -B -m unittest discover -s tests -q` con el intérprete de `.tools/env-agente`, `src` y la raíz en `PYTHONPATH` y tracing desactivado. Se usan modelos guionados, clientes dobles, peticiones ASGI y SQLite temporal; el grafo y las operaciones de persistencia se ejecutan realmente en el entorno local.

| Escenario sintético | Prueba en `tests/test_agente.py` | Comprobación |
| --- | --- | --- |
| Consulta documental | `test_02_retriever` | Invoca RAG con pipeline doble. |
| Consultar solicitud | `test_03_sensor` | Obtiene estado sin cambiar la base temporal. |
| Registrar tarea ficticia | `test_04_actuador` | Persiste solicitud y permite consultarla. |
| Registrar y consultar | `test_05_multiples` | Encadena herramientas con el identificador generado. |

Estas pruebas verifican el circuito con modelo simulado, no la precisión de selección de Gemini real. Otras suites cubren reapertura en nuevo proceso, aislamiento, límites, concurrencia, contratos, idempotencia, métricas, trazas locales y seguridad.

El entregable raíz `security_tests.py` añade cinco casos reutilizando las pruebas de seguridad: la suite conjunta se ejecuta explícitamente con `pytest tests security_tests.py` y comprende 233 casos. El grupo de testing se instala con `uv sync --locked --group dev --python 3.14`.

**LangSmith histórico:** según la evidencia proporcionada por el usuario, una ejecución real previa verificó **11 etapas, 4 llamadas LLM y 5.934 tokens**: 4.764 de entrada y 1.170 de salida. No son promedios ni resultados repetidos durante esta etapa o la auditoría final. Los costos mostrados por LangSmith no equivalen a facturación confirmada.

Los antecedentes HTTP reales anteriores a esta documentación no disponen de un acta detallada en las fuentes revisadas; no se asignan aprobaciones individuales ni se confunden con los tests ASGI. Durante la redacción inicial de esta ficha, Gemini real, LangSmith remoto, Uvicorn real y nueva instalación limpia fueron **NOT RUN**.

**Actualización 5.5:** instalación limpia desde `uv.lock` con grupo `dev` aprobada, 139 paquetes compatibles; 5 tests entregables, 233 casos conjuntos y 2 tests específicos de importación/configuración PASS. Uvicorn independiente en `127.0.0.1` con un worker y SQLite temporal: `/health` y `/metricas` 200, injection y JSON inválido 422, estado inexistente 200. Se verificaron cierre y archivos originales sin cambios. Proveedores reales permanecieron sin ejecutar; detalles en el README.

## Limitaciones

| Restricción | Consecuencia |
| --- | --- |
| Sin autenticación ni autorización por conversación | Conocer el ID permite acceder al hilo; el aislamiento técnico no acredita identidad. |
| Un worker local | Los bloqueos no coordinan procesos o servidores diferentes. |
| Métricas en memoria | Se reinician y no se agregan entre procesos; las muestras de latencia se conservan sin límite. |
| Contenido original en checkpoints | Puede persistir PII aunque la respuesta HTTP esté enmascarada; falta una política integral de retención y acceso. |
| Seguridad heurística | Admite falsos positivos y negativos, ofuscaciones y formatos no cubiertos. |
| Commits separados | Riesgo de duplicación administrativa tras fallos si cambia la clave de idempotencia. |
| `/metricas` sin autenticación | Requiere restricción de acceso administrativo antes de publicación. |
| Tracing directo del RAG | Fuera del agente no hereda necesariamente su captura acotada. |

El sistema es una implementación académica local. La exposición pública requiere decisiones adicionales de autorización, privacidad, coordinación y operación.
