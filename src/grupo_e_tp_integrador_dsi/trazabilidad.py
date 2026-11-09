"""LangSmith opt-in con spans sin contenido y callbacks seguros del RAG.

LANGSMITH_TRACING=true habilita (false tiene prioridad sobre el alias
LANGCHAIN_TRACING_V2). LANGSMITH_PROJECT selecciona proyecto. Sin configuración
explícita se desactiva. No se crea Client al importar ni estando desactivado.
Se suprime el tracing automático dentro del agente: capturaría estado, preguntas,
documentos, argumentos y firmas Gemini. Solo se publican nombres fijos, estados
públicos, tiempos y usage_metadata realmente informada, nunca costos calculados.
LangSmith puede calcular costos si dispone de precios para proveedor/modelo;
ese valor no equivale a una factura confirmada del proveedor.
"""

from contextlib import contextmanager
from contextvars import ContextVar
import os
import re
from threading import RLock

from langchain_core.callbacks import BaseCallbackHandler
from langsmith import Client, tracing_context
from langsmith.run_trees import RunTree

from .observabilidad import registrar

_actual = ContextVar("span_agente", default=None)
_RESULTADOS = {"finalizada", "sin_evidencia", "requiere_vinculacion", "limite", "error",
               "respondida", "creada", "existente", "conflicto", "encontrada", "no_encontrada"}
_TOOLS = {"consultar_rag", "consultar_solicitud_interna", "crear_solicitud_interna"}
_ETAPAS = {"recuperacion", "reranking", "generacion", "juez_relevancia", "respuesta_y_fuentes"}


def _metadata(modelo=None, usage=None):
    data = {}
    if isinstance(modelo, str) and re.fullmatch(r"gemini-[a-zA-Z0-9.-]{1,80}", modelo):
        data.update(ls_provider="google_genai", ls_model_name=modelo)
    if isinstance(usage, dict):
        counts = {k: v for k, v in usage.items() if k in {"input_tokens", "output_tokens", "total_tokens"}
                  and type(v) is int and v >= 0}
        if counts:
            data["usage_metadata"] = counts
    return data


class Span:
    def __init__(self, tracer=None, run=None):
        self.tracer, self.run = tracer, run
        self.outputs, self.metadata, self.error = {}, {}, None

    def resultado(self, value):
        if isinstance(value, str) and value in _RESULTADOS:
            self.outputs["resultado"] = value
            if value == "error":
                self.error = "ejecucion_controlada"

    def tokens(self, usage, modelo=None):
        self.metadata.update(_metadata(modelo, usage))

    def seleccion(self, calls):
        self.outputs["herramientas_seleccionadas"] = [c["name"] for c in calls if c.get("name") in _TOOLS]

    def cerrar(self):
        if self.run is not None:
            try:
                self.run.end(outputs=self.outputs, error=self.error, metadata=self.metadata)
                self.run.patch()
            except Exception:
                self.tracer.fallo()


class Trazador:
    def __init__(self, *, enabled=None, project=None, client=None):
        flag = os.getenv("LANGSMITH_TRACING", os.getenv("LANGCHAIN_TRACING_V2", "false"))
        self.enabled = str(flag).lower() == "true" if enabled is None else enabled
        self.project = project or os.getenv("LANGSMITH_PROJECT") or "agente-contable"
        self.client = client
        self._propio = client is None
        self._lock = RLock()
        self.ultimo_run_id = None
        self.error = False

    def fallo(self, *_):
        with self._lock:
            if not self.error:
                registrar("tracing.error", level=30, categoria="tracing", resultado="error")
            self.error = True

    def iniciar(self, nombre, tipo, parent=None, modelo=None):
        if not self.enabled or self.error:
            return Span()
        try:
            with self._lock:
                if self.client is None:
                    self.client = Client(hide_inputs=True, omit_traced_runtime_info=True,
                                         tracing_error_callback=self.fallo)
            extra = {"metadata": _metadata(modelo)}
            if parent is not None and parent.run is not None:
                run = parent.run.create_child(nombre, run_type=tipo, inputs={}, extra=extra)
            else:
                run = RunTree(name=nombre, run_type=tipo, project_name=self.project,
                              inputs={}, extra=extra, ls_client=self.client)
            run.post()
            return Span(self, run)
        except Exception:
            self.fallo()
            return Span()

    @contextmanager
    def consulta(self):
        # Impide capturas automáticas de payloads, incluso si .env las habilita.
        with tracing_context(enabled=False):
            span = self.iniciar("agente.consulta", "chain")
            self.ultimo_run_id = str(span.run.id) if span.run else None
            token = _actual.set(span)
            try:
                yield span, CallbacksRag(self)
            except Exception:
                span.error = "ejecucion_agente"
                raise
            finally:
                _actual.reset(token)
                span.cerrar()

    def cerrar(self):
        if self.client is not None:
            try:
                self.client.flush(timeout=3)
            except Exception:
                self.fallo()
            finally:
                if self._propio:
                    try:
                        self.client.close(timeout=3)
                    except Exception:
                        self.fallo()


@contextmanager
def tramo(nombre, tipo="chain", *, modelo=None):
    parent = _actual.get()
    span = (parent.tracer.iniciar(nombre, tipo, parent, modelo) if parent and parent.tracer else Span())
    token = _actual.set(span)
    try:
        yield span
    except Exception:
        span.error = "ejecucion_interna"
        raise
    finally:
        _actual.reset(token)
        span.cerrar()


class CallbacksRag(BaseCallbackHandler):
    """Reutiliza callbacks LCEL heredados; ignora inputs, outputs y errores crudos."""
    def __init__(self, tracer):
        self.tracer, self.runs, self.lock = tracer, {}, RLock()

    def _iniciar(self, run_id, parent_run_id, name, kind):
        with self.lock:
            parent = self.runs.get(parent_run_id) or _actual.get()
            if parent is not None and parent.run is not None:
                self.runs[run_id] = self.tracer.iniciar(name, kind, parent)

    def on_chain_start(self, serialized, inputs, *, run_id, parent_run_id=None, name=None, **kwargs):
        if name in _ETAPAS:
            self._iniciar(run_id, parent_run_id, name, "retriever" if name == "recuperacion" else "chain")

    def on_chat_model_start(self, serialized, messages, *, run_id, parent_run_id=None, **kwargs):
        self._iniciar(run_id, parent_run_id, "gemini.rag", "llm")

    def _fin(self, run_id, error=False, message=None):
        with self.lock:
            span = self.runs.pop(run_id, None)
        if span is not None:
            if error:
                span.error = "ejecucion_rag"
            if message is not None:
                metadata = getattr(message, "response_metadata", {})
                usage = getattr(message, "usage_metadata", None)
                raw = metadata.get("provider_usage")
                if usage is None and isinstance(raw, dict):
                    usage = {"input_tokens": raw.get("prompt_token_count"),
                             "output_tokens": raw.get("candidates_token_count"),
                             "total_tokens": raw.get("total_token_count")}
                span.tokens(usage, metadata.get("model_name"))
            span.cerrar()

    def on_chain_end(self, outputs, *, run_id, **kwargs):
        self._fin(run_id)

    def on_chain_error(self, error, *, run_id, **kwargs):
        self._fin(run_id, error=True)

    def on_llm_end(self, response, *, run_id, **kwargs):
        message = response.generations[0][0].message if response.generations else None
        self._fin(run_id, message=message)

    def on_llm_error(self, error, *, run_id, **kwargs):
        self._fin(run_id, error=True)
