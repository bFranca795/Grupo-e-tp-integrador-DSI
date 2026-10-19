"""Retries only the original 18 evaluation_error records; never generates answers."""
import asyncio,hashlib,json,shutil
from pathlib import Path
from ejecutar import OUT,HERE,ROOT,read,save,freeze,metrics,score,SingleTurnSample
from transporte_pausado import PacedAudit
BATCH=OUT/'reintentos/continuacion_01'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def protected():
    paths=list((OUT/'generacion').glob('*.json'))+[HERE/'golden_dataset.json',HERE/'corpus_manifest.json',HERE/'PROTOCOLO.md']
    paths += [p for p in (OUT/'evaluacion').glob('*/*.json') if read(p)['status'] in ('ok','not_applicable')]
    return {str(p.relative_to(ROOT)):sha(p) for p in paths}
def prepare():
    cases=freeze()
    if not BATCH.exists():
        targets=[p for p in (OUT/'evaluacion').glob('*/*.json') if read(p)['status']=='evaluation_error']
        if len(targets)!=18: raise RuntimeError('Expected exactly the 18 original failed metrics')
        BATCH.mkdir(parents=True)
        shutil.copytree(OUT/'resumen',BATCH/'resumen_antes')
        shutil.copy2(OUT/'configuracion.json',BATCH/'configuracion_original.json')
        plan=[]
        for p in sorted(targets):
            rel=p.relative_to(OUT/'evaluacion');dst=BATCH/'originales'/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dst)
            plan.append(dict(case_variant=p.parent.name,metric=p.stem,original_sha256=sha(p),relative=str(rel)))
        save(BATCH/'plan.json',dict(targets=plan,protected=protected(),parameters='Same RAGAS, models, prompts, metric timeouts and parameters; transport sequential, pause 12s, max three transient attempts.'))
    return cases,read(BATCH/'plan.json')
async def run():
    cases,plan=prepare();completed=[]
    for item in plan['targets']:
        key=item['case_variant'];id_,variant=key.rsplit('_',1)
        path=BATCH/'nuevos'/key/f"{item['metric']}.json"
        active=OUT/'evaluacion'/key/f"{item['metric']}.json"
        if path.exists():
            completed.append(dict(case_variant=key,metric=item['metric'],status=read(path)['status']));continue
        if sha(active)!=item['original_sha256']: raise RuntimeError('Unexpected change to a target; stop')
        if PacedAudit.blocked: break
        case=next(c for c in cases if c['id']==id_)
        gen=read(OUT/'generacion'/f'{key}.json')
        sample=SingleTurnSample(user_input=case['pregunta'],response=gen['answer'],retrieved_contexts=gen['generator_contexts'],reference=case['respuesta_esperada'])
        metric=metrics(PacedAudit(OUT/'evaluacion'/key/'calls'))[item['metric']]
        row=await score(metric,sample,path)
        row['continuation_batch']='continuacion_01';save(path,row)
        # Only failed active records may be replaced; original bytes are archived.
        if read(active)['status']!='evaluation_error': raise RuntimeError('Never overwrite a valid/NA score')
        save(active,row)
        completed.append(dict(case_variant=key,metric=item['metric'],status=row['status'],value=row.get('value')))
        save(BATCH/'progress.json',dict(completed=completed,blocked=PacedAudit.blocked))
        print(key,item['metric'],row['status'],row.get('value'),flush=True)
        if PacedAudit.blocked: break
    unchanged=all((ROOT/p).exists() and sha(ROOT/p)==digest for p,digest in plan['protected'].items())
    if not unchanged: raise RuntimeError('Protected response/reference/valid score was changed')
    save(BATCH/'resultado.json',dict(completed=completed,blocked=PacedAudit.blocked,protected_unchanged=unchanged,attempted=len(completed),recovered=sum(r['status']=='ok' for r in completed),remaining_errors=sum(read(p)['status']=='evaluation_error' for p in (OUT/'evaluacion').glob('*/*.json'))))
    freeze()
if __name__=='__main__': asyncio.run(run())
