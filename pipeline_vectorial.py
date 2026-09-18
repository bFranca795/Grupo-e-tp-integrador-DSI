import json
import os

import faiss
import numpy as np
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

ARCHIVO_DATOS = "base_conocimiento.json"
ARCHIVO_INDICE = "estudio_contable.index"
ARCHIVO_IDS = "estudio_contable_ids.json"

MODELO_EMBEDDING = "gemini-embedding-001"
DIMENSION = 768
TOP_K = 3

CONSULTAS_DE_PRUEBA = [
    "¿Qué papeles necesitan para darme de alta en monotributo?",
    "¿Cómo está mi declaración jurada de IVA?",
    "Me llegó una intimación fiscal, ¿qué hago?",
]

if not os.getenv("GEMINI_API_KEY"):
    raise ValueError("GEMINI_API_KEY no está configurada en las variables de entorno.")

client = genai.Client()


def cargar_documentos() -> list[dict]:
    with open(ARCHIVO_DATOS, encoding="utf-8") as archivo:
        return json.load(archivo)


def generar_embeddings(textos: list[str], task_type: str) -> np.ndarray:
    """Devuelve una matriz float32 (n, DIMENSION) normalizada.

    gemini-embedding-001 es Matryoshka: truncar a 768 rompe la norma unitaria, así
    que normalizar es lo que hace que el producto interno sea la similitud coseno.
    """
    respuesta = client.models.embed_content(
        model=MODELO_EMBEDDING,
        contents=textos,
        config=types.EmbedContentConfig(
            task_type=task_type,
            output_dimensionality=DIMENSION,
        ),
    )

    matriz = np.array([e.values for e in respuesta.embeddings], dtype="float32")
    faiss.normalize_L2(matriz)
    return matriz


def construir_o_cargar_indice(documentos: list[dict]) -> tuple[faiss.Index, list[str]]:
    """Recarga el índice desde disco si existe; si no, lo construye y lo persiste.

    Devuelve también los ids en orden de inserción: IndexFlatIP guarda vectores, no
    identificadores, y search() devuelve posiciones.
    """
    if os.path.exists(ARCHIVO_INDICE) and os.path.exists(ARCHIVO_IDS):
        print("Cargando índice FAISS desde disco...")
        with open(ARCHIVO_IDS, encoding="utf-8") as archivo:
            return faiss.read_index(ARCHIVO_INDICE), json.load(archivo)

    print("Generando embeddings...")
    textos = [documento["descripcion_semantica"] for documento in documentos]
    ids = [documento["id"] for documento in documentos]
    embeddings = generar_embeddings(textos, "RETRIEVAL_DOCUMENT")

    indice = faiss.IndexFlatIP(DIMENSION)
    indice.add(embeddings)

    faiss.write_index(indice, ARCHIVO_INDICE)
    with open(ARCHIVO_IDS, "w", encoding="utf-8") as archivo:
        json.dump(ids, archivo, ensure_ascii=False, indent=2)

    return indice, ids


def buscar(
    indice: faiss.Index, ids: list[str], consulta: str
) -> list[tuple[str, float]]:
    """Top-K por similitud coseno."""
    vector = generar_embeddings([consulta], "RETRIEVAL_QUERY")
    scores, posiciones = indice.search(vector, TOP_K)
    return [(ids[p], float(s)) for p, s in zip(posiciones[0], scores[0])]


def main() -> None:
    documentos = cargar_documentos()
    indice, ids = construir_o_cargar_indice(documentos)
    categorias = {d["id"]: d["metadatos"]["categoria"] for d in documentos}

    print(f"Índice listo: {indice.ntotal} vectores de dimensión {indice.d}.\n")

    for consulta in CONSULTAS_DE_PRUEBA:
        print(f"Consulta: {consulta}")
        for posicion, (id_documento, score) in enumerate(
            buscar(indice, ids, consulta), start=1
        ):
            print(
                f"  {posicion}. {id_documento}  [{categorias[id_documento]}]  score={score:.4f}"
            )
        print()


if __name__ == "__main__":
    main()
