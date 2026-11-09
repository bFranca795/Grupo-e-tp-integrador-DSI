"""Almacenamiento local de solicitudes ficticias; sin integraciones externas."""

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal
from uuid import uuid4

import aiosqlite


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RUTA_DB = PROJECT_ROOT / "data" / "agente" / "solicitudes.sqlite"
CATEGORIAS = {"IVA", "MONOTRIBUTO", "TRAMITES"}
SCHEMA = """
CREATE TABLE IF NOT EXISTS solicitudes (
    id TEXT PRIMARY KEY,
    categoria TEXT NOT NULL CHECK (categoria IN ('IVA', 'MONOTRIBUTO', 'TRAMITES')),
    descripcion TEXT NOT NULL CHECK (length(trim(descripcion)) BETWEEN 1 AND 200),
    clave_idempotencia TEXT NOT NULL UNIQUE CHECK (length(trim(clave_idempotencia)) > 0),
    id_documental TEXT,
    creada_en TEXT NOT NULL,
    estado TEXT NOT NULL DEFAULT 'pendiente' CHECK (estado = 'pendiente')
)
"""
# Heurísticas deliberadamente conservadoras; no equivalen a un detector de PII.
PERSONALES = re.compile(
    r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}"
    r"|(?<!\w)(?:\+?\d[\s().-]*){7,}(?!\w)"
    r"|\b(?:CUIT|CUIL|DNI|email|e-mail|correo|tel[eé]fono|celular|CBU|CVU|"
    r"domicilio|direcci[oó]n|nombre\s+y\s+apellido)\b"
    r"|(?:\$|\bARS\b|\bUSD\b)\s*\d",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class Solicitud:
    id: str
    categoria: str
    descripcion: str
    clave_idempotencia: str
    id_documental: str | None
    creada_en: str
    estado: str


@dataclass(frozen=True)
class ResultadoCreacion:
    resultado: Literal["creada", "existente", "conflicto"]
    solicitud: Solicitud | None


def _validar(categoria, descripcion, clave_idempotencia, id_documental):
    if not isinstance(categoria, str) or categoria not in CATEGORIAS:
        raise ValueError("Categoría inválida: usar IVA, MONOTRIBUTO o TRAMITES.")
    if (not isinstance(descripcion, str) or not descripcion.strip()
            or len(descripcion) > 200 or "\x00" in descripcion):
        raise ValueError("La descripción debe tener entre 1 y 200 caracteres, sin NUL.")
    if PERSONALES.search(descripcion):
        raise ValueError("La descripción contiene posibles datos personales o sensibles.")
    if (not isinstance(clave_idempotencia, str) or not clave_idempotencia.strip()
            or "\x00" in clave_idempotencia):
        raise ValueError("La clave de idempotencia debe ser no vacía y no contener NUL.")
    if id_documental is not None and (
        not isinstance(id_documental, str) or len(id_documental) > 128
        or not re.fullmatch(r"DOC-\d{3}(?:-dup-[1-9]\d*)?", id_documental)
    ):
        raise ValueError("El ID documental debe tener formato DOC-000, con sufijo -dup-N opcional.")
    return descripcion.strip(), clave_idempotencia.strip()


async def crear_solicitud(
    categoria: str,
    descripcion: str,
    clave_idempotencia: str,
    id_documental: str | None = None,
    *,
    ruta_db: Path = RUTA_DB,
) -> ResultadoCreacion:
    """Crea o recupera una solicitud; la misma clave con otro payload es conflicto.

    ruta_db permite aislar pruebas. No se aceptan campos adicionales del dominio.
    Los errores de validación son ValueError; los fallos de E/S se propagan.
    """
    descripcion, clave = _validar(categoria, descripcion, clave_idempotencia, id_documental)
    path = Path(ruta_db).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(path, timeout=5) as db:
        db.row_factory = aiosqlite.Row
        await db.execute(SCHEMA)
        await db.commit()
        try:
            async with db.execute(
                """INSERT INTO solicitudes
                (id, categoria, descripcion, clave_idempotencia, id_documental, creada_en, estado)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(clave_idempotencia) DO NOTHING""",
                (str(uuid4()), categoria, descripcion, clave, id_documental,
                 datetime.now(timezone.utc).isoformat(), "pendiente"),
            ) as cursor:
                creada = cursor.rowcount == 1
            async with db.execute(
                "SELECT * FROM solicitudes WHERE clave_idempotencia = ?", (clave,)
            ) as cursor:
                row = await cursor.fetchone()
            await db.commit()
        except BaseException:
            await db.rollback()
            raise
    solicitud = Solicitud(**dict(row))
    if (solicitud.categoria, solicitud.descripcion, solicitud.id_documental) != (
        categoria, descripcion, id_documental
    ):
        return ResultadoCreacion("conflicto", None)
    return ResultadoCreacion("creada" if creada else "existente", solicitud)


async def consultar_solicitud(
    identificador: str, *, ruta_db: Path = RUTA_DB,
) -> Solicitud | None:
    """Devuelve None si no existe. Abre SQLite en modo de solo lectura."""
    if not isinstance(identificador, str) or not identificador.strip():
        raise ValueError("El identificador no puede estar vacío.")
    path = Path(ruta_db).resolve()
    if not path.exists():
        return None
    async with aiosqlite.connect(path.as_uri() + "?mode=ro", uri=True, timeout=5) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?", ("solicitudes",)
        ) as cursor:
            if await cursor.fetchone() is None:
                return None
        async with db.execute("SELECT * FROM solicitudes WHERE id = ?", (identificador,)) as cursor:
            row = await cursor.fetchone()
    return Solicitud(**dict(row)) if row else None
