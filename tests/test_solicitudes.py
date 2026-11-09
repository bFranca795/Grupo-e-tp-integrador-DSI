"""Pruebas del almacenamiento: solamente bases temporales, sin APIs."""

import asyncio
import hashlib
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch
from uuid import UUID

import aiosqlite

from grupo_e_tp_integrador_dsi.solicitudes import (
    PROJECT_ROOT, RUTA_DB, crear_solicitud, consultar_solicitud,
)


class SolicitudesTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.path = self.root / "data" / "agente" / "solicitudes.sqlite"

    async def crear(self, **kwargs):
        datos = dict(categoria="IVA", descripcion="Revisar documentación del período",
                     clave_idempotencia="operacion-1", id_documental="DOC-007")
        datos.update(kwargs)
        return await crear_solicitud(**datos, ruta_db=self.path)

    async def test_01_crear_valida(self):
        result = await self.crear()
        self.assertEqual(result.resultado, "creada")
        row = result.solicitud
        UUID(row.id)
        self.assertEqual(row.estado, "pendiente")
        self.assertEqual(row.categoria, "IVA")
        self.assertEqual(row.id_documental, "DOC-007")
        self.assertEqual(datetime.fromisoformat(row.creada_en).utcoffset(), timedelta(0))
        for categoria in ("MONOTRIBUTO", "TRAMITES"):
            self.assertEqual((await self.crear(categoria=categoria, clave_idempotencia=categoria,
                                             id_documental=None)).resultado, "creada")

    async def test_02_consultar_existente_sin_escritura(self):
        row = (await self.crear()).solicitud
        before = self.path.read_bytes()
        self.assertEqual(await consultar_solicitud(row.id, ruta_db=self.path), row)
        self.assertEqual(self.path.read_bytes(), before)

    async def test_03_inexistente(self):
        self.assertIsNone(await consultar_solicitud("ausente", ruta_db=self.path))
        self.assertFalse(self.path.exists())
        await self.crear()
        self.assertIsNone(await consultar_solicitud("ausente", ruta_db=self.path))

    async def test_04_persistencia_reapertura(self):
        row = (await self.crear()).solicitud  # La función ya cerró su conexión.
        async with aiosqlite.connect(self.path) as db:
            async with db.execute("SELECT id, estado FROM solicitudes") as cursor:
                self.assertEqual(await cursor.fetchone(), (row.id, "pendiente"))
        self.assertEqual(await consultar_solicitud(row.id, ruta_db=self.path), row)

    async def test_05_idempotencia(self):
        first, second = await self.crear(), await self.crear()
        self.assertEqual(second.resultado, "existente")
        self.assertEqual(first.solicitud, second.solicitud)
        async with aiosqlite.connect(self.path) as db:
            async with db.execute("SELECT count(*) FROM solicitudes") as cursor:
                self.assertEqual((await cursor.fetchone())[0], 1)

    async def test_06_conflicto(self):
        first = (await self.crear()).solicitud
        for cambio in (dict(descripcion="Otra tarea"), dict(categoria="TRAMITES"),
                       dict(id_documental="DOC-003")):
            with self.subTest(cambio=cambio):
                result = await self.crear(**cambio)
                self.assertEqual(result.resultado, "conflicto")
                self.assertIsNone(result.solicitud)
                self.assertEqual(await consultar_solicitud(first.id, ruta_db=self.path), first)

    async def test_07_categoria_invalida(self):
        for categoria in ("GANANCIAS", "iva", None, []):
            with self.subTest(categoria=categoria), self.assertRaises(ValueError):
                await self.crear(categoria=categoria)
        self.assertFalse(self.path.exists())

    async def test_08_limites_descripcion(self):
        for texto in ("", "   ", "x" * 201, " " + "x" * 200, None):
            with self.subTest(texto=texto), self.assertRaises(ValueError):
                await self.crear(descripcion=texto)
        self.assertEqual((await self.crear(descripcion="x" * 200)).resultado, "creada")

    async def test_09_datos_personales(self):
        for texto in ("Contactar ana@example.com", "CUIT 20-30456789-9", "DNI 30.456.789",
                      "Llamar al +54 (11) 4567-8901", "Revisar 20304567899",
                      "Teléfono de contacto", "Domicilio particular", "Saldo $1500"):
            with self.subTest(texto=texto), self.assertRaises(ValueError):
                await self.crear(descripcion=texto)
        self.assertFalse(self.path.exists())

    async def test_10_aislamiento(self):
        checkpoints = self.path.parent / "checkpoints.sqlite"
        chroma = self.root / "chroma_db" / "chroma.sqlite3"
        for path in (checkpoints, chroma):
            path.parent.mkdir(parents=True, exist_ok=True)
            async with aiosqlite.connect(path) as db:
                await db.execute("CREATE TABLE testigo (valor TEXT)")
                await db.execute("INSERT INTO testigo VALUES (?)", ("intacto",))
                await db.commit()
        def snapshot():
            return {str(p.relative_to(self.root)): hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in self.root.rglob("*") if p.is_file() and p != self.path}
        before = snapshot()
        original_connect = aiosqlite.connect
        with patch("grupo_e_tp_integrador_dsi.solicitudes.aiosqlite.connect",
                   wraps=original_connect) as connect:
            row = (await self.crear()).solicitud
            await consultar_solicitud(row.id, ruta_db=self.path)
            self.assertEqual(connect.call_count, 2)
            self.assertEqual(Path(connect.call_args_list[0].args[0]), self.path)
            self.assertEqual(connect.call_args_list[1].args[0], self.path.as_uri() + "?mode=ro")
        self.assertEqual(snapshot(), before)

    async def test_clave_vacia_y_campos_extra(self):
        for clave in ("", "  ", None):
            with self.assertRaises(ValueError):
                await self.crear(clave_idempotencia=clave)
        for campo in ("cuit", "correo", "telefono", "saldo"):
            with self.subTest(campo=campo), self.assertRaises(TypeError):
                await self.crear(**{campo: "dato"})
        with self.assertRaises(ValueError):
            await self.crear(id_documental="persona@example.com")
        self.assertFalse(self.path.exists())

    async def test_concurrencia_misma_clave(self):
        resultados = await asyncio.gather(*(self.crear() for _ in range(5)))
        self.assertEqual(sum(r.resultado == "creada" for r in resultados), 1)
        self.assertEqual(len({r.solicitud.id for r in resultados}), 1)

    async def test_sql_parametrizado(self):
        row = (await self.crear(descripcion="Revisar '); DROP TABLE solicitudes; --")).solicitud
        self.assertEqual(await consultar_solicitud(row.id, ruta_db=self.path), row)
        self.assertIsNone(await consultar_solicitud("' OR 1=1 --", ruta_db=self.path))

    def test_ruta_desde_raiz(self):
        self.assertEqual(RUTA_DB, PROJECT_ROOT / "data/agente/solicitudes.sqlite")
        self.assertTrue(RUTA_DB.is_absolute())
        self.assertEqual(PROJECT_ROOT, Path(__file__).resolve().parents[1])


if __name__ == "__main__":
    unittest.main()
