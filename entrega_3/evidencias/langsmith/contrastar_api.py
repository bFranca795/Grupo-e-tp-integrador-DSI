"""Contrasta la exportación API real con el JSON local, sin generar llamadas LLM."""
import json
from pathlib import Path
from datetime import datetime

ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
api=json.loads((OUT/'traza_api.json').read_text(encoding='utf-8'))
root=api['root']
local=json.loads((ROOT/'entrega_3/evidencias/b4_companero/resultado_langsmith.json').read_text(encoding='utf-8'))
def flat(node):
    yield node
    for child in node['child_runs']:yield from flat(child)
nodes=list(flat(root))
def named(name):return next(n for n in nodes if n['name']==name)
llms=[n for n in nodes if n['run_type']=='llm']
judge=next(n for n in llms if n['id']==local['usage'][0]['run_id'])
generator=next(n for n in llms if n['id']==local['usage'][1]['run_id'])
def human_payload(model):
    messages=model['inputs']['messages'][0]
    message=next(m for m in messages if m['kwargs'].get('type')=='human')
    return json.loads(message['kwargs']['content'])
retrieved=named('recuperacion')['outputs']['candidates']
judged=human_payload(judge)['candidatos']
post=named('reranking')['outputs']
selected=post['selected']
context=human_payload(generator)['contexto']
expected_candidates=[{'id':r['id'],'contenido':r['documento']} for r in retrieved]
expected_context=[{'id':r['id'],'contenido':r['documento']} for r in selected]
raw_verdict=json.loads(judge['outputs']['generations'][0][0]['message']['kwargs']['content'])
raw_answer=generator['outputs']['generations'][0][0]['message']['kwargs']['content']
final=root['outputs']
checks={
 'all_nodes_same_trace':all(n['trace_id']==root['id'] for n in nodes),
 'all_remote_outputs_equal_local':all(local.get(k)==v for k,v in final.items()),
 'retrieval_candidates_equal_local':retrieved==local['candidates'],
 'all_eight_candidates_sent_to_judge':judged==expected_candidates and len(judged)==8,
 'selected_equal_local':selected==local['selected'],
 'selected_subset_candidates':all(r in retrieved for r in selected),
 'judge_response_equal_rerank_verdict':raw_verdict==post['judge'],
 'generator_context_exact_selected_order_and_content':context==expected_context,
 'generator_answer_equal_final_and_local':raw_answer==final['answer']==local['answer'],
 'final_sources_equal_selected':final['sources']==selected,
 'two_model_calls_only':len(llms)==2,
 'leaf_tokens_sum_equals_root':all(sum(n[field] for n in llms)==root[field] for field in ('prompt_tokens','completion_tokens','total_tokens')),
 'no_run_errors':not any(n.get('error') for n in nodes),
}
assert all(checks.values()),checks
for call,usage in zip((judge,generator),local['usage']):
    assert (call['prompt_tokens'],call['completion_tokens'],call['total_tokens'])==tuple(usage['usage'][k] for k in ('input_tokens','output_tokens','total_tokens'))
def seconds(n):return (datetime.fromisoformat(n['end_time'])-datetime.fromisoformat(n['start_time'])).total_seconds()
summary={
 'api_verified':True,'project':api['project'],'trace_url':api['trace_url'],
 'access':'Enlace de workspace autenticado; no verificado como público, no se publicó la traza',
 'root_id':root['id'],'start_time_utc':root['start_time'],'end_time_utc':root['end_time'],
 'revision_recorded':root['extra']['metadata'].get('revision_id'),
 'settings_remote':final['settings'],
 'checks':checks,
 'durations_seconds_api':{'root':seconds(root),'retrieval':seconds(named('recuperacion')),
    'reranking':seconds(named('reranking')),'judge_model':seconds(judge),'generation_chain':seconds(named('generacion')),'generator_model':seconds(generator)},
 'tokens_api_leaf_calls':[{'role':role,'id':n['id'],'input':n['prompt_tokens'],'output':n['completion_tokens'],'total':n['total_tokens']}
                         for role,n in [('judge',judge),('generator',generator)]],
 'root_aggregate_tokens_api':{'input':root['prompt_tokens'],'output':root['completion_tokens'],'total':root['total_tokens']},
 'selected_remote':[{'id':r['id'],'parent_id':r['metadatos']['parent_id'],'score':next(j['score'] for j in post['judge']['items'] if j['id']==r['id'])} for r in selected],
 'above_028_actually_sent_to_judge':[r['id'] for r in retrieved if r['distancia']>.28],
 'chunking_parameters_in_trace':False,
 'chunking_evidence':'Manifiesto local declara 500/100; la traza no registra esos campos ni hash de indexación',
 'visual_gap':None,
 'visual_evidence':'juez1.png, juez2.png y select.png; revisión manual en revision_capturas_finales.json',
 'b4_complete_under_requested_audit':True,
 'chunking_local_manifest_accepted_for_assignment':True,
 'optional_audit_improvements':['Registrar parámetros de chunking y hash de indexación en futuras trazas; no obligatorio para la consigna'],
 'remaining':[],
 'final_visual_review':'revision_capturas_finales.json',
}
(OUT/'contraste_api.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(summary,ensure_ascii=True,indent=2))
