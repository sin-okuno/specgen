import copy,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from parser import parse
from model_validator import validate_model
from pipeline import run
class LegacyPortTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.docs=[parse(p) for p in sorted((ROOT/'examples').glob('*.md'))]
 def sample(self,screen='LIST'):
  return copy.deepcopy(next(x for x in self.docs if x['metadata']['screen_type']==screen))
 def codes(self,d):return {x['code'] for x in validate_model(d)}
 def test_samples(self):
  _,report=run(sorted((ROOT/'examples').glob('*.md')));self.assertEqual(report['total_errors'],0)
 def test_unknown_area(self):
  d=self.sample();d['model']['inputs'][0]['area_id']='BAD';self.assertIn('REF001',self.codes(d))
 def test_init_dependency_cycle(self):
  d=self.sample();r=d['model']['initialization'][0];r['depends_on']=r['init_id'];self.assertIn('FLOW001',self.codes(d))
 def test_unknown_event_api(self):
  d=self.sample();r=next(x for x in d['model']['event_steps'] if x['operation']=='CALL_API');r['reference']='API-UNKNOWN';self.assertIn('REF001',self.codes(d))
 def test_step_bad_jump(self):
  d=self.sample();d['model']['event_steps'][0]['on_success']='STEP:999';self.assertIn('FLOW003',self.codes(d))
 def test_api_path_binding(self):
  d=self.sample('DETAIL');r=next(x for x in d['model']['requests'] if x['location']=='PATH');r['location']='QUERY';self.assertIn('API001',self.codes(d))
 def test_unknown_named_type(self):
  d=self.sample();d['model']['named_type_fields'][0]['data_type']='UnknownThing';self.assertIn('TYPE001',self.codes(d))
 def test_duplicate_named_type(self):
  d=self.sample();d['model']['named_type_catalog'].append(copy.deepcopy(d['model']['named_type_catalog'][0]));self.assertIn('TYPE003',self.codes(d))
 def test_cycle_named_type(self):
  d=self.sample();r=d['model']['named_type_fields'][0];r['data_type']=r['type_name'];self.assertIn('TYPE004',self.codes(d))
 def test_anonymous_object(self):
  d=self.sample();d['model']['responses'][0]['data_type']='object[]';self.assertIn('TYPE007',self.codes(d))
 def test_bad_response_path(self):
  d=self.sample('DETAIL');d['model']['response_mappings'][0]['response_field']='notAField';self.assertIn('TYPE009',self.codes(d))
 def test_model_only_no_markdown(self):
  d=self.sample();d['source']='nonexistent.md';self.assertEqual(self.codes(d),set())
if __name__=='__main__':unittest.main()
