"""Generar, evaluar y reanudar sin modificar los pipelines ni el golden aprobado."""
import os
os.environ['RAGAS_DO_NOT_TRACK']='true'
# La evaluación se audita localmente, separada de la telemetría de B.
os.environ['LANGSMITH_TRACING']='false'
import argparse,asyncio,hashlib,json,math,sys,time,types,platform
from dataclasses import asdict
from importlib.metadata import version
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from corpus import read_corpus
from validar import validate
from adaptadores import Audit,EvaluatorLLM,EvaluatorEmbeddings,MODEL,EMBEDDING,now,transient,error_info
from dotenv import load_dotenv
load_dotenv(ROOT/'.env')
from ragas import SingleTurnSample
from ragas.metrics import Faithfulness,ResponseRelevancy,LLMContextPrecisionWithReference,LLMContextRecall
from entrega_3.rag_pipeline.pipeline import Settings,UsageRecorder,build_pipeline,GENERATION_PROMPT,ESCAPE
OUT=ROOT/'entrega_3/evidencias/ragas'
HERE=Path(__file__).resolve().parent
NAMES=['faithfulness','answer_relevancy','context_precision','context_recall']
def save(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8');tmp.replace(path)
def read(path): return json.loads(path.read_text(encoding='utf-8-sig'))
def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def freeze():
    if validate(): raise RuntimeError('El corpus o dataset cambió; evaluación detenida')
    config=dict(dataset_sha256=digest(HERE/'golden_dataset.json'),manifest_sha256=digest(HERE/'corpus_manifest.json'),protocol_sha256=digest(HERE/'PROTOCOLO.md'),pipeline_hashes={p.name:digest(p) for p in sorted((ROOT/'entrega_3/rag_pipeline').glob('*.py'))},prompt=[dict(type=m.type,content=m.content) for m in GENERATION_PROMPT.format_messages(payload="{payload}")],generator=dict(model=MODEL,temperature=0.0),settings={v:asdict(Settings(variant=v)) for v in ('basic','rerank')},evaluator=dict(ragas=version('ragas'),llm=MODEL,temperature=0.0,max_output_tokens=8192,embeddings=EMBEDDING,embedding_dimension=768,embedding_task='SEMANTIC_SIMILARITY',answer_relevancy_strictness=3,transient_max_attempts=3,parser_repair_attempts=0),implementations={n:f'ragas.metrics.{c.__name__}' for n,c in zip(NAMES,[Faithfulness,ResponseRelevancy,LLMContextPrecisionWithReference,LLMContextRecall])},python=platform.python_version(),dependencies={n:version(n) for n in ('ragas','google-genai','langchain-core','langchain-community','pydantic','numpy','chromadb')},uv_lock_sha256=digest(ROOT/'uv.lock'))
    path=OUT/'configuracion.json'
    if path.exists() and read(path)!=config: raise RuntimeError('Configuración cambió: no mezclar ejecuciones')
    if not path.exists(): save(path,config)
    return read(HERE/'golden_dataset.json')
def metrics(audit):
    llm=EvaluatorLLM(audit);emb=EvaluatorEmbeddings(audit)
    result=[Faithfulness(llm=llm),ResponseRelevancy(llm=llm,embeddings=emb,strictness=3),LLMContextPrecisionWithReference(llm=llm),LLMContextRecall(llm=llm)]
    # Deshabilitar reparaciones de JSON; no cambia prompts ni fórmula de RAGAS.
    seen=set()
    for metric in result:
        for prompt in metric.get_prompts().values():
            if id(prompt) in seen: continue
            seen.add(id(prompt));original=prompt.generate
            async def no_repair(*args,_original=original,**kwargs):
                kwargs['retries_left']=0
                return await _original(*args,**kwargs)
            object.__setattr__(prompt,'generate',no_repair)
    return dict(zip(NAMES,result))
async def score(metric,sample,path,force=False):
    if path.exists(): return read(path)
    started=time.perf_counter();row=dict(started_at=now(),metric=metric.name,input=sample.model_dump())
    try:
        value=float(await metric.single_turn_ascore(sample,timeout=180))
        row.update(value=value if math.isfinite(value) else None,raw_value=value if math.isfinite(value) else str(value),status='ok' if math.isfinite(value) else 'evaluation_undefined')
        if not math.isfinite(value) and metric.name=='faithfulness':
            row.update(status='not_applicable',reason='no_claims')
    except Exception as error: row.update(value=None,status='evaluation_error',error=error_info(error))
    row['seconds']=time.perf_counter()-started;save(path,row);return row
async def smoke():
    freeze()
    for id,q,response,contexts,reference in [('factual','¿Qué integra la cuota mensual del Monotributo?','Integra impuesto integrado, aporte jubilatorio y aporte a obra social.',['La cuota del Monotributo integra el impuesto integrado, el aporte jubilatorio y el aporte a la obra social.'],'La cuota integra impuesto integrado, aporte jubilatorio y aporte a obra social.'),('escape_empty','¿Qué certificado fitosanitario necesito para exportar ganado?',ESCAPE,[],ESCAPE)]:
        folder=OUT/'smoke_compatible'/id
        sample=SingleTurnSample(user_input=q,response=response,retrieved_contexts=contexts,reference=reference)
        for name,metric in metrics(Audit(folder/'calls')).items():
            row=await score(metric,sample,folder/f'{name}.json',True)
            print('smoke',id,name,row['status'],row['value'],flush=True)
    rows=[read(p) for p in (OUT/'smoke_compatible').glob('*/*.json')]
    if any(r['status']=='evaluation_error' for r in rows): raise RuntimeError('Prueba mínima con errores técnicos: revisar antes de corrida final')
def generate():
    data=freeze()
    for case in data:
        for variant in ('basic','rerank'):
            path=OUT/'generacion'/f"{case['id']}_{variant}.json"
            if path.exists(): continue
            settings=Settings(variant=variant);attempts=[]
            for attempt in range(1,4):
                started=time.perf_counter();usage=UsageRecorder();date=now()
                try:
                    result=build_pipeline(settings).invoke({'question':case['pregunta']},config={'callbacks':[usage],'tags':['parte_c',variant]})
                    row=dict(id=case['id'],variant=variant,started_at=date,total_seconds=time.perf_counter()-started,**result,usage=usage.calls,attempts=attempts)
                    row['generator_contexts']=[s['documento'] for s in result['sources']]
                    row['generator_payload']=dict(pregunta=case['pregunta'],contexto=[dict(id=s['id'],contenido=s['documento']) for s in result['sources']]) if any(c['role']=='generator' for c in usage.calls) else None
                    break
                except Exception as error:
                    attempts.append(dict(attempt=attempt,started_at=date,seconds=time.perf_counter()-started,error=error_info(error),usage=usage.calls))
                    save(OUT/'generacion'/f"{case['id']}_{variant}_attempts.json",attempts)
                    if attempt<3 and transient(error): time.sleep(2*attempt);continue
                    row=dict(id=case['id'],variant=variant,started_at=date,status='execution_error',answer=None,candidates=[],selected=[],sources=[],generator_contexts=[],generator_payload=None,settings=asdict(settings),usage=usage.calls,attempts=attempts,total_seconds=time.perf_counter()-started)
                    break
            save(path,row);print('generation',case['id'],variant,row['status'],flush=True)
    freeze()
async def evaluate():
    data=freeze()
    smoke_rows=list((OUT/'smoke_compatible').glob('*/*.json'))
    if len(smoke_rows)!=8 or any(read(p)['status']=='evaluation_error' for p in smoke_rows): raise RuntimeError('Falta smoke v?lido')
    semaphore=asyncio.Semaphore(2)
    async def one(case,variant,name,metric,gen,sample,folder):
        path=folder/f'{name}.json'
        if path.exists(): return
        reason=None;status='not_applicable'
        if gen['status'] not in ('ok','insufficient_context'): reason=gen['status'];status='pipeline_error'
        elif name in ('context_precision','context_recall') and case['espera_escape']: reason='no_positive_factual_reference'
        elif name=='context_precision' and not gen['generator_contexts']: reason='empty_context_ranking'
        if reason: row=dict(status=status,value=None,reason=reason);save(path,row)
        else:
            async with semaphore: row=await score(metric,sample,path)
        print('evaluation',case['id'],variant,name,row['status'],row['value'],flush=True)
    tasks=[]
    for case in data:
        for variant in ('basic','rerank'):
            gen=read(OUT/'generacion'/f"{case['id']}_{variant}.json")
            sample=SingleTurnSample(user_input=case['pregunta'],response=gen['answer'] or '',retrieved_contexts=gen['generator_contexts'],reference=case['respuesta_esperada'])
            folder=OUT/'evaluacion'/f"{case['id']}_{variant}"
            for name,metric in metrics(Audit(folder/'calls')).items():
                tasks.append(one(case,variant,name,metric,gen,sample,folder))
    await asyncio.gather(*tasks)
    freeze()
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('phase',choices=['smoke','generate','evaluate']);args=parser.parse_args()
    if args.phase=='generate': generate()
    else: asyncio.run(smoke() if args.phase=='smoke' else evaluate())
