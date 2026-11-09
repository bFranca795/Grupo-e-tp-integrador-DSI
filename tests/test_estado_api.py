"""Resumen HTTP de checkpoints: sin proveedores ni bases reales."""

import asyncio
import hashlib
import tempfile
import unittest
from contextlib import asynccontextmanager
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import httpx
from langchain_core.messages import AIMessage, HumanMessage

from grupo_e_tp_integrador_dsi.api import crear_app
from grupo_e_tp_integrador_dsi.agente import AgenteContable
from grupo_e_tp_integrador_dsi.herramienta_rag import crear_herramienta_rag
from grupo_e_tp_integrador_dsi.herramientas_solicitudes import crear_herramientas_solicitudes
from test_agente import ModeloSimulado


class EstadoApiTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.agente = Mock()
        self.agente.consultar_estado = AsyncMock(return_value={
            "mensajes": [HumanMessage(content="privado"), AIMessage(content="privado")],
            "final": {"resultado": "finalizada", "respuesta": "privado"}})
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

    async def test_01_existente(self):
        async with self.cliente() as client:
            response = await client.get("/estado/demo")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["existe"])
        self.agente.consultar_estado.assert_awaited_once_with("demo")

    async def test_02_inexistente(self):
        self.agente.consultar_estado.return_value = {}
        async with self.cliente() as client:
            response = await client.get("/estado/ausente")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"thread_id": "ausente", "existe": False,
                                          "cantidad_mensajes": 0, "ultimo_resultado": None})

    async def test_03_contrato_exacto(self):
        async with self.cliente() as client:
            response = await client.get("/estado/demo")
        self.assertEqual(response.json(), {"thread_id": "demo", "existe": True,
                                          "cantidad_mensajes": 2, "ultimo_resultado": "finalizada"})
        self.assertEqual(response.headers["content-type"], "application/json")

    async def test_04_cantidad_mensajes(self):
        self.agente.consultar_estado.return_value = {"mensajes": ["privado"] * 6, "final": None}
        async with self.cliente() as client:
            response = await client.get("/estado/demo")
        self.assertEqual(response.json()["cantidad_mensajes"], 6)

    async def test_05_ultimo_resultado(self):
        async with self.cliente() as client:
            for status in ("finalizada", "limite", "sin_evidencia", "requiere_vinculacion", "error"):
                self.agente.consultar_estado.return_value = {
                    "mensajes": [], "final": {"resultado": status, "respuesta": "Controlada"}}
                self.assertEqual((await client.get("/estado/demo")).json()["ultimo_resultado"], status)
            for final in (None, {}, "finalizada", {"resultado": "inventado", "respuesta": "Texto"},
                          {"resultado": "finalizada"}):
                self.agente.consultar_estado.return_value = {"mensajes": ["finalizada"], "final": final}
                self.assertIsNone((await client.get("/estado/demo")).json()["ultimo_resultado"])
            self.agente.consultar_estado.return_value = {"mensajes": ["resultado: finalizada"]}
            self.assertIsNone((await client.get("/estado/demo")).json()["ultimo_resultado"])

    async def test_06_identificadores_invalidos(self):
        async with self.cliente() as client:
            for value in ("%20%20", "%09", "x" * 129):
                self.assertEqual((await client.get("/estado/" + value)).status_code, 422)
            self.assertEqual((await client.get("/estado/")).status_code, 422)
        self.agente.consultar_estado.assert_not_called()

    async def test_07_sin_datos_sensibles(self):
        self.agente.consultar_estado.return_value = {
            "mensajes": ["API_KEY=secreto", "C:/ruta/privada", "prompt completo", "tool_calls"],
            "final": {"resultado": "finalizada", "respuesta": "secreto"},
            "checkpoints": "interno"}
        async with self.cliente() as client:
            response = await client.get("/estado/demo")
        self.assertEqual(set(response.json()), {"thread_id", "existe", "cantidad_mensajes", "ultimo_resultado"})
        for texto in ("secreto", "privada", "prompt", "tool_calls", "checkpoints"):
            self.assertNotIn(texto, response.text)

    async def test_08_sin_proveedores_ni_herramientas(self):
        with patch("google.genai.Client", side_effect=AssertionError("Gemini")), \
             patch("chromadb.PersistentClient", side_effect=AssertionError("Chroma")), \
             patch("aiosqlite.connect", side_effect=AssertionError("SQLite real")):
            async with self.cliente() as client:
                self.assertEqual((await client.get("/estado/demo")).status_code, 200)
        self.agente.ainvoke.assert_not_called()
        self.assertEqual(len(self.agente.mock_calls), 1)

    async def test_09_checkpoint_temporal_sin_modificacion(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)
            model = ModeloSimulado(AIMessage(content="Respuesta"))
            pipeline = Mock()
            tools = [crear_herramienta_rag(pipeline_factory=Mock(return_value=pipeline)),
                     *crear_herramientas_solicitudes(ruta_db=path / "solicitudes.sqlite")]
            opener = lambda: AgenteContable.abrir(ruta_checkpoints=path / "checkpoints.sqlite",
                                                 modelo=model, herramientas=tools)
            def snapshot():
                # SQLite puede actualizar read-marks en SHM durante una lectura.
                # Los checkpoints persistidos están en la base y el WAL.
                return {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                        for p in path.iterdir() if p.is_file() and not p.name.endswith("-shm")}
            async with self.cliente(opener) as client:
                await client.post("/consultar", json={"thread_id": "demo", "pregunta": "Hola"})
                before = snapshot()
                response = await client.get("/estado/demo")
                absent = await client.get("/estado/ausente")
                self.assertEqual(response.json(), {"thread_id": "demo", "existe": True,
                                                  "cantidad_mensajes": 2, "ultimo_resultado": "finalizada"})
                self.assertFalse(absent.json()["existe"])
                self.assertEqual(snapshot(), before)
                self.assertEqual(len(model.historial), 1)
                pipeline.invoke.assert_not_called()
                self.assertFalse((path / "solicitudes.sqlite").exists())

    async def test_10_lectura_consistente_mismo_hilo(self):
        entered, release, read_started = asyncio.Event(), asyncio.Event(), asyncio.Event()
        state = {"mensajes": [], "final": None}
        async def invoke(*args, **kwargs):
            state["mensajes"] = ["parcial"]
            entered.set()
            await release.wait()
            state.update(mensajes=["consulta", "respuesta"], final={"resultado": "finalizada", "respuesta": "Texto"})
            return state["final"]
        async def leer(id_):
            read_started.set()
            return state
        self.agente.ainvoke.side_effect = invoke
        self.agente.consultar_estado.side_effect = leer
        async with self.cliente() as client:
            writing = asyncio.create_task(client.post("/consultar", json={"thread_id": "demo", "pregunta": "Hola"}))
            await asyncio.wait_for(entered.wait(), 2)
            reading = asyncio.create_task(client.get("/estado/demo"))
            await asyncio.sleep(0)
            self.assertFalse(read_started.is_set())
            release.set()
            write, read = await asyncio.gather(writing, reading)
        self.assertEqual(write.status_code, 200)
        self.assertEqual(read.json()["cantidad_mensajes"], 2)
        self.assertEqual(read.json()["ultimo_resultado"], "finalizada")

    async def test_11_error_inesperado(self):
        self.agente.consultar_estado.side_effect = RuntimeError("API_KEY=secreto C:/privado")
        async with self.cliente() as client:
            response = await client.get("/estado/demo")
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.json(), {"detail": "No se pudo consultar el estado."})

    async def test_12_reutiliza_agente(self):
        async with self.cliente() as client:
            for _ in range(3):
                await client.get("/estado/demo")
        self.assertEqual(self.inicios, 1)
        self.assertEqual(self.agente.consultar_estado.await_count, 3)

    async def test_hilos_distintos_no_bloqueados(self):
        entered, release = asyncio.Event(), asyncio.Event()
        async def invoke(*args, **kwargs):
            entered.set()
            await release.wait()
            return {"resultado": "finalizada", "respuesta": "Texto"}
        self.agente.ainvoke.side_effect = invoke
        async with self.cliente() as client:
            writing = asyncio.create_task(client.post("/consultar", json={"thread_id": "A", "pregunta": "Hola"}))
            await asyncio.wait_for(entered.wait(), 2)
            try:
                response = await asyncio.wait_for(client.get("/estado/B"), 2)
                self.assertEqual(response.status_code, 200)
            finally:
                release.set()
                await writing


if __name__ == "__main__":
    unittest.main()
