import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[3]))
import json,ast,hashlib
from types import SimpleNamespace
from datetime import datetime,timezone
import chromadb
from entrega_3.rag_pipeline.__main__ import CASES,run
from entrega_3.rag_pipeline.config import PERSIST_PATH,PROJECT_ROOT
from entrega_3.rag_pipeline.indexing import snapshot,fingerprint
OUT=Path(__file__).resolve().parent

def save(name,data):
    (OUT/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
args=SimpleNamespace(candidates=8,selected=3,max_distance=.28,min_score=.5,filters='{}')
cases=dict(CASES)
names=['b1_compuesta','factual','fuera_dominio','complacencia','sinonimos']
client=chromadb.PersistentClient(path=str(PERSIST_PATH))
before={n:fingerprint(snapshot(client.get_collection(n,embedding_function=None)))
        for n in ('estudio_contable','estudio_contable_chunks')}
results=[]
for name in names:
    try:
        row={'case':name,**run(cases[name],'rerank',args)}
    except Exception as error:
        row={'case':name,'question':cases[name],'status':'execution_error','error_type':type(error).__name__,'provider_code':getattr(error,'code',None)}
    results.append(row)
    save('resultados.json',results)
    print(name,row['status'],flush=True)
previous=json.loads((PROJECT_ROOT/'entrega_3/evidencias/validacion_actual/resultados.json').read_text(encoding='utf-8'))
old={r['case']:r for r in previous if r.get('settings',{}).get('variant')=='basic'}
regression=[]
for name in names:
    try:
        row={'case':name,**run(cases[name],'basic',args)}
        row['answer_identical_to_previous']=row['answer']==old[name]['answer']
        row['source_ids_identical_to_previous']=[d['id'] for d in row['sources']]==[d['id'] for d in old[name]['sources']]
    except Exception as error:
        row={'case':name,'status':'execution_error','error_type':type(error).__name__}
    regression.append(row)
    save('basico_regresion.json',regression)
    print('basic',name,row['status'],flush=True)
after={n:fingerprint(snapshot(client.get_collection(n,embedding_function=None))) for n in before}
assert before==after
save('control.json',{'executed_at_utc':datetime.now(timezone.utc).isoformat(),
    'collection_hashes_before':before,'collection_hashes_after':after,'collections_unchanged':True,
    'rerank_count':len(results),'basic_regression_count':len(regression),
    'technical_errors':sum(r['status'] in ('execution_error','judge_error') for r in results+regression),
    'selection_limit':3,'chunk_size':500,'chunk_overlap':100,'candidate_k':8,
    'rerank_effective_max_distance':None,'basic_effective_max_distance':.28})
from langchain_core.tracers.langchain import wait_for_all_tracers
wait_for_all_tracers()
print('Ejecución terminada.',flush=True)
