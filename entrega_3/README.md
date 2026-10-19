# Entrega 3 — instalación, reproducción y revisión

**Estado vigente:** A y B conservadas; B.1–B.4 completos. La instalación limpia en `.venv-repro` pasó sus comprobaciones. Se completaron exclusivamente las 18 métricas fallidas: **72 puntuaciones válidas, 8 no aplicables y 0 errores pendientes**. C.1–C.4 están cumplidos para esta corrida, con las limitaciones y anomalías del evaluador documentadas en el informe. No se regeneraron respuestas ni embeddings del corpus.

## Entorno realmente utilizado y alcance de la verificación

| Componente | Versión / configuración observada |
|---|---|
| Sistema operativo | Windows 11, versión de plataforma `Windows-11-10.0.26200-SP0` |
| Arquitectura | AMD64 / x86-64, intérprete de 64 bits |
| Python de la evaluación | **CPython 3.14.8**, compilación `MSC v.1944 64 bit (AMD64)` |
| Gestor | **uv 0.13.1**, build `62faed335`, target `x86_64-pc-windows-msvc` |
| RAGAS | **0.2.15** |
| SDK Gemini | `google-genai==2.24.0` |
| Interfaces LangChain | `langchain-core==1.6.12`, `langchain-community==0.3.31`, `langchain-openai==1.7.2` |
| Otras dependencias relevantes | `pydantic==2.13.5`, `numpy==2.5.3`, `chromadb==1.5.9`, `nest-asyncio==1.6.0` |

La versión histórica de Python está registrada en [configuracion.json](evidencias/ragas/configuracion.json): `python=3.14.8`. Las versiones instaladas se comprobaron localmente, al igual que la compatibilidad declarada del grafo con `uv pip check`, los imports y las pruebas locales. **Se verificó una instalación nueva de las dependencias desde `uv.lock` en `.venv-repro`, conservando `.venv`**, con CPython 3.14.8 ya disponible. Pasaron imports, grafo de dependencias, once pruebas del pipeline, cuatro de evaluación y cinco de continuación/identidad. [Evidencia de instalación limpia](evidencias/ragas/instalacion_limpia/resultado.json). No se probaron Linux, macOS, ARM64, otras versiones de Python ni una descarga nueva del intérprete.

`pyproject.toml` exige `requires-python = ">=3.14"`; `.python-version` indica `3.14` y `uv.lock` conserva ese requisito. Ya era así en el commit base `5a9b9b7`: **instalar RAGAS no cambió el requisito de Python del proyecto**. RAGAS 0.2.15 declara por separado `Requires-Python: >=3.9`; ese dato no reduce el requisito del TP ni demuestra que todas las combinaciones de dependencias funcionen. Para reproducir esta corrida, elegir explícitamente 3.14.8.

Modelos explícitos, sin defaults de otro proveedor:

- Generación básica/avanzada y juez de reranking: `gemini-3.1-flash-lite`, temperatura 0.
- Evaluador RAGAS: `gemini-3.1-flash-lite`, temperatura 0, salida máxima 8192 tokens; timeout HTTP de 120 s y timeout de métrica de 180 s.
- Recuperación e indexación: `gemini-embedding-001`, dimensión 768; tareas `RETRIEVAL_QUERY` y `RETRIEVAL_DOCUMENT`, respectivamente.
- Embeddings del evaluador: `gemini-embedding-001`, dimensión 768, tarea `SEMANTIC_SIMILARITY` en ambas variantes.

## Problema de instalación: evidencia y solución

No quedó guardado un log terminal completo de instalación dentro del repositorio. Los fragmentos exactos siguientes están disponibles en las salidas de herramientas de la sesión de trabajo; se transcriben identificando su procedencia, sin presentarlos como un archivo de log original:

```text
error: Failed to add dependencies
```

El intento de `uv add ragas --upgrade-package ragas` resolvió RAGAS 0.4.3 e intentó construir `scikit-network==0.33.5`. La salida de compilación terminó con esta línea:

```text
error: Microsoft Visual C++ 14.0 or greater is required. Get it with "Microsoft C++ Build Tools": https://visualstudio.microsoft.com/visual-cpp-build-tools/
```

La causa comprobada fue **la falta del compilador requerido para construir esa dependencia nativa en este entorno Windows/CPython 3.14**. El intento utilizó una distribución fuente; no se conserva un inventario de todos los wheels disponibles. Esto **no prueba que RAGAS 0.4.3 sea incompatible con Python 3.14** ni con otros sistemas. No se instalaron Build Tools para resolverlo.

Se eligió `ragas==0.2.15`, que no introduce esa dependencia, y se fijó en `pyproject.toml`, `requirements.txt` y `uv.lock`. Después se observó este error exacto de importación en la sesión:

```text
ModuleNotFoundError: No module named 'langchain_community.chat_models.vertexai'
```

RAGAS 0.2.15 importaba ese módulo y no estaba disponible con `langchain-community==0.4.2` instalado en ese intento. Se fijó **`langchain-community==0.3.31`**, con el que los imports funcionaron, conservando `langchain-core==1.6.12` del pipeline. No se atribuye aquí una incompatibilidad a todas las versiones de LangChain ni se afirma en qué versión histórica se eliminó el módulo.

Hubo además una adaptación de ejecución local, distinta del fallo del compilador: el parche de notebooks `nest_asyncio`, aplicado durante el import del executor de RAGAS 0.2.15, provocó en este CLI/Python 3.14.8:

```text
RuntimeError: Timeout should be used inside a task
```

El traceback exacto se vio en la sesión; los [ocho registros iniciales](evidencias/ragas/smoke/) guardan el tipo `RuntimeError`, sin el texto completo del traceback. [adaptadores.py](evaluacion_ragas/adaptadores.py) impide únicamente esa aplicación del parche durante el import y restaura la función inmediatamente. Se usa un solo event loop nativo y las interfaces oficiales `BaseRagasLLM` / `BaseRagasEmbeddings`, con el SDK `google-genai`. No se editan las fórmulas RAGAS. La [prueba mínima corregida](evidencias/ragas/smoke_compatible/) sí completó las cuatro métricas con llamadas reales, antes de la evaluación final. No se deduce una incompatibilidad general de RAGAS o de nest_asyncio con todos los usos de Python 3.14.

La solución aplicada fue, por tanto, **fijar versiones y adaptar el import del CLI**, no cambiar Python. Las dependencias adicionales incluyen SDKs de otros proveedores por transitividad, pero estos comandos no necesitan `OPENAI_API_KEY`. Ver [implementaciones y documentación oficial](evaluacion_ragas/INTEGRACION.md).

## Instalación en un entorno nuevo desde el lockfile

Ejecutar PowerShell desde la raíz del proyecto. Se necesita previamente un Python con `pip` para instalar el gestor; en la sesión se usó un Python 3.11 para ese bootstrap, separado del Python 3.14.8 que ejecuta el TP. Se requiere acceso a internet para descargar gestor, intérprete y paquetes. En una copia nueva, `.tools/` y `.venv-repro/` no deben existir; no se borra ni reutiliza `.venv`.

```powershell
python -m pip install --target .tools "uv==0.13.1"
$uv = Join-Path (Get-Location).Path '.tools\bin\uv.exe'
& $uv --version
& $uv --cache-dir .uv-cache python find --system 3.14.8
& $uv --cache-dir .uv-cache venv --python 3.14.8 .venv-repro
$env:UV_PROJECT_ENVIRONMENT = Join-Path (Get-Location).Path '.venv-repro'
& $uv --cache-dir .uv-cache sync --locked --python 3.14.8
$python = Join-Path $env:UV_PROJECT_ENVIRONMENT 'Scripts\python.exe'
& $python --version
& $uv --cache-dir .uv-cache pip check --python $python
& $uv --cache-dir .uv-cache lock --check --offline
```

En la comprobación real, `uv python install 3.14.8` encontró una restricción de permisos del sandbox al abrir el lock del runtime gestionado por usuario. No se instaló ni modificó el runtime: `uv venv` reutilizó CPython 3.14.8 existente y el `home` del nuevo entorno apunta a ese intérprete base, no a `.venv`. `--cache-dir .uv-cache` mantiene la caché de paquetes en el proyecto. Si no existe el intérprete, su descarga es un paso separado no probado aquí; no instalar herramientas globales ni modificar el sistema para resolverlo.

`UV_PROJECT_ENVIRONMENT` dirige `sync` al entorno nuevo. `--locked` impide resolver silenciosamente otro grafo. No usar `uv add` para reproducir una corrida ya fijada. `requirements.txt` enumera versiones directas coherentes, pero no congela todas las transitivas: el lockfile es la fuente para la reproducción exacta. Para volver al comportamiento predeterminado de uv en esa terminal: `Remove-Item Env:UV_PROJECT_ENVIRONMENT`; esto elimina solo la variable, no el entorno.

Comprobar versiones e imports sin red ni llamadas a modelos:

```powershell
$env:RAGAS_DO_NOT_TRACK = 'true'
$env:LANGSMITH_TRACING = 'false'
& $python entrega_3/evaluacion_ragas/comprobar_entorno.py
& $python entrega_3/evaluacion_ragas/test_evaluacion.py -v
& $python -m unittest entrega_3.rag_pipeline.test_pipeline -v
```

`comprobar_entorno.py` verifica versiones directas contra los archivos de dependencias y realiza los imports necesarios. Importa `adaptadores` antes de RAGAS, como el CLI, sin crear clientes ni llamar a modelos. No verifica una instalación limpia ni modifica evidencias.

## Variables de entorno

Crear `.env` en la raíz a partir de `.env.example`, colocando la clave localmente sin publicarla. No sobrescribir un `.env` ya configurado. Ninguna evidencia debe contener sus valores.

| Variable | Uso |
|---|---|
| `GEMINI_API_KEY` | Obligatoria para embeddings, generación y evaluación reales. No se necesita para leer evidencias, leer SQLite con `corpus.py` ni validar el dataset/vectores locales. |
| `RAGAS_DO_NOT_TRACK=true` | Desactiva analítica de RAGAS; el CLI ya lo fija. |
| `LANGSMITH_TRACING=false` | La Parte C lo fija antes de importar el pipeline. |
| `LANGSMITH_API_KEY`, `LANGSMITH_PROJECT`, `LANGSMITH_ENDPOINT` | Opcionales para trazabilidad B.4, cuando se habilita expresamente; no necesarias para esta evaluación local. |
| `LANGSMITH_WORKSPACE_ID` | Opcional si la cuenta requiere seleccionar workspace. |
| `UV_PROJECT_ENVIRONMENT` | Solo instalación/selección del entorno con uv; no es una credencial. |

No hace falta configurar `GOOGLE_API_KEY` ni una clave de OpenAI: los adaptadores evaluadores pasan explícitamente `GEMINI_API_KEY`. Para reproducir el modo probado, evitar otras configuraciones heredadas que seleccionen Vertex AI u otro proveedor. El SDK de generación del pipeline también lee las variables de su proveedor; el entorno probado no tenía `GOOGLE_API_KEY` ni `GOOGLE_GENAI_USE_VERTEXAI` configuradas.

## ChromaDB: preparación y comprobación del corpus aprobado

Instalar paquetes no crea el corpus. Se necesitan `chroma_db/` con `estudio_contable` y `estudio_contable_chunks`, y `base_conocimiento_limpia.json`. La persistencia binaria y el JSON limpio están ignorados en Git. Los textos, metadatos, correspondencias y hashes aprobados se conservan en [corpus_manifest.json](evaluacion_ragas/corpus_manifest.json). No regenerar embeddings si ya se dispone de las colecciones aprobadas.

Con la persistencia usada para la corrida y el JSON limpio correspondiente, comprobar **sin APIs ni escrituras en Chroma**:

```powershell
& $python entrega_3/evaluacion_ragas/corpus.py
& $python entrega_3/evaluacion_ragas/validar.py
```

La salida de `corpus.py` debe indicar `estudio_contable 17` y `estudio_contable_chunks 35`. `validar.py` comprueba además contenido, metadatos, referencias y hashes: contar 17/35 no basta. DOC-003 debe representar el estado finalizado, presentado y pagado o compensado. DOC-00X no pertenece a este corpus; la evidencia histórica 18/36 corresponde a otra persistencia.

Si no se tienen las colecciones, estos son los comandos existentes de reconstrucción, **con llamadas a embeddings y escrituras locales**; no ejecutarlos sobre la persistencia aprobada ni como simple comprobación:

```powershell
& $python pipeline_vectorial.py
& $python vector_db.py
& $python -m entrega_3.rag_pipeline index --output entrega_3/evidencias/reproduccion/indexacion.json
& $python entrega_3/evaluacion_ragas/corpus.py
& $python entrega_3/evaluacion_ragas/validar.py
```

`pipeline_vectorial.py` prepara/purga el JSON limpio, construye o carga FAISS y ejecuta consultas de prueba: consume embeddings. También existe `etl_purga.py` para generar el JSON limpio, con consumo de embeddings; no es un paso adicional obligatorio si ya lo prepara el primer comando. `vector_db.py` ingesta la colección original, simula el cambio de DOC-003 y hace una consulta de prueba; `index` reconstruye la derivada con 500/100 desde la original, generando embeddings y eliminando chunks obsoletos. No crean necesariamente una copia física idéntica del experimento previo.

**Identidad lógica y almacenamiento:** la validación excluye únicamente `collection_id` (UUID interno de Chroma) y compara configuración/schema como JSON parseado para que el orden o espaciado no definan identidad. Conserva comparación exacta de IDs de documentos/chunks, textos, metadatos, dimensión y toda la configuración pertinente. Comprueba además que el splitter 500/100 produzca exactamente los chunks, posiciones, IDs y metadatos aprobados. Una modificación de contenido, metadatos, dimensión o configuración sigue rechazándose; las pruebas locales demuestran que cambiar solo UUID no altera la identidad lógica.

[embedding_identity.json](evaluacion_ragas/embedding_identity.json) añade hashes SHA256 de los vectores float32 de 768 dimensiones, asociados a IDs lógicos, con comprobación de valores finitos. Se capturaron de las colecciones locales sin regenerar embeddings y se comprobó que sus registros no cambiaron. No existía una huella histórica de vectores: esta captura no demuestra retroactivamente qué vectores se usaron antes, ni permite inferir su modelo de origen. Modelo y tareas se respaldan en código/configuración; no se inventa esa procedencia a partir de números.

El manifiesto aprobado y el corpus no se modificaron. `validar.py` lee textos/metadatos con SQLite en modo de solo lectura; para leer vectores usa `get(include=['embeddings'])` de las colecciones existentes con `embedding_function=None`, sin consultas ni llamadas al proveedor. La apertura del cliente Chroma puede realizar tareas internas de persistencia; no se ejecutan upserts, deletes ni indexación. Una base reconstruida debe conservar contenido, configuración y huellas de vectores, aunque sus UUID difieran. No se reconstruyó físicamente el corpus desde cero en esta verificación; regenerar embeddings con un proveedor no garantiza identidad numérica con los guardados. No sobrescribir el manifiesto ni la huella para aceptar cambios.

## Validar, generar, evaluar y resumir

Estos comandos usan el intérprete del entorno nuevo seleccionado arriba. Primero comprobar el corpus. Los pasos de red se muestran para reproducción futura, **no se ejecutaron en esta revisión documental**:

```powershell
& $python entrega_3/evaluacion_ragas/validar.py
& $python entrega_3/evaluacion_ragas/ejecutar.py smoke
& $python entrega_3/evaluacion_ragas/ejecutar.py generate
& $python entrega_3/evaluacion_ragas/ejecutar.py evaluate
& $python entrega_3/evaluacion_ragas/resumir.py
& $python entrega_3/evaluacion_ragas/extraer_juicios.py
& $python entrega_3/evaluacion_ragas/auditar_llamadas.py
& $python entrega_3/evaluacion_ragas/verificar_resultados.py
```

- `smoke`: prueba de integración separada, con llamadas reales a evaluador y embeddings cuando no existen sus resultados.
- `generate`: diez respuestas `basic` y diez `rerank`; consume embeddings de consulta, generación y juez según cada caso pendiente.
- `evaluate`: llamadas RAGAS/Gemini y embeddings para métricas aplicables pendientes. Evalúa `generator_contexts` de `sources`, no los candidatos completos ni los chunks de referencia.
- Los otros comandos son locales; `validar` y `verificar_resultados` escriben reportes, y los de resumen/auditoría regeneran archivos derivados. Leer directamente JSON/CSV/Markdown existentes no los modifica.

La reanudación normal usa los mismos comandos `generate` y `evaluate`: ambos reutilizan los archivos existentes, **incluidos errores terminales**. No vuelven a evaluar una puntuación válida ni un error agotado automáticamente. Hay evidencia de reanudaciones sin llamadas nuevas en [generación](evidencias/ragas/resumen/reanudacion_generacion.json) y [evaluación](evidencias/ragas/resumen/reanudacion_evaluacion.json). No hay un flag `--retry-failed` implementado.

`freeze()` exige el mismo dataset, manifiesto, protocolo, parámetros, versión exacta de Python, dependencias registradas, hash de `uv.lock` y hashes de los archivos del pipeline. Diferencias de finales de línea del checkout también pueden cambiar esos hashes. No modificar `configuracion.json` para saltear el control. Las dependencias instaladas desde el lock no bastan por sí solas para reanudar una persistencia/código diferentes.

## Errores de ejecución y reanudación solo de las fallidas

La instalación quedó operativa: imports correctos, prueba mínima real y veinte generaciones terminadas. Los errores siguientes ocurrieron **en la evaluación inicial**, no durante la instalación, y sus registros originales se conservaron en `reintentos/continuacion_01/originales/`:

- **HTTP 429:** 17 métricas terminaron con `ClientError`, código 429, después de los reintentos limitados. Se conservan tipo/código e intentos, pero en esos registros históricos no quedó el cuerpo detallado del error. No se puede afirmar si fue cuota diaria, límite temporal de tasa u otra restricción del proveedor. Resolver esa condición antes de una nueva tanda.
- **Timeout:** Faithfulness de S1/rerank agotó el plazo de métrica de 180 s, con valor null y `TimeoutError`; sus llamadas registraron 504/503. El timeout HTTP del adaptador es otro límite, de 120 s por petición. No es una abstención ni una puntuación cero.

Ese estado inicial tenía 54 puntuaciones válidas, 8 no aplicables y 18 errores. La continuación autorizada recuperó las 18 métricas, conservando intactos los otros 62 estados: **ya no quedan errores técnicos pendientes**. [C.3/C.4](informe.md#c3--comparación-básico-vs-avanzado) muestran los deltas pareados, soportes y diagnóstico del evaluador. La comparación actual usa todos los pares válidos; las limitaciones del conjunto pequeño y del evaluador permanecen.

Alternativa manual documentada antes de existir el runner específico (no utilizada en esta tanda): para una futura continuación autorizada de **solo las fallidas**, el mecanismo consiste en archivar sus JSON terminales y retirar únicamente esos archivos del conjunto activo. Los logs de llamadas quedan donde están; los nuevos logs usan identificadores únicos. No tocar archivos `ok`, `not_applicable`, resultados de generación, dataset ni configuración. No ejecutar el bloque siguiente para inspeccionar evidencias.

El bloque primero valida localmente y luego mueve únicamente archivos cuyo estado es `evaluation_error`, guardando sus hashes y rutas. La ruta absoluta de cada origen y destino se verifica dentro de `evidencias/ragas`. No borra ningún resultado. No se ejecutó este archivado durante la revisión documental.

```powershell
& $python entrega_3/evaluacion_ragas/validar.py
if ($LASTEXITCODE -ne 0) { throw 'Corpus o dataset diferente: detener.' }
$ragasRoot = (Resolve-Path -LiteralPath 'entrega_3/evidencias/ragas').Path
$evaluationRoot = Join-Path $ragasRoot 'evaluacion'
$failedMetrics = @(Get-ChildItem -LiteralPath $evaluationRoot -Directory | ForEach-Object {
    Get-ChildItem -LiteralPath $_.FullName -File -Filter '*.json'
} | Where-Object {
    (Get-Content -Raw -Encoding UTF8 -LiteralPath $_.FullName | ConvertFrom-Json).status -eq 'evaluation_error'
})
$failedMetrics | Select-Object FullName
if ($failedMetrics.Count -eq 0) { throw 'No hay errores terminales para archivar.' }
$batchName = 'fallidas-' + (Get-Date -Format 'yyyyMMdd-HHmmss-fff')
$retryArchive = Join-Path $ragasRoot ('reintentos/' + $batchName)
if (Test-Path -LiteralPath $retryArchive) { throw 'El destino de archivo ya existe.' }
$ragasPrefix = $ragasRoot + [IO.Path]::DirectorySeparatorChar
$retryPlan = @($failedMetrics | ForEach-Object {
    $sourcePath = [IO.Path]::GetFullPath($_.FullName)
    $caseVariant = $_.Directory.Name
    $targetPath = [IO.Path]::GetFullPath((Join-Path $retryArchive ($caseVariant + '/' + $_.Name)))
    if (-not $sourcePath.StartsWith($ragasPrefix, [StringComparison]::OrdinalIgnoreCase)) { throw 'Origen fuera de evidencias.' }
    if (-not $targetPath.StartsWith($ragasPrefix, [StringComparison]::OrdinalIgnoreCase)) { throw 'Destino fuera de evidencias.' }
    [pscustomobject]@{source=$sourcePath; target=$targetPath; sha256=(Get-FileHash -LiteralPath $sourcePath -Algorithm SHA256).Hash}
})
New-Item -ItemType Directory -Path $retryArchive | Out-Null
$retryPlan | ConvertTo-Json -Depth 5 | Set-Content -Encoding UTF8 -LiteralPath (Join-Path $retryArchive 'plan.json')
Copy-Item -LiteralPath (Join-Path $ragasRoot 'configuracion.json') -Destination (Join-Path $retryArchive 'configuracion.json')
Copy-Item -LiteralPath (Join-Path $ragasRoot 'resumen') -Destination (Join-Path $retryArchive 'resumen-antes') -Recurse
foreach ($retryItem in $retryPlan) {
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $retryItem.target) | Out-Null
    Move-Item -LiteralPath $retryItem.source -Destination $retryItem.target
}
```

Después del archivado, y solo cuando se autorice volver a consumir API:

```powershell
& $python entrega_3/evaluacion_ragas/ejecutar.py evaluate
& $python entrega_3/evaluacion_ragas/resumir.py
& $python entrega_3/evaluacion_ragas/extraer_juicios.py
& $python entrega_3/evaluacion_ragas/auditar_llamadas.py
& $python entrega_3/evaluacion_ragas/verificar_resultados.py
```

`evaluate` encuentra faltantes únicamente en esas métricas archivadas, reutiliza las veinte respuestas y salta los estados válidos/no aplicables existentes. Los errores originales y el resumen anterior permanecen en `reintentos/`; no se sobreescriben. Cada nueva operación conserva un máximo de tres intentos transitorios. No repetir tandas hasta conseguir un score mejor. Esta preparación de reintento y la ejecución posterior **no se probaron con llamadas reales**; solo se revisó la sintaxis y se comprobó localmente qué 18 archivos seleccionaría el filtro.

## Evidencias que pueden inspeccionarse sin ejecutar APIs

- [Dataset aprobado](evaluacion_ragas/golden_dataset.json), [manifiesto](evaluacion_ragas/corpus_manifest.json), [revisión editorial](evaluacion_ragas/REVISION.md) y [protocolo previo](evaluacion_ragas/PROTOCOLO.md).
- [Configuración de la corrida](evidencias/ragas/configuracion.json), [generaciones](evidencias/ragas/generacion/) y [evaluaciones](evidencias/ragas/evaluacion/).
- [Veinte respuestas, contextos y tablas](evidencias/ragas/resumen/resultados_para_revision.md), [métricas JSON](evidencias/ragas/resumen/metricas_individuales.json), [CSV](evidencias/ragas/resumen/metricas_individuales.csv) y [resumen pareado](evidencias/ragas/resumen/resumen.json).
- [Juicios brutos indexados](evidencias/ragas/resumen/juicios_evaluador.json), [intentos](evidencias/ragas/resumen/auditoria_llamadas.json), [escapes revisados](evidencias/ragas/resumen/revision_escapes.json) y [comprobaciones](evidencias/ragas/resumen/verificaciones.json).

Los snapshots de código ejecutado se conservan en `evidencias/ragas/codigo_ejecutado/`, con hashes contrastados. Los JSON de auditoría no sustituyen una base Chroma con embeddings. El informe de esta entrega es `entrega_3/informe.md`; el de la raíz pertenece a otra entrega.

## Operación de A/B conservada

Los comandos siguientes son los de A/B y usan `.venv` por convención histórica; para el entorno nuevo usar `$python` en lugar de `.\.venv\Scripts\python.exe`. Las fases de indexación, consultas y trazabilidad pueden consumir API. No ejecutarlas para una inspección documental. La Parte C usa los comandos específicos anteriores, no el `compare` de ocho casos históricos. Se conserva también la guía histórica [CONTINUAR_B4.md](CONTINUAR_B4.md); B.4 ya está cumplida.

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
expongan secretos antes de compartirlos. **B.4 ya está cumplido con las evidencias enlazadas en el informe**;
no se genera una captura ficticia ni se habilitan trazas remotas sin credenciales.

## Archivos y revisión

- `rag_pipeline/retriever.py`: retriever de A, con rutas desde la raíz.
- `rag_pipeline/model.py`: SDK Google GenAI adaptado a ChatModel de LangChain.
- `rag_pipeline/pipeline.py`: composición LCEL y salida con fuentes reales.
- `rag_pipeline/indexing.py`: colección derivada y verificación de corpus.
- `rag_pipeline/reranking.py`: schema y validación del juez.
- `rag_pipeline/test_pipeline.py`: pruebas locales, sin consumir la API.
- `evidencias/`: salidas reales de indexación, comparación y diagnóstico.
- `informe.md`: resultados y limitaciones de A/B y C.3/C.4; la corrida C está completa, con sus limitaciones documentadas.

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
No enviar la clave al chat. Requisito histórico de B.4, ya cumplido: ejecutar y verificar una
traza real con candidatos, seleccionados, recuperación, juez, generación, tiempos
y uso reportado. Configurar las variables no equivale a completar B.4.

Los snapshots JSON de `evidencias/` son registros de auditoría del corpus simulado y sus resultados; no reemplazan ni incluyen la base ChromaDB o índices FAISS locales, que se reconstruyen y no se versionan. Los scripts auxiliares dentro de evidencias registran ensayos históricos; usar los comandos actuales de esta guía para la implementación final.


## Anexo de etapas anteriores

Se conservaron los estados y planes anteriores de C en [README_etapas_previas.md](README_etapas_previas.md). No sustituyen el estado vigente.

## Continuación autorizada de las 18 métricas fallidas

La continuación usa el entorno limpio, manteniendo RAGAS 0.2.15, modelos, prompts, temperatura, límites de salida, strictness y timeout de métrica originales. Solo cambia el transporte: una llamada por vez (incluidas las llamadas internas de Answer Relevancy), pausa mínima de 12 segundos y hasta tres intentos ante fallos transitorios. Se respeta `Retry-After` HTTP y `RetryInfo.retryDelay`; si la espera requerida supera 60 segundos, se detiene la tanda y se registra el aplazamiento, sin reintentar antes de tiempo. Una cuota diaria/agotada detiene la tanda; un 429 sin información suficiente también detiene, sin asumir que sea temporal. Los límites por minuto/segundo se distinguen con los detalles devueltos por el proveedor.

```powershell
& $python entrega_3/evaluacion_ragas/retomar_fallidas.py
```

No combinar este comando con el archivado manual anterior. `retomar_fallidas.py` conserva los 18 errores originales y el resumen anterior en `evidencias/ragas/reintentos/continuacion_01/`, calcula hashes de las veinte generaciones, dataset, manifiesto, protocolo y 62 estados válidos/no aplicables, y evalúa únicamente los 18 objetivos del plan. Cada resultado nuevo queda junto con el original; ningún score válido o no aplicable se vuelve a calcular. El progreso es reanudable dentro de esta tanda, sin repetir objetivos ya intentados. Si se registra un bloqueo de cuota, no relanzar automáticamente: resolverlo y acordar una nueva tanda acotada.

### Resultado de la continuación verificada

Se intentaron exactamente los 18 objetivos del plan y se recuperaron los 18, con 0 errores restantes. Hubo 55 intentos nuevos de API: 48 exitosos y siete 503 transitorios recuperados; no hubo 429 ni bloqueo de cuota. No se reconstruye la causa concreta de los 429 históricos sin sus cuerpos originales. Los 85 artefactos protegidos conservaron sus hashes y los inputs de los 18 objetivos coinciden con los errores originales. [Resultado de tanda](evidencias/ragas/reintentos/continuacion_01/resultado.json).

La comparación actualizada está en [C.3/C.4](informe.md#c3--comparación-básico-vs-avanzado) y [resumen](evidencias/ragas/resumen/resumen.json). La menor media avanzada es Context Precision 0.6250 sobre ocho casos. C2/Precision y S2/Faithfulness conservan los scores y juicios anómalos originales, sin recalcularlos ni cambiar el evaluador. La instalación limpia no equivale a una reconstrucción física del corpus: esta última no se ejecutó; se verificó que los UUID no forman parte de su identidad lógica.

`retomar_fallidas.py` ya completó esta tanda: no ejecutarlo para obtener otras puntuaciones. Los errores de cada intento y el resumen anterior permanecen auditables. El estado `incompleto` que aparece en anexos o registros anteriores corresponde al momento previo a esta recuperación.
