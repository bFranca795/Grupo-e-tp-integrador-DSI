"""Índice de juicios brutos del evaluador; no recalcula métricas."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]/'entrega_3/evidencias/ragas'
def extract():
    rows=[]
    for p in sorted((ROOT/'evaluacion').glob('*/calls/*.json')):
        d=json.loads(p.read_text(encoding='utf-8'))
        if d['kind']!='evaluator_llm' or d['status']!='ok': continue
        texts=[part.get('text','') for c in d['response'].get('candidates',[]) for part in c.get('content',{}).get('parts',[]) if not part.get('thought',False)]
        text=''.join(texts)
        try: parsed=json.loads(text)
        except ValueError: parsed=None
        stage='unclassified'
        if isinstance(parsed,dict):
            if 'noncommittal' in parsed: stage='answer_relevancy_question'
            elif 'classifications' in parsed: stage='context_recall_classifications'
            elif 'verdict' in parsed: stage='context_precision_verdict'
            elif isinstance(parsed.get('statements'),list):
                stage='faithfulness_verdicts' if parsed['statements'] and isinstance(parsed['statements'][0],dict) else 'faithfulness_statements'
        rows.append(dict(case_variant=p.parent.parent.name,call_id=d['call_id'],attempt=d['attempt'],stage=stage,judgment=parsed,raw_text=text,path=str(p.relative_to(ROOT)).replace('\\','/')))
    out=ROOT/'resumen/juicios_evaluador.json';out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Juicios indexados:',len(rows))
if __name__=='__main__': extract()
