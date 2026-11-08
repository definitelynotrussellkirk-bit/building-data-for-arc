"""Confirm the reviewer's finite overlap gap against saved original lessons."""
from pathlib import Path
import importlib.util,json,hashlib

home=Path('generators/17f92e205b34/workspace/parametric')
spec=importlib.util.spec_from_file_location('gap_audit',home/'audit.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
base=Path('../checks/17f92e205b34/audit-r1/audit.json')
old=json.loads(base.read_bytes())
completion='(map-grid (overlay g (transpose g)) (lambda (r c v) (if (and (not (= r c)) (not (= (cell-at g r c) 0)) (not (= (cell-at g c r) 0))) 0 v)))'
result={'schema':'reflection-overlap-gap-v1','source_binding':old['source_binding'],
        'saved_gold_evidence':{'path':'checks/17f92e205b34/audit-r1/audit.json','sha256':hashlib.sha256(base.read_bytes()).hexdigest()},
        'scope':'Original seed0 three-demo lessons and first query. Gold reuses hash-bound protected audit; only rival labels executed here.',
        'cases':[]}
with m.Evaluator() as e:
    for episode in old['episodes']:
        if episode['seed']!=0:continue
        selection=episode['settings']['selection']
        program=m.selection_program(selection,completion=completion)
        outputs=[e.apply(program,p['input']) for p in episode['train']]
        assert outputs==[p['output'] for p in episode['train']]
        query=episode['test'][0]
        rival=e.apply(program,query['input'])
        assert rival!=query['output']
        result['cases'].append({'settings':episode['settings'],'seed':0,
            'train':episode['train'],'query':query,'program':episode['program'],
            'alternative_program':program,'alternative_output':rival,
            'changed_cells':m.changed_cells(rival,query['output'])})
    result['racket']=e.identity;result['executions']=e.records
    result['unique_protected_executions']=len(e.records)
Path('../checks/17f92e205b34/prefilled-gap-r1.json').write_bytes(m.raw(result))
print(json.dumps({'cases':[{'settings':c['settings'],'changed_cells':c['changed_cells']} for c in result['cases']],
                  'protected_executions':result['unique_protected_executions']}))
