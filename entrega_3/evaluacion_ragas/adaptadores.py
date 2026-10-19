"""Adaptadores Gemini para las interfaces oficiales de RAGAS 0.2.15."""
import asyncio,json,os,time,uuid
from datetime import datetime,timezone
from pathlib import Path
from google import genai
from google.genai import types
from langchain_core.outputs import LLMResult,Generation
# RAGAS 0.2.15 aplica nest_asyncio al importar su executor. Este CLI usa
# un solo event loop nativo: evitar el parche de notebooks incompatible con 3.14.
import nest_asyncio
_apply=nest_asyncio.apply
nest_asyncio.apply=lambda *a,**k: None
from ragas.llms import BaseRagasLLM
from ragas.embeddings import BaseRagasEmbeddings
from ragas.run_config import RunConfig
nest_asyncio.apply=_apply
MODEL='gemini-3.1-flash-lite'
EMBEDDING='gemini-embedding-001'
def now(): return datetime.now(timezone.utc).isoformat()
def transient(error):
    code=getattr(error,'code',None)
    return code in (429,500,502,503,504) or isinstance(error,(TimeoutError,ConnectionError)) or any(s in type(error).__name__.lower() for s in ('timeout','connecterror','networkerror'))
def error_info(error):
    message=str(error)
    for key in ('GEMINI_API_KEY','GOOGLE_API_KEY','LANGSMITH_API_KEY'):
        if os.environ.get(key): message=message.replace(os.environ[key],'[REDACTED]')
    return dict(type=type(error).__name__,code=getattr(error,'code',None),message=message)
class Audit:
    def __init__(self,path): self.path=Path(path);self.path.mkdir(parents=True,exist_ok=True)
    def call(self,kind,payload,operation):
        id=uuid.uuid4().hex
        for attempt in range(1,4):
            start=time.perf_counter();row=dict(call_id=id,kind=kind,attempt=attempt,started_at=now(),input=payload)
            try:
                response=operation()
                row.update(status='ok',response=response.model_dump(mode='json'))
            except Exception as error:
                row.update(status='error',error=error_info(error),transient=transient(error))
                (self.path/f'{id}_{attempt}.json').write_text(json.dumps({**row,'seconds':time.perf_counter()-start},ensure_ascii=False,indent=2),encoding='utf-8')
                if attempt<3 and transient(error): time.sleep(attempt*2);continue
                raise
            (self.path/f'{id}_{attempt}.json').write_text(json.dumps({**row,'seconds':time.perf_counter()-start},ensure_ascii=False,indent=2),encoding='utf-8')
            return response

def client():
    return genai.Client(api_key=os.environ['GEMINI_API_KEY'],http_options=types.HttpOptions(timeout=120000,retry_options=types.HttpRetryOptions(attempts=1)))
class EvaluatorLLM(BaseRagasLLM):
    def __init__(self,audit):
        super().__init__(run_config=RunConfig(max_retries=1,timeout=180));self.audit=audit
    def is_finished(self,response): return True
    def generate_text(self,prompt,n=1,temperature=None,stop=None,callbacks=None):
        text=prompt.to_string();generations=[]
        for _ in range(n):
            payload=dict(model=MODEL,prompt=text,temperature=0.0,max_output_tokens=8192,response_mime_type='application/json',stop=stop)
            def operation():
                with client() as c:
                    return c.models.generate_content(model=MODEL,contents=text,config=types.GenerateContentConfig(temperature=0.0,max_output_tokens=8192,response_mime_type='application/json',stop_sequences=stop,automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True)))
            r=self.audit.call('evaluator_llm',payload,operation)
            if not r.text: raise ValueError('Evaluator returned empty text')
            generations.append(Generation(text=r.text))
        return LLMResult(generations=[generations])
    async def agenerate_text(self,*args,**kwargs): return await asyncio.to_thread(self.generate_text,*args,**kwargs)
class EvaluatorEmbeddings(BaseRagasEmbeddings):
    def __init__(self,audit): super().__init__();self.audit=audit;self.run_config=RunConfig(max_retries=1)
    def embed_documents(self,texts):
        payload=dict(model=EMBEDDING,texts=texts,task_type='SEMANTIC_SIMILARITY',output_dimensionality=768)
        def operation():
            with client() as c: return c.models.embed_content(model=EMBEDDING,contents=texts,config=types.EmbedContentConfig(task_type='SEMANTIC_SIMILARITY',output_dimensionality=768))
        r=self.audit.call('evaluator_embeddings',payload,operation)
        return [e.values for e in r.embeddings]
    def embed_query(self,text): return self.embed_documents([text])[0]
    async def aembed_documents(self,texts): return await asyncio.to_thread(self.embed_documents,texts)
    async def aembed_query(self,text): return (await self.aembed_documents([text]))[0]
