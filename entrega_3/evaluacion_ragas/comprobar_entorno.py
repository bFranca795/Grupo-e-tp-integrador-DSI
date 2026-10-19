"""Comprueba instalación, versiones e imports sin APIs ni cambios en evidencias."""
import json
import os
import platform
import struct
import sys
import tomllib
from importlib.metadata import metadata, version
from pathlib import Path

os.environ['RAGAS_DO_NOT_TRACK'] = 'true'
os.environ['LANGSMITH_TRACING'] = 'false'
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from packaging.requirements import Requirement


def check_environment():
    project = tomllib.loads((ROOT / 'pyproject.toml').read_text(encoding='utf-8-sig'))
    lock = tomllib.loads((ROOT / 'uv.lock').read_text(encoding='utf-8-sig'))
    locked = {row['name']: row['version'] for row in lock['package'] if 'version' in row}
    errors = []
    direct = [Requirement(value) for value in project['project']['dependencies']]
    pinned = [Requirement(line) for line in (ROOT / 'requirements.txt').read_text(encoding='utf-8-sig').splitlines()
              if line.strip() and not line.startswith('#')]
    for requirement in direct + pinned:
        name = requirement.name
        if locked[name] not in requirement.specifier:
            errors.append(f'{name}: constraint differs from lock')
        if version(name) != locked[name]:
            errors.append(f'{name}: installed version differs from lock')
    if project['project']['requires-python'] != lock['requires-python']:
        errors.append('Python constraint differs between pyproject and lock')
    recorded = json.loads((ROOT / 'entrega_3/evidencias/ragas/configuracion.json').read_text(encoding='utf-8'))
    if platform.python_version() != recorded['python']:
        errors.append('Python differs from recorded evaluation; do not merge runs')

    # Import ordering matches the CLI's standalone event-loop adaptation.
    import adaptadores
    from ragas import SingleTurnSample
    from ragas.metrics import Faithfulness, ResponseRelevancy, LLMContextPrecisionWithReference, LLMContextRecall
    from entrega_3.rag_pipeline.pipeline import Settings

    report = dict(status='PASS' if not errors else 'FAIL', python=sys.version,
                  evaluation_python=recorded['python'], platform=platform.platform(),
                  architecture=platform.machine(), bits=struct.calcsize('P') * 8,
                  project_requires_python=project['project']['requires-python'],
                  ragas_requires_python=metadata('ragas')['Requires-Python'],
                  versions={name: version(name) for name in ['ragas', 'google-genai', 'langchain-core',
                            'langchain-community', 'langchain-openai', 'pydantic', 'numpy', 'chromadb', 'nest-asyncio']},
                  imports='OK', errors=errors, api_calls=0,
                  clean_install_recorded=(ROOT / 'entrega_3/evidencias/ragas/instalacion_limpia/resultado.json').exists())
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return bool(errors)


if __name__ == '__main__':
    raise SystemExit(check_environment())
