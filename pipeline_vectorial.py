import json
import os

import faiss
import numpy as np
from dotenv import load_dotenv
from google import genai
from google.genai import types

from etl_purga import (
    DISTANCIA_MAXIMA,
    informar_purga,
    normalizar_documento,
    pares_candidatos,
    purgar,
    resolver_ids,
)

load_dotenv()

ARCHIVO_DATOS_ORIGINAL = "base_conocimiento.json"
ARCHIVO_DATOS = "base_conocimiento_limpia.json"
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
    if not os.path.exists(ARCHIVO_DATOS):
        raise FileNotFoundError(f"No existe {ARCHIVO_DATOS}.")
    with open(ARCHIVO_DATOS, encoding="utf-8") as archivo:
        return json.load(archivo)


def guardar_documentos_limpios(documentos: list[dict]) -> None:
    documentos_serializables = [
        {
            clave: valor
            for clave, valor in documento.items()
            if clave not in {"_colision_id", "_normalizaciones"}
        }
        for documento in documentos
    ]
    with open(ARCHIVO_DATOS, "w", encoding="utf-8") as archivo:
        json.dump(documentos_serializables, archivo, ensure_ascii=False, indent=2)
        archivo.write("\n")


def preparar_dataset() -> tuple[list[dict], np.ndarray]:
    """Normaliza y purga el dataset, reutilizando sus embeddings para FAISS."""
    with open(ARCHIVO_DATOS_ORIGINAL, encoding="utf-8") as archivo:
        documentos = json.load(archivo)
    documentos = resolver_ids([normalizar_documento(documento) for documento in documentos])

    vectores = generar_embeddings(
        [documento["descripcion_semantica"] for documento in documentos],
        "RETRIEVAL_DOCUMENT",
    )
    pares = pares_candidatos(documentos, vectores)
    documentos_limpios, eliminaciones = purgar(documentos, pares)
    ids_limpios = {documento["id"] for documento in documentos_limpios}
    posiciones_limpias = [
        posicion
        for posicion, documento in enumerate(documentos)
        if documento["id"] in ids_limpios
    ]
    vectores_limpios = vectores[posiciones_limpias]
    guardar_documentos_limpios(documentos_limpios)
    informar_purga(documentos, documentos_limpios, eliminaciones)
    print(
        f"ETL: {len(documentos)} entradas -> {len(documentos_limpios)} documentos "
        f"(distancia coseno <= {DISTANCIA_MAXIMA:.2f})"
    )
    return documentos_limpios, vectores_limpios


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


def construir_o_cargar_indice(
    documentos: list[dict], embeddings: np.ndarray | None = None
) -> tuple[faiss.Index, list[str]]:
    """Recarga el índice desde disco si existe; si no, lo construye y lo persiste.

    Devuelve también los ids en orden de inserción: IndexFlatIP guarda vectores, no
    identificadores, y search() devuelve posiciones.
    """
    if os.path.exists(ARCHIVO_INDICE) and os.path.exists(ARCHIVO_IDS):
        with open(ARCHIVO_IDS, encoding="utf-8") as archivo:
            ids_guardados = json.load(archivo)
        ids_actuales = [documento["id"] for documento in documentos]
        indice_guardado = faiss.read_index(ARCHIVO_INDICE)
        if ids_guardados == ids_actuales and indice_guardado.ntotal == len(ids_actuales):
            print("Cargando índice FAISS desde disco...")
            return indice_guardado, ids_guardados
        print("El índice existente no coincide con la base limpia; se reconstruye.")

    textos = [documento["descripcion_semantica"] for documento in documentos]
    ids = [documento["id"] for documento in documentos]
    if embeddings is None:
        print("Generando embeddings...")
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
    documentos, embeddings = preparar_dataset()
    indice, ids = construir_o_cargar_indice(documentos, embeddings)
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
