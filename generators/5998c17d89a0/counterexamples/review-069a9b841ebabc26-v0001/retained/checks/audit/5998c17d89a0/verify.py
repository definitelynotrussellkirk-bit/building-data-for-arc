"""Compare retained public Racket results; emit the minimal audit witness."""
from pathlib import Path
import hashlib
import json
from collections import Counter
from reviewer_support import find_root, load_selected_generator

ID='5998c17d89a0'
HERE=Path(__file__).resolve().parent
prepared=json.loads((HERE/'prepared.json').read_text())
public=json.loads((HERE/'racket.json').read_text())
root=find_root(__file__)
gen,source,source_sha=load_selected_generator(ID,root=root)
assert source_sha==prepared['generator_sha256']==public['generator_sha256']
assert public['rule_hash_matches_catalog'] is True
assert public['rule_text_sha256']==prepared['canonical_program_sha256']
cases=prepared['cases']
results=public['results']
assert len(cases)==len(results)==53
counts=Counter()
key_counts=Counter()
canonical=[]
for case,result in zip(cases,results):
    assert result['index']==case['apply_index']
    assert result['input']==case['input']
    assert result['valid_output'] is True and result['error'] is None
    assert result['output']==case['python_mirror_output']
    assert gen.self_check(case['input'],difficulty=case.get('difficulty'))==case['self_check']==[]
    kind=case['kind']
    counts[kind+'_checked']+=1
    if result['output']==case['rival_output']:
        counts[kind+'_rival_matches']+=1
    if kind=='generated':
        key_counts[case['attributes']['key']]+=1
        assert case['attributes']['component_normalized_corner_filled']==[True,True]
        if case['attributes']['key']==2:
            assert result['output'][0][0]==8
    if kind=='canonical':
        assert result['output']==case['output']
        canonical.append({'variant':case['variant'],'split':case['split'],'pair_index':case['pair_index'],
                          'apply_index':case['apply_index'],'rival_matches_racket':result['output']==case['rival_output']})
assert counts['canonical_rival_matches']==4
assert counts['generated_rival_matches']==48
assert counts['counterexample_rival_matches']==0
case=cases[-1]
result=results[-1]
assert case['attributes']['component_areas']==[5,5]
assert case['attributes']['component_bbox_hw']==[[3,3],[3,3]]
assert result['output']==[[0,8,0],[8,8,8]]
assert case['rival_output']==[[8,8,0],[8,8,8]]
grid=case['input']
color_cells={color:{(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v==color} for color in (2,3,6)}
assert color_cells[2]=={(0,0)}
for left,right in ((2,3),(2,6),(3,6)):
    assert min(max(abs(r1-r2),abs(c1-c2)) for r1,c1 in color_cells[left] for r2,c2 in color_cells[right])>=2
for color in (3,6):
    cells=color_cells[color]
    seen={next(iter(cells))}
    changed=True
    while changed:
        prior=len(seen)
        seen|={q for p in seen for q in cells if abs(p[0]-q[0])+abs(p[1]-q[1])==1}
        changed=len(seen)>prior
    assert seen==cells
assert max(c for r,c in color_cells[3])<min(c for r,c in color_cells[6])
summary={
    'task_id':ID,'classification':'suspected shortcut; reproduced support gap',
    'source_status':'assigned unchanged source; no generator or Racket edits',
    'generator_sha256':source_sha,'generator_version':gen.VERSION,
    'rule_text_sha256':public['rule_text_sha256'],'executed_rule_hash':public['executed_rule_hash'],
    'counts':dict(counts),'public_racket_valid_outputs':53,'unique_input_count':len({json.dumps(x['input']) for x in cases}),
    'generated_seed':0,'generated_sample_indices':list(range(16)),
    'generated_difficulties':['easy','medium','hard'],'generated_overrides':{},
    'generated_key_counts':dict(sorted(key_counts.items())),
    'generated_both_normalized_corners_filled':48,
    'canonical_pair_results':canonical,
    'input_validator_failures':0,'python_mirror_mismatches_with_racket':0,
    'lesson_checks':'not run; per-grid support audit only',
    'checks_scope':'4 usable canonical pairs, 48 deterministic generated inputs, 1 hand-authored counterexample; no broad battery',
    'rival':prepared['rival'],
    'counterexample_apply_index':52,
    'counterexample_domain':'Passes self_check and all documented invariants; 8x11 easy grid, two 4-connected 3x3 boxes with 5 cells each and at least one-cell separation. Outside actual generated support because both source masks omit normalized (0,0).',
    'evidence_files':{name:hashlib.sha256((HERE/name).read_bytes()).hexdigest() for name in ('probe.py','input.json','prepared.json','racket.json')},
}
witness={
    'task_id':ID,'generator_sha256':source_sha,'rule_text_sha256':public['rule_text_sha256'],
    'executed_rule_hash':public['executed_rule_hash'],'kind':'hand-authored domain counterexample',
    'seed':None,'sample_index':None,'overrides':None,
    'input':grid,'actual_racket_output':result['output'],'rival_output':case['rival_output'],
    'rival':prepared['rival'],'self_check_errors':case['self_check'],'domain':summary['counterexample_domain'],
    'attributes':case['attributes'],'input_sha256':result['input_sha256'],'output_sha256':result['output_sha256'],
    'public_racket_result_index':52,'racket_result_path':'checks/audit/5998c17d89a0/racket.json',
    'command_cwd':'.','argv':['python3','run_with_racket.py','python3','-m','arcpuzzles','apply',ID,'--input','../checks/audit/5998c17d89a0/input.json','--out','../checks/audit/5998c17d89a0/racket.json'],
    'effective_payload_cwd':'repo',
}
(HERE/'result.json').write_text(json.dumps(summary,indent=2)+'\n')
(HERE/'counterexample.json').write_text(json.dumps(witness,indent=2)+'\n')
print(json.dumps({k:summary[k] for k in ('task_id','generator_sha256','rule_text_sha256','counts','public_racket_valid_outputs','unique_input_count','generated_key_counts','input_validator_failures','python_mirror_mismatches_with_racket')}))
