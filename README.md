# TP Integrador DSI — Grupo E

**Dominio elegido:** Legal Contable

**Integrantes:** Franca Bruno, Franzoni Clara, Rodrigo Martinez, Nicolas Lucas Grassi.

## Requisitos

- Python 3.14 o superior; la evaluación de Entrega 3 se probó con **CPython 3.14.8 en Windows 11 AMD64**. El registro previo de 3.14.7/Linux corresponde a etapas anteriores, no a la verificación del entorno RAGAS actual.
- Una API key de Google Gemini

## Instalación

Con `pip`:

```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Con `uv` (el entorno con el que se desarrolló):

```bash
uv sync --locked
```

## Variables de entorno

Copiar `.env.example` a `.env` y completar el valor:

```bash
cp .env.example .env
```

| Variable | Descripción |
| --- | --- |
| `GEMINI_API_KEY` | API key de Google Gemini. Se usa para la extracción estructurada y para generar los embeddings. |

El archivo `.env` está en `.gitignore` y nunca se commitea.

## Cómo correr

### Entrega 1 — extracción estructurada

```bash
python app.py        # procesa una consulta y devuelve el JSON validado
python lote.py       # corre el lote de casos de prueba
python a4.py         # comparación de tokens español vs inglés
```

### Entrega 2 — base de conocimiento vectorial

El pipeline es el punto de entrada único: carga la base cruda, normaliza las
	inconsistencias, purga los casi-duplicados, muestra el resultado por consola,
	genera `base_conocimiento_limpia.json`
y construye el índice FAISS.

Ejecución:

```
pipeline_vectorial.py  →  vector_db.py  →  búsqueda híbrida
```

| Script | Qué hace |
| --- | --- |
| `pipeline_vectorial.py` | Ejecuta el ETL, genera los embeddings de la base limpia y construye el índice FAISS |
| `vector_db.py` | Carga los documentos en ChromaDB persistente y expone el CLI de búsqueda |
| `etl_purga.py` | Comando independiente de ETL y purga; el pipeline lo reutiliza como módulo |

Los binarios que generan estos scripts (`*.index`, `chroma_db/`) están
ignorados: se reconstruyen corriendo el pipeline desde `base_conocimiento.json`.


## Entrega 3 — RAG básico LCEL y RAG avanzado

**Estado vigente:** A y B conservadas, B.1–B.4 completos y Parte C aprobada para la corrida documentada. Hay veinte respuestas, 72 puntuaciones RAGAS válidas, ocho no aplicables y cero errores pendientes. Los deltas pareados y las limitaciones del evaluador se detallan en C.3/C.4; no se afirma mejora general ni significancia estadística.

La instalación limpia de C se verificó con uv 0.13.1 en `.venv-repro`, conservando el entorno anterior. Para reproducirla, usar el lockfile y los comandos específicos de `entrega_3/README.md`; la instalación genérica con pip de esta guía no congela todas las dependencias transitivas.

Código y comandos: [`entrega_3/README.md`](entrega_3/README.md).
Informe consolidado, con evidencia histórica y resultados nuevos separados:
[`entrega_3/informe.md`](entrega_3/informe.md).

Los antiguos `retriever.py`, `Trazabilidad_de_fuentes.py` e
`informe_entrega3.md` se trasladaron a esa carpeta. Las entregas 1 y 2
permanecen en la raíz.

Guía histórica de reproducción de B.4: [comandos y trazabilidad](entrega_3/CONTINUAR_B4.md). B.4 ya está cumplido; ese archivo no declara un pendiente vigente.

## Agente inteligente — FastAPI y LangGraph

Asistente de un estudio contable para consultar documentación y registrar o
consultar tareas administrativas ficticias. No realiza pagos, declaraciones,
operaciones contables reales ni comunicaciones externas.

### Arquitectura y herramientas

```text
Cliente HTTP → FastAPI → AgenteContable (LangGraph ReAct) → Gemini
                              ↓ llamadas decididas por el modelo
                consultar_rag / consultar_solicitud_interna / crear_solicitud_interna
                              ↓
                ChromaDB existente / SQLite de solicitudes
                Memoria del grafo → SQLite de checkpoints
```

| Herramienta | Responsabilidad |
| --- | --- |
| `consultar_rag` | Reutiliza `entrega_3.rag_pipeline.pipeline.build_pipeline()` con variante `rerank`; conserva recuperación, embeddings, reranking, generación y abstenciones existentes. Inicialización diferida única por instancia; ejecución síncrona delegada a un hilo. |
| `consultar_solicitud_interna` | Sensor de solo lectura: consulta una solicitud ficticia por su identificador. |
| `crear_solicitud_interna` | Actuador: guarda una tarea de categoría `IVA`, `MONOTRIBUTO` o `TRAMITES`, con descripción, clave de idempotencia y referencia documental opcional. |

El grafo alterna nodos `modelo` y `herramientas`. Por defecto permite seis
invocaciones del modelo y ocho llamadas a herramientas por consulta; cada llamada
del lote cuenta individualmente. Los límites se configuran en el constructor de
`AgenteContable`, no mediante variables de entorno ni argumentos HTTP. Al agotarse
devuelve `limite`; las acciones ya realizadas no se deshacen.

Código principal en `src/grupo_e_tp_integrador_dsi/`: `api.py`, `agente.py`,
`modelo_agente.py`, `herramienta_rag.py`, `herramientas_solicitudes.py`,
`solicitudes.py`, `seguridad.py`, `observabilidad.py`, `metricas.py` y `trazabilidad.py`.

### Instalación y configuración del agente

Python declarado: **≥3.14** (`.python-version`: `3.14`). Las verificaciones locales
se realizaron con CPython **3.14.8**; no se afirma compatibilidad probada con todas
las versiones posteriores. Dependencias principales: LangGraph 1.2.20,
langgraph-checkpoint 4.3.1, langgraph-checkpoint-sqlite 3.1.3, aiosqlite 0.22.1,
FastAPI 0.162.2 y Uvicorn 0.54.0. `uv.lock` fija también las transitivas;
`requirements.txt` congela dependencias directas y pip resuelve las transitivas.

Desde la raíz, en PowerShell, instalación recomendada:

```powershell
$uvAgente = if (Test-Path .\.tools\bin\uv.exe) { (Resolve-Path .\.tools\bin\uv.exe).Path } else { 'uv' }
& $uvAgente sync --locked --group dev --python 3.14
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
```

Requiere uv instalado: en una copia nueva debe estar disponible en `PATH`. En este
workspace está en `.tools/bin/uv.exe`, que no se distribuye por Git. El bloque
selecciona esa copia si existe. No asumir que `python` o `py -3.14` apuntan a 3.14:
el Python del `PATH` local es 3.11 y el launcher no registra una instalación 3.14.

Para la alternativa pip de la instalación general, ejecutar la creación del entorno
con un intérprete Python 3.14 comprobado; después usar
`.\.venv\Scripts\python.exe -m pip install -r requirements.txt`.

Completar `.env` localmente, sin publicarlo. La configuración compartida del RAG
carga ese archivo desde la raíz mediante `python-dotenv`, sin sobrescribir las
variables ya presentes en el proceso.

| Variable | Uso |
| --- | --- |
| `GEMINI_API_KEY` | Necesaria para las consultas reales al modelo `gemini-3.1-flash-lite` y los componentes Gemini del RAG. `/health` no comprueba la clave. |
| `LANGSMITH_TRACING` | Opcional; usar `false` para desactivar y `true` para habilitar las trazas acotadas del agente. Vacía también desactiva. |
| `LANGSMITH_API_KEY` | Credencial de LangSmith si se habilita tracing remoto. |
| `LANGSMITH_PROJECT` | Proyecto opcional; por defecto `agente-contable`. |
| `LANGSMITH_ENDPOINT` | Endpoint opcional del SDK LangSmith. Dejar vacío salvo configuración específica. |

Se admite `LANGCHAIN_TRACING_V2` como alias si `LANGSMITH_TRACING` no está definida;
esta última tiene prioridad. No hay variables implementadas para cambiar las rutas
SQLite o ChromaDB: los tests inyectan recursos mediante interfaces internas.

Las consultas documentales requieren `chroma_db/` con las colecciones existentes
`estudio_contable` y `estudio_contable_chunks`; la variante utilizada consulta esta
última. Estos artefactos están excluidos de Git y no se distribuyen al clonar.
Obtener una copia autorizada de la base preparada o consultar el procedimiento de
[Entrega 3](entrega_3/README.md). Arrancar la API no reconstruye embeddings ni
colecciones. Sin la colección necesaria, una consulta documental puede devolver
un error controlado aunque `/health` responda correctamente.

### Ejecutar la API

Desde la raíz, con el entorno creado por uv:

```powershell
& $uvAgente run --locked python -m uvicorn grupo_e_tp_integrador_dsi.api:app --app-dir src --host 127.0.0.1 --port 8000 --workers 1
```

En la misma sesión donde se definió `$uvAgente`. Con instalación pip, sustituir
`& $uvAgente run --locked python` por
`.\.venv\Scripts\python.exe`. Para el entorno local de desarrollo existente:

```powershell
.\.tools\env-agente\Scripts\python.exe -m uvicorn grupo_e_tp_integrador_dsi.api:app --app-dir src --host 127.0.0.1 --port 8000 --workers 1
```

`--app-dir src` resuelve el paquete sin configurar `PYTHONPATH`. El lifespan abre
una única instancia del agente, la guarda en `app.state.agente` y cierra sus
recursos al detener el servidor. Importar `api.py` no abre SQLite ni modelos.
Documentación interactiva local: `http://127.0.0.1:8000/docs`.

### Endpoints y ejemplos sintéticos

Los siguientes JSON ilustran los contratos; las respuestas generadas, tiempos e
identificadores dependen de cada ejecución. No son evidencia de una llamada real.

**GET `/health`**, HTTP 200:

```json
{"status":"ok","service":"agente-contable"}
```

Indica que la aplicación atiende HTTP; no ejecuta herramientas ni certifica la
disponibilidad de Gemini, ChromaDB o LangSmith.

**POST `/consultar`**. Solicitud:

```json
{"thread_id":"usuario-demo-001","pregunta":"Hola, ¿qué podés hacer?"}
```

Respuesta HTTP 200 de ejemplo:

```json
{"thread_id":"usuario-demo-001","resultado":"finalizada","respuesta":"Puedo consultar documentación del estudio y gestionar tareas administrativas ficticias."}
```

Los resultados públicos son `finalizada`, `sin_evidencia`, `requiere_vinculacion`,
`limite` y `error`. Un resultado controlado `error` también puede llegar con HTTP
200; una excepción inesperada de la API produce HTTP 500 genérico.

Ejemplo ejecutable con cliente PowerShell:

```powershell
$consultaDemo = @{ thread_id = 'usuario-demo-001'; pregunta = 'Hola' } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri 'http://127.0.0.1:8000/consultar' -ContentType 'application/json; charset=utf-8' -Body $consultaDemo
Invoke-RestMethod 'http://127.0.0.1:8000/health'
Invoke-RestMethod 'http://127.0.0.1:8000/estado/usuario-demo-001'
Invoke-RestMethod 'http://127.0.0.1:8000/metricas'
```

`thread_id` es obligatorio, no vacío, de hasta 128 caracteres; usar identificadores
opacos sin datos personales. `pregunta` es obligatoria, no vacía y de hasta 2000
caracteres Unicode. Se rechazan tipos incorrectos y campos adicionales.

HTTP 422 de ejemplo ante manipulación explícita de instrucciones:

```json
{"detail":{"motivo":"prompt_injection"}}
```

Otros motivos son `entrada_vacia`, `longitud_excedida`, `unicode_invalido`,
`tipo_invalido` y `estructura_invalida`, según la capa que rechace la entrada.
Los defectos estructurales tienen prioridad si coinciden con errores de contenido.
Las respuestas de error no reflejan la pregunta ni excepciones internas.

**GET `/estado/{thread_id}`**, HTTP 200. Tras un intercambio simple de dos mensajes:

```json
{"thread_id":"usuario-demo-001","existe":true,"cantidad_mensajes":2,"ultimo_resultado":"finalizada"}
```

Para un hilo inexistente:

```json
{"thread_id":"usuario-inexistente","existe":false,"cantidad_mensajes":0,"ultimo_resultado":null}
```

Solo lee el checkpoint; no ejecuta Gemini ni herramientas. La cantidad incluye
mensajes internos de herramientas cuando existen. `ultimo_resultado` procede del
resultado público persistido y es `null` si no hay una estructura confiable. Un ID
inválido devuelve 422 con `estructura_invalida`, sin reflejar el identificador.

**GET `/metricas`**, HTTP 200. Snapshot inicial:

```json
{
  "consultas_recibidas": 0,
  "consultas_completadas": 0,
  "errores": 0,
  "consultas_por_resultado": {"finalizada":0,"sin_evidencia":0,"requiere_vinculacion":0,"limite":0,"error":0},
  "latencia_promedio_ms": 0.0,
  "latencia_p95_ms": 0.0,
  "ejecuciones_herramientas": 0,
  "herramientas_por_nombre": {"consultar_rag":0,"consultar_solicitud_interna":0,"crear_solicitud_interna":0},
  "bloqueos_seguridad": 0
}
```

Consultar métricas no cambia contadores. Si el registro falla, devuelve HTTP 503
genérico. Es un endpoint administrativo **sin protección de acceso**.

### Persistencia y concurrencia

- `data/agente/checkpoints.sqlite`: historial y estado LangGraph, identificado por `thread_id`.
- `data/agente/solicitudes.sqlite`: registro de tareas ficticias; se crea al registrar la primera.
- `chroma_db/`: conocimiento vectorial de Entrega 3, separado de ambas bases SQLite.

Las rutas se resuelven desde la raíz del proyecto. Las bases y tablas necesarias
se crean automáticamente al utilizar sus componentes; ChromaDB debe estar
preparada. Conservar los archivos SQLite permite recuperar conversaciones tras
reiniciar el servidor. Reutilizar un `thread_id` continúa su historial; otro ID
separa la conversación, pero **no constituye una autorización**.

La API serializa consultas y lecturas de estado del mismo hilo; permite progreso
concurrente de hilos distintos. La coordinación funciona únicamente dentro de un
proceso: ejecutar localmente con **un worker**.

### Logs, métricas y LangSmith

Los logs propios usan `logging` estándar y JSON con timestamp UTC, nivel, evento
y, cuando corresponde, ID de hilo enmascarado, duración y resultado público. No
incluyen preguntas, respuestas, argumentos completos, documentos ni excepciones
crudas. Los logs de Uvicorn y terceros son independientes.

Cada POST recibido cuenta una vez, incluidos los 422. Solo las respuestas HTTP
200 con resultado público cuentan como completadas. HTTP 5xx y resultado público
`error` incrementan errores una vez. Un rechazo de seguridad incrementa bloqueos,
sin completar ni registrar error; un 422 estructural no incrementa bloqueos.
Las herramientas se cuentan individualmente. Las latencias usan reloj monotónico
e incluyen espera por hilo y ejecución para consultas aceptadas, también fallidas;
excluyen rechazos previos. P95 es el rango más próximo sobre muestras reales:
`sorted(muestras)[ceil(0.95*n)-1]`, o cero si no hay muestras.

El tracing del agente es opt-in y publica nombres de etapas, selección de
herramientas, resultados públicos, duraciones y tokens realmente informados
(entrada, salida, total). Suprime el tracing automático de payloads durante la
consulta y asocia las llamadas internas del RAG mediante callbacks.
**Ejecutar el RAG directamente fuera del agente no aplica esta protección ni
garantiza esa asociación**; revisar la configuración de tracing antes de hacerlo.

Como evidencia histórica **proporcionada por el usuario**, existió una prueba real
exitosa previa de LangSmith con **11 etapas verificadas, 4 llamadas LLM, 4.764 tokens
de entrada, 1.170 de salida y 5.934 totales**. No se repitió durante la auditoría
final ni durante esta actualización documental. Los tests locales de trazabilidad
usan dobles y no sustituyen la verificación remota. Los costos que calcule LangSmith
dependen de sus precios configurados y **no equivalen a facturación confirmada**.

### Seguridad y limitaciones conocidas

Antes del agente se aplican dos validadores determinísticos: longitud/contenido y
patrones explícitos de prompt injection. Los bloqueos devuelven 422 sin ejecutar
agente, herramientas ni modificar checkpoints. No se utiliza Gemini para decidir
estos rechazos. La detección es heurística: citas de ataques pueden causar falsos
positivos; paráfrasis, codificación e instrucciones indirectas pueden evadirla.

La respuesta textual HTTP se filtra para ocultar emails, teléfonos argentinos y
CUIT/CUIL. Se prioriza CUIT frente a teléfono y no se exige dígito verificador
válido para ocultar identificadores reconocibles. El filtro no certifica ausencia
de PII: números ambiguos, formatos no cubiertos o identificadores mal rotulados
pueden no detectarse. Si falla, la API responde 500 sin publicar texto sin filtrar.

**Los checkpoints conservan contenido original**: el enmascaramiento de salida
se limita a `respuesta` HTTP y no modifica historial, argumentos ni resultados
internos. El ID de hilo se conserva en las respuestas; no usar PII como ID.

El sistema está diseñado para demostración local, **no para exposición pública**:
no tiene autenticación ni autorización por conversación; `/metricas` tampoco está
protegido. Las métricas viven en memoria, se reinician con el proceso y mantienen
las muestras de latencia sin límite. Proteger archivos, acceso a red y retención
de datos requiere decisiones adicionales antes de un despliegue público.

La solicitud administrativa y el checkpoint se confirman en transacciones
independientes. La misma clave con el mismo contenido no duplica; con contenido
distinto devuelve conflicto. Si una acción se guarda y luego falla el checkpoint,
un reintento con **otra clave** puede duplicarla: no hay garantía transaccional
de ejecución exactamente una vez entre ambas bases.

### Tests locales sin proveedores reales

Desde la raíz, PowerShell; con el entorno local existente:

```powershell
$env:PYTHONPATH = (Join-Path (Get-Location) 'src') + ';' + (Get-Location).Path
$env:LANGSMITH_TRACING = 'false'
$env:LANGCHAIN_TRACING_V2 = 'false'
.\.tools\env-agente\Scripts\python.exe -B -m unittest discover -s tests -q
```

Para una instalación nueva, sustituir el ejecutable por
`.\.venv\Scripts\python.exe` (pip) o `& $uvAgente run --locked python` (uv,
tras definir `$uvAgente` como en instalación).
La suite utiliza modelos y clientes simulados, SQLite temporal y no consume Gemini
ni LangSmith reales. Incluye contratos HTTP, persistencia en nuevo proceso,
idempotencia, concurrencia, observabilidad y seguridad.

El entregable de seguridad es **`security_tests.py`**, con cinco pruebas que
reutilizan casos de `tests/test_seguridad.py` y `tests/test_seguridad_api.py`.
Pytest **9.2.0** está declarado en el grupo de desarrollo `dev` de `pyproject.toml`
y fijado con sus dependencias en `uv.lock`; no es una dependencia de producción.
Tras definir `$uvAgente` como en instalación, preparar el entorno de evaluación:

```powershell
& $uvAgente sync --locked --group dev --python 3.14
$env:PYTHONPATH = (Join-Path (Get-Location) 'src') + ';' + (Get-Location).Path
$env:LANGSMITH_TRACING = 'false'
$env:LANGCHAIN_TRACING_V2 = 'false'
$env:PYTHON_DOTENV_DISABLED = '1'
.\.venv\Scripts\python.exe -B -m pytest security_tests.py -v
.\.venv\Scripts\python.exe -B -m pytest tests security_tests.py -q
```

`PYTHON_DOTENV_DISABLED=1` impide cargar `.env` durante la evaluación aislada.
Para el entorno local previo puede sustituirse el ejecutable por
`.\.tools\env-agente\Scripts\python.exe`, siempre que tenga instalado el grupo de
testing. El nombre `security_tests.py` no coincide con el descubrimiento estándar
de pytest: incluirlo explícitamente en la suite conjunta.

Conteos de referencia: **228 tests anteriores**, **5 casos entregables** y
**233 casos en la suite conjunta**. Los subtests reutilizados no se suman otra vez.
Cada evaluación debe confirmar el resultado mediante una nueva ejecución.

### Advertencias conocidas del entorno de evaluación

Pytest muestra 15 advertencias de deprecación de dependencias externas en Python
3.14.8, sin fallos asociados en las verificaciones realizadas:

| Origen | Cantidad observada | Aviso |
| --- | ---: | --- |
| `langsmith/_internal/_beta_decorator.py` | 13 | `asyncio.iscoroutinefunction` se retirará en Python 3.16; recomienda `inspect.iscoroutinefunction`. |
| `google/genai/types.py` | 1 | `_UnionGenericAlias` se retirará en Python 3.17. |
| `chromadb/telemetry/opentelemetry/__init__.py` | 1 | Mismo uso de `asyncio.iscoroutinefunction`. |

No se modificaron bibliotecas de terceros ni se ocultaron estos avisos. Su número
puede variar con el orden de importación o futuras versiones. uv 0.13.1 también
avisa que su versión difiere del rango de `uv_build` declarado como backend; la
instalación usa el backend resuelto por ese rango y la construcción se verificó
correctamente, sin cambiar el pin.

### Evidencia de reproducibilidad de la entrega

En la auditoría 5.5 se creó un entorno vacío independiente con Python 3.14.8 y
`uv sync --locked --group dev`, usando la caché local sin red. Se instalaron 139
paquetes y el proyecto; `uv pip check` confirmó compatibilidad y se importaron los
módulos principales. No se copió `.env`; su carga se desactivó. Las versiones
compartidas con el entorno principal se mantuvieron sin cambios.

En ese entorno pasaron **5 tests entregables**, la **suite conjunta de 233 casos**
y **2 tests específicos de importación y configuración Uvicorn**. Las 15
advertencias descritas arriba siguieron visibles.

También se inició Uvicorn como proceso independiente en `127.0.0.1`, con un worker,
agente y checkpoints SQLite temporales y proveedores externos bloqueados. Un
cliente HTTP independiente de la aplicación, basado en `urllib`, verificó:

| Comprobación HTTP real | Resultado |
| --- | --- |
| `GET /health` | 200, contrato esperado |
| `GET /metricas` | 200, snapshot inicial |
| `POST /consultar`, injection sintética | 422, `prompt_injection` |
| `POST /consultar`, JSON inválido | 422, `estructura_invalida` |
| `GET /estado/ausente-demo` | 200, hilo inexistente |

Tras los dos POST: dos consultas recibidas, un bloqueo, cero completadas, errores
y herramientas. El servidor y los recursos se cerraron cooperativamente. Se
comprobó igualdad de hashes de los archivos originales de ChromaDB y persistencia
antes y después. El lanzador y el entorno temporales se retiraron tras la prueba.
No se ejecutaron consultas válidas con Gemini ni verificaciones remotas nuevas
de LangSmith. Esta prueba HTTP no sustituye la evidencia histórica de consumo.
