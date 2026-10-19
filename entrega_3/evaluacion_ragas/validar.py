"""Validación local de referencias: no importa ni ejecuta el pipeline."""
import hashlib,json
from collections import Counter
from pathlib import Path
from corpus import ROOT,read_corpus
from identidad_corpus import logical_collection,embeddings_fingerprints
import sys
sys.path.insert(0,str(ROOT))
OUT=Path(__file__).resolve().parent
def sha(x): return hashlib.sha256(json.dumps(x,ensure_ascii=False,sort_keys=True).encode()).hexdigest()
def validate():
    data=json.loads((OUT/'golden_dataset.json').read_text(encoding='utf-8'))
    manifest=json.loads((OUT/'corpus_manifest.json').read_text(encoding='utf-8'))
    live=read_corpus(); errors=[]; checks=[]
    def check(ok,label):
        checks.append(dict(check=label,passed=bool(ok)))
        if not ok: errors.append(label)
    check(len(data)==10 and {r['id'] for r in data}=={'S1','S2','S3','C1','C2','C3','E1','E2','I1','I2'},'Diez IDs únicos previstos')
    check(Counter(r['categoria'] for r in data)==dict(simple=3,compleja=3,escape=2,informal=2),'Distribución 3/3/2/2')
    check(hashlib.sha256((OUT/'golden_dataset.json').read_bytes()).hexdigest()==manifest['dataset_sha256'],'Hash del dataset aprobado para este manifiesto')
    check(hashlib.sha256((ROOT/'base_conocimiento_limpia.json').read_bytes()).hexdigest()==manifest['clean_json_sha256'],'JSON limpio sin cambios')
    for name,c in live.items():
        check(sha(c['rows'])==manifest['sha256'][name] and logical_collection(c)==logical_collection(manifest['collections'][name]),f'{name}: logical identity, parsed configuration and content hash (storage UUID excluded)')
    from entrega_3.rag_pipeline.indexing import split_documents
    expected_chunks=split_documents(live['estudio_contable']['rows'],chunk_size=manifest['configuration']['chunk_size'],chunk_overlap=manifest['configuration']['chunk_overlap_max'])
    check(sorted(expected_chunks,key=lambda r:r['id'])==live['estudio_contable_chunks']['rows'],'Deterministic 500/100 chunk texts, IDs, positions and metadata')
    embedding_baseline=OUT/'embedding_identity.json'
    if embedding_baseline.exists():
        check(embeddings_fingerprints(ROOT)==json.loads(embedding_baseline.read_text(encoding='utf-8'))['collections'],'Embedding dimensions, finite values and vector hashes by logical ID')
    else:
        check(False,'Missing embedding identity baseline; do not silently accept new vectors')
    docs={r['id']:r for r in live['estudio_contable']['rows']}; chunks={r['id']:r for r in live['estudio_contable_chunks']['rows']}
    for id,c in chunks.items():
        m=c['metadatos']; parent=docs.get(m['parent_id']); text=c['documento']; start=m['start_index']
        digest=hashlib.sha256(text.encode()).hexdigest()[:16]
        check(parent is not None and parent['documento'][start:start+len(text)]==text and id==f"{m['parent_id']}::chunk-{m['chunk_index']:03d}-{digest}" and m['chunk_id']==id and len(text)<=500,f'{id}: padre, posición, contenido e ID')
        check(all(m.get(k)==v for k,v in parent['metadatos'].items()),f'{id}: metadatos heredados')
    check(set(docs)=={c['metadatos']['parent_id'] for c in chunks.values()},'Todos los documentos tienen chunks y no hay huérfanos')
    review=[]
    required={'id','categoria','pregunta','respuesta_esperada','hechos_obligatorios','document_ids','chunk_ids','espera_escape','justificacion_escape','reutilizacion_b'}
    for r in data:
        id=r['id']; facts=r['hechos_obligatorios']
        check(required<=r.keys() and all(r[k] for k in ['pregunta','respuesta_esperada','hechos_obligatorios','justificacion_escape','reutilizacion_b']),id+': campos completos')
        check(isinstance(r['espera_escape'],bool) and r['espera_escape']==(r['categoria']=='escape'),id+': categoría y escape coherentes')
        check(all(f.get('hecho','').strip() for f in facts),id+': hechos no vacíos')
        if r['espera_escape']:
            check(not r['document_ids'] and not r['chunk_ids'] and all(set(f)=={'hecho'} for f in facts),id+': escape sin fuentes inventadas')
            review.append(dict(id=id,automatico='Ausencia de referencias y coherencia de escape comprobadas.',semantico='Revisar ausencia de respuesta en los 17 documentos; no se demuestra con búsquedas léxicas.'))
            continue
        check(set(r['document_ids'])=={f['document_id'] for f in facts} and set(r['chunk_ids'])=={f['chunk_id'] for f in facts},id+': listas coinciden con respaldo de hechos')
        for i,f in enumerate(facts):
            c=chunks.get(f['chunk_id']); d=docs.get(f['document_id'])
            check(c is not None and d is not None and c['metadatos']['parent_id']==d['id'] and bool(f['fragmento']) and f['fragmento'] in c['documento'] and f['fragmento'] in d['documento'],f'{id}: hecho {i+1}, fuente y cita literal')
        covering=[c['id'] for c in chunks.values() if all(f['fragmento'] in c['documento'] for f in facts)]
        if r['categoria']=='simple': check(bool(covering),id+': todos los respaldos caben en un único chunk real')
        if r['categoria']=='compleja': check(len(r['chunk_ids'])>1 and not covering,id+': respaldos distribuidos, ningún chunk contiene todos')
        review.append(dict(id=id,chunk_count=len(r['chunk_ids']),single_chunk_covering=covering,semantico='Revisar que cada cita implique el hecho y que los hechos cubran la pregunta. La distribución de citas no demuestra necesidad semántica.'))
    report=dict(status='PASS' if not errors else 'FAIL',automatic_checks=len(checks),errors=errors,checks=checks,semantic_review=review,scope='Sin llamadas generativas, pipelines, RAGAS, upserts, deletes ni regeneración de embeddings; lectura local de vectores con cliente Chroma. PASS estructural no equivale a aprobación semántica.')
    (OUT/'validacion.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(report['status'],len(checks),'comprobaciones automáticas;',len(errors),'errores')
    return bool(errors)
if __name__=='__main__': raise SystemExit(validate())
