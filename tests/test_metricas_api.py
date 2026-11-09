"""Presentación HTTP del snapshot existente, sin proveedores ni bases reales."""

import asyncio
from contextlib import asynccontextmanager
import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import AsyncMock, Mock, patch

import httpx
from langchain_core.messages import AIMessage

from grupo_e_tp_integrador_dsi.api import crear_app
from grupo_e_tp_integrador_dsi.agente import AgenteContable
from grupo_e_tp_integrador_dsi.herramienta_rag import crear_herramienta_rag
from grupo_e_tp_integrador_dsi.herramientas_solicitudes import crear_herramientas_solicitudes
from test_agente import ModeloSimulado, call


class MetricasApiTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.fake = Mock()
        self.fake.ainvoke = AsyncMock(return_value={"resultado": "finalizada", "respuesta": "Respuesta"})
        self.fake.consultar_estado = AsyncMock(return_value={})

    @asynccontextmanager
    async def client(self, agent=None):
        @asynccontextmanager
        async def abrir():
            yield self.fake if agent is None else agent
        app = crear_app(abrir_agente=abrir)
        async with app.router.lifespan_context(app):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                yield client, app

    async def post(self, client, **kwargs):
        return await client.post("/consultar", json={"thread_id": "demo", "pregunta": "Hola", **kwargs})

    async def test_01_http_200_json(self):
        async with self.client() as (client, app):
            response = await client.get("/metricas")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["content-type"], "application/json")
        self.assertIsInstance(json.loads(response.text), dict)

    async def test_02_contrato_completo(self):
        async with self.client() as (client, app):
            expected = app.state.metricas.consultar()
            with patch.object(app.state.metricas, "consultar", wraps=app.state.metricas.consultar) as consultar:
                response = await client.get("/metricas")
                consultar.assert_called_once_with()
            schema = app.openapi()
        self.assertEqual(response.json(), expected)
        self.assertEqual(set(response.json()), {"consultas_recibidas", "consultas_completadas", "errores",
                         "consultas_por_resultado", "latencia_promedio_ms", "latencia_p95_ms",
                         "ejecuciones_herramientas", "herramientas_por_nombre", "bloqueos_seguridad"})
        self.assertIn("MetricasResponse", schema["components"]["schemas"])

    async def test_03_iniciales_cero(self):
        async with self.client() as (client, app):
            data = (await client.get("/metricas")).json()
        for value in data.values():
            if isinstance(value, dict):
                self.assertTrue(all(v == 0 for v in value.values()))
            else:
                self.assertEqual(value, 0)

    async def test_04_incremento_consultas(self):
        async with self.client() as (client, app):
            await self.post(client)
            data = (await client.get("/metricas")).json()
        self.assertEqual(data["consultas_recibidas"], 1)
        self.assertEqual(data["consultas_completadas"], 1)
        self.assertEqual(data["consultas_por_resultado"]["finalizada"], 1)

    async def test_05_errores(self):
        async with self.client() as (client, app):
            self.fake.ainvoke.side_effect = RuntimeError("privado")
            self.assertEqual((await self.post(client)).status_code, 500)
            self.fake.ainvoke.side_effect = None
            self.fake.ainvoke.return_value = {"resultado": "error", "respuesta": "Error controlado"}
            self.assertEqual((await self.post(client)).status_code, 200)
            data = (await client.get("/metricas")).json()
        self.assertEqual(data["errores"], 2)
        self.assertEqual(data["consultas_completadas"], 1)
        self.assertEqual(data["consultas_por_resultado"]["error"], 1)

    async def test_06_http_422(self):
        async with self.client() as (client, app):
            self.assertEqual((await self.post(client, pregunta="")).status_code, 422)
            data = (await client.get("/metricas")).json()
        self.assertEqual(data["consultas_recibidas"], 1)
        self.assertEqual(data["consultas_completadas"], 0)
        self.assertEqual(data["errores"], 0)
        self.assertEqual(data["latencia_p95_ms"], 0)

    async def test_07_herramientas(self):
        with tempfile.TemporaryDirectory() as temp:
            tools = [crear_herramienta_rag(pipeline_factory=Mock()),
                     *crear_herramientas_solicitudes(ruta_db=Path(temp) / "solicitudes.sqlite")]
            model = ModeloSimulado(call("consultar_solicitud_interna", {"identificador": "ausente"}),
                                   AIMessage(content="No encontrada"))
            agent = AgenteContable(modelo=model, herramientas=tools)
            async with self.client(agent) as (client, app):
                await self.post(client)
                data = (await client.get("/metricas")).json()
            self.assertFalse((Path(temp) / "solicitudes.sqlite").exists())
        self.assertEqual(data["ejecuciones_herramientas"], 1)
        self.assertEqual(data["herramientas_por_nombre"]["consultar_solicitud_interna"], 1)

    async def test_08_promedio_p95_sin_recalculo(self):
        async with self.client() as (client, app):
            for value in range(1, 21):
                app.state.metricas.recibir_consulta()
                app.state.metricas.finalizar_consulta(status=200, resultado="finalizada", duration_ms=value)
            expected = app.state.metricas.consultar()
            data = (await client.get("/metricas")).json()
        self.assertEqual(data, expected)
        self.assertEqual(data["latencia_promedio_ms"], 10.5)
        self.assertEqual(data["latencia_p95_ms"], 19)

    async def test_09_bloqueo_entrada_vacia(self):
        async with self.client() as (client, app):
            await self.post(client, pregunta="")
            data = (await client.get("/metricas")).json()
        self.assertEqual(data["bloqueos_seguridad"], 1)

    async def test_10_lecturas_sin_modificacion(self):
        async with self.client() as (client, app):
            await self.post(client)
            registro = app.state.metricas
            before = registro.consultar()
            for _ in range(4):
                self.assertEqual((await client.get("/metricas")).json(), before)
                self.assertIs(app.state.metricas, registro)
            self.assertEqual(registro.consultar(), before)

    async def test_11_sin_datos_sensibles(self):
        self.fake.ainvoke.return_value = {"resultado": "finalizada", "respuesta": "RESPUESTA_PRIVADA"}
        async with self.client() as (client, app):
            await self.post(client, thread_id="IDENTIFICADOR_PRIVADO", pregunta="PREGUNTA_PRIVADA")
            text = (await client.get("/metricas")).text
        for value in ("IDENTIFICADOR_PRIVADO", "PREGUNTA_PRIVADA", "RESPUESTA_PRIVADA", "thread_id",
                      "GEMINI_API_KEY", "prompt", "documento", "argumentos", "Traceback", "C:/"):
            self.assertNotIn(value, text)

    async def test_12_aislamiento_aplicaciones(self):
        async with self.client() as (client_a, app_a), self.client() as (client_b, app_b):
            await self.post(client_a)
            a = (await client_a.get("/metricas")).json()
            b = (await client_b.get("/metricas")).json()
        self.assertEqual(a["consultas_recibidas"], 1)
        self.assertEqual(b["consultas_recibidas"], 0)

    async def test_13_snapshot_concurrente(self):
        started, release = threading.Event(), threading.Event()
        async with self.client() as (client, app):
            registro = app.state.metricas
            def actualizar():
                for i in range(500):
                    registro.recibir_consulta()
                    registro.ejecutar_herramienta("consultar_rag")
                    registro.finalizar_consulta(status=200, resultado="finalizada", duration_ms=float(i))
                    if i == 0:
                        started.set()
                        if not release.wait(5):
                            raise RuntimeError("La lectura HTTP quedó bloqueada")
            task = asyncio.create_task(asyncio.to_thread(actualizar))
            try:
                await asyncio.wait_for(asyncio.to_thread(started.wait), 2)
                first = await asyncio.wait_for(client.get("/metricas"), 2)
                self.assertEqual(first.status_code, 200)
                release.set()
                responses = await asyncio.gather(*(client.get("/metricas") for _ in range(20)))
            finally:
                release.set()
                await task
            final = (await client.get("/metricas")).json()
        for response in [first, *responses]:
            data = response.json()
            self.assertEqual(data["consultas_completadas"], sum(data["consultas_por_resultado"].values()))
            self.assertEqual(data["ejecuciones_herramientas"], sum(data["herramientas_por_nombre"].values()))
            self.assertGreaterEqual(data["consultas_recibidas"], data["consultas_completadas"])
        self.assertEqual(final["consultas_completadas"], 500)

    async def test_14_error_registro_controlado(self):
        async with self.client() as (client, app):
            registro = app.state.metricas
            for replacement in (None, Mock(consultar=Mock(side_effect=RuntimeError("API_KEY=secreto C:/privado"))),
                                Mock(consultar=Mock(return_value={"credencial": "secreto"}))):
                app.state.metricas = replacement
                response = await client.get("/metricas")
                self.assertEqual(response.status_code, 503)
                self.assertEqual(response.json(), {"detail": "Métricas no disponibles."})
            del app.state.metricas
            self.assertEqual((await client.get("/metricas")).status_code, 503)
            self.assertEqual(registro.consultar()["errores"], 0)

    async def test_15_sin_proveedores_ni_sqlite(self):
        with patch("google.genai.Client", side_effect=AssertionError("Gemini")), \
             patch("chromadb.PersistentClient", side_effect=AssertionError("Chroma")), \
             patch("aiosqlite.connect", side_effect=AssertionError("SQLite async")), \
             patch("sqlite3.connect", side_effect=AssertionError("SQLite sync")):
            async with self.client() as (client, app):
                self.assertEqual((await client.get("/metricas")).status_code, 200)
        self.fake.ainvoke.assert_not_called()
        self.fake.consultar_estado.assert_not_called()


if __name__ == "__main__":
    unittest.main()
