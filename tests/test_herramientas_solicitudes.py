"""Pruebas de herramientas nativas sobre almacenamiento temporal."""

import json
import tempfile
import unittest
from pathlib import Path

from langchain_core.messages import ToolMessage
from langchain_core.tools import BaseTool
from langchain_core.utils.function_calling import convert_to_openai_tool
from pydantic import ValidationError

from grupo_e_tp_integrador_dsi.herramientas_solicitudes import (
    crear_herramientas_solicitudes,
    consultar_solicitud_interna,
    crear_solicitud_interna,
)


class HerramientasTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "solicitudes.sqlite"
        self.sensor, self.actuador = crear_herramientas_solicitudes(ruta_db=self.path)
        self.args = dict(categoria="IVA", descripcion="Revisar documentación pendiente",
                         clave_idempotencia="prueba-1", id_documental="DOC-007")

    async def test_01_registro(self):
        for herramienta in (self.sensor, self.actuador, consultar_solicitud_interna,
                            crear_solicitud_interna):
            self.assertIsInstance(herramienta, BaseTool)
            self.assertIsNotNone(herramienta.coroutine)
        self.assertFalse(self.path.exists())

    async def test_02_nombres_descripciones(self):
        self.assertEqual(self.sensor.name, "consultar_solicitud_interna")
        self.assertEqual(self.actuador.name, "crear_solicitud_interna")
        for herramienta in (self.sensor, self.actuador):
            spec = convert_to_openai_tool(herramienta)["function"]
            self.assertEqual(spec["name"], herramienta.name)
            for texto in ("Parámetros", "Retorno", "Errores"):
                self.assertIn(texto, spec["description"])

    async def test_03_validacion_pydantic(self):
        for datos in ({}, {**self.args, "categoria": 123}, {**self.args, "descripcion": None},
                      {**self.args, "clave_idempotencia": False},
                      {**self.args, "id_documental": 7}, {**self.args, "cuit": "extra"}):
            with self.subTest(datos=datos), self.assertRaises(ValidationError):
                await self.actuador.ainvoke(datos)
        with self.assertRaises(ValidationError):
            await self.sensor.ainvoke({"identificador": 123})
        self.assertFalse(self.path.exists())

    async def test_04_creacion(self):
        result = await self.actuador.ainvoke(self.args)
        self.assertEqual(result["resultado"], "creada")
        self.assertEqual(result["solicitud"]["estado"], "pendiente")
        self.assertEqual(result["solicitud"]["id_documental"], "DOC-007")
        self.assertNotIn("clave_idempotencia", result["solicitud"])
        self.assertEqual(json.loads(json.dumps(result)), result)

    async def test_05_consulta_posterior(self):
        creada = await self.actuador.ainvoke(self.args)
        result = await self.sensor.ainvoke({"identificador": creada["solicitud"]["id"]})
        self.assertEqual(result["resultado"], "encontrada")
        self.assertEqual(result["solicitud"], creada["solicitud"])
        self.assertEqual(set(result["solicitud"]),
                         {"id", "categoria", "descripcion", "estado", "creada_en", "id_documental"})

    async def test_06_inexistente(self):
        for inicializar in (False, True):
            if inicializar:
                await self.actuador.ainvoke(self.args)
            result = await self.sensor.ainvoke({"identificador": "inexistente"})
            self.assertEqual(result, {"resultado": "no_encontrada",
                                     "identificador": "inexistente", "solicitud": None})
            self.assertEqual(self.path.exists(), inicializar)

    async def test_07_idempotencia_conflicto(self):
        primera = await self.actuador.ainvoke(self.args)
        repetida = await self.actuador.ainvoke(self.args)
        self.assertEqual(repetida["resultado"], "existente")
        self.assertEqual(repetida["solicitud"], primera["solicitud"])
        conflicto = await self.actuador.ainvoke({**self.args, "descripcion": "Otra tarea"})
        self.assertEqual(conflicto, {"resultado": "conflicto", "solicitud": None})
        leida = await self.sensor.ainvoke({"identificador": primera["solicitud"]["id"]})
        self.assertEqual(leida["solicitud"], primera["solicitud"])

    async def test_08_rechazos_dominio(self):
        for campo, valor in (("categoria", "OTRA"), ("descripcion", ""),
                             ("descripcion", " " * 2), ("descripcion", "x" * 201),
                             ("descripcion", "Contactar ana@example.com"),
                             ("descripcion", "CUIT 20-30456789-9"),
                             ("clave_idempotencia", " "), ("id_documental", "incorrecto")):
            with self.subTest(campo=campo, valor=valor), self.assertRaises(ValueError):
                await self.actuador.ainvoke({**self.args, campo: valor})
        with self.assertRaises(ValueError):
            await self.sensor.ainvoke({"identificador": " "})
        self.assertFalse(self.path.exists())

    async def test_09_ruta_oculta(self):
        for herramienta in (self.sensor, self.actuador):
            spec = convert_to_openai_tool(herramienta)
            self.assertNotIn("ruta_db", json.dumps(spec))
            self.assertNotIn(str(self.path), json.dumps(spec))
            self.assertFalse(herramienta.args_schema.model_json_schema()["additionalProperties"])
        with self.assertRaises(ValidationError):
            await self.actuador.ainvoke({**self.args, "ruta_db": "otra.sqlite"})
        with self.assertRaises(ValidationError):
            await self.sensor.ainvoke({"identificador": "id", "ruta_db": "otra.sqlite"})
        self.assertFalse(self.path.exists())

    async def test_10_sensor_no_modifica(self):
        row = (await self.actuador.ainvoke(self.args))["solicitud"]
        before = self.path.read_bytes()
        await self.sensor.ainvoke({"identificador": row["id"]})
        await self.sensor.ainvoke({"identificador": "ausente"})
        self.assertEqual(self.path.read_bytes(), before)

    async def test_tool_call_serializable(self):
        mensaje = await self.actuador.ainvoke(
            {"type": "tool_call", "id": "call-1", "name": self.actuador.name, "args": self.args})
        self.assertIsInstance(mensaje, ToolMessage)
        self.assertEqual(mensaje.tool_call_id, "call-1")
        self.assertEqual(mensaje.status, "success")
        self.assertEqual(json.loads(mensaje.content)["resultado"], "creada")


if __name__ == "__main__":
    unittest.main()
