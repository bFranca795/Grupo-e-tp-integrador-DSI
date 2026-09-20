import json
import os

import chromadb
from chromadb import Documents, EmbeddingFunction, Embeddings
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

ARCHIVO_DATOS = "base_conocimiento.json"
MODELO_EMBEDDING = "gemini-embedding-001"
DIMENSION = 768

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
    print(f"Get Colección '{coleccion.get(ids=["DOC-001"])}'")
    print(f"Cambio verificado: {coleccion.get(ids=['DOC-00X'])}")

