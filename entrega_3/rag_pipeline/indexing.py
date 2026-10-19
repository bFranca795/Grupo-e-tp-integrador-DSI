"""Reconstruye exclusivamente la colección derivada desde la colección efectiva."""

import hashlib
import json

import chromadb
from langchain_text_splitters import RecursiveCharacterTextSplitter

from .config import CHUNKS_COLLECTION, ORIGINAL_COLLECTION, PERSIST_PATH, PROJECT_ROOT
from .retriever import GeminiEmbeddingFunction, limpiar_texto_guardrails


def snapshot(collection) -> list[dict]:
    data = collection.get(include=["documents", "metadatas"])
    return sorted(
        ({"id": id_, "documento": text, "metadatos": meta or {}}
         for id_, text, meta in zip(data["ids"], data["documents"], data["metadatas"])),
        key=lambda row: row["id"],
    )


def fingerprint(rows: list[dict]) -> str:
    return hashlib.sha256(json.dumps(rows, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def split_documents(rows: list[dict], chunk_size=500, chunk_overlap=100) -> list[dict]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, chunk_overlap=chunk_overlap, length_function=len,
        add_start_index=True,
    )
    chunks = []
    for row in rows:
        # Sanitizar ANTES de dividir: de otro modo la cola coloquial puede quedar
        # en otro chunk y escapar a la expresión regular heredada de A.
        text = limpiar_texto_guardrails(row["documento"])
        for index, doc in enumerate(splitter.create_documents([text])):
            digest = hashlib.sha256(doc.page_content.encode()).hexdigest()[:16]
            id_ = f"{row['id']}::chunk-{index:03d}-{digest}"
            chunks.append({
                "id": id_, "documento": doc.page_content,
                "metadatos": {**row["metadatos"], "parent_id": row["id"],
                              "chunk_id": id_, "chunk_index": index,
                              "start_index": doc.metadata["start_index"]},
            })
    return chunks


def rebuild(chunk_size=500, chunk_overlap=100) -> dict:
    client = chromadb.PersistentClient(path=str(PERSIST_PATH))
    original = client.get_collection(ORIGINAL_COLLECTION, embedding_function=None)
    before = snapshot(original)
    if not before:
        raise ValueError("La colección original está vacía; cargar Entrega 2 primero.")
    chunks = split_documents(before, chunk_size, chunk_overlap)
    # Generar todos los embeddings antes de tocar la colección derivada. Una
    # caída de la API no destruye un índice derivado previamente utilizable.
    embed = GeminiEmbeddingFunction(task_type="RETRIEVAL_DOCUMENT")
    vectors = []
    for start in range(0, len(chunks), 32):
        vectors.extend(embed([row["documento"] for row in chunks[start:start + 32]]))
    collection = client.get_or_create_collection(
        CHUNKS_COLLECTION, embedding_function=None, metadata={"hnsw:space": "cosine"},
    )
    collection.upsert(ids=[row["id"] for row in chunks], embeddings=vectors,
                      documents=[row["documento"] for row in chunks],
                      metadatas=[row["metadatos"] for row in chunks])
    obsolete = set(collection.get()["ids"]) - {row["id"] for row in chunks}
    if obsolete:
        collection.delete(ids=sorted(obsolete))
    after = snapshot(original)
    if before != after:
        raise RuntimeError("La colección original cambió durante la indexación.")
    clean_path = PROJECT_ROOT / "base_conocimiento_limpia.json"
    differences = []
    if clean_path.exists():
        clean = {row["id"]: row for row in json.loads(clean_path.read_text(encoding="utf-8"))}
        for row in before:
            expected = clean.get(row["id"])
            metadata = dict(expected["metadatos"]) if expected else {}
            if isinstance(metadata.get("tags_regionales"), list):
                metadata["tags_regionales"] = ", ".join(metadata["tags_regionales"])
            if not expected or expected["descripcion_semantica"] != row["documento"] or metadata != row["metadatos"]:
                differences.append(row["id"])
        differences.extend(sorted(set(clean) - {row["id"] for row in before}))
    return {
        "original_documents": len(before), "chunks": collection.count(),
        "chunk_size": chunk_size, "chunk_overlap": chunk_overlap, "length_unit": "characters",
        "original_sha256_before": fingerprint(before), "original_sha256_after": fingerprint(after),
        "differences_with_clean_json": differences if clean_path.exists() else None,
        "collection": CHUNKS_COLLECTION,
    }
