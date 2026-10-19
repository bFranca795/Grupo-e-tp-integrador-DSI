"""Inventario técnico de llamadas del evaluador, separado de generación."""
import json
from pathlib import Path
from collections import Counter
ROOT=Path(__file__).resolve().parents[2]/'entrega_3/evidencias/ragas'
rows=[]
for p in (ROOT/'evaluacion').glob('*/calls/*.json'):
    d=json.loads(p.read_text(encoding='utf-8'))
    rows.append(dict(case_variant=p.parent.parent.name,call_id=d['call_id'],kind=d['kind'],attempt=d['attempt'],status=d['status'],seconds=d['seconds'],error=d.get('error'),started_at=d['started_at'],path=str(p.relative_to(ROOT)).replace('\\','/')))
pipeline=[]
for p in (ROOT/'generacion').glob('*.json'):
    g=json.loads(p.read_text(encoding='utf-8'))
    if isinstance(g,dict): pipeline.append(dict(id=g['id'],variant=g['variant'],status=g['status'],calls_by_role=dict(Counter(c['role'] for c in g['usage'])),usage=g['usage'],total_seconds=g['total_seconds']))
report=dict(evaluator_attempts=len(rows),evaluator_status_counts=dict(Counter(r['status'] for r in rows)),evaluator_errors=[r for r in rows if r['status']=='error'],evaluator_attempts_detail=rows,pipeline_runs=pipeline,notes='Los reintentos de un mismo call_id son intentos de la misma operación. Los callbacks del pipeline no informan uso de embeddings de consulta; no se estima. Smoke excluido de estos totales.')
out=ROOT/'resumen/auditoria_llamadas.json';out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Intentos evaluadores:',len(rows),'Errores de intento:',len(report['evaluator_errors']))
