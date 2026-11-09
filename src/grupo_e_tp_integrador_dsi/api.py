r"""API inicial: /health verifica la aplicación, no los proveedores externos.

Desde la raíz del repositorio, en PowerShell:
.\.tools\env-agente\Scripts\python.exe -m uvicorn grupo_e_tp_integrador_dsi.api:app --app-dir src --host 127.0.0.1 --port 8000

El agente y sus recursos se inicializan únicamente al entrar al lifespan.
"""

from collections.abc import Callable
from contextlib import asynccontextmanager
import asyncio
from typing import Annotated, Literal, get_args

from fastapi import FastAPI, HTTPException, Path as PathParam, Request
from fastapi.exceptions import RequestValidationError
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.responses import JSONResponse
from pydantic import AfterValidator, BaseModel, ConfigDict, Field, field_validator

from .observabilidad import consulta_http, registrar
from .metricas import MetricasMiddleware, RegistroMetricas
from .seguridad import validar_entrada, detectar_prompt_injection, enmascarar_pii


class ConsultaRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    thread_id: str = Field(min_length=1, max_length=128)
    pregunta: str = Field(min_length=1, max_length=2000)

    @field_validator("thread_id", "pregunta")
    @classmethod
    def no_vacio(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("El campo no puede estar vacío.")
        return value


ResultadoPublico = Literal["finalizada", "sin_evidencia", "requiere_vinculacion", "limite", "error"]


class ConsultaResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    thread_id: str
    resultado: ResultadoPublico
    respuesta: str


class DetalleRechazo(BaseModel):
    motivo: Literal["estructura_invalida", "entrada_vacia", "longitud_excedida",
                    "prompt_injection", "tipo_invalido", "unicode_invalido"]


class RechazoConsultaResponse(BaseModel):
    detail: DetalleRechazo


class EstadoResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    thread_id: str
    existe: bool
    cantidad_mensajes: int = Field(ge=0)
    ultimo_resultado: ResultadoPublico | None


Contador = Annotated[int, Field(ge=0)]
Latencia = Annotated[float, Field(ge=0, allow_inf_nan=False)]


class ResultadosMetricas(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    finalizada: Contador
    sin_evidencia: Contador
    requiere_vinculacion: Contador
    limite: Contador
    error: Contador


class HerramientasMetricas(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    consultar_rag: Contador
    consultar_solicitud_interna: Contador
    crear_solicitud_interna: Contador


class MetricasResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    consultas_recibidas: Contador
    consultas_completadas: Contador
    errores: Contador
    consultas_por_resultado: ResultadosMetricas
    latencia_promedio_ms: Latencia
    latencia_p95_ms: Latencia
    ejecuciones_herramientas: Contador
    herramientas_por_nombre: HerramientasMetricas
    bloqueos_seguridad: Contador


def crear_app(*, abrir_agente: Callable | None = None) -> FastAPI:
    """Permite inyectar un contexto de agente para pruebas sin recursos reales."""
    locks = {}

    @asynccontextmanager
    async def serializar(thread_id):
        # Un event loop/proceso: sin awaits entre buscar, registrar y referenciar.
        # Se cuenta también a quienes esperan; retirar al último evita fuga de IDs.
        entry = locks.setdefault(thread_id, [asyncio.Lock(), 0])
        entry[1] += 1
        try:
            async with entry[0]:
                yield
        finally:
            entry[1] -= 1
            if entry[1] == 0:
                locks.pop(thread_id, None)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        registrar("app.inicio")
        try:
            abrir = abrir_agente
            if abrir is None:
                from .agente import AgenteContable

                abrir = AgenteContable.abrir
            async with abrir() as agente:
                app.state.agente = agente
                try:
                    yield
                finally:
                    app.state.agente = None
        except Exception:
            registrar("app.error", level=40, categoria="inicializacion", resultado="error")
            raise
        finally:
            registrar("app.cierre")

    app = FastAPI(title="Agente contable", lifespan=lifespan)
    app.state.agente = None
    app.state.metricas = RegistroMetricas()
    app.add_middleware(MetricasMiddleware, registro=app.state.metricas)

    def rechazar(request: Request, motivo: str, *, seguridad: bool) -> JSONResponse:
        request.scope["metricas_bloqueo_seguridad"] = seguridad
        return JSONResponse(status_code=422, content=RechazoConsultaResponse(
            detail=DetalleRechazo(motivo=motivo)).model_dump())

    @app.exception_handler(RequestValidationError)
    async def validacion_http(request: Request, exc: RequestValidationError):
        if request.method == "GET" and request.scope.get("route") is not None and (
                request.scope["route"].path == "/estado/{thread_id:path}"):
            # El handler por defecto refleja input; no publicar IDs inválidos.
            return rechazar(request, "estructura_invalida", seguridad=False)
        if request.method != "POST" or request.url.path != "/consultar":
            return await request_validation_exception_handler(request, exc)
        # Mantener Pydantic y clasificar solo sus rechazos de contenido/longitud.
        # Cualquier defecto estructural tiene prioridad; nunca reflejar input/ctx.
        errores = exc.errors()
        if (errores and isinstance(exc.body, dict)
                and isinstance(exc.body.get("pregunta"), str)
                and all(e["loc"] == ("body", "pregunta") and e["type"] in
                        {"string_too_short", "string_too_long", "value_error", "string_unicode"}
                        for e in errores)):
            validacion = validar_entrada(exc.body["pregunta"])
            if not validacion["permitida"]:
                return rechazar(request, validacion["motivo"], seguridad=True)
        return rechazar(request, "estructura_invalida", seguridad=False)

    @app.get("/health")
    async def health() -> dict[str, str]:
        """Indica que la aplicación atiende HTTP; no comprueba servicios externos."""
        return {"status": "ok", "service": "agente-contable"}

    @app.get("/metricas", response_model=MetricasResponse)
    def metricas(request: Request) -> MetricasResponse:
        """Expone el snapshot existente sin recalcular ni modificar sus valores.

        Endpoint administrativo: antes de publicar la API debe protegerse mediante
        autenticación o acceso restringido. No incorpora autenticación en esta etapa.
        FastAPI ejecuta esta lectura síncrona en un worker thread para que ordenar
        las muestras del registro no bloquee el event loop.
        """
        try:
            return MetricasResponse.model_validate(request.app.state.metricas.consultar())
        except Exception:
            raise HTTPException(status_code=503, detail="Métricas no disponibles.") from None

    @app.post("/consultar", response_model=ConsultaResponse,
              responses={422: {"model": RechazoConsultaResponse}})
    async def consultar(consulta: ConsultaRequest, request: Request) -> ConsultaResponse | JSONResponse:
        """Continúa un hilo con el agente compartido, sin exponer su estado interno.

        El bloqueo cubre la ejecución completa por hilo dentro de este proceso.
        Ejecutar con un solo worker; no coordina procesos ni servidores distintos.
        La seguridad se valida antes del bloqueo y del agente. Solo se enmascara
        la copia pública de respuesta; el historial persistido permanece intacto.
        Si el filtro falla, se devuelve 500 genérico, nunca texto sin filtrar.
        """
        try:
            for validar in (validar_entrada, detectar_prompt_injection):
                validacion = validar(consulta.pregunta)
                if not validacion["permitida"]:
                    return rechazar(request, validacion["motivo"], seguridad=True)
            request.scope["metricas_consulta_validada"] = True
            with consulta_http(consulta.thread_id, "consultar") as log:
                async with serializar(consulta.thread_id):
                    agente = request.app.state.agente
                    resultado = await agente.ainvoke(consulta.pregunta, thread_id=consulta.thread_id)
                    respuesta = ConsultaResponse(thread_id=consulta.thread_id,
                                                 resultado=resultado["resultado"],
                                                 respuesta=enmascarar_pii(resultado["respuesta"]))
                    log["resultado"] = respuesta.resultado
                    request.scope["metricas_resultado"] = respuesta.resultado
                    return respuesta
        except Exception:
            raise HTTPException(status_code=500, detail="No se pudo procesar la consulta.") from None

    # El convertidor path permite validar también un segmento vacío con HTTP 422.
    @app.get("/estado/{thread_id:path}", response_model=EstadoResponse,
             responses={422: {"model": RechazoConsultaResponse}})
    async def estado(
        thread_id: Annotated[str, PathParam(min_length=1, max_length=128, pattern=r"\S"),
                             AfterValidator(ConsultaRequest.no_vacio)],
        request: Request,
    ) -> EstadoResponse:
        """Lee un resumen del checkpoint bajo el mismo bloqueo que POST /consultar.

        final contiene el resultado público persistido por el grafo. Si falta o
        no tiene la estructura esperada, no se infiere a partir de los mensajes.
        La coordinación es local a este proceso, como en /consultar.
        """
        try:
            with consulta_http(thread_id, "estado") as log:
                async with serializar(thread_id):
                    persisted = await request.app.state.agente.consultar_estado(thread_id)
                    if not isinstance(persisted, dict):
                        raise ValueError("Estado inesperado")
                    messages = persisted.get("mensajes", [])
                    if not isinstance(messages, list):
                        raise ValueError("Mensajes inesperados")
                    final = persisted.get("final")
                    ultimo = None
                    if (isinstance(final, dict) and isinstance(final.get("respuesta"), str)
                            and final.get("resultado") in get_args(ResultadoPublico)):
                        ultimo = final["resultado"]
                    if ultimo is not None:
                        log["resultado"] = ultimo
                    return EstadoResponse(thread_id=thread_id, existe=bool(persisted),
                                          cantidad_mensajes=len(messages), ultimo_resultado=ultimo)
        except Exception:
            raise HTTPException(status_code=500, detail="No se pudo consultar el estado.") from None

    return app


app = crear_app()
