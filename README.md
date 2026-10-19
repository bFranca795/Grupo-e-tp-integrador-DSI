# TP Integrador DSI — Grupo E

**Dominio elegido:** Legal Contable

**Integrantes:** Franca Bruno, Franzoni Clara, Tonelli Javier, Garcia Vior Nicolas, Gagliardi Martin

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
