"""Verificaciones finales de integridad y evidencia, sin llamadas externas."""
import hashlib,json,math,subprocess
from pathlib import Path
from ejecutar import OUT,HERE,ROOT,NAMES,read,save,freeze
from entrega_3.rag_pipeline.retriever import limpiar_texto_guardrails

def verify():
    cases=freeze();config=read(OUT/'configuracion.json');errors=[];checks=[]
    def check(ok,label):
        checks.append(dict(check=label,passed=bool(ok)))
        if not ok: errors.append(label)
    base=read(HERE/'corpus_manifest.json')['base_commit']
    for p in (ROOT/'entrega_3/rag_pipeline').glob('*.py'):
        content=subprocess.check_output(['git','show',f'{base}:entrega_3/rag_pipeline/{p.name}'],cwd=ROOT)
        # Git conserva LF; checkout de Windows puede usar CRLF.
        check(content.replace(b'\r\n',b'\n')==p.read_bytes().replace(b'\r\n',b'\n'),f'Pipeline intacto: {p.name}')
    manifest=read(HERE/'corpus_manifest.json')
    originals={r['id']:r for r in manifest['collections']['estudio_contable']['rows']}
    chunks={r['id']:r for r in manifest['collections']['estudio_contable_chunks']['rows']}
    for c in cases:
        for v in ('basic','rerank'):
            g=read(OUT/'generacion'/f"{c['id']}_{v}.json")
            check(g['settings']==config['settings'][v],f"{c['id']}/{v}: configuración vigente")
            check(g['question']==c['pregunta'],f"{c['id']}/{v}: pregunta aprobada")
            check(g['generator_contexts']==[s['documento'] for s in g['sources']],f"{c['id']}/{v}: contextos efectivamente suministrados")
            source=originals if v=='basic' else chunks
            for s in g['sources']:
                check(s['id'] in source and s['documento']==limpiar_texto_guardrails(source[s['id']]['documento']),f"{c['id']}/{v}/{s['id']}: fuente efectiva sanitizada")
            if v=='rerank': check(len(g['candidates'])<=8 and len(g['selected'])<=4,f"{c['id']}/{v}: límites")
            check(g['status'] in ('ok','insufficient_context'),f"{c['id']}/{v}: ejecución sin error técnico")
            for m in NAMES:
                r=read(OUT/'evaluacion'/f"{c['id']}_{v}"/f'{m}.json')
                check(r['status']!='pending',f"{c['id']}/{v}/{m}: estado terminal")
                if 'input' in r:
                    check(r['input']['retrieved_contexts']==g['generator_contexts'] and r['input']['response']==g['answer'] and r['input']['reference']==c['respuesta_esperada'] and r['input']['user_input']==c['pregunta'],f"{c['id']}/{v}/{m}: entradas correctas")
                if r['status']=='ok': check(r['value'] is not None and math.isfinite(r['value']),f"{c['id']}/{v}/{m}: score finito")
    # Buscar valores secretos completos configurados, sin exponerlos en consola.
    import os
    secrets=[os.environ[k] for k in ('GEMINI_API_KEY','GOOGLE_API_KEY','LANGSMITH_API_KEY') if os.environ.get(k)]
    check(not any(secret in p.read_text(encoding='utf-8') for p in OUT.rglob('*') if p.is_file() and p.suffix in ('.json','.md','.csv') for secret in secrets),'Evidencias sin valores completos de credenciales')
    report=dict(status='PASS' if not errors else 'FAIL',checks=checks,errors=errors,count=len(checks))
    save(OUT/'resumen/verificaciones.json',report)
    print(report['status'],len(checks),'checks',errors)
    return bool(errors)
if __name__=='__main__': raise SystemExit(verify())
