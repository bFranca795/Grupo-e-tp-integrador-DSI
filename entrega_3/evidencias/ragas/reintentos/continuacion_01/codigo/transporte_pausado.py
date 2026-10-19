"""Sequential transport with bounded retries and explicit quota handling."""
import json,time,threading,uuid,re
from datetime import datetime,timezone
from email.utils import parsedate_to_datetime
from adaptadores import Audit,error_info,now,transient

class QuotaBlocked(RuntimeError): pass

def retry_classification(error):
    info=error_info(error)
    details=getattr(error,'details',None)
    text=json.dumps(details,default=str).lower() if details is not None else info.get('message','').lower()
    response=getattr(error,'response',None)
    headers=getattr(response,'headers',{}) or {}
    raw=headers.get('retry-after')
    delay=None
    if raw:
        try: delay=max(0,float(raw))
        except ValueError:
            try: delay=max(0,(parsedate_to_datetime(raw)-datetime.now(timezone.utc)).total_seconds())
            except (ValueError,TypeError): pass
    # Google RPC RetryInfo is retained when no HTTP Retry-After is supplied.
    for seconds in re.findall(r'"retrydelay"\s*:\s*"([0-9.]+)s"',text):
        delay=max(delay or 0,float(seconds))
    code=getattr(error,'code',None)
    if code!=429: category='transient' if transient(error) else 'permanent_error'
    elif any(t in text for t in ('perday','per_day','per day','daily','billingdisabled')) or re.search(r'"limit"\s*:\s*0\b',text): category='quota_exhausted'
    elif any(t in text for t in ('perminute','per_minute','per minute','persecond','per_second','rate_limit')): category='temporary_rate_limit'
    else: category='unknown_429'
    return dict(category=category,retry_after=raw,retry_delay_seconds=delay,error=info)

class PacedAudit(Audit):
    lock=threading.Lock()
    last_finished=0.0
    blocked=None
    min_pause=12.0
    def call(self,kind,payload,operation):
        # Includes the three inverse-question calls launched by ResponseRelevancy.
        with self.lock:
            if type(self).blocked: raise QuotaBlocked(type(self).blocked)
            call_id=uuid.uuid4().hex
            for attempt in range(1,4):
                pause=max(0,self.min_pause-(time.monotonic()-type(self).last_finished))
                if pause: time.sleep(pause)
                start=time.perf_counter();row=dict(call_id=call_id,kind=kind,attempt=attempt,started_at=now(),input=payload,transport='sequential_12s')
                try:
                    response=operation()
                    row.update(status='ok',response=response.model_dump(mode='json'))
                except Exception as error:
                    policy=retry_classification(error)
                    row.update(status='error',error=policy['error'],retry_policy=policy)
                    row['seconds']=time.perf_counter()-start
                    (self.path/f'{call_id}_{attempt}.json').write_text(json.dumps(row,ensure_ascii=False,indent=2),encoding='utf-8')
                    type(self).last_finished=time.monotonic()
                    if policy['category'] in ('quota_exhausted','unknown_429'):
                        type(self).blocked=json.dumps(policy,ensure_ascii=False)
                        raise QuotaBlocked(type(self).blocked) from error
                    delay=max(15.0*attempt,policy['retry_delay_seconds'] or 0)
                    if delay>60:
                        type(self).blocked=f'Retry-After requires deferment of {delay} seconds; no early retry.'
                        raise QuotaBlocked(type(self).blocked) from error
                    if attempt<3 and policy['category'] in ('transient','temporary_rate_limit'):
                        time.sleep(delay);continue
                    if policy['category']=='temporary_rate_limit':
                        type(self).blocked='Temporary rate limit persists after three attempts; stop this batch.'
                    raise
                row['seconds']=time.perf_counter()-start
                (self.path/f'{call_id}_{attempt}.json').write_text(json.dumps(row,ensure_ascii=False,indent=2),encoding='utf-8')
                type(self).last_finished=time.monotonic()
                return response
