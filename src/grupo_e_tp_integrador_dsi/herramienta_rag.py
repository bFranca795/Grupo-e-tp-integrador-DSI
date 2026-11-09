"""Adaptación acotada del RAG existente a una herramienta asíncrona."""

import asyncio
import re
from threading import Lock
from typing import Callable

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, ConfigDict, Field, field_validator

from entrega_3.rag_pipeline.pipeline import ESCAPE, Settings, build_pipeline


class ArgumentosRag(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    pregunta: str = Field(min_length=1, max_length=4000,
                          description="Consulta contable de hasta 4000 caracteres; no puede estar vacía.")

    @field_validator("pregunta")
    @classmethod
    def no_vacia(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("La pregunta no puede estar vacía.")
        return value.strip()


def _error() -> dict:
    return {"resultado": "error", "respuesta": "No se pudo completar la consulta al RAG.", "fuentes": []}


def _respuesta_publica(state: dict) -> dict:
    status = state.get("status")
    if status == "insufficient_context":
        return {"resultado": "sin_evidencia", "respuesta": ESCAPE, "fuentes": []}
    if status == "insufficient_client_binding":
        return {"resultado": "requiere_vinculacion", "respuesta": ESCAPE, "fuentes": []}
    if status != "ok":  # Incluye judge_error y estados desconocidos.
        return _error()
    answer = state.get("answer")
    if not isinstance(answer, str) or not answer.strip():
        return _error()
    # El generador puede abstenerse conservando status=ok en el pipeline original.
    if ESCAPE in answer:
        return {"resultado": "sin_evidencia", "respuesta": ESCAPE, "fuentes": []}
    sources = state.get("sources")
    if not isinstance(sources, list) or not sources:
        return _error()
    referencias = []
    for row in sources[:4]:
        source_id = row.get("id") if isinstance(row, dict) else None
        # Incluye sufijos de colisión del ETL; nunca metadatos arbitrarios.
        if not isinstance(source_id, str) or len(source_id) > 128 or not re.fullmatch(
            r"DOC-\d{3}(?:-dup-[1-9]\d*)?(?:::chunk-\d{3}-[0-9a-f]{16})?", source_id
        ):
            return _error()
        referencia = {"id": source_id, "id_documental": source_id.split("::", 1)[0]}
        if referencia not in referencias:
            referencias.append(referencia)
    return {"resultado": "respondida", "respuesta": answer[:6000], "fuentes": referencias}


def crear_herramienta_rag(
    *, pipeline_factory: Callable = build_pipeline,
) -> StructuredTool:
    """Crea una instancia con inicialización diferida única y variante rerank.

    La fábrica es configuración interna para pruebas, no un argumento del modelo.
    Si la inicialización falla, esta instancia conserva el fallo hasta recrearla.
    """
    lock = Lock()
    pipeline = None
    inicializado = False

    def ejecutar(pregunta: str) -> dict:
        nonlocal pipeline, inicializado
        try:
            with lock:
                if not inicializado:
                    inicializado = True
                    pipeline = pipeline_factory(Settings(variant="rerank"))
            if pipeline is None:
                return _error()
            return _respuesta_publica(pipeline.invoke({"question": pregunta}))
        except Exception:
            # Nunca serializar excepciones: pueden incluir claves, rutas o prompts.
            return _error()

    async def consultar_rag(pregunta: str) -> dict:
        """Consulta el RAG contable de Entrega 3 conservando sus abstenciones.

        Parámetros:
            pregunta: Consulta obligatoria no vacía, de hasta 4000 caracteres.
        Retorno:
            JSON serializable con resultado respondida, sin_evidencia,
            requiere_vinculacion o error; respuesta de hasta 6000 caracteres y
            hasta cuatro fuentes con id de fragmento e id_documental. No incluye
            contenido completo de chunks, candidatos, embeddings ni metadatos.
        Errores:
            Pydantic rechaza argumentos inválidos o adicionales. Los fallos de
            inicialización, recuperación, juez o generación devuelven error con
            mensaje genérico, sin claves, rutas ni trazas. No se afirman estados
            personales cuando el RAG exige vinculación. No ejecuta operaciones
            contables. La ejecución síncrona existente se delega a un hilo para
            no bloquear el event loop; se reutiliza un único pipeline por instancia.
        """
        return await asyncio.to_thread(ejecutar, pregunta)

    return StructuredTool.from_function(
        coroutine=consultar_rag, args_schema=ArgumentosRag, infer_schema=False,
    )


consultar_rag = crear_herramienta_rag()
