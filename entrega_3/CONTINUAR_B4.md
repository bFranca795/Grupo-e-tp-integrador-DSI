# Continuar B.4 desde b-rag-avanzado

B.1–B.3 están implementados y validados en los casos documentados en el informe.
B.4 está instrumentado pero **pendiente de ejecución y verificación con las
credenciales del compañero**. No hay una traza remota real verificada en esta entrega.
No hay resultados RAGAS ni una afirmación de mejora general.

## 1. Descargar e instalar (PowerShell, clon nuevo)

Necesita Git y un Python disponible para instalar uv. `uv sync` instala Python
3.14 si hace falta, según `.python-version`, y crea `.venv` desde `uv.lock`.

```powershell
git clone --branch b-rag-avanzado --single-branch https://github.com/bFranca795/Grupo-e-tp-integrador-DSI.git
cd Grupo-e-tp-integrador-DSI
python -m pip install --user uv
python -m uv sync --locked
python -m uv run --locked python -m unittest entrega_3.rag_pipeline.test_pipeline -v
Copy-Item -LiteralPath .env.example -Destination .env
notepad .env
```

La copia de `.env.example` es para un clon nuevo sin `.env`. En un checkout que
ya tenga `.env`, editarlo sin reemplazarlo. Si ya tiene el repositorio, usar:

```powershell
git fetch origin
git switch b-rag-avanzado
git pull --ff-only origin b-rag-avanzado
```

No descartar ni sobrescribir cambios locales si Git pide resolverlos.

## 2. Configurar credenciales propias en .env

Completar localmente (no pegar claves en chats ni incluirlas en Git):

```dotenv
GEMINI_API_KEY=<clave Gemini que pueda usar el compañero>
LANGSMITH_API_KEY=<clave propia de LangSmith>
LANGSMITH_TRACING=true
LANGSMITH_PROJECT=grupo-e-entrega-3-b4
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
```

Crear la clave desde https://smith.langchain.com/ → Settings → API Keys.
Un Personal Access Token (PAT) con acceso al workspace permite enviar y leer
trazas desde el SDK. Una clave Tracing Only solo permite enviarlas; en ese caso
verificar la traza desde una sesión de la interfaz de LangSmith.
Usar el endpoint de la región de la cuenta (el ejemplo es EE. UU.; para UE,
`https://eu.api.smith.langchain.com`). Si la clave abarca varios workspaces,
agregar `LANGSMITH_WORKSPACE_ID=<id de Settings → General>`.
Guía oficial: https://docs.langchain.com/langsmith/create-account-api-key

Las pruebas locales del paso 1 se ejecutan antes de habilitar tracing para no
confundir pruebas con modelos simulados y trazas reales de Gemini. Las claves
no vienen en el repositorio. Se requieren ambas para reconstrucción y generación.

## 3. Reconstruir bases locales en el clon nuevo

```powershell
python -m uv run --locked python pipeline_vectorial.py
python -m uv run --locked python vector_db.py
python -m uv run --locked python -m entrega_3.rag_pipeline index --output entrega_3/evidencias/b4_companero/indexacion.json
```

Estos comandos llaman a Gemini y consumen cuota. No ejecutar las primeras dos
líneas sobre una base de trabajo que se quiera preservar: son el arranque de
un clon sin bases locales. `vector_db.py` incluye la simulación de cambio de
estado de DOC-003. Luego `index` toma la colección efectiva, preserva la original
y crea/reconstruye solo `estudio_contable_chunks`.

ChromaDB, los índices FAISS y el JSON limpio se generan localmente y están
ignorados. Los snapshots JSON versionados son evidencia del corpus simulado y
las corridas anteriores, no una base instalada para ejecutar el programa.
Los conteos y respuestas pueden cambiar con la API/corpus efectivo; registrar
lo que realmente ocurra sin forzar IDs ni copiar resultados históricos.

## 4. Ejecutar la prueba real con LangSmith

Desde la raíz, después de guardar `.env`:

```powershell
python -m uv run --locked python -m entrega_3.rag_pipeline ask --variant rerank --question "Soy empleador y responsable inscripto: ¿qué necesito para liquidar IVA, cuándo presento y pago esa declaración y qué obligaciones tengo con las cargas sociales?" --output entrega_3/evidencias/b4_companero/resultado_langsmith.json
```

Se omite `--selected`: debe resolverse en 4. Configuración final:
500/100 caracteres, hasta ocho candidatos, filtros de metadatos y sanitización,
sin corte duro de distancia antes del juez, relevancia mínima 0.5 y hasta cuatro
seleccionados por defecto, configurable de 1 a 4. Puede seleccionar menos o cero.
El básico y chunks sin reranking mantienen su comportamiento de referencia.

El JSON guarda `settings`, pregunta, respuesta, `candidates`, `selected`,
`sources`, juicio, tiempos y `usage` separado por `judge` y `generator`.
No basta con que el comando termine: revisar que no haya `judge_error` y que la
consulta efectivamente haya ejecutado generación. Los datos de uso ausentes
quedan en null; no se estiman tokens.

## 5. Verificar y guardar la evidencia remota real

Abrir LangSmith, proyecto `grupo-e-entrega-3-b4`, y localizar `rag_rerank` de la
pregunta/hora ejecutada. Contrastar los IDs de llamadas `usage[*].run_id` del JSON
con las llamadas al modelo de esa traza para no confundirla con otra ejecución.

Comprobar y registrar:

- `recuperacion`: candidatos iniciales, IDs, distancias y contenidos.
- `reranking` / `juez_relevancia`: puntuaciones, motivos y orden de seleccionados.
- `generacion`: contexto que recibe únicamente los seleccionados y respuesta.
- Tiempos de las etapas; tokens del juez y del generador por separado.
- Correspondencia de candidatos, seleccionados y fuentes con el JSON guardado.
- Configuración efectiva `settings.selected_k=4`; hasta ocho candidatos, sin
  suponer que siempre deben seleccionarse cuatro.

Guardar una captura real como `entrega_3/langsmith_trace.png` y/o documentar en
`entrega_3/informe.md` un enlace accesible al revisor. Se pueden guardar capturas
adicionales en `entrega_3/evidencias/b4_companero/`. Conservar el JSON de la corrida,
la fecha, proyecto e ID/enlace de traza y la comprobación realizada. No exponer
claves en capturas, archivos ni enlaces. No sustituir esta evidencia con una imagen
inventada o solo con el log local.

**Solo marcar B.4 completo después de ver y verificar la traza remota.** Si hay
un fallo de autenticación, permisos, cuota o envío, registrarlo como bloqueo;
no afirmar que la traza existe ni inventar métricas. Los campos de tokens/tiempos
que no estén disponibles deben señalarse expresamente como no disponibles.

La rama se entrega sin merge ni PR. Las evidencias históricas se conservan;
las nuevas van en `b4_companero/` para no sobrescribirlas.
