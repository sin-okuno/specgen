"""Semantic checks over normalized Screen Model JSON; no Markdown parsing."""
import re
from legacy_rules import validate_legacy
from flow_validator import validate_flow
from state_nav_validator import validate_initial, validate_navigation
from collections import defaultdict

PRIMITIVES={'string','integer','number','boolean','date','datetime','string[]','integer[]'}

def validate_model(doc):
    m=doc['model']; errors=[]; screen=doc['metadata']['screen_id']
    def err(code,row,message):
        errors.append({'code':code,'screen_id':screen,'line':row.get('line'),'message':message})
    types=defaultdict(dict)
    for r in m['named_type_fields']:
        types[r['type_name']][r['field']]=r
    states={r['state_path']:r for r in m['state_types']}
    inputs={r['field_id']:r for r in m['inputs']}
    routes={r['destination']:r for r in m['route_parameters']}
    responses={(r['api_id'],r['field']):r for r in m['responses']}
    apis={r['api_id'] for r in m['apis']}
    def resolve(path):
        if path.startswith('input.'):
            r=inputs.get(path[6:]);return (r['data_type'], 'No' if r['required']=='Yes' else 'Yes') if r else None
        if path.startswith('route.'):
            r=routes.get(path);return (r['data_type'], 'No' if r['required']=='Yes' else 'Yes') if r else None
        if path.startswith('query.applied.'):
            r=inputs.get(path[14:]);return (r['data_type'],'No' if r['required']=='Yes' else 'Yes') if r else None
        if path in states:
            r=states[path];return r['data_type'],r['nullable']
        candidates=sorted((s for s in states if path.startswith(s+'.')),key=len,reverse=True)
        if not candidates:return None
        s=candidates[0];r=states[s];dtype=r['data_type'];nullable=r['nullable']
        for part in path[len(s)+1:].split('.'):
            if dtype.endswith('[]'):return None
            field=types.get(dtype,{}).get(part)
            if not field:return None
            dtype=field['data_type'];nullable='Yes' if nullable=='Yes' or field['nullable']=='Yes' or field['required']=='No' else 'No'
        return dtype,nullable
    for r in m['requests']:
        if r['api_id'] not in apis:err('API001',r,'未定義API: '+r['api_id']);continue
        src=r['source'];resolved=resolve(src)
        if src.startswith('const.'):continue  # constants need their own declared type in a later version
        if resolved is None:err('REF001',r,'Request設定元が未宣言: '+src)
        elif resolved[0]!=r['data_type']:err('TYPE001',r,f'Request {src}: {resolved[0]} != {r["data_type"]}')
        elif resolved[1]=='Yes' and r['required']=='Yes':
            # An optional input may be omitted; not enough information to prove an unsafe request.
            pass
    for r in m['response_mappings']:
        key=(r['api_id'],r['response_field']);src=responses.get(key)
        if src is None:err('REF002',r,'Response項目が未宣言: '+str(key));continue
        dest=resolve(r['destination'])
        if dest is None:err('REF003',r,'反映先が未宣言: '+r['destination']);continue
        if src['data_type']!=dest[0]:err('TYPE002',r,f'Response {key} ({src["data_type"]}) != {r["destination"]} ({dest[0]})')
        if (src['nullable']=='Yes' or src['required']=='No') and dest[1]=='No':
            err('NULL001',r,'NULLまたは省略可能なResponseを非NULLの状態に代入: '+r['destination'])
    for r in m['displays']:
        resolved=resolve(r['source'])
        if resolved and resolved[0]!=r['data_type']:err('TYPE003',r,'表示項目の型不一致: '+r['field_id'])
    errors.extend(validate_legacy(doc))
    errors.extend(validate_flow(doc))
    errors.extend(validate_initial(doc))
    return errors

def validate_project(documents):
    errors=[]; urls={};ids={}
    for d in documents:
        meta=d['metadata'];url=meta['url'];sid=meta['screen_id']
        if url in urls:errors.append({'code':'NAV001','screen_id':sid,'message':'画面URL重複: '+url})
        if sid in ids:errors.append({'code':'NAV002','screen_id':sid,'message':'画面ID重複: '+sid})
        urls[url]=d;ids[sid]=d
    for d in documents:
        sid=d['metadata']['screen_id']
        for r in d['model']['navigation']:
            target=r['target'];canonical=re.sub(r'\{([A-Za-z_]\w*)\}',r':\1',target)
            if canonical not in urls:
                errors.append({'code':'NAV003','screen_id':sid,'line':r['line'],'message':'遷移先画面が存在しない: '+target});continue
            placeholders=set(re.findall(r'\{([A-Za-z_]\w*)\}',target))
            params={} if r['parameters']=='NONE' else dict(p.split('=',1) for p in r['parameters'].split(',') if '=' in p)
            if placeholders!=set(params):errors.append({'code':'NAV004','screen_id':sid,'line':r['line'],'message':'URLプレースホルダと遷移パラメータが不一致: '+target})
            dest_routes={x['parameter']:x for x in urls[canonical]['model']['route_parameters']}
            for key,source in params.items():
                if key not in dest_routes:errors.append({'code':'NAV005','screen_id':sid,'line':r['line'],'message':'遷移先で未宣言のPATHパラメータ: '+key})
                if source.startswith('route.') and source not in {x['destination'] for x in d['model']['route_parameters']}:
                    errors.append({'code':'NAV006','screen_id':sid,'line':r['line'],'message':'遷移元の未宣言ルート値: '+source})
    errors.extend(validate_navigation(documents))
    return errors
