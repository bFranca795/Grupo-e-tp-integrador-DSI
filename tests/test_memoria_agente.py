"""Persistencia real del grafo con modelos simulados y SQLite temporal."""
import json
import subprocess
import sys
import unittest
from pathlib import Path

from langchain_core.messages import AIMessage, ToolMessage

from grupo_e_tp_integrador_dsi.agente import AgenteContable
import test_agente as soporte
from test_agente import ModeloSimulado, call


class MemoriaTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        await soporte.AgenteTests.asyncSetUp(self)
        self.db = Path(self.temp.name) / "checkpoints.sqlite"

    def abrir(self, model, **kwargs):
        return AgenteContable.abrir(ruta_checkpoints=self.db, modelo=model,
                                   herramientas=self.tools, **kwargs)

    async def test_memoria_01_creacion(self):
        async with self.abrir(ModeloSimulado(AIMessage(content="Hola"))) as agent:
            self.assertEqual((await agent.ainvoke("Hola", thread_id="A"))["resultado"], "finalizada")
            self.assertEqual(len((await agent.consultar_estado("A"))["mensajes"]), 2)

    async def test_memoria_02_continuacion(self):
        model = ModeloSimulado(AIMessage(content="Monotributo"), AIMessage(content="Resumen"))
        async with self.abrir(model) as agent:
            await agent.ainvoke("Monotributo", thread_id="A")
            await agent.ainvoke("Resumilo", thread_id="A")
            self.assertEqual(len(model.historial[1]), 4)  # Sistema + 3 mensajes.

    async def test_memoria_03_contexto(self):
        def responder(messages):
            self.assertIn("Monotributo", [m.content for m in messages])
            return AIMessage(content="Monotributo")
        async with self.abrir(ModeloSimulado(AIMessage(content="Entendido"), responder)) as agent:
            await agent.ainvoke("Monotributo", thread_id="A")
            self.assertEqual((await agent.ainvoke("¿Tema?", thread_id="A"))["respuesta"], "Monotributo")

    async def test_memoria_04_aislamiento(self):
        model = ModeloSimulado(AIMessage(content="Tema A"), AIMessage(content="Tema B"))
        async with self.abrir(model) as agent:
            await agent.ainvoke("Consulta A", thread_id="A")
            await agent.ainvoke("Consulta B", thread_id="B")
            self.assertEqual(len(model.historial[1]), 2)
            self.assertNotIn("Consulta A", str(await agent.consultar_estado("B")))

    async def test_memoria_05_nuevo_proceso(self):
        async with self.abrir(ModeloSimulado(AIMessage(content="Monotributo"))) as agent:
            await agent.ainvoke("Tema persistido", thread_id="A")
        code = '''
import asyncio, sys
from grupo_e_tp_integrador_dsi.agente import AgenteContable
async def main():
    async with AgenteContable.abrir(ruta_checkpoints=sys.argv[1]) as agent:
        state = await agent.consultar_estado("A")
        assert state["mensajes"][0].content == "Tema persistido"
        assert state["mensajes"][1].content == "Monotributo"
asyncio.run(main())
'''
        result = subprocess.run([sys.executable, "-B", "-c", code, str(self.db)],
                                capture_output=True, text=True, timeout=90)
        self.assertEqual(result.returncode, 0, result.stderr)

    async def test_memoria_06_api_y_cierre(self):
        async with self.abrir(ModeloSimulado(AIMessage(content="Respuesta"))) as agent:
            self.assertEqual(await agent.consultar_estado("ausente"), {})
            await agent.ainvoke("Hola", thread_id="A")
        with self.assertRaises(RuntimeError):
            await agent.consultar_estado("A")
        async with self.abrir(ModeloSimulado()) as reopened:
            self.assertEqual((await reopened.consultar_estado("A"))["final"]["respuesta"], "Respuesta")

    async def test_memoria_07_herramientas(self):
        model = ModeloSimulado(call(self.actuador.name, self.args), AIMessage(content="Registrada"))
        async with self.abrir(model) as agent:
            await agent.ainvoke("Creá la tarea", thread_id="A")
        async with self.abrir(ModeloSimulado()) as agent:
            messages = (await agent.consultar_estado("A"))["mensajes"]
            self.assertEqual(messages[1].tool_calls[0]["name"], self.actuador.name)
            self.assertIsInstance(messages[2], ToolMessage)
            self.assertEqual(json.loads(messages[2].content)["resultado"], "creada")

    async def test_memoria_08_limites_por_consulta(self):
        model = ModeloSimulado(call(self.sensor.name, {"identificador": "ausente"}),
                               AIMessage(content="Nueva respuesta"))
        async with self.abrir(model, max_iteraciones=1) as agent:
            self.assertEqual((await agent.ainvoke("Estado", thread_id="A"))["resultado"], "limite")
            previous = await agent.consultar_estado("A")
            self.assertTrue(any(isinstance(m, ToolMessage) for m in previous["mensajes"]))
            self.assertEqual((await agent.ainvoke("Hola", thread_id="A"))["resultado"], "finalizada")
            state = await agent.consultar_estado("A")
            self.assertEqual(state["iteraciones"], 1)
            self.assertEqual(state["llamadas"], 0)

    async def test_memoria_09_identificadores(self):
        async with self.abrir(ModeloSimulado()) as agent:
            for id_ in (None, "", " ", "x" * 129, 12):
                with self.subTest(id=id_), self.assertRaises(ValueError):
                    await agent.ainvoke("Hola", thread_id=id_)
            # El ID es una clave SQLite, nunca una ruta.
            self.assertEqual(await agent.consultar_estado("../../otro"), {})

    async def test_memoria_10_no_duplicar(self):
        model = ModeloSimulado(call(self.actuador.name, self.args), AIMessage(content="Creada"),
                               AIMessage(content="La tarea anterior está registrada"))
        async with self.abrir(model) as agent:
            await agent.ainvoke("Creá tarea", thread_id="A")
            await agent.ainvoke("¿Qué hicimos?", thread_id="A")
        import aiosqlite
        async with aiosqlite.connect(self.path) as db:
            async with db.execute("SELECT count(*) FROM solicitudes") as cursor:
                self.assertEqual((await cursor.fetchone())[0], 1)
