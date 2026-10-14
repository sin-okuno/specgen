"""Validate pre-generated Screen Model JSON without opening any Markdown files."""
import argparse,json
from pathlib import Path
from jsonschema import Draft202012Validator
from model_validator import validate_model,validate_project
ROOT=Path(__file__).parent
SCHEMA=json.loads((ROOT/'screen-model.schema.json').read_text(encoding='utf-8'))
def run(paths):
 docs=[];reports=[]
 for path in paths:
  try:
   doc=json.loads(path.read_text(encoding='utf-8'))
   issues=[{'code':'SCHEMA','message':e.message,'path':'/'.join(map(str,e.path))} for e in Draft202012Validator(SCHEMA).iter_errors(doc)]
   if not issues:issues.extend(validate_model(doc));docs.append(doc)
   sid=doc.get('metadata',{}).get('screen_id')
  except (ValueError,OSError,TypeError) as exc:issues=[{'code':'JSON','message':str(exc)}];sid=None
  reports.append({'file':path.name,'screen_id':sid,'errors':issues})
 for issue in validate_project(docs):
  for r in reports:
   if r['screen_id']==issue['screen_id']:r['errors'].append(issue);break
 for r in reports:r['status']='FAIL' if r['errors'] else 'PASS'
 return {'version':'0.5','files':reports,'total_errors':sum(len(r['errors']) for r in reports)}
def main():
 p=argparse.ArgumentParser();p.add_argument('paths',nargs='+',type=Path);p.add_argument('--report',type=Path);a=p.parse_args()
 paths=[f for x in a.paths for f in (sorted(x.glob('*.json')) if x.is_dir() else [x])]
 report=run(paths)
 if a.report:a.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(json.dumps({'total':len(paths),'errors':report['total_errors']},ensure_ascii=False))
 raise SystemExit(bool(report['total_errors']))
if __name__=='__main__':main()
