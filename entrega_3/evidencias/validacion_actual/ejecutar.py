import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
import json
import os
import hashlib
from datetime import datetime, timezone
from types import SimpleNamespace
import chromadb
from entrega_3.rag_pipeline.config import PERSIST_PATH, PROJECT_ROOT
from entrega_3.rag_pipeline.indexing import rebuild, snapshot, fingerprint
from entrega_3.rag_pipeline.retriever import RetrieverContable
from entrega_3.rag_pipeline.__main__ import CASES, run

OUT = Path(__file__).resolve().parent

def save(name, data):
    (OUT / name).write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

def code_hashes():
    paths = sorted((PROJECT_ROOT/'entrega_3/rag_pipeline').glob('*.py'))
    paths += [PROJECT_ROOT/name for name in ('pyproject.toml','uv.lock','requirements.txt','.env.example')]
    return {str(p.relative_to(PROJECT_ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}

before_code=code_hashes()
save('implementacion_antes.json', before_code)
credentials={name:bool(os.getenv(name)) for name in ('GEMINI_API_KEY','LANGSMITH_API_KEY','LANGSMITH_PROJECT','LANGSMITH_ENDPOINT')}
credentials['LANGSMITH_TRACING_configured']=bool(os.getenv('LANGSMITH_TRACING'))
credentials['LANGSMITH_TRACING_enabled']=os.getenv('LANGSMITH_TRACING','').lower() in ('true','1')
save('credenciales.json',credentials)
client=chromadb.PersistentClient(path=str(PERSIST_PATH))
original=client.get_collection('estudio_contable',embedding_function=None)
chunks=client.get_collection('estudio_contable_chunks',embedding_function=None)
before_original=snapshot(original)
before_chunks=snapshot(chunks)
save('original_antes.json',before_original)
save('chunks_antes.json',before_chunks)
index_result=rebuild()
after_original=snapshot(original)
after_chunks=snapshot(chunks)
save('original_despues.json',after_original)
save('chunks_despues.json',after_chunks)
integrity={
    'original_count_before':original.count(), 'original_count_after':len(after_original),
    'chunks_count_before':len(before_chunks),'chunks_count_after':len(after_chunks),
    'original_unique_ids_before':len({r['id'] for r in before_original}),
    'original_unique_ids_after':len({r['id'] for r in after_original}),
    'chunks_unique_ids_before':len({r['id'] for r in before_chunks}),
    'chunks_unique_ids_after':len({r['id'] for r in after_chunks}),
    'original_full_equality':before_original==after_original,
    'original_hash_before':fingerprint(before_original),'original_hash_after':fingerprint(after_original),
    'changed_text_ids':[a['id'] for a,b in zip(before_original,after_original) if a['documento']!=b['documento']],
    'changed_metadata_ids':[a['id'] for a,b in zip(before_original,after_original) if a['metadatos']!=b['metadatos']],
    'chunks_same_ids':{r['id'] for r in before_chunks}=={r['id'] for r in after_chunks},
    'index_result':index_result,
}
save('integridad.json',integrity)
print('Indexación repetida; integridad guardada.',flush=True)
args=SimpleNamespace(candidates=8,selected=3,max_distance=0.28,min_score=0.5,filters='{}')
cases=dict(CASES)
results=[]
for case,variant in [('factual','basic'),('fuera_dominio','basic'),('complacencia','basic'),('sinonimos','basic'),('b1_compuesta','basic'),('b1_compuesta','chunks'),('b1_compuesta','rerank')]:
    try:
        result={'case':case,**run(cases[case],variant,args)}
    except Exception as error:
        result={'case':case,'variant':variant,'question':cases[case],'status':'execution_error','error_type':type(error).__name__,'provider_code':getattr(error,'code',None)}
    results.append(result)
    save('resultados.json',results)
    print(case,variant,result['status'],flush=True)
# Observación sin umbral: no se altera el pipeline ejecutado arriba.
diagnostics={}
for variant,collection,k in [('basic','estudio_contable',3),('chunks','estudio_contable_chunks',3),('rerank','estudio_contable_chunks',8)]:
    retriever=RetrieverContable(collection_name=collection)
    raw=retriever.recuperar(cases['b1_compuesta'],n_resultados=k,distancia_maxima=None)
    ranking=retriever.recuperar(cases['b1_compuesta'],n_resultados=retriever.coleccion.count(),distancia_maxima=None)
    diagnostics[variant]={'question':cases['b1_compuesta'],'top_k':k,'threshold':0.28,
        'before_distance_filter':raw,'after_distance_filter':[r for r in raw if r['distancia']<=0.28],
        'all_active_ranked_diagnostic':ranking}
    save('diagnosticos.json',diagnostics)
# Conservar el corpus completo para cotejar expectativas sin depender del JSON limpio.
save('implementacion_despues.json',code_hashes())
assert before_code==code_hashes(), 'La implementación cambió durante la validación'
save('resumen.json',{'executed_at_utc':datetime.now(timezone.utc).isoformat(),'implementation_unchanged':True,
    'cases_executed':len(results),'technical_errors':sum(r['status'] in ('execution_error','judge_error') for r in results),
    'langsmith_credentials':credentials})
from langchain_core.tracers.langchain import wait_for_all_tracers
wait_for_all_tracers()
print('Validación terminada; implementación sin cambios.',flush=True)
