"""Herramientas asíncronas de solicitudes, sin agente ni integraciones externas."""

from dataclasses import asdict
from pathlib import Path

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, ConfigDict, Field

from . import solicitudes


class ArgumentosCrearSolicitud(BaseModel):
    """Tipos de entrada; las reglas de negocio pertenecen a solicitudes.py."""

    model_config = ConfigDict(extra="forbid", strict=True)
    categoria: str = Field(description="Categoría permitida: IVA, MONOTRIBUTO o TRAMITES.")
    descripcion: str = Field(description="Tarea ficticia, breve, sin datos personales; máximo 200 caracteres.")
    clave_idempotencia: str = Field(description="Clave no vacía para evitar creaciones duplicadas.")
    id_documental: str | None = Field(default=None, description="Referencia DOC-000 opcional; admite sufijo de colisión -dup-N.")


class ArgumentosConsultarSolicitud(BaseModel):
    """Identificador público de la solicitud que se desea consultar."""

    model_config = ConfigDict(extra="forbid", strict=True)
    identificador: str = Field(description="ID de solicitud devuelto por crear_solicitud_interna.")


def _datos_publicos(solicitud: solicitudes.Solicitud | None) -> dict | None:
    if solicitud is None:
        return None
    datos = asdict(solicitud)
    datos.pop("clave_idempotencia")
    return datos


def crear_herramientas_solicitudes(
    *, ruta_db: Path = solicitudes.RUTA_DB,
) -> tuple[StructuredTool, StructuredTool]:
    """Configura sensor y actuador; la ruta queda capturada fuera del esquema LLM.

    No abre conexiones ni crea archivos hasta invocar el actuador.
    """
    ruta_interna = Path(ruta_db).resolve()

    async def consultar_solicitud_interna(identificador: str) -> dict:
        """Consulta una solicitud administrativa ficticia sin modificar la base.

        Parámetros:
            identificador: ID de solicitud recibido al crearla.
        Retorno:
            Diccionario serializable con resultado 'encontrada' y solicitud
            (id, categoria, descripcion, estado, creada_en UTC e id_documental),
            o resultado 'no_encontrada', identificador consultado y solicitud null.
        Errores:
            Pydantic rechaza tipos incorrectos y campos adicionales. ValueError
            indica un identificador vacío. Los fallos de SQLite/E/S se propagan.
        Esta herramienta no consulta estados fiscales ni organismos externos.
        """
        solicitud = await solicitudes.consultar_solicitud(identificador, ruta_db=ruta_interna)
        return {
            "resultado": "encontrada" if solicitud else "no_encontrada",
            "identificador": identificador,
            "solicitud": _datos_publicos(solicitud),
        }

    async def crear_solicitud_interna(
        categoria: str, descripcion: str, clave_idempotencia: str,
        id_documental: str | None = None,
    ) -> dict:
        """Registra una tarea administrativa ficticia; no realiza operaciones contables.

        Parámetros:
            categoria: IVA, MONOTRIBUTO o TRAMITES.
            descripcion: Tarea no vacía de hasta 200 caracteres sin datos personales.
            clave_idempotencia: Clave no vacía; repetir el mismo contenido no duplica.
            id_documental: Referencia DOC-000 opcional; admite sufijo de colisión -dup-N del ETL.
        Retorno:
            Diccionario serializable con resultado 'creada' o 'existente' y datos
            públicos de la solicitud, inicialmente pendiente. Una clave ya usada
            con contenido diferente devuelve 'conflicto' y solicitud null.
        Errores:
            Pydantic rechaza tipos incorrectos y campos adicionales. ValueError
            conserva los rechazos de dominio de solicitudes.py. Los fallos de
            SQLite/E/S se propagan; ningún error se presenta como éxito.
        No presenta declaraciones, registra pagos ni envía comunicaciones.
        """
        resultado = await solicitudes.crear_solicitud(
            categoria, descripcion, clave_idempotencia, id_documental,
            ruta_db=ruta_interna,
        )
        return {"resultado": resultado.resultado,
                "solicitud": _datos_publicos(resultado.solicitud)}

    sensor = StructuredTool.from_function(
        coroutine=consultar_solicitud_interna,
        args_schema=ArgumentosConsultarSolicitud,
        infer_schema=False,
    )
    actuador = StructuredTool.from_function(
        coroutine=crear_solicitud_interna,
        args_schema=ArgumentosCrearSolicitud,
        infer_schema=False,
    )
    return sensor, actuador


consultar_solicitud_interna, crear_solicitud_interna = crear_herramientas_solicitudes()
