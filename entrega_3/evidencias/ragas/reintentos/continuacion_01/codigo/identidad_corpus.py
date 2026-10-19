"""Identity independent of storage UUIDs; strict logical/configuration equality."""
import hashlib,json

def canonical_hash(value):
    return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True).encode()).hexdigest()

def logical_collection(collection):
    return dict(dimension=collection['dimension'],configuration=json.loads(collection['configuration']),
                schema=json.loads(collection['schema']),rows=sorted(collection['rows'],key=lambda row:row['id']))

def embeddings_fingerprints(root):
    import chromadb
    import numpy as np
    client=chromadb.PersistentClient(path=str(root/'chroma_db'))
    result={}
    for name in ('estudio_contable','estudio_contable_chunks'):
        collection=client.get_collection(name,embedding_function=None)
        data=collection.get(include=['embeddings'])
        vectors={}
        for id_,vector in zip(data['ids'],data['embeddings']):
            array=np.asarray(vector,dtype='<f4')
            if array.shape!=(768,) or not np.isfinite(array).all():
                raise ValueError(f'Invalid embedding dimension/value for {id_}')
            vectors[id_]=hashlib.sha256(array.tobytes()).hexdigest()
        result[name]=dict(count=len(vectors),dimension=768,vector_sha256_by_logical_id=dict(sorted(vectors.items())))
    return result
