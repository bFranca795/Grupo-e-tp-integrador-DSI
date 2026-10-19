"""Exporta resultados existentes sin llamadas externas."""
import csv,json,math,statistics
from pathlib import Path
from ejecutar import OUT,HERE,NAMES,read,save

def summarize():
    cases=read(HERE/'golden_dataset.json');rows=[];generations=[]
    for c in cases:
        for variant in ('basic','rerank'):
            gp=OUT/'generacion'/f"{c['id']}_{variant}.json"
            if gp.exists(): generations.append(read(gp))
            for metric in NAMES:
                p=OUT/'evaluacion'/f"{c['id']}_{variant}"/f'{metric}.json'
                r=read(p) if p.exists() else dict(value=None,status='pending')
                rows.append({**r,'id':c['id'],'variant':variant,'metric':metric})
    def valid(row): return row['status']=='ok' and isinstance(row['value'],(int,float)) and math.isfinite(row['value'])
    aggregates=[];paired=[]
    for metric in NAMES:
        for variant in ('basic','rerank'):
            group=[r for r in rows if r['variant']==variant and r['metric']==metric];values=[r['value'] for r in group if valid(r)]
            aggregates.append(dict(metric=metric,variant=variant,mean=statistics.mean(values) if values else None,n=len(values),valid_ids=[r['id'] for r in group if valid(r)],excluded=[dict(id=r['id'],status=r['status'],reason=r.get('reason') or r.get('error')) for r in group if not valid(r)]))
        lookup={(r['id'],r['variant']):r for r in rows if r['metric']==metric}
        ids=[c['id'] for c in cases if all(valid(lookup[(c['id'],v)]) for v in ('basic','rerank'))]
        means={v:statistics.mean(lookup[(id,v)]['value'] for id in ids) if ids else None for v in ('basic','rerank')}
        paired.append(dict(metric=metric,**means,delta=means['rerank']-means['basic'] if ids else None,n=len(ids),paired_ids=ids,excluded=[dict(id=c['id'],states={v:dict(status=lookup[(c['id'],v)]['status'],reason=lookup[(c['id'],v)].get('reason') or lookup[(c['id'],v)].get('error')) for v in ('basic','rerank')}) for c in cases if c['id'] not in ids]))
    escapes=[]
    for g in generations:
        if g['id'] not in ('E1','E2'): continue
        expected=next(c['respuesta_esperada'] for c in cases if c['id']==g['id'])
        escapes.append(dict(id=g['id'],variant=g['variant'],status=g['status'],answer=g['answer'],exact_abstention=g['status'] in ('ok','insufficient_context') and g['answer'].strip()==expected,correct_abstention=None,source_ids=[s['id'] for s in g['sources']]))
    manual_path=OUT/'resumen/revision_escapes.json'
    if manual_path.exists():
        manual=read(manual_path)
        for e in escapes:
            review=next((r for r in manual if r['id']==e['id'] and r['variant']==e['variant']),None)
            if review: e.update(correct_abstention=review['correct_abstention'],review_reason=review['reason'])
    advanced=[r for r in aggregates if r['variant']=='rerank' and r['mean'] is not None]
    lowest=min((r['mean'] for r in advanced),default=None)
    worst=[r['metric'] for r in advanced if math.isclose(r['mean'],lowest,abs_tol=1e-9)]
    summary=dict(aggregates=aggregates,paired=paired,escapes=escapes,worst_advanced_metrics=worst,any_improvement=any(p['delta'] is not None and p['delta']>1e-9 for p in paired),pending=sum(r['status']=='pending' for r in rows),generation_count=len(generations))
    summary['technical_evaluation_errors']=sum(r['status'] in ('evaluation_error','pipeline_error','evaluation_undefined') for r in rows)
    summary['c_complete']=summary['pending']==0 and summary['technical_evaluation_errors']==0 and len(generations)==20 and summary['any_improvement']
    save(OUT/'resumen/resumen.json',summary)
    save(OUT/'resumen/metricas_individuales.json',rows)
    p=OUT/'resumen/metricas_individuales.csv'
    with p.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['id','variant','metric','value','status','reason']);w.writeheader();w.writerows({k:r.get(k) for k in w.fieldnames} for r in rows)
    report=['# Evaluación real de Parte C','', '## Comparación pareada','', '| Métrica | Basic | Rerank | Delta | Pares |','|---|---:|---:|---:|---:|']
    fmt=lambda x:'—' if x is None else f'{x:.6f}'
    for p in paired: report.append(f"| {p['metric']} | {fmt(p['basic'])} | {fmt(p['rerank'])} | {fmt(p['delta'])} | {p['n']} |")
    report+=['','## Agregados por variante','', '| Métrica | Variante | Media | n |','|---|---|---:|---:|']
    for r in aggregates: report.append(f"| {r['metric']} | {r['variant']} | {fmt(r['mean'])} | {r['n']} |")
    report+=['','## Métricas individuales','', '| ID | Variante | Faithfulness | Answer Relevancy | Context Precision | Context Recall |','|---|---|---|---|---|---|']
    for c in cases:
        for v in ('basic','rerank'):
            rr=[next(r for r in rows if r['id']==c['id'] and r['variant']==v and r['metric']==m) for m in NAMES]
            report.append('| '+ ' | '.join([c['id'],v]+[fmt(r['value'])+' ('+r['status']+')' for r in rr])+' |')
    report+=['','## Exclusiones pareadas','']
    for p in paired:
        report.append(f"- {p['metric']}: "+(json.dumps(p['excluded'],ensure_ascii=False) if p['excluded'] else 'ninguna'))
    report+=['','## Escapes funcionales','']
    for e in escapes: report.append(f"- {e['id']} / {e['variant']}: estado {e['status']}; abstención exacta y sin contenido añadido: {e['correct_abstention']}.")
    report+=['','## Veinte respuestas completas y fuentes','']
    for g in generations:
        c=next(c for c in cases if c['id']==g['id'])
        report += [f"### {g['id']} / {g['variant']}",'',c['pregunta'],'',g['answer'] or '(Sin respuesta: error técnico)','','Estado: '+g['status']+'. Fuentes: '+(', '.join(s['id'] for s in g['sources']) or 'ninguna')+'.','']
        for s in g['sources']: report+=['> '+s['id']+': '+s['documento'],'']
    (OUT/'resumen/resultados_para_revision.md').write_text('\n'.join(report)+'\n',encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=='__main__': summarize()
