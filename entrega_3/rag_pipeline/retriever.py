import os
import re
from typing import Any
import chromadb
from chromadb import Documents, EmbeddingFunction, Embeddings
from google import genai
from google.genai import types

from .config import PERSIST_PATH

# Constantes fijadas de la Entrega 2
RUTA_PERSISTENCIA = str(PERSIST_PATH)
NOMBRE_COLECCION = "estudio_contable"
MODELO_EMBEDDING = "gemini-embedding-001"
DIMENSION = 768


class GeminiEmbeddingFunction(EmbeddingFunction[Documents]):
    #Envuelve gemini-embedding-001 para ChromaDB.
    #Usa task_type asimétrico: RETRIEVAL_QUERY para consultas de búsqueda.
    

    def __init__(self, task_type: str = "RETRIEVAL_QUERY") -> None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY no está configurada en las variables de entorno."
            )
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


PATRON_PREGUNTAS_CLIENTES = re.compile(
    r"\s*(?:(?:En criollo,\s*)?[Ll]os clientes (?:preguntan|lo preguntan)[^.]*:|(?:En criollo,\s*)?[Ll]os clientes preguntan\b|[Ee]l cliente suele decir:).*$",
    re.DOTALL,
)


def limpiar_texto_guardrails(texto: str) -> str:
    #Elimina fragmentos como 'Los clientes preguntan: ...' para sanitizar los guardrails/contexto.
    if not texto:
        return ""
    return PATRON_PREGUNTAS_CLIENTES.sub("", texto).strip()


class RetrieverContable:
    #Consulta la base vectorial ChromaDB construida en la Entrega 2.

    def __init__(
        self,
        persist_path: str = RUTA_PERSISTENCIA,
        collection_name: str = NOMBRE_COLECCION,
    ) -> None:
        self.persist_path = persist_path
        self.collection_name = collection_name

        # Inicialización del cliente persistente de ChromaDB
        self.client = chromadb.PersistentClient(path=self.persist_path)

        # Función de embeddings asimétrica para consultas
        self.embedding_function = GeminiEmbeddingFunction(task_type="RETRIEVAL_QUERY")

        # Obtención de la colección existente respetando el esquema de Entrega 2
        self.coleccion = self.client.get_collection(
            name=self.collection_name,
            embedding_function=self.embedding_function,
        )

    def recuperar(
        self,
        query: str,
        n_resultados: int = 3,
        filtros: dict[str, Any] | None = None,
        filtro_categoria: str | None = None,
        solo_activos: bool = True,
        distancia_maxima: float | None = None,
        limpiar_guardrails: bool = True,
    ) -> list[dict[str, Any]]:

        #Permite filtros exactos sobre metadatos y filtrado por distancia máxima (umbral).
        # Por defecto elimina fragmentos no normativos ('Los clientes preguntan...') mediante `limpiar_guardrails=True`.
        # Retorna una lista de diccionarios con 'id', 'documento', 'metadatos', 'distancia' y 'similitud'.
        
        if not query.strip():
            raise ValueError("La query no puede estar vacía.")
        if n_resultados < 1:
            raise ValueError("n_resultados debe ser mayor que cero.")

        condiciones: list[dict[str, Any]] = []
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
        elif len(condiciones) > 1:
            where = {"$and": condiciones}

        parametros: dict[str, Any] = {
            "query_texts": [query],
            "n_results": n_resultados,
        }
        if where is not None:
            parametros["where"] = where

        resultados = self.coleccion.query(**parametros)

        ids = resultados.get("ids", [[]])[0]
        documentos = resultados.get("documents", [[]])[0]
        metadatas = resultados.get("metadatas", [[]])[0]
        distancias = resultados.get("distances", [[]])[0]

        items_recuperados: list[dict[str, Any]] = []
        for i, doc_id in enumerate(ids):
            dist = distancias[i] if i < len(distancias) else 0.0
            if distancia_maxima is not None and dist > distancia_maxima:
                continue

            raw_doc = documentos[i] if i < len(documentos) else ""
            doc_texto = limpiar_texto_guardrails(raw_doc) if limpiar_guardrails else raw_doc
            similitud = max(0.0, 1.0 - dist)
            items_recuperados.append(
                {
                    "id": doc_id,
                    "documento": doc_texto,
                    "documento_raw": raw_doc,
                    "metadatos": metadatas[i] if i < len(metadatas) else {},
                    "distancia": dist,
                    "similitud": round(similitud, 4),
                }
            )

        return items_recuperados

    def formatear_contexto(
        self,
        documentos_recuperados: list[dict[str, Any]],
        limpiar_guardrails: bool = True,
    ) -> str:
    
        if not documentos_recuperados:
            return "No se encontró información relevante en la base de conocimiento."

        bloques = []
        for item in documentos_recuperados:
            meta = item.get("metadatos", {})
            categoria = meta.get("categoria", "general")
            contenido = item.get("documento", "")
            if limpiar_guardrails:
                contenido = limpiar_texto_guardrails(contenido)

            bloques.append(
                f"[{item['id']}] (Categoría: {categoria}, Similitud: {item['similitud']})\n"
                f"{contenido}"
            )
        return "\n\n".join(bloques)


# Alias por convención
Retriever = RetrieverContable


def get_retriever() -> RetrieverContable:
    """Función de fábrica para instanciar el retriever estándar."""
    return RetrieverContable(
        persist_path=RUTA_PERSISTENCIA,
        collection_name=NOMBRE_COLECCION,
    )


if __name__ == "__main__":
    print(f"Instanciando Retriever apuntando a '{RUTA_PERSISTENCIA}' / '{NOMBRE_COLECCION}'...")
    retriever = get_retriever()
    print(f"Colección cargada con {retriever.coleccion.count()} documentos.")

    consulta_ejemplo = "¿Cuándo vence la presentación y pago del IVA?"
    print(f"\nConsulta: '{consulta_ejemplo}'")
    resultados = retriever.recuperar(consulta_ejemplo, n_resultados=2)

    for res in resultados:
        print(f"\n- ID: {res['id']} | Distancia: {res['distancia']:.4f} | Similitud: {res['similitud']:.4f}")
        print(f"  Contenido: {res['documento'][:120]}...")

    print("\n--- Contexto formateado para RAG ---")
    print(retriever.formatear_contexto(resultados))
