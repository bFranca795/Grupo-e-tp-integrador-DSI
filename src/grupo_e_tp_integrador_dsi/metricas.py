"""Métricas por aplicación/proceso, sin persistencia ni contenido de consultas.

POST /consultar cuenta una recibida incluso si falla el esquema (422).
Completadas: HTTP 200 con resultado público, incluidos error y limite.
Errores: HTTP 5xx/excepción inesperada o resultado público error, una vez.
422 no cuenta como completada, error ni muestra de latencia.
Solo rechazos de seguridad incrementan bloqueos; un 422 estructural no lo hace.
Latencias reales: consultas validadas, incluidos fallos, desde entrada HTTP hasta
fin de respuesta; incluyen parseo, espera del bloqueo por hilo y ejecución.
P95: rango más próximo, sorted(muestras)[ceil(0.95*n)-1]. Sin muestras: 0 ms.
Se conservan todas las muestras numéricas para calcular el percentil exacto.
Las ejecuciones de herramientas incluyen invocaciones rechazadas por validación;
un nombre desconocido que no puede invocarse no constituye una ejecución.
"""

from contextlib import contextmanager
from contextvars import ContextVar
from math import ceil, isfinite
from threading import Lock
from time import perf_counter


RESULTADOS = ("finalizada", "sin_evidencia", "requiere_vinculacion", "limite", "error")
HERRAMIENTAS = ("consultar_rag", "consultar_solicitud_interna", "crear_solicitud_interna")
_registro_actual = ContextVar("registro_metricas", default=None)


class RegistroMetricas:
    def __init__(self):
        self._lock = Lock()
        self._recibidas = self._completadas = self._errores = 0
        self._bloqueos_seguridad = 0
        self._resultados = dict.fromkeys(RESULTADOS, 0)
        self._herramientas = dict.fromkeys(HERRAMIENTAS, 0)
        self._latencias = []

    def recibir_consulta(self):
        with self._lock:
            self._recibidas += 1

    def finalizar_consulta(self, *, status, resultado=None, duration_ms=None, fallo=False,
                           bloqueo_seguridad=False):
        with self._lock:
            if bloqueo_seguridad:
                self._bloqueos_seguridad += 1
            if not fallo and status == 200 and resultado in RESULTADOS:
                self._completadas += 1
                self._resultados[resultado] += 1
            if fallo or status >= 500 or resultado == "error":
                self._errores += 1
            if duration_ms is not None and isfinite(duration_ms) and duration_ms >= 0:
                self._latencias.append(duration_ms)

    def ejecutar_herramienta(self, nombre):
        if nombre in HERRAMIENTAS:
            with self._lock:
                self._herramientas[nombre] += 1

    def consultar(self) -> dict:
        """Devuelve un snapshot independiente y JSON serializable."""
        with self._lock:
            muestras = list(self._latencias)
            snapshot = {
                "consultas_recibidas": self._recibidas,
                "consultas_completadas": self._completadas,
                "errores": self._errores,
                "consultas_por_resultado": dict(self._resultados),
                "ejecuciones_herramientas": sum(self._herramientas.values()),
                "herramientas_por_nombre": dict(self._herramientas),
                "bloqueos_seguridad": self._bloqueos_seguridad,
            }
        ordenadas = sorted(muestras)
        snapshot["latencia_promedio_ms"] = sum(muestras) / len(muestras) if muestras else 0.0
        snapshot["latencia_p95_ms"] = ordenadas[ceil(.95 * len(ordenadas)) - 1] if ordenadas else 0.0
        return snapshot


@contextmanager
def contexto_metricas(registro):
    token = _registro_actual.set(registro)
    try:
        yield
    finally:
        _registro_actual.reset(token)


def registrar_ejecucion_herramienta(nombre):
    registro = _registro_actual.get()
    if registro is not None:
        registro.ejecutar_herramienta(nombre)


class MetricasMiddleware:
    """ASGI puro: observa metadatos HTTP sin leer cuerpos ni alterar respuestas."""

    def __init__(self, app, registro):
        self.app, self.registro = app, registro

    async def __call__(self, scope, receive, send):
        if not (scope["type"] == "http" and scope["method"] == "POST" and scope["path"] == "/consultar"):
            return await self.app(scope, receive, send)
        self.registro.recibir_consulta()
        inicio, status, fallo = perf_counter(), 0, False

        async def enviar(message):
            nonlocal status
            if message["type"] == "http.response.start":
                status = message["status"]
            await send(message)

        with contexto_metricas(self.registro):
            try:
                await self.app(scope, receive, enviar)
            except Exception:
                fallo = True
                raise
            finally:
                duracion = (perf_counter() - inicio) * 1000
                self.registro.finalizar_consulta(
                    status=status, resultado=scope.get("metricas_resultado"), fallo=fallo,
                    duration_ms=duracion if scope.get("metricas_consulta_validada") else None,
                    bloqueo_seguridad=bool(scope.get("metricas_bloqueo_seguridad")),
                )
