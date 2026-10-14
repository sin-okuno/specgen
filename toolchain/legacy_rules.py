"""v0.3 and v0.4 legacy semantic rules ported to normalized Screen Model JSON.
No Markdown access. PARSE/SCHEMA diagnostics are handled by parser/pipeline.
"""
import re
from collections import defaultdict

PRIMITIVES={'string','integer','number','boolean','date','datetime'}
IDENT=re.compile(r'^[A-Za-z][A-Za-z0-9_]*$')
def base(t):return t[:-2] if t.endswith('[]') else t

def validate_legacy(doc):
 m=doc['model'];sid=doc['metadata']['screen_id'];errors=[]
 def rows(k):return m.get(k,[])
 def err(code,r,msg):errors.append({'code':code,'screen_id':sid,'line':r.get('line',0),'message':msg})
 def idset(k,field):return {r[field] for r in rows(k)}
 areas=idset('areas','area_id');events=idset('events','event_id');apis=idset('apis','api_id');navs=idset('navigation','nav_id');opts=idset('options','option_id');inits=idset('initialization','init_id');inputs=idset('inputs','field_id');buttons=idset('actions','field_id');routes=idset('route_parameters','parameter')
 responses={(r['api_id'],r['field']):r for r in rows('responses')}
 mappings={(r['api_id'],r['destination']):r['response_field'] for r in rows('response_mappings')}
 def reference(ref,r):
  if ref.startswith('query.applied.') and ref[len('query.applied.'):] not in inputs:err('REF002',r,'未定義検索項目: '+ref)
  if ref.startswith('input.') and ref[6:] not in inputs:err('REF002',r,'未定義入力項目: '+ref)
  if ref.startswith('route.') and ref[6:] not in routes:err('REF002',r,'未定義ルート項目: '+ref)
  # options are declared by state_types in v1.5, option IDs are OPT-001 (not options.status)
  if ref.startswith('options.') and not any(ref==s['state_path'] or ref.startswith(s['state_path']+'.') for s in rows('state_types')):err('REF002',r,'未定義候補状態: '+ref)
 for key in ('layout','inputs','displays','actions'):
  for r in rows(key):
   if r['area_id'] not in areas:err('REF001',r,'未定義領域: '+r['area_id'])
 for r in rows('actions'):
  if r['event_id'] not in events:err('REF001',r,'未定義イベント: '+r['event_id'])
 for r in rows('inputs'):
  for opt in re.findall(r'options:(OPT-\d+)',r['constraints']):
   if opt not in opts:err('REF001',r,'未定義候補: '+opt)
 for r in rows('options'):
  if r['fetch_method']=='API':
   api,_,field=r['option_source'].partition('.')
   if api not in apis or (api,field) not in responses:err('REF002',r,'候補取得元が未定義: '+r['option_source'])
 graph={}
 for r in rows('initialization'):
  deps=[] if r['depends_on']=='NONE' else [x.strip() for x in r['depends_on'].split(',')];graph[r['init_id']]=deps
  for dep in deps:
   if dep not in inits:err('FLOW001',r,'未定義依存処理: '+dep)
  if r['operation']=='CALL_API' and r['reference'] not in apis:err('REF001',r,'未定義API: '+r['reference'])
  if r['operation']=='CALL_EVENT' and r['reference'] not in events:err('REF001',r,'未定義イベント: '+r['reference'])
  if r['operation']=='READ_ROUTE':reference(r['reference'],r)
 seen=set();active=set()
 def dfs(key):
  if key in active:err('FLOW001',{},'初期表示依存が循環: '+key);return
  if key in seen:return
  active.add(key)
  for dep in graph.get(key,[]):
   if dep in graph:dfs(dep)
  active.remove(key);seen.add(key)
 for key in graph:dfs(key)
 for r in rows('events'):
  triggers=r['trigger'].split(',');origins=r['origin'].split(',')
  if len(triggers)!=len(origins):err('FLOW002',r,'起動条件と発生元の数が不一致')
  for trig,origin in zip(triggers,origins):
   if trig=='ON_INIT' and not any(x['init_id']==origin and x['operation']=='CALL_EVENT' and x['reference']==r['event_id'] for x in rows('initialization')):err('FLOW002',r,'ON_INITの起動元が不正')
   if trig=='ON_CLICK' and origin not in buttons:err('REF001',r,'未定義ボタン: '+origin)
 steps=defaultdict(dict)
 for r in rows('event_steps'):
  ev=r['event_id']
  if ev not in events:err('REF001',r,'未定義イベント: '+ev)
  try:idx=int(r['step'])
  except ValueError:err('FLOW003',r,'ステップ番号が数値ではない');continue
  if idx in steps[ev]:err('FLOW003',r,'ステップ番号重複: '+ev)
  steps[ev][idx]=r
  op=r['operation'];ref=r['reference']
  if op=='CALL_API' and ref not in apis:err('REF001',r,'未定義API: '+ref)
  if op=='NAVIGATE' and ref not in navs:err('REF001',r,'未定義遷移: '+ref)
  if op=='SET_VALUE' and '=' in ref:
   a,b=ref.split('=',1);reference(a,r);reference(b,r)
  if op=='APPLY_QUERY' and ref!='QUERY':err('FLOW005',r,'APPLY_QUERYの参照先はQUERY')
 dialogs={r['dialog_id']:r for r in rows('dialogs')}
 for ev,ss in steps.items():
  if sorted(ss)!=list(range(1,len(ss)+1)):err('FLOW003',{},'ステップ番号が連番でない: '+ev)
  for idx,r in ss.items():
   if r['operation']=='CONFIRM':
    dlg=dialogs.get(r['reference'])
    if not dlg:err('REF001',r,'未定義確認ダイアログ: '+r['reference'])
    elif dlg['event_id']!=ev or dlg['on_confirm']!=r['on_success'] or dlg['on_cancel']!=r['on_failure']:err('FLOW004',r,'CONFIRM分岐がダイアログ定義と不一致')
   for branch in ('on_success','on_failure'):
    target=r[branch]
    if target=='NEXT' and idx+1 not in ss:err('FLOW003',r,'最後のステップにNEXT: '+ev)
    if target.startswith('STEP:'):
     try:num=int(target.split(':')[1])
     except ValueError:num=-1
     if num not in ss or num<=idx:err('FLOW003',r,'無効なステップ遷移: '+target)
 if any(r['area_type']=='LIST' for r in rows('areas')):
  query_apis={r['api_id'] for r in rows('requests') if r['source'].startswith('query.applied.')}
  for r in rows('requests'):
   if r['api_id'] in query_apis and r['source'].startswith('input.'):err('FLOW005',r,'検索APIはquery.appliedを参照')
  for ev,ss in steps.items():
   if not any(r['operation']=='CALL_API' and r['reference'] in query_apis for r in ss.values()):continue
   is_search=any(r['event_id']==ev and '検索' in r['event_name'] for r in rows('events'))
   count=sum(r['operation']=='APPLY_QUERY' for r in ss.values())
   if (is_search and count!=1) or (not is_search and count!=0):err('FLOW005',{},'検索/ページング時のAPPLY_QUERY使用が不正: '+ev)
 for r in rows('apis'):
  for name in re.findall(r'\{(\w+)\}',r['endpoint']):
   matches=[x for x in rows('requests') if x['api_id']==r['api_id'] and x['parameter']==name and x['location']=='PATH']
   if len(matches)!=1:err('API001',r,f'{r["api_id"]}: PATH {name} が1件でない')
 for r in rows('requests'):reference(r['source'],r)
 for r in rows('response_mappings'):
  api,path=r['api_id'],r['response_field'];root=path.split('.')[0].replace('[]','')
  if (api,root) not in responses:err('REF002',r,'Response項目が未定義: '+api+'.'+path)
  if r['destination'].startswith(('input.','route.','options.')):reference(r['destination'],r)
  typ=responses.get((api,root),{}).get('data_type','')
  if r['mapping_mode'] in ('REPLACE','APPEND') and not typ.endswith('[]'):err('API002',r,'配列以外へのREPLACE/APPEND: '+api+'.'+path)
  if r['destination']=='list.items' and not typ.endswith('[]'):err('API002',r,'list.itemsには配列型が必要')
 for r in rows('displays'):
  src=r['source']
  if src.startswith('data.') and not any(src==dest or src.startswith(dest+'.') for _,dest in mappings):err('REF002',r,'表示元へのResponse反映がない: '+src)
  if src.startswith('list.items[].') and not any(dest=='list.items' for _,dest in mappings):err('REF002',r,'一覧項目に対応するResponseがない: '+src)
 for r in rows('navigation'):
  if r['event_id'] not in events:err('REF001',r,'未定義イベント: '+r['event_id'])
  if re.search(r':\w+',r['target']):err('NAV002',r,'遷移先には{param}を使用する')
  params=dict(x.split('=',1) for x in r['parameters'].split(',') if '=' in x)
  for name in re.findall(r'\{(\w+)\}',r['target']):
   if name not in params:err('NAV001',r,'遷移パラメータ未定義: '+name)
  for ref in params.values():reference(ref,r)
 # named types (v0.4)
 catalog={};fields=defaultdict(dict)
 for r in rows('named_type_catalog'):
  name=r['type_name']
  if not IDENT.fullmatch(name) or name in PRIMITIVES|{'object','array'}:err('TYPE001',r,'不正な型名: '+name)
  if name in catalog:err('TYPE003',r,'型名重複: '+name)
  catalog[name]=r
 for r in rows('named_type_fields'):
  owner,name,typ=r['type_name'],r['field'],r['data_type']
  if owner not in catalog:err('TYPE001',r,'未宣言の型: '+owner)
  if not IDENT.fullmatch(name):err('TYPE003',r,'不正なフィールド名: '+name)
  if name in fields[owner]:err('TYPE003',r,'フィールド重複: '+owner+'.'+name)
  fields[owner][name]=r
  if r['required'] not in ('Yes','No') or r['nullable'] not in ('Yes','No'):err('TYPE008',r,'必須・NULL許可はYes/No')
  if base(typ) not in PRIMITIVES|catalog.keys():err('TYPE001',r,'未定義フィールド型: '+typ)
 for name,r in catalog.items():
  if not fields[name]:err('TYPE002',r,'フィールドがない型: '+name)
 visited=set();active=set();cycle=False
 def walk(name):
  nonlocal cycle
  if name in active:cycle=True;return
  if name in visited:return
  active.add(name)
  for r in fields[name].values():
   child=base(r['data_type'])
   if child in catalog:walk(child)
  active.remove(name);visited.add(name)
 for name in catalog:walk(name)
 if cycle:err('TYPE004',{},'名前付き型の循環参照')
 for key in ('requests','responses'):
  for r in rows(key):
   typ=r['data_type']
   if typ in ('object','object[]'):err('TYPE007',r,'匿名object型は禁止: '+typ)
   elif base(typ) not in PRIMITIVES|catalog.keys():err('TYPE001',r,'APIの未定義型: '+typ)
 for r in rows('response_mappings'):
  api,path=r['api_id'],r['response_field'];segments=path.replace('[]','').split('.')
  typ=responses.get((api,segments[0]),{}).get('data_type')
  for seg in segments[1:]:typ=fields.get(base(typ or ''),{}).get(seg,{}).get('data_type')
  if typ is None:err('TYPE009',r,'Response参照先の型を解決できない: '+api+'.'+path)
 return errors
