"""Logs de aplicación, una línea JSON por evento, sin payloads ni excepciones.

Eventos estables:
app.inicio / app.cierre / app.error: ciclo de vida y fallo de inicialización.
http.consulta.inicio / http.consulta.fin / http.consulta.error: POST consultar y GET estado.
herramienta.ejecutada / herramienta.error: una ejecución, nombre y resultado público.
agente.limite: presupuesto agotado (categoria iteraciones o llamadas).
agente.error: fallo de modelo o grafo.

El logger es independiente del root y de Uvicorn. thread_id debe ser un ID
opaco, no un dato personal. Se enmascara PII reconocible del ID al emitirlo;
si el filtro falla, se omite ese campo. No se inspeccionan payloads.
"""

from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime, timezone
import json
import logging
import threading
from time import perf_counter
from .seguridad import enmascarar_pii


NOMBRE_LOGGER = "grupo_e_tp_integrador_dsi.observabilidad"
_hilo = ContextVar("log_thread_id", default=None)
_config_lock = threading.Lock()
_EVENTOS = {"app.inicio", "app.cierre", "app.error", "http.consulta.inicio",
            "http.consulta.fin", "http.consulta.error", "herramienta.ejecutada",
            "herramienta.error", "agente.limite", "agente.error"}
_EVENTOS.add("tracing.error")
_RESULTADOS = {"finalizada", "sin_evidencia", "requiere_vinculacion", "limite", "error",
               "respondida", "creada", "existente", "conflicto", "encontrada", "no_encontrada"}
_HERRAMIENTAS = {"consultar_rag", "consultar_solicitud_interna", "crear_solicitud_interna"}
_CATEGORIAS = {"inicializacion", "consulta", "estado", "herramienta", "modelo", "grafo",
               "iteraciones", "llamadas"}
_CATEGORIAS.add("tracing")


class JsonFormatter(logging.Formatter):
    """Ignora message, args, exc_info y extras no incluidos en la lista permitida."""

    def format(self, record):
        payload = {"timestamp": datetime.fromtimestamp(record.created, timezone.utc).isoformat(),
                   "level": record.levelname,
                   "event": record.event if getattr(record, "event", None) in _EVENTOS else "log.no_clasificado"}
        thread_id = getattr(record, "thread_id", None)
        if isinstance(thread_id, str):
            try:
                seguro = enmascarar_pii(thread_id)
                if isinstance(seguro, str):
                    payload["thread_id"] = seguro
            except Exception:
                pass  # No impedir la consulta ni publicar el ID sin filtrar.
        for name, allowed in (("resultado", _RESULTADOS), ("herramienta", _HERRAMIENTAS),
                              ("categoria", _CATEGORIAS), ("operacion", {"consultar", "estado"})):
            value = getattr(record, name, None)
            if isinstance(value, str) and value in allowed:
                payload[name] = value
        duration = getattr(record, "duration_ms", None)
        if isinstance(duration, (int, float)) and 0 <= duration < float("inf"):
            payload["duration_ms"] = round(duration, 3)
        return json.dumps(payload, ensure_ascii=False, allow_nan=False)


def configurar_logger(*, stream=None):
    """Configuración idempotente; stream permite capturar logs en pruebas."""
    with _config_lock:
        logger = logging.getLogger(NOMBRE_LOGGER)
        handler = next((h for h in logger.handlers if h.name == "agente-json"), None)
        if handler is None:
            handler = logging.StreamHandler(stream)
            handler.name = "agente-json"
            handler.setFormatter(JsonFormatter())
            logger.addHandler(handler)
        elif stream is not None:
            handler.setStream(stream)
        logger.setLevel(logging.INFO)
        logger.propagate = False
        return logger


@contextmanager
def contexto_hilo(thread_id):
    token = _hilo.set(thread_id if thread_id is not None else _hilo.get())
    try:
        yield
    finally:
        _hilo.reset(token)


def registrar(event, *, level=logging.INFO, **campos):
    """Solo el formatter decide qué campos escalares se publican."""
    campos = {k: v for k, v in campos.items()
              if k in {"resultado", "herramienta", "categoria", "operacion", "duration_ms"}}
    configurar_logger().log(level, "", extra={"event": event, "thread_id": _hilo.get(), **campos})


@contextmanager
def consulta_http(thread_id, operacion):
    """Un inicio y un fin por consulta validada; errores sin mensajes internos."""
    with contexto_hilo(thread_id):
        inicio = perf_counter()
        campos = {}
        registrar("http.consulta.inicio", operacion=operacion)
        try:
            yield campos
        except Exception:
            campos["resultado"] = "error"
            registrar("http.consulta.error", level=logging.ERROR, operacion=operacion,
                      categoria="consulta" if operacion == "consultar" else "estado", resultado="error")
            raise
        finally:
            registrar("http.consulta.fin", operacion=operacion,
                      duration_ms=(perf_counter() - inicio) * 1000, **campos)
