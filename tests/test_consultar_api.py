"""POST /consultar: contrato, memoria temporal y concurrencia sin proveedores."""

import asyncio
import tempfile
import unittest
from contextlib import asynccontextmanager
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import httpx
from langchain_core.messages import AIMessage

from grupo_e_tp_integrador_dsi.api import crear_app
from grupo_e_tp_integrador_dsi.agente import AgenteContable
from grupo_e_tp_integrador_dsi.herramienta_rag import crear_herramienta_rag
from grupo_e_tp_integrador_dsi.herramientas_solicitudes import crear_herramientas_solicitudes
from test_agente import ModeloSimulado


class ConsultarApiTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.agente = Mock()
        self.agente.ainvoke = AsyncMock(return_value={"resultado": "finalizada", "respuesta": "Respuesta"})
        self.inicios = 0

    @asynccontextmanager
    async def cliente(self, opener=None):
        @asynccontextmanager
        async def abrir():
            self.inicios += 1
            yield self.agente
        app = crear_app(abrir_agente=opener or abrir)
        async with app.router.lifespan_context(app):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                yield client

    async def post(self, client, **kwargs):
        return await client.post("/consultar", json={"thread_id": "demo", "pregunta": "Hola", **kwargs})

    async def test_01_valida(self):
        async with self.cliente() as client:
            response = await self.post(client)
        self.assertEqual(response.status_code, 200)
        self.agente.ainvoke.assert_awaited_once_with("Hola", thread_id="demo")

    async def test_02_contrato(self):
        async with self.cliente() as client:
            response = await self.post(client)
        self.assertEqual(response.json(), {"thread_id": "demo", "resultado": "finalizada", "respuesta": "Respuesta"})
        self.assertEqual(response.headers["content-type"], "application/json")

    async def test_03_instancia_unica(self):
        async with self.cliente() as client:
            for _ in range(3):
                await self.post(client)
        self.assertEqual(self.inicios, 1)
        self.assertEqual(self.agente.ainvoke.await_count, 3)

    @asynccontextmanager
    async def cliente_persistente(self, model):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)
            pipeline = Mock()
            tools = [crear_herramienta_rag(pipeline_factory=Mock(return_value=pipeline)),
                     *crear_herramientas_solicitudes(ruta_db=path / "solicitudes.sqlite")]
            async with self.cliente(opener=lambda: AgenteContable.abrir(
                ruta_checkpoints=path / "checkpoints.sqlite", modelo=model, herramientas=tools)) as client:
                yield client
            self.assertFalse((path / "solicitudes.sqlite").exists())
            pipeline.invoke.assert_not_called()

    async def test_04_continuidad(self):
        model = ModeloSimulado(AIMessage(content="Monotributo"), AIMessage(content="Resumen"))
        async with self.cliente_persistente(model) as client:
            await self.post(client, pregunta="Monotributo")
            response = await self.post(client, pregunta="Resumilo")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Monotributo", [m.content for m in model.historial[1]])
        self.assertEqual(len(model.historial[1]), 4)

    async def test_05_aislamiento(self):
        model = ModeloSimulado(AIMessage(content="Tema privado A"), AIMessage(content="Sin contexto"))
        async with self.cliente_persistente(model) as client:
            await self.post(client, thread_id="A", pregunta="Consulta del hilo A")
            response = await self.post(client, thread_id="B")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(model.historial[1]), 2)
        self.assertNotIn("Tema privado A", str(model.historial[1]))

    async def test_06_thread_invalido(self):
        async with self.cliente() as client:
            for value in ("", "  ", "x" * 129, None, 3):
                with self.subTest(value=value):
                    self.assertEqual((await self.post(client, thread_id=value)).status_code, 422)
            self.assertEqual((await client.post("/consultar", json={"pregunta": "Hola"})).status_code, 422)
        self.agente.ainvoke.assert_not_called()

    async def test_07_pregunta_invalida(self):
        async with self.cliente() as client:
            for value in ("", " \n ", "x" * 2001, None, 3):
                with self.subTest(value=value):
                    self.assertEqual((await self.post(client, pregunta=value)).status_code, 422)
            self.assertEqual((await client.post("/consultar", json={"thread_id": "demo"})).status_code, 422)
            self.assertEqual((await self.post(client, pregunta="x" * 2000)).status_code, 200)

    async def test_08_error_inesperado(self):
        async with self.cliente() as client:
            self.agente.ainvoke.side_effect = RuntimeError("API_KEY=secreto C:/privado")
            response = await self.post(client)
            self.assertEqual(response.status_code, 500)
            self.assertEqual(response.json(), {"detail": "No se pudo procesar la consulta."})
            self.agente.ainvoke.side_effect = None
            self.agente.ainvoke.return_value = {"resultado": "inventado", "respuesta": "privado"}
            self.assertEqual((await self.post(client)).status_code, 500)

    async def test_09_estados_controlados(self):
        async with self.cliente() as client:
            for status in ("finalizada", "limite", "sin_evidencia", "requiere_vinculacion", "error"):
                self.agente.ainvoke.return_value = {"resultado": status, "respuesta": "Mensaje controlado"}
                response = await self.post(client)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json()["resultado"], status)

    async def test_10_sin_informacion_interna(self):
        self.agente.ainvoke.return_value = {"resultado": "finalizada", "respuesta": "Texto público",
                                           "mensajes": ["secreto"], "prompt": "secreto", "tool_calls": ["interno"]}
        async with self.cliente() as client:
            response = await self.post(client)
        self.assertEqual(set(response.json()), {"thread_id", "resultado", "respuesta"})
        self.assertNotIn("secreto", response.text)

    async def test_11_mismo_hilo_serializado(self):
        entered, release = asyncio.Event(), asyncio.Event()
        active, max_active = 0, 0
        order = []
        async def invoke(question, **kwargs):
            nonlocal active, max_active
            active += 1
            max_active = max(active, max_active)
            order.append(question)
            entered.set()
            await release.wait()
            active -= 1
            return {"resultado": "finalizada", "respuesta": question}
        self.agente.ainvoke.side_effect = invoke
        async with self.cliente() as client:
            first = asyncio.create_task(self.post(client, pregunta="Primera"))
            await asyncio.wait_for(entered.wait(), 2)
            second = asyncio.create_task(self.post(client, pregunta="Segunda"))
            await asyncio.sleep(0)
            self.assertEqual(order, ["Primera"])
            release.set()
            responses = await asyncio.gather(first, second)
        self.assertEqual(max_active, 1)
        self.assertEqual(order, ["Primera", "Segunda"])
        self.assertTrue(all(r.status_code == 200 for r in responses))

    async def test_12_hilos_distintos_concurrentes(self):
        both, release = asyncio.Event(), asyncio.Event()
        entered = []
        async def invoke(question, *, thread_id):
            entered.append(thread_id)
            if len(entered) == 2:
                both.set()
            await release.wait()
            return {"resultado": "finalizada", "respuesta": "Respuesta"}
        self.agente.ainvoke.side_effect = invoke
        async with self.cliente() as client:
            tasks = [asyncio.create_task(self.post(client, thread_id=id_)) for id_ in ("A", "B")]
            try:
                await asyncio.wait_for(both.wait(), 2)
            finally:
                release.set()
                responses = await asyncio.gather(*tasks)
        self.assertEqual(set(entered), {"A", "B"})
        self.assertTrue(all(r.status_code == 200 for r in responses))

    async def test_13_sin_proveedores(self):
        with patch("google.genai.Client", side_effect=AssertionError("Gemini")), \
             patch("chromadb.PersistentClient", side_effect=AssertionError("Chroma")), \
             patch("aiosqlite.connect", side_effect=AssertionError("SQLite real")):
            async with self.cliente() as client:
                self.assertEqual((await self.post(client)).status_code, 200)


if __name__ == "__main__":
    unittest.main()
