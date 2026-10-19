"""Lectura SQLite en modo ro: no abre Chroma ni calcula embeddings."""
import sqlite3
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def read_corpus():
    with sqlite3.connect((ROOT/'chroma_db/chroma.sqlite3').as_uri()+'?mode=ro',uri=True) as db:
        db.execute('PRAGMA query_only=ON')
        db.execute('BEGIN')
        result={}
        for name in ('estudio_contable','estudio_contable_chunks'):
            collection=db.execute('SELECT id,dimension,config_json_str,schema_str FROM collections WHERE name=?',(name,)).fetchone()
            if not collection: raise RuntimeError(f'Falta {name}: preparar corpus de Entrega 2 y derivada aprobada; no se crean automáticamente.')
            rows=[]
            for internal,id_ in db.execute('SELECT e.id,e.embedding_id FROM embeddings e JOIN segments s ON s.id=e.segment_id WHERE s.collection=? AND s.scope=? ORDER BY e.embedding_id',(collection[0],'METADATA')).fetchall():
                meta={}
                for key,s,i,f,b in db.execute('SELECT key,string_value,int_value,float_value,bool_value FROM embedding_metadata WHERE id=?',(internal,)):
                    meta[key]=s if s is not None else (bool(b) if b is not None else i if i is not None else f)
                rows.append(dict(id=id_,documento=meta.pop('chroma:document'),metadatos=meta))
            result[name]=dict(collection_id=collection[0],dimension=collection[1],configuration=collection[2],schema=collection[3],rows=rows)
        return result
if __name__=='__main__':
    for name,c in read_corpus().items():
        print(name,len(c['rows']))
        for row in c['rows']: print(row['id'],row['documento'])
