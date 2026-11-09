"""SDK LangSmith real con transporte local doble: nunca servicios externos."""
import asyncio
import copy
from contextlib import asynccontextmanager
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import AsyncMock, Mock, patch

import httpx
from google.genai import types
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from langchain_core.messages import AIMessage, HumanMessage

from grupo_e_tp_integrador_dsi.agente import AgenteContable
from grupo_e_tp_integrador_dsi.api import crear_app
from grupo_e_tp_integrador_dsi.herramienta_rag import crear_herramienta_rag
from grupo_e_tp_integrador_dsi.herramientas_solicitudes import crear_herramientas_solicitudes
from grupo_e_tp_integrador_dsi.modelo_agente import GeminiAgente
from grupo_e_tp_integrador_dsi.observabilidad import configurar_logger
from grupo_e_tp_integrador_dsi.trazabilidad import Trazador, tramo
from entrega_3.rag_pipeline.pipeline import Settings, build_pipeline
from test_agente import ModeloSimulado, call


class ClienteLocal:
    def __init__(self):
        self.creados, self.actualizados = [], []
    def create_run(self, **kwargs):
        self.creados.append(copy.deepcopy(kwargs))
    def update_run(self, run_id, **kwargs):
        self.actualizados.append({"id": run_id, **copy.deepcopy(kwargs)})
    def flush(self, **kwargs):
        pass


class TracingTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.client = ClienteLocal()
        self.tracer = Trazador(enabled=True, project="prueba-local", client=self.client)
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        class Retriever:
            def recuperar(self, *args, **kwargs):
                return [{"id": "DOC-002", "documento": "DOCUMENTO_PRIVADO", "metadatos": {}}]
        class Model(FakeListChatModel):
            def _generate(self, *args, **kwargs):
                result = super()._generate(*args, **kwargs)
                message = result.generations[0].message
                message.usage_metadata = {"input_tokens": 5, "output_tokens": 2, "total_tokens": 7}
                message.response_metadata = {"model_name": "gemini-3.1-flash-lite"}
                return result
        def factory(settings):
            return build_pipeline(settings, retriever=Retriever(), model=Model(responses=[
                '{"items":[{"id":"DOC-002","score":0.9,"reason":"MOTIVO_PRIVADO"}]}',
                "RESPUESTA_PRIVADA [DOC-002]"]))
        self.tools = [crear_herramienta_rag(pipeline_factory=factory),
                      *crear_herramientas_solicitudes(ruta_db=Path(self.temp.name)/"solicitudes.sqlite")]

    def agent(self, model, **kwargs):
        return AgenteContable(modelo=model, herramientas=self.tools, trazador=self.tracer, **kwargs)

    async def test_01_configuracion_on_off(self):
        with patch.dict(os.environ, {"LANGSMITH_TRACING": "false", "LANGCHAIN_TRACING_V2": "true"}):
            tracer = Trazador()
            self.assertFalse(tracer.enabled)
            with patch("grupo_e_tp_integrador_dsi.trazabilidad.Client", side_effect=AssertionError("Red")):
                agent = AgenteContable(modelo=ModeloSimulado(AIMessage(content="Hola")), herramientas=self.tools,
                                      trazador=tracer)
                self.assertEqual((await agent.ainvoke("Hola"))["resultado"], "finalizada")
            self.assertIsNone(tracer.ultimo_run_id)
        with patch.dict(os.environ, {"LANGSMITH_TRACING": "true"}):
            tracer = Trazador(client=self.client)
            with tracer.consulta():
                pass
            self.assertIsNotNone(tracer.ultimo_run_id)

    async def test_02_contexto_async_y_thread(self):
        with self.tracer.consulta():
            async def child():
                await asyncio.sleep(0)
                with tramo("etapa.async"):
                    pass
            def thread():
                with tramo("etapa.thread"):
                    pass
            await asyncio.gather(child(), asyncio.to_thread(thread))
        root = self.client.creados[0]
        self.assertEqual(len(self.client.creados), 3)
        self.assertTrue(all(r["trace_id"] == root["trace_id"] for r in self.client.creados))
        self.assertTrue(all(r["parent_run_id"] == root["id"] for r in self.client.creados[1:]))

    async def gemini(self, usage):
        response = types.GenerateContentResponse(candidates=[types.Candidate(content=types.Content(
            role="model", parts=[types.Part(text="RESPUESTA_PRIVADA")]))], usage_metadata=usage)
        client = Mock()
        client.models.generate_content = AsyncMock(return_value=response)
        ctx = Mock(__aenter__=AsyncMock(return_value=client), __aexit__=AsyncMock(return_value=False))
        with patch("grupo_e_tp_integrador_dsi.modelo_agente.genai.Client") as factory:
            factory.return_value.aio = ctx
            with self.tracer.consulta():
                return await GeminiAgente().bind_tools(self.tools).ainvoke([HumanMessage(content="PREGUNTA_PRIVADA")])

    async def test_03_llamada_modelo(self):
        await self.gemini(None)
        models = [r for r in self.client.creados if r["run_type"] == "llm"]
        self.assertEqual(len(models), 1)
        self.assertEqual(models[0]["name"], "gemini.agente")
        self.assertEqual(models[0]["parent_run_id"], self.client.creados[0]["id"])
        self.assertTrue(all(r.get("end_time") is not None for r in self.client.actualizados))

    async def test_04_herramientas_y_limite(self):
        model = ModeloSimulado(call("consultar_solicitud_interna", {"identificador": "ID_PRIVADO"}))
        result = await self.agent(model, max_iteraciones=1).ainvoke("PREGUNTA_PRIVADA", thread_id="HILO_PRIVADO")
        self.assertEqual(result["resultado"], "limite")
        tools = [r for r in self.client.creados if r["run_type"] == "tool"]
        self.assertEqual([r["name"] for r in tools], ["consultar_solicitud_interna"])
        self.assertEqual(self.client.actualizados[-1]["outputs"], {"resultado": "limite"})

    async def test_05_asociacion_rag_interno(self):
        model = ModeloSimulado(call("consultar_rag", {"pregunta": "PREGUNTA_PRIVADA"}), AIMessage(content="Final"))
        result = await self.agent(model).ainvoke("PREGUNTA_PRIVADA")
        self.assertEqual(result["resultado"], "finalizada")
        names = {r["name"] for r in self.client.creados}
        self.assertTrue({"agente.consulta", "consultar_rag", "recuperacion", "juez_relevancia", "generacion", "gemini.rag"} <= names, names)
        root = self.client.creados[0]
        self.assertTrue(all(r["trace_id"] == root["trace_id"] for r in self.client.creados))
        llms = [r for r in self.client.creados if r["run_type"] == "llm"]
        self.assertEqual(len(llms), 2)
        updates = {str(r["id"]): r for r in self.client.actualizados}
        self.assertTrue(all(updates[str(r["id"])]["extra"]["metadata"]["usage_metadata"]["total_tokens"] == 7 for r in llms))

    async def test_06_tokens_informados(self):
        usage = types.GenerateContentResponseUsageMetadata(prompt_token_count=10, candidates_token_count=3, total_token_count=13)
        message = await self.gemini(usage)
        self.assertEqual(message.usage_metadata, {"input_tokens": 10, "output_tokens": 3, "total_tokens": 13})
        updates = [r for r in self.client.actualizados if "usage_metadata" in r.get("extra", {}).get("metadata", {})]
        self.assertEqual(len(updates), 1)
        self.assertEqual(updates[0]["extra"]["metadata"]["usage_metadata"], message.usage_metadata)

    async def test_07_consumo_no_informado(self):
        message = await self.gemini(None)
        self.assertIsNone(message.usage_metadata)
        self.assertFalse(any("usage_metadata" in r.get("extra", {}).get("metadata", {}) for r in self.client.actualizados))

    async def test_08_privacidad(self):
        model = ModeloSimulado(call("consultar_rag", {"pregunta": "PREGUNTA_PRIVADA"}), AIMessage(content="RESPUESTA_PRIVADA"))
        await self.agent(model).ainvoke("PREGUNTA_PRIVADA", thread_id="HILO_PRIVADO")
        await self.agent(ModeloSimulado(RuntimeError("GEMINI_API_KEY=CLAVE_PRIVADA"))).ainvoke("PREGUNTA_PRIVADA")
        encoded = json.dumps([self.client.creados, self.client.actualizados], default=str)
        for value in ("PREGUNTA_PRIVADA", "RESPUESTA_PRIVADA", "DOCUMENTO_PRIVADO", "MOTIVO_PRIVADO", "HILO_PRIVADO",
                      "CLAVE_PRIVADA", "GEMINI_API_KEY", "serialized.messages", "Sos el asistente"):
            self.assertNotIn(value, encoded)
        self.assertTrue(all(not r.get("inputs") for r in self.client.creados))

    async def test_09_fallo_tracing_no_rompe_agente(self):
        stream = io.StringIO()
        logger = configurar_logger()
        original = next(h.stream for h in logger.handlers if h.name == "agente-json")
        configurar_logger(stream=stream)
        try:
            self.client.create_run = Mock(side_effect=RuntimeError("GEMINI_API_KEY=CLAVE_PRIVADA"))
            result = await self.agent(ModeloSimulado(AIMessage(content="Hola"))).ainvoke("Hola")
            self.assertEqual(result["resultado"], "finalizada")
            self.assertTrue(self.tracer.error)
            self.assertNotIn("CLAVE_PRIVADA", stream.getvalue())
            self.assertEqual([json.loads(line)["event"] for line in stream.getvalue().splitlines()], ["tracing.error"])
        finally:
            configurar_logger(stream=original)

    async def test_10_http_metricas_sin_cambios(self):
        model = ModeloSimulado(call("consultar_solicitud_interna", {"identificador": "ausente"}), AIMessage(content="No encontrada"))
        @asynccontextmanager
        async def abrir():
            async with AgenteContable.abrir(ruta_checkpoints=Path(self.temp.name)/"checkpoints.sqlite",
                                           modelo=model, herramientas=self.tools, trazador=self.tracer) as agent:
                yield agent
        app = crear_app(abrir_agente=abrir)
        async with app.router.lifespan_context(app):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                self.assertEqual((await client.get("/health")).status_code, 200)
                response = await client.post("/consultar", json={"thread_id": "demo", "pregunta": "Estado"})
                self.assertEqual(response.json(), {"thread_id": "demo", "resultado": "finalizada", "respuesta": "No encontrada"})
                self.assertEqual((await client.get("/estado/demo")).json()["cantidad_mensajes"], 4)
                metrics = (await client.get("/metricas")).json()
                self.assertEqual(metrics["consultas_recibidas"], 1)
                self.assertEqual(metrics["consultas_completadas"], 1)
                self.assertEqual(metrics["ejecuciones_herramientas"], 1)


if __name__ == "__main__":
    unittest.main()
