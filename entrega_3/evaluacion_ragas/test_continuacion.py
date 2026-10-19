import copy,unittest,json
from types import SimpleNamespace
from identidad_corpus import logical_collection
from transporte_pausado import retry_classification
class ContinuationTests(unittest.TestCase):
    def collection(self):
        return dict(collection_id='storage-a',dimension=768,configuration='{"a":1,"b":2}',schema='{}',rows=[dict(id='DOC-1',documento='approved',metadatos={'activo':True})])
    def test_storage_uuid_and_json_order_do_not_define_logical_identity(self):
        a=self.collection();b=copy.deepcopy(a);b['collection_id']='storage-b';b['configuration']='{ "b": 2, "a": 1 }'
        self.assertEqual(logical_collection(a),logical_collection(b))
    def test_content_metadata_dimension_and_config_changes_rejected(self):
        a=self.collection()
        for field in ('text','metadata','dimension','config'):
            b=copy.deepcopy(a)
            if field=='text': b['rows'][0]['documento']='changed'
            elif field=='metadata': b['rows'][0]['metadatos']['activo']=False
            elif field=='dimension': b['dimension']=1024
            else: b['configuration']='{"a":9,"b":2}'
            self.assertNotEqual(logical_collection(a),logical_collection(b))
    def error(self,detail,header=None):
        e=RuntimeError('redacted test');e.code=429;e.details=detail;e.response=SimpleNamespace(headers={'retry-after':header} if header else {})
        return e
    def test_daily_quota_stops(self):
        self.assertEqual(retry_classification(self.error({'quotaId':'GenerateRequestsPerDay'}))['category'],'quota_exhausted')
    def test_temporary_retry_after_and_rpc_delay_are_respected(self):
        r=retry_classification(self.error({'quotaId':'GenerateRequestsPerMinute','retryDelay':'30s'},'12'))
        self.assertEqual(r['category'],'temporary_rate_limit');self.assertEqual(r['retry_delay_seconds'],30)
    def test_unknown_429_is_not_assumed_temporary(self):
        self.assertEqual(retry_classification(self.error({'status':'RESOURCE_EXHAUSTED'}))['category'],'unknown_429')
if __name__=='__main__': unittest.main()
