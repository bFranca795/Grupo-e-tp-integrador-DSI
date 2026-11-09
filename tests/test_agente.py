"""Grafo real con modelo guionado, RAG doble y solicitudes temporales."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

from google.genai import types
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage

from grupo_e_tp_integrador_dsi.agente import AgenteContable
from grupo_e_tp_integrador_dsi.herramienta_rag import crear_herramienta_rag, ESCAPE
from grupo_e_tp_integrador_dsi.herramientas_solicitudes import crear_herramientas_solicitudes
from grupo_e_tp_integrador_dsi.modelo_agente import GeminiAgente


def call(name, args, id="call-1"):
    return AIMessage(content="", tool_calls=[{"name": name, "args": args, "id": id}])


class ModeloSimulado:
    def __init__(self, *steps):
        self.steps, self.historial = list(steps), []

    def bind_tools(self, tools):
        self.tools = tools
        return self

    async def ainvoke(self, messages):
        self.historial.append(messages)
        step = self.steps.pop(0)
        if isinstance(step, Exception):
            raise step
        return step(messages) if callable(step) else step


class AgenteTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "solicitudes.sqlite"
        self.pipeline = Mock()
        self.pipeline.invoke.return_value = {"status": "ok", "answer": "Requisitos [DOC-007]",
                                            "sources": [{"id": "DOC-007"}]}
        self.rag = crear_herramienta_rag(pipeline_factory=Mock(return_value=self.pipeline))
        self.sensor, self.actuador = crear_herramientas_solicitudes(ruta_db=self.path)
        self.tools = [self.rag, self.sensor, self.actuador]
        self.args = {"categoria": "IVA", "descripcion": "Revisar documentación",
                     "clave_idempotencia": "prueba-1"}

    def agente(self, model, **kwargs):
        return AgenteContable(modelo=model, herramientas=self.tools, **kwargs)

    async def test_01_registro(self):
        model = ModeloSimulado(AIMessage(content="Hola"))
        self.agente(model)
        self.assertEqual({t.name for t in model.tools},
                         {"consultar_rag", "consultar_solicitud_interna", "crear_solicitud_interna"})
        self.assertFalse(self.path.exists())

    async def test_02_retriever(self):
        model = ModeloSimulado(call("consultar_rag", {"pregunta": "Documentación IVA"}),
                               AIMessage(content="Requisitos [DOC-007]"))
        result = await self.agente(model).ainvoke("¿Qué documentación necesito para IVA?")
        self.assertEqual(result["resultado"], "finalizada")
        self.pipeline.invoke.assert_called_once_with({"question": "Documentación IVA"})
        self.assertFalse(self.path.exists())

    async def test_03_sensor(self):
        id_ = (await self.actuador.ainvoke(self.args))["solicitud"]["id"]
        before = self.path.read_bytes()
        def finalizar(messages):
            result = json.loads(messages[-1].content)
            return AIMessage(content=result["solicitud"]["estado"])
        model = ModeloSimulado(call(self.sensor.name, {"identificador": id_}), finalizar)
        result = await self.agente(model).ainvoke("Consultá mi solicitud " + id_)
        self.assertEqual(result["respuesta"], "pendiente")
        self.assertEqual(self.path.read_bytes(), before)
        self.pipeline.invoke.assert_not_called()

    async def test_04_actuador(self):
        model = ModeloSimulado(call(self.actuador.name, self.args), AIMessage(content="Solicitud registrada"))
        await self.agente(model).ainvoke("Registrá una tarea ficticia de revisión")
        data = json.loads(model.historial[1][-1].content)
        self.assertEqual(data["resultado"], "creada")
        leida = await self.sensor.ainvoke({"identificador": data["solicitud"]["id"]})
        self.assertEqual(leida["resultado"], "encontrada")

    async def test_05_multiples(self):
        def consultar(messages):
            id_ = json.loads(messages[-1].content)["solicitud"]["id"]
            return call(self.sensor.name, {"identificador": id_}, "call-2")
        model = ModeloSimulado(call(self.actuador.name, self.args), consultar,
                               AIMessage(content="La tarea creada está pendiente"))
        result = await self.agente(model).ainvoke("Creá la tarea y consultá su estado")
        self.assertEqual(result["resultado"], "finalizada")
        self.assertEqual(len(model.historial), 3)
        self.assertEqual(len([m for m in model.historial[-1] if isinstance(m, ToolMessage)]), 2)

    async def test_06_abstenciones(self):
        for status, expected in (("insufficient_context", "sin_evidencia"),
                                 ("insufficient_client_binding", "requiere_vinculacion")):
            with self.subTest(status=status):
                self.pipeline.invoke.return_value = {"status": status, "answer": ESCAPE}
                model = ModeloSimulado(call("consultar_rag", {"pregunta": "IVA"}),
                                       AIMessage(content="AFIRMACION INVENTADA"))
                result = await self.agente(model).ainvoke("IVA")
                self.assertEqual(result, {"resultado": expected, "respuesta": ESCAPE})
                self.assertEqual(len(model.historial), 1)

    async def test_07_sin_herramientas(self):
        model = ModeloSimulado(AIMessage(content="Hola, puedo ayudarte con consultas del estudio."))
        result = await self.agente(model).ainvoke("Hola")
        self.assertEqual(result["resultado"], "finalizada")
        self.assertFalse(self.path.exists())
        self.pipeline.invoke.assert_not_called()

    async def test_08_limites(self):
        for kwargs, model_calls in (({"max_iteraciones": 2}, 2), ({"max_llamadas": 1}, 2)):
            model = ModeloSimulado(*(call(self.sensor.name, {"identificador": "ausente"}) for _ in range(5)))
            result = await self.agente(model, **kwargs).ainvoke("Consultá el estado")
            self.assertEqual(result["resultado"], "limite")
            self.assertEqual(len(model.historial), model_calls)
        batch = AIMessage(content="", tool_calls=[
            {"name": self.actuador.name, "args": {**self.args, "clave_idempotencia": str(i)}, "id": str(i)}
            for i in range(3)])
        model = ModeloSimulado(batch)
        result = await self.agente(model, max_llamadas=1).ainvoke("Registrar tareas ficticias")
        self.assertEqual(result["resultado"], "limite")
        import aiosqlite
        async with aiosqlite.connect(self.path) as db:
            async with db.execute("SELECT count(*) FROM solicitudes") as cursor:
                self.assertEqual((await cursor.fetchone())[0], 1)

    async def test_09_errores(self):
        for step in (RuntimeError("API_KEY=secreto C:/privado"),
                     call("no_existe", {}),
                     call(self.actuador.name, {**self.args, "categoria": "INVALIDA"})):
            result = await self.agente(ModeloSimulado(step)).ainvoke("Consulta")
            self.assertEqual(result["resultado"], "error")
            self.assertNotIn("secreto", json.dumps(result))
            self.assertNotIn("C:/", json.dumps(result))
        self.pipeline.invoke.side_effect = RuntimeError("secreto")
        model = ModeloSimulado(call("consultar_rag", {"pregunta": "IVA"}))
        self.assertEqual((await self.agente(model).ainvoke("IVA"))["resultado"], "error")

    async def test_10_salida_publica(self):
        model = ModeloSimulado(AIMessage(content="Respuesta pública", additional_kwargs={"interno": "secreto"}))
        result = await self.agente(model).ainvoke("Hola")
        self.assertEqual(result, {"resultado": "finalizada", "respuesta": "Respuesta pública"})
        self.assertNotIn("secreto", json.dumps(result))

    async def test_configuracion_y_sin_memoria(self):
        for value in (0, 51, True, "2"):
            with self.assertRaises(ValueError):
                self.agente(ModeloSimulado(), max_iteraciones=value)
        model = ModeloSimulado(AIMessage(content="Hola"), AIMessage(content="Hola otra vez"))
        agent = self.agente(model)
        await agent.ainvoke("Hola")
        await agent.ainvoke("Hola otra vez")
        self.assertEqual(len(model.historial[1]), 2)  # Sistema + nueva entrada.

    async def test_adapter_gemini_sin_api(self):
        content = types.Content(role="model", parts=[types.Part(
            function_call=types.FunctionCall(name="consultar_rag", args={"pregunta": "IVA"}, id="provider-1"),
            thought_signature=b"firma-original")])
        generate = AsyncMock(side_effect=[
            types.GenerateContentResponse(candidates=[types.Candidate(content=content)]),
            types.GenerateContentResponse(candidates=[types.Candidate(content=types.Content(
                role="model", parts=[types.Part(text="Respuesta")]))])])
        client = Mock()
        client.models.generate_content = generate
        context = Mock()
        context.__aenter__ = AsyncMock(return_value=client)
        context.__aexit__ = AsyncMock(return_value=False)
        with patch("grupo_e_tp_integrador_dsi.modelo_agente.genai.Client") as factory:
            factory.return_value.aio = context
            model = GeminiAgente().bind_tools(self.tools)
            initial = [SystemMessage(content="Sistema"), HumanMessage(content="IVA")]
            message = await model.ainvoke(initial)
            self.assertEqual(message.tool_calls[0]["name"], "consultar_rag")
            final = await model.ainvoke([*initial, message, ToolMessage(
                name="consultar_rag", tool_call_id="provider-1", content='{"resultado":"respondida"}')])
            self.assertEqual(final.content, "Respuesta")
            request = generate.call_args.kwargs
            self.assertEqual(request["contents"][1].parts[0].thought_signature, b"firma-original")
            self.assertEqual(request["contents"][2].parts[0].function_response.id, "provider-1")
            self.assertTrue(request["config"].automatic_function_calling.disable)
            self.assertEqual(len(request["config"].tools[0].function_declarations), 3)


if __name__ == "__main__":
    unittest.main()
