import copy
import json
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from state_nav_validator import validate_initial, validate_navigation
from model_validator import validate_model, validate_project
ROOT=Path(__file__).resolve().parents[1]

class StateNavigationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.docs=[json.loads(p.read_text(encoding='utf-8')) for p in sorted((ROOT/'models').glob('*.json'))]
    def doc(self,kind):
        return copy.deepcopy(next(d for d in self.docs if d['metadata']['screen_type']==kind))
    def test_valid_examples(self):
        for d in self.docs: self.assertEqual([],validate_initial(d))
        self.assertEqual([],validate_navigation(self.docs))
    def test_unknown_initial_destination(self):
        d=self.doc('CREATE');d['model']['defaults'][0]['destination']='data.unknown'
        self.assertIn('INIT201',[e['code'] for e in validate_model(d)])
    def test_null_to_nonnullable(self):
        d=self.doc('CREATE');d['model']['defaults'][0]['value']='NULL'
        self.assertIn('NULL201',[e['code'] for e in validate_model(d)])
    def test_invalid_literal(self):
        d=self.doc('CREATE');d['model']['defaults'][0]['value']='random_identifier'
        self.assertIn('INIT202',[e['code'] for e in validate_model(d)])
    def test_wrong_initial_type(self):
        d=self.doc('CREATE');d['model']['defaults'][0]['value']='123'
        self.assertIn('INIT203',[e['code'] for e in validate_model(d)])
    def test_navigation_source_unknown(self):
        docs=copy.deepcopy(self.docs)
        detail=next(d for d in docs if d['metadata']['screen_type']=='DETAIL')
        detail['model']['navigation'][0]['parameters']='id=data.notDeclared'
        self.assertIn('NAV201',[e['code'] for e in validate_project(docs)])
    def test_navigation_type_mismatch(self):
        docs=copy.deepcopy(self.docs)
        detail=next(d for d in docs if d['metadata']['screen_type']=='DETAIL')
        detail['model']['navigation'][0]['parameters']='id=data.product.name'
        self.assertIn('NAV202',[e['code'] for e in validate_project(docs)])
    def test_navigation_nullable(self):
        docs=copy.deepcopy(self.docs)
        detail=next(d for d in docs if d['metadata']['screen_type']=='DETAIL')
        detail['model']['state_types'][0]['nullable']='Yes'
        detail['model']['navigation'][0]['parameters']='id=data.product.id'
        self.assertIn('NAV203',[e['code'] for e in validate_project(docs)])

if __name__=='__main__':unittest.main()
