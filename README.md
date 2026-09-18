# TP Integrador DSI — Grupo E

**Dominio elegido:** Legal Contable

**Integrantes:** Franca Bruno, Franzoni Clara, Tonelli Javier, Garcia Vior Nicolas, Gagliardi Martin

## Requisitos

- Python 3.14 o superior (probado en 3.14.7, Linux)
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
uv sync
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

Orden de ejecución:

```
pipeline_vectorial.py  →  vector_db.py  →  etl_purga.py  →  búsqueda híbrida
```

| Script | Qué hace |
| --- | --- |
| `pipeline_vectorial.py` | Genera los embeddings de `base_conocimiento.json` y construye el índice FAISS |
| `vector_db.py` | Carga los documentos en ChromaDB persistente y expone el CLI de búsqueda |
| `etl_purga.py` | ETL y purga semántica; produce `base_conocimiento_limpia.json` |

Los binarios que generan estos scripts (`*.index`, `chroma_db/`) están
ignorados: se reconstruyen corriendo el pipeline desde `base_conocimiento.json`.
