"""Logs JSON con agentes simulados, sin proveedores ni bases reales."""

import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
import io
import json
import logging
from pathlib import Path
import tempfile
import unittest
from unittest.mock import AsyncMock, Mock, patch

import httpx
from langchain_core.messages import AIMessage, HumanMessage

from grupo_e_tp_integrador_dsi.api import crear_app
from grupo_e_tp_integrador_dsi.agente import AgenteContable
from grupo_e_tp_integrador_dsi.herramienta_rag import crear_herramienta_rag
from grupo_e_tp_integrador_dsi.herramientas_solicitudes import crear_herramientas_solicitudes
from grupo_e_tp_integrador_dsi.observabilidad import configurar_logger, contexto_hilo, registrar
from test_agente import ModeloSimulado, call


class ObservabilidadTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        logger = configurar_logger()
        self.old_stream = next(h.stream for h in logger.handlers if h.name == "agente-json")
        self.stream = io.StringIO()
        configurar_logger(stream=self.stream)
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.addCleanup(lambda: configurar_logger(stream=self.old_stream))
        self.fake = Mock()
        self.fake.ainvoke = AsyncMock(return_value={"resultado": "finalizada", "respuesta": "RESPUESTA_PRIVADA"})
        self.fake.consultar_estado = AsyncMock(return_value={})

    def records(self):
        return [json.loads(line) for line in self.stream.getvalue().splitlines()]

    @asynccontextmanager
    async def client(self, agente=None):
        @asynccontextmanager
        async def abrir():
            yield agente if agente is not None else self.fake
        app = crear_app(abrir_agente=abrir)
        async with app.router.lifespan_context(app):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                yield client

    def agent(self, model, **kwargs):
        tools = [crear_herramienta_rag(pipeline_factory=Mock()),
                 *crear_herramientas_solicitudes(ruta_db=Path(self.temp.name) / "solicitudes.sqlite")]
        return AgenteContable(modelo=model, herramientas=tools, **kwargs)

    async def test_01_json_valido(self):
        registrar("app.inicio")
        registrar("app.cierre")
        self.assertEqual(len(self.records()), 2)
        self.assertTrue(all(isinstance(r, dict) for r in self.records()))

    async def test_02_campos_obligatorios(self):
        with contexto_hilo("demo"):
            registrar("http.consulta.fin", duration_ms=12.3456, resultado="finalizada")
        record = self.records()[0]
        self.assertEqual(set(record), {"timestamp", "level", "event", "thread_id", "duration_ms", "resultado"})
        self.assertEqual(record["thread_id"], "demo")
        self.assertEqual(record["duration_ms"], 12.346)
        self.assertEqual(record["level"], "INFO")

    async def test_03_timestamp_utc(self):
        registrar("app.inicio")
        timestamp = datetime.fromisoformat(self.records()[0]["timestamp"])
        self.assertEqual(timestamp.utcoffset(), timedelta(0))

    async def test_04_http_inicio_fin_y_lifecycle(self):
        async with self.client() as client:
            response = await client.post("/consultar", json={"thread_id": "demo", "pregunta": "PREGUNTA_PRIVADA"})
        self.assertEqual(response.status_code, 200)
        records = self.records()
        self.assertEqual([r["event"] for r in records],
                         ["app.inicio", "http.consulta.inicio", "http.consulta.fin", "app.cierre"])
        self.assertEqual(records[2]["resultado"], "finalizada")
        self.assertGreaterEqual(records[2]["duration_ms"], 0)
        self.assertNotIn("PREGUNTA_PRIVADA", self.stream.getvalue())
        self.assertNotIn("RESPUESTA_PRIVADA", self.stream.getvalue())

    async def test_05_herramienta_registrada_una_vez(self):
        model = ModeloSimulado(call("consultar_solicitud_interna", {"identificador": "ausente"}),
                               AIMessage(content="No encontrada"))
        await self.agent(model).ainvoke("Estado", thread_id="demo")
        records = self.records()
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["event"], "herramienta.ejecutada")
        self.assertEqual(records[0]["herramienta"], "consultar_solicitud_interna")
        self.assertEqual(records[0]["resultado"], "no_encontrada")
        self.assertEqual(records[0]["thread_id"], "demo")

    async def test_06_errores_controlados(self):
        self.fake.ainvoke.side_effect = RuntimeError("API_KEY=secreto C:/privado")
        async with self.client() as client:
            response = await client.post("/consultar", json={"thread_id": "demo", "pregunta": "Hola"})
        self.assertEqual(response.status_code, 500)
        errors = [r for r in self.records() if r["event"] == "http.consulta.error"]
        self.assertEqual(len(errors), 1)
        self.assertEqual(errors[0]["categoria"], "consulta")
        self.assertEqual(errors[0]["level"], "ERROR")
        model = ModeloSimulado(call("crear_solicitud_interna", {"categoria": "IVA", "descripcion": "ana@example.com",
                                                               "clave_idempotencia": "clave-privada"}))
        result = await self.agent(model).ainvoke("Registrar tarea", thread_id="demo")
        self.assertEqual(result["resultado"], "error")
        tool_errors = [r for r in self.records() if r["event"] == "herramienta.error"]
        self.assertEqual(len(tool_errors), 1)
        self.assertEqual(tool_errors[0]["categoria"], "herramienta")

    async def test_07_limites(self):
        for config, category in (({"max_iteraciones": 1}, "iteraciones"), ({"max_llamadas": 1}, "llamadas")):
            model = ModeloSimulado(*(call("consultar_solicitud_interna", {"identificador": "ausente"}) for _ in range(3)))
            self.assertEqual((await self.agent(model, **config).ainvoke("Estado", thread_id=category))["resultado"], "limite")
        limits = [r for r in self.records() if r["event"] == "agente.limite"]
        self.assertEqual(len(limits), 2)
        self.assertEqual({r["categoria"] for r in limits}, {"iteraciones", "llamadas"})
        self.assertTrue(all(r["resultado"] == "limite" for r in limits))

    async def test_08_privacidad_y_formatter(self):
        registrar("app.error", categoria="inicializacion", resultado="error",
                  pregunta="PREGUNTA_PRIVADA", GEMINI_API_KEY="CLAVE_PRIVADA", documento="DOCUMENTO_PRIVADO")
        try:
            raise RuntimeError("EXCEPCION_PRIVADA")
        except RuntimeError:
            configurar_logger().error("PROMPT_PRIVADO %s", "ARGUMENTO_PRIVADO", exc_info=True,
                                      extra={"event": "agente.error"})
        await self.agent(ModeloSimulado(RuntimeError("CLAVE_PRIVADA"))).ainvoke("PREGUNTA_PRIVADA")
        encoded = self.stream.getvalue()
        for value in ("CLAVE_PRIVADA", "GEMINI_API_KEY", "PREGUNTA_PRIVADA", "DOCUMENTO_PRIVADO",
                      "EXCEPCION_PRIVADA", "PROMPT_PRIVADO", "ARGUMENTO_PRIVADO", "Traceback"):
            self.assertNotIn(value, encoded)
        self.assertEqual(len(self.records()), 3)

    async def test_09_handlers_no_duplicados(self):
        for _ in range(10):
            logger = configurar_logger()
        self.assertEqual(len([h for h in logger.handlers if h.name == "agente-json"]), 1)
        self.assertFalse(logger.propagate)
        registrar("app.inicio")
        self.assertEqual(len(self.records()), 1)

    async def test_10_contratos_http_sin_cambios(self):
        async with self.client() as client:
            self.assertEqual((await client.get("/health")).json(), {"status": "ok", "service": "agente-contable"})
            self.assertEqual((await client.post("/consultar", json={"thread_id": "demo", "pregunta": "Hola"})).json(),
                             {"thread_id": "demo", "resultado": "finalizada", "respuesta": "RESPUESTA_PRIVADA"})
            self.assertEqual((await client.get("/estado/demo")).json(),
                             {"thread_id": "demo", "existe": False, "cantidad_mensajes": 0, "ultimo_resultado": None})
            self.assertEqual((await client.post("/consultar", json={"thread_id": "demo", "pregunta": ""})).status_code, 422)

    async def test_11_sin_proveedores(self):
        with patch("google.genai.Client", side_effect=AssertionError("Gemini")), \
             patch("chromadb.PersistentClient", side_effect=AssertionError("Chroma")), \
             patch("aiosqlite.connect", side_effect=AssertionError("SQLite real")):
            async with self.client() as client:
                self.assertEqual((await client.post("/consultar", json={"thread_id": "demo", "pregunta": "Hola"})).status_code, 200)

    async def test_12_contexto_concurrente(self):
        class Model:
            def bind_tools(self, tools):
                return self
            async def ainvoke(self, messages):
                await asyncio.sleep(0)
                if isinstance(messages[-1], HumanMessage):
                    return call("consultar_solicitud_interna", {"identificador": "ausente"})
                return AIMessage(content="No encontrada")
        async with self.client(self.agent(Model())) as client:
            responses = await asyncio.gather(*(client.post("/consultar", json={"thread_id": id_, "pregunta": "Estado"})
                                               for id_ in ("A", "B")))
        self.assertTrue(all(r.status_code == 200 for r in responses))
        records = self.records()
        for id_ in ("A", "B"):
            events = [r["event"] for r in records if r.get("thread_id") == id_]
            self.assertEqual(events, ["http.consulta.inicio", "herramienta.ejecutada", "http.consulta.fin"])
        self.assertNotIn("thread_id", records[-1])  # El contexto no escapa al cierre.

    async def test_13_fallo_inicio_sin_trazas(self):
        @asynccontextmanager
        async def abrir():
            raise RuntimeError("EXCEPCION_PRIVADA")
            yield
        app = crear_app(abrir_agente=abrir)
        with self.assertRaises(RuntimeError):
            async with app.router.lifespan_context(app):
                pass
        self.assertEqual([r["event"] for r in self.records()], ["app.inicio", "app.error", "app.cierre"])
        self.assertNotIn("EXCEPCION_PRIVADA", self.stream.getvalue())


if __name__ == "__main__":
    unittest.main()
