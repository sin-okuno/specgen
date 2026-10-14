"""Conservative static checks for INIT, events, and conditions over Screen Model JSON.

Condition grammar v0.6: ALWAYS | IS_SET(path) | IS_EMPTY(path) |
EQ(path,scalar) | NE(path,scalar). No arbitrary code evaluation.
"""
import re
from collections import defaultdict

PATH = r"[A-Za-z][A-Za-z0-9_]*(?:\.[A-Za-z][A-Za-z0-9_]*)*"
CONDITION = re.compile(r"^(IS_SET|IS_EMPTY)\((" + PATH + r")\)$|^(EQ|NE)\((" + PATH + r"),\s*(true|false|null|-?\d+(?:\.\d+)?|\"[^\"]*\")\)$")
TERMINALS = {'END', 'STOP', 'COMMON_ERROR'}


def validate_flow(doc):
    m=doc['model']; sid=doc['metadata']['screen_id']; errors=[]
    def error(code,row,msg):
        errors.append({'code':code,'screen_id':sid,'line':row.get('line',0),'message':msg})
    types={r['type_name']:{} for r in m.get('named_type_catalog',[])}
    for r in m.get('named_type_fields',[]):types.setdefault(r['type_name'],{})[r['field']]=r['data_type']
    states={r['state_path']:r['data_type'] for r in m.get('state_types',[])}
    inputs={r['field_id']:r['data_type'] for r in m.get('inputs',[])}
    routes={r['destination']:r['data_type'] for r in m.get('route_parameters',[])}
    def resolve(path):
        if path.startswith('input.'):return inputs.get(path[6:])
        if path.startswith('query.applied.'):return inputs.get(path[len('query.applied.'):])
        if path.startswith('route.'):return routes.get(path)
        if path in states:return states[path]
        roots=sorted((x for x in states if path.startswith(x+'.')),key=len,reverse=True)
        if not roots:return None
        root=roots[0];t=states[root]
        for segment in path[len(root)+1:].split('.'):
            if t.endswith('[]'):return None
            t=types.get(t,{}).get(segment)
            if t is None:return None
        return t
    def condition(raw,row):
        if raw=='ALWAYS':return
        match=CONDITION.fullmatch(raw)
        if not match:
            error('COND001',row,'未対応の条件式。ALWAYS / IS_SET(path) / IS_EMPTY(path) / EQ(path,value) / NE(path,value): '+raw);return
        op=match.group(1) or match.group(3);path=match.group(2) or match.group(4)
        t=resolve(path)
        if t is None:error('COND002',row,'条件式の参照先が未宣言: '+path);return
        if op in ('EQ','NE'):
            val=match.group(5)
            if val=='null':return # NULL許可は別工程で検証
            actual=('boolean' if val in ('true','false') else 'string' if val.startswith('"') else 'number' if '.' in val else 'integer')
            if not (actual==t or (actual=='integer' and t=='number')):
                error('COND003',row,f'条件式の型不一致: {path} ({t}) vs {val} ({actual})')
    for r in m.get('initialization',[]):condition(r['condition'],r)
    steps=defaultdict(dict)
    for r in m.get('event_steps',[]):
        condition(r['condition'],r)
        try:steps[r['event_id']][int(r['step'])]=r
        except (ValueError,TypeError):pass # legacy validator reports malformed numbers
    # Branch graph: every step must be reachable from step 1; every reachable path
    # must be able to terminate. Forward-only STEP jumps enforced by legacy validator.
    for event,by_step in steps.items():
        if 1 not in by_step:continue
        graph={};bad=False
        for n,r in by_step.items():
            outgoing=[]
            for branch in ('on_success','on_failure'):
                v=r[branch]
                if v=='NEXT':
                    if n+1 in by_step:outgoing.append(n+1)
                    else:bad=True
                elif v.startswith('STEP:'):
                    try:
                        target=int(v[5:])
                        if target in by_step:outgoing.append(target)
                        else:bad=True
                    except ValueError:bad=True
                elif v not in TERMINALS:
                    error('FLOW101',r,'未対応の分岐先: '+v);bad=True
            graph[n]=outgoing
        reachable=set();pending=[1]
        while pending:
            n=pending.pop()
            if n in reachable:continue
            reachable.add(n);pending.extend(graph.get(n,[]))
        for n in sorted(set(by_step)-reachable):error('FLOW102',by_step[n],f'到達不能ステップ: {event} STEP:{n}')
        if not bad:
            terminal={n for n,r in by_step.items() if r['on_success'] in TERMINALS or r['on_failure'] in TERMINALS}
            reverse=defaultdict(list)
            for a,targets in graph.items():
                for b in targets:reverse[b].append(a)
            can_finish=set(terminal);pending=list(terminal)
            while pending:
                for prev in reverse[pending.pop()]:
                    if prev not in can_finish:can_finish.add(prev);pending.append(prev)
            for n in sorted(reachable-can_finish):error('FLOW103',by_step[n],f'終了できないイベント経路: {event} STEP:{n}')
    return errors
