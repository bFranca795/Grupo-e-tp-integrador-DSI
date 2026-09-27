import json
import os

import chromadb
from chromadb import Documents, EmbeddingFunction, Embeddings
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

ARCHIVO_DATOS = "base_conocimiento_limpia.json"
MODELO_EMBEDDING = "gemini-embedding-001"
DIMENSION = 768
DISTANCIA_MAXIMA_BUSQUEDA = None

if not os.getenv("GEMINI_API_KEY"):
    raise ValueError("GEMINI_API_KEY no está configurada en las variables de entorno.")


class GeminiEmbeddingFunction(EmbeddingFunction[Documents]):
    """Envuelve gemini-embedding-001 para que ChromaDB use el mismo modelo que FAISS (A.4).

    task_type es asimétrico igual que en pipeline_vectorial.py: RETRIEVAL_DOCUMENT al
    ingestar, RETRIEVAL_QUERY al consultar (ver B.4).
    """

    def __init__(self, task_type: str = "RETRIEVAL_DOCUMENT") -> None:
        self._client = genai.Client()
        self._task_type = task_type

    def __call__(self, input: Documents) -> Embeddings:
        respuesta = self._client.models.embed_content(
            model=MODELO_EMBEDDING,
            contents=list(input),
            config=types.EmbedContentConfig(
                task_type=self._task_type,
                output_dimensionality=DIMENSION,
            ),
        )
        return [e.values for e in respuesta.embeddings]


client = chromadb.PersistentClient(path="chroma_db")

coleccion = client.get_or_create_collection(
    name="estudio_contable",
    metadata={"hnsw:space": "cosine"},
    embedding_function=GeminiEmbeddingFunction(task_type="RETRIEVAL_DOCUMENT"),
)


def buscar_contable(
    query_semantica: str,
    filtro_categoria: str | None = None,
    solo_activos: bool = True,
    n_resultados: int = 3,
    filtros: dict[str, str | bool] | None = None,
    distancia_maxima: float | None = DISTANCIA_MAXIMA_BUSQUEDA,
) -> dict:
    """Busca por significado y filtros exactos, sin umbral por defecto."""
    if not query_semantica.strip():
        raise ValueError("query_semantica no puede estar vacío")
    if n_resultados < 1:
        raise ValueError("n_resultados debe ser mayor que cero")

    condiciones = []
    if filtros:
        condiciones.extend(
            {campo: {"$eq": valor}} for campo, valor in filtros.items()
        )
    if filtro_categoria is not None:
        condiciones.append({"categoria": {"$eq": filtro_categoria}})
    if solo_activos:
        condiciones.append({"activo": {"$eq": True}})

    where = None
    if len(condiciones) == 1:
        where = condiciones[0]
    elif condiciones:
        where = {"$and": condiciones}

    parametros = {
        "query_texts": [query_semantica],
        "n_results": n_resultados,
    }
    if where is not None:
        parametros["where"] = where

    resultados = coleccion.query(**parametros)
    if distancia_maxima is None or not resultados.get("distances"):
        return resultados

    ids_filtrados = []
    documentos_filtrados = []
    metadatos_filtrados = []
    distancias_filtradas = []
    for indice, distancia in enumerate(resultados["distances"][0]):
        if distancia <= distancia_maxima:
            ids_filtrados.append(resultados["ids"][0][indice])
            documentos_filtrados.append(resultados["documents"][0][indice])
            metadatos_filtrados.append(resultados["metadatas"][0][indice])
            distancias_filtradas.append(distancia)
    return {
        **resultados,
        "ids": [ids_filtrados],
        "documents": [documentos_filtrados],
        "metadatas": [metadatos_filtrados],
        "distances": [distancias_filtradas],
    }


def aplanarTagsRegionales(metadatos: list[dict]) -> None:
    """Aplana los tags regionales en los metadatos de cada documento.

    Por ejemplo, si un documento tiene:
        "tags_regionales": ["Buenos Aires", "CABA"]
    Se reemplaza por:
        "tags_regionales": "Buenos Aires, CABA"
    """
    for metadato in metadatos:
            metadato["tags_regionales"] = ", ".join(metadato["tags_regionales"])

def cargar_documentos() -> list[dict]:
    if not os.path.exists(ARCHIVO_DATOS):
        raise FileNotFoundError(
            f"No existe {ARCHIVO_DATOS}. Ejecutá primero: "
            "python etl_purga.py"
        )
    with open(ARCHIVO_DATOS, encoding="utf-8") as archivo:
        return json.load(archivo)


def insertar_documentos(documentos: list[dict]) -> None:
    """Inserta documentos en la colección de ChromaDB.

    Cada documento debe tener los campos:
        - id: str
        - descripcion_semantica: str
        - metadatos: dict
    """
    ids = [documento["id"] for documento in documentos]
    documents = [documento["descripcion_semantica"] for documento in documentos]
    metadatas = [documento["metadatos"] for documento in documentos]

    aplanarTagsRegionales(metadatas)

    coleccion.upsert(ids=ids, documents=documents, metadatas=metadatas)


def simular_cambio_estado() -> None:
    """Simula la actualización del estado de un documento existente."""
    coleccion.upsert(
        ids=["DOC-00X"],
        documents=["La declaración jurada de IVA fue presentada y está finalizada."],
        metadatas=[
            {
                "categoria": "tramites",
                "activo": True,
                "jurisdiccion": "nacional",
                "tipo_contribuyente": "responsable_inscripto",
                "tags_regionales": "iva, estado, presentada, finalizada",
            }
        ],
    )


if __name__ == "__main__":
    documentos = cargar_documentos()
    insertar_documentos(documentos)
    simular_cambio_estado()
    print(f"Colección '{coleccion.name}' lista: {coleccion.count()} documentos.")
    print(f"Get Colección '{coleccion.get(ids=['DOC-001'])}'")
    print(f"Cambio verificado: {coleccion.get(ids=['DOC-00X'])}")

