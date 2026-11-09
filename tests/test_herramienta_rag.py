"""Pruebas del adaptador RAG con dobles; sin Gemini ni ChromaDB."""

import asyncio
import json
import threading
import unittest
from unittest.mock import Mock

from langchain_core.messages import ToolMessage
from langchain_core.tools import BaseTool
from langchain_core.utils.function_calling import convert_to_openai_tool
from pydantic import ValidationError

from grupo_e_tp_integrador_dsi.herramienta_rag import (
    ESCAPE, consultar_rag, crear_herramienta_rag,
)


def estado_ok():
    return {"status": "ok", "answer": "Se requiere documentación [DOC-007].",
            "sources": [{"id": "DOC-007::chunk-000-0123456789abcdef",
                         "documento": "CONTENIDO_INTERNO", "documento_raw": "RAW_INTERNO",
                         "metadatos": {"cuit": "DATO_SENSIBLE"}, "embedding": [1, 2]}],
            "candidates": ["CANDIDATO_INTERNO"], "judge": {"reason": "JUICIO_INTERNO"},
            "prompt": "PROMPT_INTERNO"}


class RagTests(unittest.IsolatedAsyncioTestCase):
    def herramienta(self, state=None):
        pipeline = Mock()
        pipeline.invoke.return_value = estado_ok() if state is None else state
        factory = Mock(return_value=pipeline)
        return crear_herramienta_rag(pipeline_factory=factory), pipeline, factory

    async def test_01_registro_esquema(self):
        self.assertIsInstance(consultar_rag, BaseTool)
        tool, _, factory = self.herramienta()
        spec = convert_to_openai_tool(tool)["function"]
        self.assertEqual(spec["name"], "consultar_rag")
        self.assertEqual(set(spec["parameters"]["properties"]), {"pregunta"})
        self.assertEqual(spec["parameters"]["required"], ["pregunta"])
        self.assertFalse(tool.args_schema.model_json_schema()["additionalProperties"])
        for palabra in ("Parámetros", "Retorno", "Errores"):
            self.assertIn(palabra, spec["description"])
        factory.assert_not_called()

    async def test_02_pregunta_valida(self):
        tool, pipeline, _ = self.herramienta()
        await tool.ainvoke({"pregunta": "  ¿Qué documentación necesito?  "})
        pipeline.invoke.assert_called_once_with({"question": "¿Qué documentación necesito?"})

    async def test_03_rechazo_pregunta(self):
        tool, pipeline, factory = self.herramienta()
        for args in ({}, {"pregunta": ""}, {"pregunta": " \n "}, {"pregunta": 1},
                     {"pregunta": None}, {"pregunta": "x" * 4001},
                     {"pregunta": "IVA", "filters": {"activo": False}}):
            with self.subTest(args=args), self.assertRaises(ValidationError):
                await tool.ainvoke(args)
        pipeline.invoke.assert_not_called()
        factory.assert_not_called()

    async def test_04_conversion_exitosa(self):
        tool, _, _ = self.herramienta()
        result = await tool.ainvoke({"pregunta": "Documentación"})
        self.assertEqual(result["resultado"], "respondida")
        self.assertEqual(result["respuesta"], estado_ok()["answer"])
        self.assertEqual(set(result), {"resultado", "respuesta", "fuentes"})

    async def test_05_fuentes(self):
        state = estado_ok()
        state["sources"].append({"id": "DOC-002"})
        tool, _, _ = self.herramienta(state)
        result = await tool.ainvoke({"pregunta": "Documentación"})
        self.assertEqual(result["fuentes"], [
            {"id": "DOC-007::chunk-000-0123456789abcdef", "id_documental": "DOC-007"},
            {"id": "DOC-002", "id_documental": "DOC-002"}])

    async def test_06_sin_evidencia(self):
        for status in ("insufficient_context", "ok"):
            state = {**estado_ok(), "status": status, "answer": ESCAPE}
            tool, _, _ = self.herramienta(state)
            self.assertEqual(await tool.ainvoke({"pregunta": "Otra consulta"}),
                             {"resultado": "sin_evidencia", "respuesta": ESCAPE, "fuentes": []})

    async def test_07_vinculacion(self):
        tool, _, _ = self.herramienta({"status": "insufficient_client_binding", "answer": ESCAPE})
        self.assertEqual(await tool.ainvoke({"pregunta": "¿Ya presentaron mi IVA?"}),
                         {"resultado": "requiere_vinculacion", "respuesta": ESCAPE, "fuentes": []})

    async def test_08_errores(self):
        for etapa in ("recuperacion", "generacion"):
            tool, pipeline, _ = self.herramienta()
            pipeline.invoke.side_effect = RuntimeError(etapa + " API_KEY=secreto C:/ruta/interna")
            result = await tool.ainvoke({"pregunta": "IVA"})
            self.assertEqual(result["resultado"], "error")
            self.assertEqual(result["fuentes"], [])
            for dato in ("API_KEY", "secreto", "C:/", etapa):
                self.assertNotIn(dato, json.dumps(result))
        for status in ("judge_error", "estado_desconocido"):
            tool, _, _ = self.herramienta({"status": status, "judge": "secreto"})
            self.assertEqual((await tool.ainvoke({"pregunta": "IVA"}))["resultado"], "error")

    async def test_09_exclusion_interna(self):
        tool, _, _ = self.herramienta()
        encoded = json.dumps(await tool.ainvoke({"pregunta": "IVA"}))
        for dato in ("INTERNO", "metadatos", "DATO_SENSIBLE", "embedding", "candidates", "prompt"):
            self.assertNotIn(dato, encoded)

    async def test_10_inicializacion_unica(self):
        tool, pipeline, factory = self.herramienta()
        await asyncio.gather(*(tool.ainvoke({"pregunta": "IVA"}) for _ in range(4)))
        factory.assert_called_once()
        self.assertEqual(factory.call_args.args[0].variant, "rerank")
        self.assertEqual(pipeline.invoke.call_count, 4)

    async def test_11_serializacion(self):
        tool, _, _ = self.herramienta()
        result = await tool.ainvoke({"pregunta": "IVA"})
        self.assertEqual(json.loads(json.dumps(result)), result)
        message = await tool.ainvoke({"type": "tool_call", "name": "consultar_rag",
                                     "id": "call-rag", "args": {"pregunta": "IVA"}})
        self.assertIsInstance(message, ToolMessage)
        self.assertEqual(json.loads(message.content), result)

    async def test_event_loop_no_bloqueado(self):
        tool, pipeline, factory = self.herramienta()
        loop = asyncio.get_running_loop()
        entered = asyncio.Event()
        release = threading.Event()
        main_thread = threading.get_ident()
        def invoke(request):
            self.assertNotEqual(threading.get_ident(), main_thread)
            loop.call_soon_threadsafe(entered.set)
            if not release.wait(3):
                raise RuntimeError("El event loop quedó bloqueado")
            return estado_ok()
        pipeline.invoke.side_effect = invoke
        task = asyncio.create_task(tool.ainvoke({"pregunta": "IVA"}))
        try:
            await asyncio.wait_for(entered.wait(), timeout=2)
        finally:
            release.set()
        self.assertEqual((await task)["resultado"], "respondida")

    async def test_fallo_inicializacion_y_salida_invalida(self):
        factory = Mock(side_effect=RuntimeError("clave y ruta privadas"))
        tool = crear_herramienta_rag(pipeline_factory=factory)
        for _ in range(2):
            self.assertEqual((await tool.ainvoke({"pregunta": "IVA"}))["resultado"], "error")
        factory.assert_called_once()
        for state in ({"status": "ok", "answer": ""},
                      {"status": "ok", "answer": "Texto", "sources": []},
                      {"status": "ok", "answer": "Texto", "sources": [{"id": "ruta privada"}]}):
            tool, _, _ = self.herramienta(state)
            self.assertEqual((await tool.ainvoke({"pregunta": "IVA"}))["resultado"], "error")

    async def test_limites_salida(self):
        state = estado_ok()
        state["answer"] = "x" * 7000
        state["sources"] = [{"id": f"DOC-{i:03d}"} for i in range(1, 9)]
        tool, _, _ = self.herramienta(state)
        result = await tool.ainvoke({"pregunta": "IVA"})
        self.assertEqual(len(result["respuesta"]), 6000)
        self.assertEqual(len(result["fuentes"]), 4)


if __name__ == "__main__":
    unittest.main()
