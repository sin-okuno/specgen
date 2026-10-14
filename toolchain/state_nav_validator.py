"""JSON-only initial-value, nullability and cross-screen navigation type checks."""
import json
import re


def resolver(doc):
    m = doc['model']
    types = {}
    for row in m['named_type_fields']:
        types.setdefault(row['type_name'], {})[row['field']] = row
    roots = {r['state_path']: (r['data_type'], r['nullable'] == 'Yes') for r in m['state_types']}
    roots.update({'input.'+r['field_id']: (r['data_type'], r['required'] != 'Yes') for r in m['inputs']})
    roots.update({r['destination']: (r['data_type'], r['required'] != 'Yes') for r in m['route_parameters']})
    for r in m['inputs']:
        roots['query.applied.'+r['field_id']] = (r['data_type'], r['required'] != 'Yes')
    def resolve(path):
        if path in roots:
            return roots[path]
        candidates = sorted((k for k in roots if path.startswith(k+'.')), key=len, reverse=True)
        if not candidates:
            return None
        key = candidates[0]
        typ, nullable = roots[key]
        for field in path[len(key)+1:].split('.'):
            if typ.endswith('[]'):
                return None
            r = types.get(typ, {}).get(field)
            if not r:
                return None
            typ = r['data_type']
            nullable = nullable or r['nullable'] == 'Yes' or r['required'] == 'No'
        return typ, nullable
    return resolve


def literal_type(value):
    value = value.strip()
    if value == 'NULL': return 'null'
    if value == 'EMPTY': return 'empty'
    if value in ('true','false'): return 'boolean'
    if re.fullmatch(r'-?\d+', value): return 'integer'
    if re.fullmatch(r'-?\d+\.\d+', value): return 'number'
    if value == '[]': return 'array'
    if value == '{}': return 'object'
    if value.startswith('"') and value.endswith('"'):
        try:
            if isinstance(json.loads(value),str): return 'string'
        except json.JSONDecodeError: pass
    return None


def compatible(expected, value):
    kind = literal_type(value)
    if kind == 'empty': return expected == 'string'
    if kind == 'array': return expected.endswith('[]')
    if kind == 'object': return expected not in ('string','integer','number','boolean','date','datetime') and not expected.endswith('[]')
    if kind == 'integer': return expected in ('integer','number')
    return kind == expected


def validate_initial(doc):
    resolve = resolver(doc)
    sid = doc['metadata']['screen_id']
    errors = []
    for r in doc['model']['defaults']:
        target, value = r['destination'], r['value']
        def add(code, message): errors.append({'code':code,'screen_id':sid,'line':r['line'],'message':message})
        declared = resolve(target)
        if declared is None:
            add('INIT201', '初期値の設定先が未宣言: '+target)
            continue
        dtype, nullable = declared
        if value == 'NULL':
            if not nullable: add('NULL201', '非NULL状態にNULLを初期設定: '+target)
        elif literal_type(value) is None:
            add('INIT202', '未対応の初期値リテラル: '+value)
        elif not compatible(dtype, value):
            add('INIT203', f'初期値の型不一致: {target} ({dtype}) <- {value}')
    return errors


def validate_navigation(documents):
    errors = []
    urls = {d['metadata']['url']: d for d in documents}
    for d in documents:
        sid = d['metadata']['screen_id']
        resolve = resolver(d)
        for row in d['model']['navigation']:
            canonical = re.sub(r'\{([A-Za-z_]\w*)\}', r':\1', row['target'])
            target = urls.get(canonical)
            if target is None: continue  # NAV003 belongs to existing project validator
            target_routes = {r['parameter']:r for r in target['model']['route_parameters']}
            if row['parameters'] == 'NONE': continue
            for pair in row['parameters'].split(','):
                if '=' not in pair: continue  # NAV004 belongs to existing validator
                key, source = (s.strip() for s in pair.split('=',1))
                if key not in target_routes: continue  # NAV005 belongs to existing validator
                dest = target_routes[key]
                actual = resolve(source)
                if actual is None:
                    errors.append({'code':'NAV201','screen_id':sid,'line':row['line'],'message':'遷移パラメータの設定元が未宣言: '+source})
                    continue
                src_type, nullable = actual
                dst_type = dest['data_type']
                if src_type != dst_type and not (src_type == 'integer' and dst_type == 'number'):
                    errors.append({'code':'NAV202','screen_id':sid,'line':row['line'],'message':f'遷移パラメータ型不一致: {source} ({src_type}) -> {key} ({dst_type})'})
                if nullable and dest['required'] == 'Yes':
                    errors.append({'code':'NAV203','screen_id':sid,'line':row['line'],'message':'NULL許可の値を必須遷移パラメータに指定: '+source})
    return errors
