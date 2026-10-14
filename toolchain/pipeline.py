"""Markdown -> normalized JSON -> schema -> model-only semantic validation."""
import argparse,json
from pathlib import Path
from jsonschema import Draft202012Validator
from parser import parse,ParseError
from model_validator import validate_model,validate_project
ROOT=Path(__file__).parent
SCHEMA=json.loads((ROOT/'screen-model.schema.json').read_text(encoding='utf-8'))

def run(paths):
    documents=[];reports=[]
    for path in paths:
        try:
            doc=parse(path)
            issues=[{'code':'SCHEMA','message':e.message,'path':'/'.join(map(str,e.path))} for e in Draft202012Validator(SCHEMA).iter_errors(doc)]
            if not issues:issues+=validate_model(doc)
            documents.append((path,doc))
        except (ParseError,ValueError,OSError,KeyError) as exc:
            doc=None;issues=[{'code':'PARSE','message':str(exc)}]
        reports.append({'file':path.name,'screen_id':doc['metadata']['screen_id'] if doc else None,'errors':issues})
    cross=validate_project([d for _,d in documents])
    for issue in cross:
        for report in reports:
            if report['screen_id']==issue['screen_id']:
                report['errors'].append(issue);break
    for r in reports:r['status']='FAIL' if r['errors'] else 'PASS'
    return documents,{'version':'0.7','files':reports,'total_errors':sum(len(r['errors']) for r in reports)}

def main():
    p=argparse.ArgumentParser();p.add_argument('files',nargs='+',type=Path);p.add_argument('--output-dir',type=Path,default=Path('models'));p.add_argument('--report',type=Path,default=Path('validation-report.json'))
    a=p.parse_args();paths=[f for entry in a.files for f in (sorted(entry.glob('*.md')) if entry.is_dir() else [entry])]
    docs,report=run(paths);a.output_dir.mkdir(parents=True,exist_ok=True)
    valid={r['file'] for r in report['files'] if r['status']=='PASS'}
    for path,doc in docs:
        if path.name in valid:(a.output_dir/(path.stem+'.json')).write_text(json.dumps(doc,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'passed':len(valid),'total':len(paths),'errors':report['total_errors']},ensure_ascii=False))
    raise SystemExit(bool(report['total_errors']))
if __name__=='__main__':main()
