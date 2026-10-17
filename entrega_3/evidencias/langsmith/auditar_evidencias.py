"""Auditoría local de evidencias B.4. No hace llamadas a Gemini ni cambia el pipeline."""
import json
import hashlib
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
local_path=ROOT/'entrega_3/evidencias/b4_companero/resultado_langsmith.json'
r=json.loads(local_path.read_text(encoding='utf-8'))
index=json.loads((local_path.parent/'indexacion.json').read_text(encoding='utf-8'))
by_id={d['id']:d for d in r['candidates']}
judgments={j['id']:j for j in r['judge']['items']}
selected_ids=[d['id'] for d in r['selected']]
expected_ids=[j['id'] for j in sorted(r['judge']['items'],key=lambda j:j['score'],reverse=True)
              if j['score']>=r['settings']['min_judge_score']][:r['settings']['selected_k']]
checks={
    'candidate_count':len(r['candidates']),
    'selected_count':len(r['selected']),
    'candidate_ids_unique':len(by_id)==len(r['candidates']),
    'selected_ids_unique':len(set(selected_ids))==len(selected_ids),
    'selected_belong_to_candidates':all(d['id'] in by_id for d in r['selected']),
    'selected_content_metadata_equal_candidates':all(d==by_id[d['id']] for d in r['selected']),
    'sources_equal_selected_including_order_and_content':r['sources']==r['selected'],
    'selected_order_matches_judgment_and_settings':selected_ids==expected_ids,
    'judged_ids_equal_candidates':set(judgments)==set(by_id),
    'all_scores_valid':all(isinstance(j['score'],(int,float)) and not isinstance(j['score'],bool) and 0<=j['score']<=1 for j in r['judge']['items']),
    'above_point28_retrieved_and_judged':[d['id'] for d in r['candidates'] if d['distancia']>.28 and d['id'] in judgments],
}
assert all(checks[name] for name in ('candidate_ids_unique','selected_ids_unique','selected_belong_to_candidates',
    'selected_content_metadata_equal_candidates','sources_equal_selected_including_order_and_content',
    'selected_order_matches_judgment_and_settings','judged_ids_equal_candidates','all_scores_valid'))
assert checks['candidate_count']==8 and checks['selected_count']==4
images=[]
for source,target in [
 ('entrega_3/Generacion.png','entrega_3/langsmith_trace.png'),
 ('entrega_3/Juez_relevancia.png','entrega_3/evidencias/langsmith/juez_relevancia.png'),
 ('entrega_3/Recuperacion.png','entrega_3/evidencias/langsmith/recuperacion.png'),
 ('entrega_3/Reranking.png','entrega_3/evidencias/langsmith/reranking.png'),
]:
    a=(ROOT/source).read_bytes();b=(ROOT/target).read_bytes()
    assert a==b
    images.append({'original':source,'copy':target,'byte_identical':True,'sha256':hashlib.sha256(a).hexdigest()})
usage={u['role']:{'run_id_local':u['run_id'],'tokens_reported_in_local_json':u['usage']}
       for u in r['usage']}
audit={
 'audit_scope':'capturas PNG originales y JSON local; sin consulta a API por credencial no utilizable',
 'api_access':{'attempted':False,'reason':'LANGSMITH_API_KEY local es un marcador de ejemplo; permisos de lectura desconocidos'},
 'remote_identity':{'project':None,'root_run_id':None,'trace_url':None,'remote_date_verified':False,
                    'note':'No aparecen en las capturas; no se inventa URL ni se usa el ID de una llamada hija como ID raíz'},
 'local_execution':{'executed_at_utc':r['executed_at_utc'],'executed_at_buenos_aires':'2026-10-17T19:33:38.088354-03:00',
                    'status':r['status'],'settings':r['settings'],'total_seconds':r['total_seconds'],
                    'timings':r['timings'],'model_calls':usage},
 'screenshots_observed':{'root_name':'rag_rerank','clock_text':'10:33 PM, sin fecha ni zona visibles',
    'root_duration_seconds_rounded':14.70,'retrieval_seconds_rounded':.43,'reranking_seconds_rounded':8.82,
    'judge_chain_seconds_rounded':8.81,'generation_seconds_rounded':5.37,
    'judge_tokens_display':'1.732K','generator_tokens_display':'1.099K',
    'candidates_count_visible':8,'post_rerank_selected_count_visible':False,
    'full_judge_scores_visible':False,'full_final_answer_visible':False},
 'local_consistency_checks':checks,
 'local_index_manifest':index,
 'provenance_warning':'El corpus del compañero es 18 documentos / 36 chunks e incluye DOC-00X; no confundirlo con el corpus anterior de 17/35',
 'images':images,
 'missing_evidence':[
   'Proyecto, ID raíz, fecha con zona y enlace privado de la ejecución',
   'Vista Output de recuperacion con candidates expandidos y ocho IDs/contenidos',
   'Vista Output de reranking con selected y judge expandidos (orden, scores y motivos)',
   'Vista Input del modelo generador que permita contrastar los cuatro IDs y textos exactos',
   'Vista Output de respuesta_y_fuentes o raíz con respuesta completa y sources',
   'Vista de metadatos del modelo juez y generador con tokens input/output; o lectura API equivalente',
   'Configuración de esta ejecución y vínculo verificable con la indexación 500/100',
 ],
 'b4_complete':False,
}
(OUT/'verificacion_b4.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Consistencia local: ocho candidatos, cuatro fuentes; pertenencia, contenido y orden verificados.')
print('Cuatro PNG copiados sin cambiar bytes; identidad remota y API pendientes.')
for d in r['selected']:
    print(d['id'], 'padre='+d['metadatos']['parent_id'], 'score='+str(judgments[d['id']]['score']))
