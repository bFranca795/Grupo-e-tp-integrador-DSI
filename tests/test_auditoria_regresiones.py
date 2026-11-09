"""Regresiones concretas detectadas en la auditoría, sin servicios externos."""

from contextlib import asynccontextmanager
from pathlib import Path
import tempfile
import unittest
from unittest.mock import AsyncMock, Mock, patch

import httpx

from grupo_e_tp_integrador_dsi.api import crear_app
from grupo_e_tp_integrador_dsi.solicitudes import crear_solicitud
from grupo_e_tp_integrador_dsi.herramienta_rag import crear_herramienta_rag
from grupo_e_tp_integrador_dsi.trazabilidad import Trazador
from test_trazabilidad import ClienteLocal


class AuditoriaRegresionesTests(unittest.IsolatedAsyncioTestCase):
    async def test_estado_422_no_refleja_identificador_sensible(self):
        agent = Mock()
        agent.consultar_estado = AsyncMock(return_value={})

        @asynccontextmanager
        async def abrir():
            yield agent

        app = crear_app(abrir_agente=abrir)
        private = "usuario@ejemplo.com"
        async with app.router.lifespan_context(app):
            before = app.state.metricas.consultar()
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get("/estado/" + private + "x" * 129)
            self.assertEqual(response.status_code, 422)
            self.assertNotIn(private, response.text)
            self.assertEqual(app.state.metricas.consultar(), before)
        agent.consultar_estado.assert_not_called()

    async def test_thread_id_blanco_mismas_reglas_post_y_get(self):
        agent = Mock()
        agent.consultar_estado = AsyncMock(return_value={})
        @asynccontextmanager
        async def abrir():
            yield agent
        app = crear_app(abrir_agente=abrir)
        async with app.router.lifespan_context(app):
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
                # str.strip() considera estos controles espacios; el regex Unicode
                # de Pydantic no necesariamente usa el mismo conjunto de caracteres.
                for code in range(0x1C, 0x20):
                    with self.subTest(code=code):
                        post = await client.post("/consultar", json={"thread_id": chr(code), "pregunta": "Hola"})
                        get = await client.get(f"/estado/%{code:02X}")
                        self.assertEqual(post.status_code, 422)
                        self.assertEqual(get.status_code, 422)
        agent.consultar_estado.assert_not_called()

    async def test_nul_rechazado_antes_de_escribir_sqlite(self):
        with tempfile.TemporaryDirectory() as temp:
            for field in ("descripcion", "clave_idempotencia"):
                for index, value in enumerate(("\x00", "texto\x00resto")):
                    with self.subTest(field=field, index=index):
                        path = Path(temp) / f"{field}-{index}.sqlite"
                        args = {"categoria": "IVA", "descripcion": "Revisar documentación",
                                "clave_idempotencia": "auditoria"}
                        args[field] = value
                        with self.assertRaises(ValueError):
                            await crear_solicitud(**args, ruta_db=path)
                        self.assertFalse(path.exists())

    async def test_cliente_trazas_se_cierra_si_flush_falla(self):
        client = ClienteLocal()
        client.flush = Mock(side_effect=RuntimeError("fallo sintetico"))
        client.close = Mock()
        with patch("grupo_e_tp_integrador_dsi.trazabilidad.Client", return_value=client):
            tracer = Trazador(enabled=True)
            with tracer.consulta():
                pass
            tracer.cerrar()
        self.assertTrue(tracer.error)
        client.close.assert_called_once_with(timeout=3)

    async def test_rag_acepta_ids_de_colisiones_del_etl(self):
        for source_id in ("DOC-002-dup-1", "DOC-002-dup-1::chunk-000-0123456789abcdef"):
            with self.subTest(source_id=source_id):
                pipeline = Mock()
                pipeline.invoke.return_value = {"status": "ok", "answer": "Respuesta sustentada",
                                                "sources": [{"id": source_id}]}
                tool = crear_herramienta_rag(pipeline_factory=Mock(return_value=pipeline))
                response = await tool.ainvoke({"pregunta": "Consulta sintética"})
                self.assertEqual(response["resultado"], "respondida")
                self.assertEqual(response["fuentes"], [{"id": source_id, "id_documental": "DOC-002-dup-1"}])
                with tempfile.TemporaryDirectory() as temp:
                    linked = await crear_solicitud("IVA", "Revisar documentación", "auditoria-ref",
                        response["fuentes"][0]["id_documental"], ruta_db=Path(temp)/"solicitudes.sqlite")
                    self.assertEqual(linked.resultado, "creada")


if __name__ == "__main__":
    unittest.main()
