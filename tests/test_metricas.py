"""Contabilización y snapshots de métricas sin proveedores ni bases reales."""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import AsyncMock, Mock, patch

import httpx
from langchain_core.messages import AIMessage

from grupo_e_tp_integrador_dsi.api import crear_app
from grupo_e_tp_integrador_dsi.agente import AgenteContable
from grupo_e_tp_integrador_dsi.herramienta_rag import crear_herramienta_rag
from grupo_e_tp_integrador_dsi.herramientas_solicitudes import crear_herramientas_solicitudes
from grupo_e_tp_integrador_dsi.metricas import RegistroMetricas
from grupo_e_tp_integrador_dsi.observabilidad import registrar
from test_agente import ModeloSimulado, call


class MetricasTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.registro = RegistroMetricas()
        self.fake = Mock()
        self.fake.ainvoke = AsyncMock(return_value={"resultado": "finalizada", "respuesta": "Respuesta"})
        self.fake.consultar_estado = AsyncMock(return_value={})
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)

    @asynccontextmanager
    async def client(self, agent=None):
        @asynccontextmanager
        async def abrir():
            yield self.fake if agent is None else agent
        app = crear_app(abrir_agente=abrir)
        async with app.router.lifespan_context(app):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                yield client, app.state.metricas

    async def post(self, client, **kwargs):
        return await client.post("/consultar", json={"thread_id": "demo", "pregunta": "Hola", **kwargs})

    def agent(self, model):
        pipeline = Mock()
        pipeline.invoke.return_value = {"status": "ok", "answer": "Requisitos [DOC-002]",
                                        "sources": [{"id": "DOC-002"}]}
        tools = [crear_herramienta_rag(pipeline_factory=Mock(return_value=pipeline)),
                 *crear_herramientas_solicitudes(ruta_db=Path(self.temp.name) / "solicitudes.sqlite")]
        return AgenteContable(modelo=model, herramientas=tools)

    async def test_01_estado_inicial(self):
        data = self.registro.consultar()
        for key in ("consultas_recibidas", "consultas_completadas", "errores", "ejecuciones_herramientas",
                    "latencia_promedio_ms", "latencia_p95_ms", "bloqueos_seguridad"):
            self.assertEqual(data[key], 0)
        self.assertTrue(all(v == 0 for v in data["consultas_por_resultado"].values()))
        self.assertTrue(all(v == 0 for v in data["herramientas_por_nombre"].values()))

    async def test_02_recibida_antes_de_ejecutar(self):
        entered, release = asyncio.Event(), asyncio.Event()
        async def invoke(*args, **kwargs):
            entered.set()
            await release.wait()
            return {"resultado": "finalizada", "respuesta": "Texto"}
        self.fake.ainvoke.side_effect = invoke
        async with self.client() as (client, metrics):
            task = asyncio.create_task(self.post(client))
            await asyncio.wait_for(entered.wait(), 2)
            data = metrics.consultar()
            self.assertEqual(data["consultas_recibidas"], 1)
            self.assertEqual(data["consultas_completadas"], 0)
            release.set()
            await task

    async def test_03_completada(self):
        async with self.client() as (client, metrics):
            self.assertEqual((await self.post(client)).status_code, 200)
            data = metrics.consultar()
        self.assertEqual(data["consultas_completadas"], 1)
        self.assertEqual(data["errores"], 0)

    async def test_04_error_inesperado(self):
        self.fake.ainvoke.side_effect = RuntimeError("secreto")
        async with self.client() as (client, metrics):
            self.assertEqual((await self.post(client)).status_code, 500)
            data = metrics.consultar()
        self.assertEqual(data["consultas_recibidas"], 1)
        self.assertEqual(data["consultas_completadas"], 0)
        self.assertEqual(data["errores"], 1)
        self.assertEqual(sum(data["consultas_por_resultado"].values()), 0)
        self.assertGreater(data["latencia_promedio_ms"], 0)
        # Un fallo posterior al inicio HTTP 200 tampoco equivale a completada.
        self.registro.finalizar_consulta(status=200, resultado="finalizada", fallo=True)
        self.assertEqual(self.registro.consultar()["consultas_completadas"], 0)
        self.assertEqual(self.registro.consultar()["errores"], 1)

    async def test_05_resultados_publicos(self):
        async with self.client() as (client, metrics):
            for status in ("finalizada", "sin_evidencia", "requiere_vinculacion", "limite", "error"):
                self.fake.ainvoke.return_value = {"resultado": status, "respuesta": "Texto"}
                await self.post(client)
            data = metrics.consultar()
        self.assertEqual(data["consultas_completadas"], 5)
        self.assertTrue(all(v == 1 for v in data["consultas_por_resultado"].values()))
        self.assertEqual(data["errores"], 1)  # error controlado, nunca duplicado.

    async def test_06_promedio_y_reloj_monotonico(self):
        for value in (10., 20., 30.):
            self.registro.finalizar_consulta(status=200, resultado="finalizada", duration_ms=value)
        self.assertEqual(self.registro.consultar()["latencia_promedio_ms"], 20.)
        async with self.client() as (client, metrics):
            with patch("grupo_e_tp_integrador_dsi.metricas.perf_counter", side_effect=[1., 1.1]):
                await self.post(client)
            self.assertAlmostEqual(metrics.consultar()["latencia_promedio_ms"], 100.)

    async def test_07_p95_exacto(self):
        for value in range(20, 0, -1):
            self.registro.finalizar_consulta(status=200, resultado="finalizada", duration_ms=value)
        self.assertEqual(self.registro.consultar()["latencia_p95_ms"], 19)
        self.registro.finalizar_consulta(status=500, duration_ms=1000)
        self.assertEqual(self.registro.consultar()["latencia_p95_ms"], 20)
        single = RegistroMetricas()
        single.finalizar_consulta(status=200, resultado="finalizada", duration_ms=42.)
        self.assertEqual(single.consultar()["latencia_p95_ms"], 42.)

    async def test_08_una_herramienta(self):
        model = ModeloSimulado(call("consultar_solicitud_interna", {"identificador": "ausente"}),
                               AIMessage(content="No encontrada"))
        async with self.client(self.agent(model)) as (client, metrics):
            await self.post(client)
            data = metrics.consultar()
        self.assertEqual(data["ejecuciones_herramientas"], 1)
        self.assertEqual(data["herramientas_por_nombre"]["consultar_solicitud_interna"], 1)

    async def test_09_multiples_herramientas(self):
        def consultar(messages):
            id_ = json.loads(messages[-1].content)["solicitud"]["id"]
            return call("consultar_solicitud_interna", {"identificador": id_}, "call-2")
        model = ModeloSimulado(call("crear_solicitud_interna", {"categoria": "IVA", "descripcion": "Revisar tarea",
                                                               "clave_idempotencia": "demo"}),
                               consultar, call("consultar_rag", {"pregunta": "Requisitos"}, "call-3"),
                               AIMessage(content="Finalizada"))
        async with self.client(self.agent(model)) as (client, metrics):
            self.assertEqual((await self.post(client)).status_code, 200)
            data = metrics.consultar()
        self.assertEqual(data["ejecuciones_herramientas"], 3)
        self.assertTrue(all(v == 1 for v in data["herramientas_por_nombre"].values()))

    async def test_10_bloqueos_cero(self):
        async with self.client() as (client, metrics):
            await self.post(client)
            self.assertEqual(metrics.consultar()["bloqueos_seguridad"], 0)

    async def test_11_http_422_sin_latencias(self):
        async with self.client() as (client, metrics):
            for payload in ({}, {"thread_id": "demo", "pregunta": ""},
                            {"thread_id": "demo", "pregunta": "Hola", "extra": 1}):
                self.assertEqual((await client.post("/consultar", json=payload)).status_code, 422)
            self.assertEqual((await client.post("/consultar", content='{')).status_code, 422)
            data = metrics.consultar()
        self.assertEqual(data["consultas_recibidas"], 4)
        self.assertEqual(data["consultas_completadas"], 0)
        self.assertEqual(data["errores"], 0)
        self.assertEqual(data["latencia_promedio_ms"], 0)
        self.assertEqual(data["latencia_p95_ms"], 0)
        self.fake.ainvoke.assert_not_called()

    async def test_12_sin_doble_conteo(self):
        model = ModeloSimulado(call("consultar_solicitud_interna", {"identificador": "ausente"}),
                               AIMessage(content="No encontrada"))
        async with self.client(self.agent(model)) as (client, metrics):
            await self.post(client)
            before = metrics.consultar()
            registrar("herramienta.ejecutada", herramienta="consultar_solicitud_interna", resultado="no_encontrada")
            await client.get("/health")
            self.assertEqual((await client.get("/metricas")).status_code, 200)
            self.assertEqual(metrics.consultar(), before)
        self.assertEqual(before["consultas_recibidas"], 1)
        self.assertEqual(before["consultas_completadas"], 1)
        self.assertEqual(before["ejecuciones_herramientas"], 1)

    async def test_13_instancias_aisladas_y_snapshot_independiente(self):
        async with self.client() as (client_a, metrics_a), self.client() as (client_b, metrics_b):
            await self.post(client_a)
            self.assertIsNot(metrics_a, metrics_b)
            self.assertEqual(metrics_b.consultar()["consultas_recibidas"], 0)
            snapshot = metrics_a.consultar()
            snapshot["consultas_por_resultado"]["finalizada"] = 900
            self.assertEqual(metrics_a.consultar()["consultas_por_resultado"]["finalizada"], 1)

    async def test_14_actualizaciones_concurrentes(self):
        def update(index):
            self.registro.recibir_consulta()
            self.registro.ejecutar_herramienta("consultar_rag")
            self.registro.finalizar_consulta(status=200, resultado="finalizada", duration_ms=float(index))
        with ThreadPoolExecutor(max_workers=8) as pool:
            list(pool.map(update, range(400)))
        data = self.registro.consultar()
        self.assertEqual(data["consultas_recibidas"], 400)
        self.assertEqual(data["consultas_completadas"], 400)
        self.assertEqual(data["ejecuciones_herramientas"], 400)
        self.assertEqual(data["latencia_promedio_ms"], 199.5)
        async with self.client() as (client, metrics):
            await asyncio.gather(*(self.post(client, thread_id=str(i)) for i in range(30)))
            self.assertEqual(metrics.consultar()["consultas_completadas"], 30)

    async def test_15_sin_datos_sensibles_ni_proveedores(self):
        self.fake.ainvoke.return_value = {"resultado": "finalizada", "respuesta": "RESPUESTA_PRIVADA"}
        with patch("google.genai.Client", side_effect=AssertionError("Gemini")), \
             patch("chromadb.PersistentClient", side_effect=AssertionError("Chroma")), \
             patch("aiosqlite.connect", side_effect=AssertionError("SQLite real")):
            async with self.client() as (client, metrics):
                await self.post(client, thread_id="ID_PRIVADO", pregunta="PREGUNTA_PRIVADA")
                metrics.ejecutar_herramienta("ana@example.com")
                encoded = json.dumps(metrics.consultar(), allow_nan=False)
        for value in ("ID_PRIVADO", "PREGUNTA_PRIVADA", "RESPUESTA_PRIVADA", "ana@example.com", "GEMINI_API_KEY"):
            self.assertNotIn(value, encoded)


if __name__ == "__main__":
    unittest.main()
