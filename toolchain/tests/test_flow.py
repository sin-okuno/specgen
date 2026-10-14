import copy,glob,json,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from flow_validator import validate_flow
ROOT=Path(__file__).resolve().parents[1]
class FlowTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.docs=[json.loads(p.read_text(encoding='utf-8')) for p in sorted((ROOT/'models').glob('*.json'))]
 def test_four_samples(self):
  for doc in self.docs:self.assertEqual([],validate_flow(doc),doc['metadata']['screen_id'])
 def test_invalid_condition(self):
  d=copy.deepcopy(self.docs[0]);d['model']['event_steps'][0]['condition']='eval(x)'
  self.assertIn('COND001',[e['code'] for e in validate_flow(d)])
 def test_unknown_path(self):
  d=copy.deepcopy(self.docs[0]);d['model']['event_steps'][0]['condition']='IS_SET(data.unknown)'
  self.assertIn('COND002',[e['code'] for e in validate_flow(d)])
 def test_type_mismatch(self):
  d=copy.deepcopy(self.docs[0]);d['model']['event_steps'][0]['condition']='EQ(input.productName,123)'
  if not any(x['field_id']=='productName' for x in d['model']['inputs']):
   path=d['model']['inputs'][0]['field_id'];d['model']['event_steps'][0]['condition']=f'EQ(input.{path},true)' if d['model']['inputs'][0]['data_type']!='boolean' else f'EQ(input.{path},"wrong")'
  self.assertIn('COND003',[e['code'] for e in validate_flow(d)])
 def test_unreachable_step(self):
  d=copy.deepcopy(self.docs[0]);rows=d['model']['event_steps'];ev=rows[0]['event_id']
  steps=[r for r in rows if r['event_id']==ev]
  if len(steps)<2:self.skipTest('need multi-step event')
  steps[0]['on_success']='END';steps[0]['on_failure']='STOP'
  self.assertIn('FLOW102',[e['code'] for e in validate_flow(d)])
 def test_unknown_branch(self):
  d=copy.deepcopy(self.docs[0]);d['model']['event_steps'][0]['on_success']='GOTO:3'
  self.assertIn('FLOW101',[e['code'] for e in validate_flow(d)])
if __name__=='__main__':unittest.main()
