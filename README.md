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

**Estado de la entrega:** B.1–B.3 están implementados y validados en los casos
documentados. Esto no constituye una mejora general ni una evaluación RAGAS.
**B.4 queda pendiente de ejecución y verificación con las credenciales del
compañero**: todavía no hay una captura ni enlace de traza real verificada.

Código y comandos: [`entrega_3/README.md`](entrega_3/README.md).
Informe consolidado, con evidencia histórica y resultados nuevos separados:
[`entrega_3/informe.md`](entrega_3/informe.md).

Los antiguos `retriever.py`, `Trazabilidad_de_fuentes.py` e
`informe_entrega3.md` se trasladaron a esa carpeta. Las entregas 1 y 2
permanecen en la raíz.

Para continuar B.4 desde otra máquina: [guía y comandos exactos](entrega_3/CONTINUAR_B4.md).
