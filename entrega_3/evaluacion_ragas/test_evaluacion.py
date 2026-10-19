import unittest,tempfile,json,asyncio
from pathlib import Path
from unittest.mock import patch
import ejecutar,resumir
class EvaluationTests(unittest.TestCase):
    def test_completed_metric_is_not_called_again(self):
        class NeverCall:
            name='faithfulness'
            async def single_turn_ascore(self,*a,**k): raise AssertionError('duplicate call')
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'score.json';expected=dict(status='ok',value=0.0)
            ejecutar.save(p,expected)
            self.assertEqual(asyncio.run(ejecutar.score(NeverCall(),None,p)),expected)
    def test_pairs_use_same_ids_and_keep_valid_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);here=root/'code';out=root/'out';here.mkdir()
            ejecutar.save(here/'golden_dataset.json',[dict(id='A'),dict(id='B')])
            for id in ('A','B'):
                for variant in ('basic','rerank'):
                    for metric in ejecutar.NAMES:
                        row=dict(metric=metric,status='ok',value=0.0 if variant=='basic' else 0.5)
                        if id=='B' and variant=='rerank': row=dict(status='evaluation_error',value=None,error={'type':'TimeoutError'})
                        if id=='B' and variant=='basic': row=dict(status='ok',value=1.0)
                        ejecutar.save(out/'evaluacion'/f'{id}_{variant}'/f'{metric}.json',row)
            with patch.object(resumir,'HERE',here),patch.object(resumir,'OUT',out),patch('builtins.print'):
                resumir.summarize()
            summary=ejecutar.read(out/'resumen/resumen.json')
            for p in summary['paired']:
                self.assertEqual(p['n'],1);self.assertEqual(p['paired_ids'],['A'])
                self.assertEqual(p['basic'],0.0);self.assertEqual(p['rerank'],0.5);self.assertEqual(p['delta'],0.5)
                self.assertEqual(p['excluded'][0]['id'],'B')
    def test_nonfinite_is_not_coerced_to_score(self):
        class Undefined:
            name='context_recall'
            async def single_turn_ascore(self,*a,**k): return float('nan')
        with tempfile.TemporaryDirectory() as tmp:
            sample=ejecutar.SingleTurnSample(user_input='q',response='r',retrieved_contexts=[],reference='ref')
            row=asyncio.run(ejecutar.score(Undefined(),sample,Path(tmp)/'score.json'))
            self.assertIsNone(row['value']);self.assertEqual(row['status'],'evaluation_undefined')
    def test_transient_policy(self):
        class APIError(Exception):
            def __init__(self,code): self.code=code
        self.assertTrue(ejecutar.transient(APIError(429)))
        self.assertFalse(ejecutar.transient(APIError(403)))
        self.assertFalse(ejecutar.transient(ValueError('parse')))
if __name__=='__main__': unittest.main()
