import hashlib, importlib.util, json
from pathlib import Path
from reviewer_support import find_root
TASK='cde6cd1740f9'; root=find_root(Path('generators')/TASK/'generator.py'); out=root.parent/'checks/audit'/TASK
spec=json.loads((out/'probe-spec.json').read_text()); sha=hashlib.sha256((root/'generators'/TASK/'generator.py').read_bytes()).hexdigest(); assert sha==spec['generator_sha256']
module_spec=importlib.util.spec_from_file_location('audit_generator',root/'generators'/TASK/'generator.py'); gen=importlib.util.module_from_spec(module_spec); module_spec.loader.exec_module(gen)
summary={'task_id':TASK,'generator_sha256':sha,'rule_hash':spec['rule_hash'],'groups':{},'records':[]}
for group in ('canonical','ordinary','witness'):
    receipt=json.loads((out/f'{group}-racket.json').read_text())
    assert receipt['generator_sha256']==sha
    assert receipt['executed_rule_hash']==spec['rule_hash']
    records=[r for r in spec['records'] if r['group']==group]
    assert len(records)==len(receipt['results'])
    matches=0
    for record,actual in zip(records,receipt['results']):
        assert actual['input']==record['input'] and actual['error'] is None and actual['valid_output']
        if group=='canonical': assert actual['output']==record['output']
        equal=actual['output']==record['rival_output']; matches+=equal
        diffs=[{'row':r,'col':c,'racket':actual['output'][r][c],'rival':record['rival_output'][r][c]} for r in range(len(record['input'])) for c in range(len(record['input'][0])) if actual['output'][r][c]!=record['rival_output'][r][c]]
        summary['records'].append({**record,'actual_public_racket_output':actual['output'],'rival_matches':equal,'differing_cells':diffs,'public_receipt':f'{group}-racket.json','public_index':actual['index']})
    summary['groups'][group]={'public_racket_executions':len(records),'rival_matches':matches,'valid_outputs':len(records)}
demos=[{'input':r['input'],'output':r['actual_public_racket_output']} for r in summary['records'] if r['group']=='ordinary']
witness=next(r for r in summary['records'] if r['group']=='witness')
summary['lesson_hook_on_8_ordinary_demos_and_handmade_witness_query']=gen.lesson_identifiable(demos,{'input':witness['input'],'output':witness['actual_public_racket_output']})
summary['witness_color_counts']={str(color):sum(row[6]==color for row in witness['input']) for color in (2,5)}
assert summary['groups']['canonical']['rival_matches']==4
assert summary['groups']['ordinary']['rival_matches']==8
assert summary['groups']['witness']['rival_matches']==0
assert witness['self_check']==[] and witness['strict_canonical_like']==[]
(out/'comparison.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps({k:v for k,v in summary.items() if k!='records'}))
print(json.dumps({'witness_differing_cells':witness['differing_cells'],'witness_nonzero_cells':[(r,c,v) for r,row in enumerate(witness['input']) for c,v in enumerate(row) if v]}))
