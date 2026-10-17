# Entrega 3 — ejecución y revisión

**Estado de la entrega:** B.1–B.3 están implementados y validados en los casos
documentados. Esto no constituye una mejora general ni una evaluación RAGAS.
**B.4 queda pendiente de ejecución y verificación con las credenciales del
compañero**: todavía no hay una captura ni enlace de traza real verificada.

Continuación en otra máquina: [CONTINUAR_B4.md](CONTINUAR_B4.md).

El entorno `.venv` de esta máquina ya está preparado con Python 3.14 y las
dependencias del lockfile. Para reconstruirlo desde cero, usar `uv sync --locked`
con uv instalado. Si no está disponible, instalarlo con
`python -m pip install --user uv` y usar `python -m uv sync --locked`.

Desde la raíz del repositorio:

```powershell
.\.venv\Scripts\python.exe -m unittest entrega_3.rag_pipeline.test_pipeline -v
```

El único secreto obligatorio es `GEMINI_API_KEY` en el `.env` de la raíz.
Los comandos resuelven la persistencia desde la ubicación del proyecto.
No se necesita activar el entorno en PowerShell.

## Preparar y conservar la base

El básico abre `chroma_db`, colección `estudio_contable`, creada en Entrega 2.
No la crea ni la reemplaza automáticamente. Si no existe, ejecutar desde la raíz
`pipeline_vectorial.py` y `vector_db.py` de la Entrega 2. Este último simula un
cambio de estado sobre DOC-003: esa modificación forma parte del corpus efectivo.
Las ejecuciones de Entrega 3 no modifican esa colección.

```powershell
.\.venv\Scripts\python.exe -m entrega_3.rag_pipeline index --output entrega_3/evidencias/nueva_ejecucion/indexacion.json
```

Esto toma textos y metadatos de la colección efectiva, sanitiza la cola de
preguntas coloquiales heredada de A y aplica `RecursiveCharacterTextSplitter`
con tamaño 500, solapamiento máximo 100 y longitud en caracteres. Los separadores
pueden producir solapamientos menores a 100; no se promete un overlap exacto.
Se conserva cada metadato y se agregan `parent_id`, `chunk_id`, `chunk_index` y
`start_index`. Los IDs incluyen padre, posición y hash de contenido.
Los embeddings usan `gemini-embedding-001`, dimensión 768, documentos con
`RETRIEVAL_DOCUMENT` y consultas con `RETRIEVAL_QUERY`, igual que la base anterior.

La reconstrucción hace upsert de los IDs deterministas y elimina únicamente
chunks obsoletos de `estudio_contable_chunks`. Los embeddings se calculan antes
de escribir para no vaciar la colección ante un error de API. No se promete
atomicidad de toda la reconstrucción: ejecutar sin consultas concurrentes.

## Ejecutar y comparar

```powershell
.\.venv\Scripts\python.exe -m entrega_3.rag_pipeline ask --variant basic --question "¿Qué papeles necesito para darme de alta en Monotributo?"
.\.venv\Scripts\python.exe -m entrega_3.rag_pipeline ask --variant chunks --question "¿Qué papeles necesito para darme de alta en Monotributo?"
.\.venv\Scripts\python.exe -m entrega_3.rag_pipeline ask --variant rerank --question "¿Qué papeles necesito para darme de alta en Monotributo?"
.\.venv\Scripts\python.exe -m entrega_3.rag_pipeline compare --output entrega_3/evidencias/nueva_ejecucion/comparacion.json
.\.venv\Scripts\python.exe -m entrega_3.trazabilidad_de_fuentes
```

`compare` usa ocho preguntas fijas, cada una en las tres variantes, y guarda
progresivamente resultados o errores reales. Se pueden seleccionar casos con
`--case factual --case b1_compuesta`. No sobrescribir evidencia revisada sin
cambiar el nombre de `--output` si se desea conservarla.

Para ejecutar desde otro directorio, usar rutas absolutas al intérprete y a
`entrega_3/run.py`; admite los mismos argumentos. Ejemplo desde esta máquina:

```powershell
& 'C:\Users\Usuario\Downloads\TP_DSI_GRUPOE\.venv\Scripts\python.exe' 'C:\Users\Usuario\Downloads\TP_DSI_GRUPOE\entrega_3\run.py' ask --variant basic --question '¿Cuándo vence el IVA?'
```

Modelo compartido: `gemini-3.1-flash-lite`, temperatura 0.0, prompt de generación
idéntico. Básico y chunks usan top-3 y distancia máxima 0.28. Reranking recupera
hasta 8 sin corte duro previo por distancia y permite seleccionar hasta 4 con score mínimo
0.5. El máximo predeterminado del avanzado es 4: ejecutar `ask --variant rerank`
sin `--selected` o usar `Settings(variant="rerank")`. Puede configurarse entre
1 y 4 con `--selected`. Básico y chunks conservan sus valores anteriores.
No es una cuota: puede seleccionar menos o ninguno. El juez valora evidencia útil para alguna parte de la pregunta; no exige que
cada chunk responda toda la consulta. `--max-distance` y el campo de configuración
`max_distance` solo se aplican a básico y chunks; en reranking el límite efectivo
es `None`. Ajustables por CLI:
`--candidates`, `--selected`, `--min-score`, `--max-distance` y `--filters` (JSON
con filtros de igualdad). La API Python conserva filtro por categoría y activos.
Cambiar parámetros al comparar requiere aplicarlos a todas las variantes;
la selección de documentos y el fraccionamiento son las diferencias evaluadas.

La salida separa `candidates`, `selected` y `sources`. `sources` coincide con los
fragmentos entregados al generador; el historial de recuperación no se presenta
como fundamento de la respuesta. Para consultas de estado con CUIT, una validación
común exige que ese identificador esté explícitamente vinculado en texto o metadatos.
Si falta, conserva los seleccionados para auditoría pero no llama al generador y
`sources` queda vacío (`insufficient_client_binding`). Es una defensa puntual;
no implementa autenticación ni reemplaza un sistema de autorización de clientes.
Si no hay contexto útil, se devuelve la frase
`No poseo información suficiente en la base de conocimiento para responder esa consulta.`
Si el juez falla, se registra `judge_error`, tipo de error y política
`fail_closed_no_generation`; no se sustituye por un ranking semántico fingido.
`status=ok` señala que la ejecución técnica terminó, no que la respuesta sea completa o correcta.
Los errores de recuperación/generación se propagan en `ask` y se registran como
`execution_error` en `compare`.

## LangSmith (B.4)

La instrumentación LCEL ya separa recuperación, reranking, juez, generación y
respuesta/fuentes. Configurar en `.env` las variables de `.env.example`:

```dotenv
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=<clave de tu cuenta>
LANGSMITH_PROJECT=grupo-e-entrega-3
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
```

Usar el endpoint regional que corresponda a la cuenta. No compartir el `.env`.
Luego ejecutar `ask --variant rerank` con una consulta que recupere candidatos,
abrir el proyecto en LangSmith y revisar `rag_rerank`: `recuperacion` muestra
candidatos, `reranking` seleccionados y motivos, `juez_relevancia`/`generacion`
contienen las llamadas al modelo, sus tiempos y uso reportado. Los tags `judge`
y `generator` distinguen roles. `usage` del JSON también registra ambos por
separado. Los campos ausentes quedan en null; no se estiman tokens.

Guardar una captura real como `entrega_3/langsmith_trace.png` o agregar al informe
un enlace accesible para el revisor. Revisar que la captura o el enlace no
expongan secretos antes de compartirlos. **B.4 sigue pendiente sin esa evidencia**;
no se genera una captura ficticia ni se habilitan trazas remotas sin credenciales.

## Archivos y revisión

- `rag_pipeline/retriever.py`: retriever de A, con rutas desde la raíz.
- `rag_pipeline/model.py`: SDK Google GenAI adaptado a ChatModel de LangChain.
- `rag_pipeline/pipeline.py`: composición LCEL y salida con fuentes reales.
- `rag_pipeline/indexing.py`: colección derivada y verificación de corpus.
- `rag_pipeline/reranking.py`: schema y validación del juez.
- `rag_pipeline/test_pipeline.py`: pruebas locales, sin consumir la API.
- `evidencias/`: salidas reales de indexación, comparación y diagnóstico.
- `informe.md`: resultados y limitaciones; no implementa Parte C ni RAGAS.

Las pruebas locales usan modelos simulados únicamente para validar contratos,
fuentes y errores. No son evidencia de calidad del modelo ni reemplazan las
llamadas reales guardadas por separado.


## Configuración final del avanzado

- Splitter: 500 caracteres y solapamiento máximo de 100.
- Hasta 8 candidatos, con filtros de metadatos y sanitización conservados.
- Sin corte duro de distancia antes del juez.
- Puntuación mínima de relevancia: 0.5; aportes a alguna parte de la pregunta.
- Hasta 4 seleccionados por defecto, configurable de 1 a 4; puede seleccionar cero.

Ejecución habitual (no requiere `--selected`):

```powershell
.\.venv\Scripts\python.exe -m entrega_3.rag_pipeline ask --variant rerank --question "Soy empleador y responsable inscripto: ¿qué necesito para liquidar IVA, cuándo presento y pago esa declaración y qué obligaciones tengo con las cargas sociales?"
```

LangSmith: crear una clave en https://smith.langchain.com/ → Settings → API Keys
→ Create API Key. Para verificar también la traza mediante el SDK, usar un
Personal Access Token (PAT) de la cuenta con acceso al workspace. Una clave
Tracing Only permite enviar trazas pero no leerlas; con ese tipo de clave,
la verificación visual debe realizarse desde una sesión de la interfaz.
Guardar la clave solo en el `.env` de la raíz, junto con `LANGSMITH_TRACING=true`,
`LANGSMITH_PROJECT=grupo-e-entrega-3` y el endpoint de la región de la cuenta.
EE. UU.: `https://api.smith.langchain.com`; UE: `https://eu.api.smith.langchain.com`.
Si la clave abarca varios workspaces, configurar también `LANGSMITH_WORKSPACE_ID`.
Guía oficial: https://docs.langchain.com/langsmith/create-account-api-key
No enviar la clave al chat. B.4 seguirá pendiente hasta ejecutar y verificar una
traza real con candidatos, seleccionados, recuperación, juez, generación, tiempos
y uso reportado. Configurar las variables no equivale a completar B.4.

Los snapshots JSON de `evidencias/` son registros de auditoría del corpus simulado y sus resultados; no reemplazan ni incluyen la base ChromaDB o índices FAISS locales, que se reconstruyen y no se versionan. Los scripts auxiliares dentro de evidencias registran ensayos históricos; usar los comandos actuales de esta guía para la implementación final.
