"""API inicial: lifecycle con dobles y SQLite temporal, sin llamadas externas."""

import hashlib
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import asynccontextmanager
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import aiosqlite
from fastapi import FastAPI
from fastapi.testclient import TestClient

from grupo_e_tp_integrador_dsi.api import app, crear_app
from grupo_e_tp_integrador_dsi.agente import AgenteContable
from grupo_e_tp_integrador_dsi.solicitudes import PROJECT_ROOT


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.agente = Mock()
        self.agente.ainvoke = AsyncMock(side_effect=AssertionError("No ejecutar el agente"))
        self.events = []

        @asynccontextmanager
        async def abrir():
            self.events.append("abrir")
            try:
                yield self.agente
            finally:
                self.events.append("cerrar")

        self.abrir = Mock(side_effect=abrir)
        self.app = crear_app(abrir_agente=self.abrir)

    def test_01_app(self):
        self.assertIsInstance(app, FastAPI)
        self.assertIsInstance(self.app, FastAPI)
        self.assertIsNone(app.state.agente)
        self.abrir.assert_not_called()

    def test_02_http_200(self):
        with TestClient(self.app) as client:
            response = client.get("/health")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.headers["content-type"], "application/json")

    def test_03_contrato(self):
        with TestClient(self.app) as client:
            self.assertEqual(client.get("/health").json(),
                             {"status": "ok", "service": "agente-contable"})

    def test_04_inicializacion_unica(self):
        with TestClient(self.app) as client:
            for _ in range(3):
                client.get("/health")
            self.abrir.assert_called_once_with()
            self.assertEqual(self.events, ["abrir"])

    def test_05_misma_instancia(self):
        with TestClient(self.app) as client:
            for _ in range(3):
                self.assertIs(self.app.state.agente, self.agente)
                client.get("/health")

    def test_06_cierre(self):
        with TestClient(self.app):
            self.assertIs(self.app.state.agente, self.agente)
        self.assertEqual(self.events, ["abrir", "cerrar"])
        self.assertIsNone(self.app.state.agente)

    def test_07_importacion_sin_recursos(self):
        script = '''
import sys
from unittest.mock import patch
with patch('aiosqlite.connect', side_effect=AssertionError('SQLite async')), \\
     patch('sqlite3.connect', side_effect=AssertionError('SQLite sync')), \\
     patch('google.genai.Client', side_effect=AssertionError('Gemini')), \\
     patch('chromadb.PersistentClient', side_effect=AssertionError('Chroma')):
    from grupo_e_tp_integrador_dsi.api import app
    assert app.state.agente is None
    assert 'grupo_e_tp_integrador_dsi.agente' not in sys.modules
    from uvicorn.importer import import_from_string
    assert import_from_string('grupo_e_tp_integrador_dsi.api:app') is app
'''
        result = subprocess.run([sys.executable, "-B", "-c", script],
                                capture_output=True, text=True, timeout=90)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_08_health_sin_efectos(self):
        with patch("google.genai.Client", side_effect=AssertionError("Gemini")), \
             patch("chromadb.PersistentClient", side_effect=AssertionError("Chroma")), \
             patch("aiosqlite.connect", side_effect=AssertionError("SQLite")):
            with TestClient(self.app) as client:
                self.assertEqual(client.get("/health").status_code, 200)
        self.agente.ainvoke.assert_not_called()
        self.assertEqual(self.agente.mock_calls, [])

    def test_09_error_inicio_cierra_sqlite(self):
        class AgenteFallido(AgenteContable):
            def __init__(self, **kwargs):
                raise RuntimeError("Fallo simulado de inicialización")

        connections = []
        connect = aiosqlite.connect

        def conectar(*args, **kwargs):
            connection = connect(*args, **kwargs)
            connections.append(connection)
            return connection

        with tempfile.TemporaryDirectory() as temp:
            api = crear_app(abrir_agente=lambda: AgenteFallido.abrir(
                ruta_checkpoints=Path(temp) / "checkpoints.sqlite"))
            with patch("grupo_e_tp_integrador_dsi.agente.aiosqlite.connect", side_effect=conectar):
                with self.assertRaisesRegex(RuntimeError, "Fallo simulado"):
                    with TestClient(api):
                        self.fail("No debe aceptar peticiones si falla el inicio")
            self.assertEqual(len(connections), 1)
            with self.assertRaises(ValueError):
                _ = connections[0]._conn  # El driver confirma que ya no hay conexión activa.
            self.assertIsNone(api.state.agente)

    def test_10_bases_reales_intactas(self):
        def snapshot():
            files = []
            for folder in (PROJECT_ROOT / "chroma_db", PROJECT_ROOT / "data/agente"):
                if folder.exists():
                    files.extend(p for p in folder.rglob("*") if p.is_file())
            return {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}

        before = snapshot()
        with TestClient(self.app) as client:
            client.get("/health")
        self.assertEqual(snapshot(), before)

    def test_endpoints_permitidos(self):
        with TestClient(self.app) as client:
            self.assertEqual(client.get("/metricas").status_code, 200)
            self.assertEqual(client.get("/consultar").status_code, 405)
        self.assertEqual(set(self.app.openapi()["paths"]), {"/health", "/consultar", "/estado/{thread_id}", "/metricas"})

    def test_comando_uvicorn_desde_raiz(self):
        script = '''
from unittest.mock import patch
import uvicorn
def ejecutar_simulado(server, **kwargs):
    server.started = True
with patch('uvicorn.Server.run', autospec=True, side_effect=ejecutar_simulado) as run:
    uvicorn.main(args=['grupo_e_tp_integrador_dsi.api:app', '--app-dir', 'src',
                       '--host', '127.0.0.1', '--port', '8000'], standalone_mode=False)
    run.assert_called_once()
    config = run.call_args.args[0].config
    config.load()
    from grupo_e_tp_integrador_dsi.api import app
    assert app.state.agente is None
    assert config.host == '127.0.0.1' and config.port == 8000
'''
        env = os.environ.copy()
        env.pop("PYTHONPATH", None)
        result = subprocess.run([sys.executable, "-B", "-c", script], cwd=PROJECT_ROOT,
                                env=env, capture_output=True, text=True, timeout=90)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
