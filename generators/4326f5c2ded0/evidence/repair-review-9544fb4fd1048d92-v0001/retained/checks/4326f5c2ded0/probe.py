"""Bounded ordinary-default teaching audit; Python locates, Racket labels."""
from __future__ import annotations
import ast
import hashlib
import json
from pathlib import Path
import signal
import time

from reviewer_support import find_root, load_selected_generator
from arc_repl.racket_bridge import RacketBridge

ROOT = find_root(__file__)
OUT = Path(__file__).resolve().parent
TASK = '4326f5c2ded0'

def sha(value):
    return hashlib.sha256(value).hexdigest()

def rival(grid, name):
    cells = [(r,c,v) for r,row in enumerate(grid) for c,v in enumerate(row) if v]
    bottom = max(r for r,c,v in cells)
    result = [[0]*len(grid[0]) for _ in grid]
    for r,c,v in cells:
        if name == 'occupied_row_rank':
            shift = len({rr for rr,cc,vv in cells if rr > r})
        else:
            shift = max(rr for rr,cc,vv in cells if vv == v)-r
        target = c-shift
        if 0 <= target < len(grid[0]):
            result[r][target] = v
    return result

def main():
    signal.alarm(120)
    started = time.monotonic()
    mod, source, source_hash = load_selected_generator(TASK, root=ROOT)
    declaration = None
    for node in ast.parse(source.read_text()).body:
        if isinstance(node, ast.Assign) and any(isinstance(t,ast.Name) and t.id=='EXAMPLES_NEEDED' for t in node.targets):
            declaration = ast.literal_eval(node.value)
    assert declaration is None
    rows = [json.loads(line) for line in (ROOT/'shared/data/canonical/puzzles.jsonl').read_text().splitlines()]
    programs = {row['program_solution'] for row in rows if row.get('task_id')==TASK}
    assert len(programs)==1
    intended = programs.pop()
    normalized = sha(' '.join(intended.split()).encode())[:12]
    assert normalized == mod.RULE_HASH
    wrong = {
        'occupied_row_rank': intended.replace('(- max-r cr)', '(length (remove-duplicates (for/list ((other cells) #:when (> (first other) cr)) (first other))))'),
        'color_bottom': intended.replace('(- max-r cr)', '(- (max-of first (filter (lambda (other) (= (third other) cv)) cells)) cr)'),
    }
    result = {'schema':'bounded-peer-learnability-v1', 'task_id':TASK,
        'outcome':'unchanged', 'source_sha256':source_hash,
        'canonical_full_program_sha256':sha(intended.encode()),
        'normalized_rule_hash':normalized, 'declared_examples_needed':declaration,
        'ordinary_generate_default_demos':3, 'dataset_runner_default_demos':4,
        'searched_demos':4, 'seed_limit':32, 'rivals':list(wrong),
        'scope':'production ordinary defaults, no profile overrides or input mutations; opt-in parametric prototype excluded',
        'programs':{'intended':intended, **wrong},
        'runtime_pair_applications':0, 'self_check_calls':0, 'trace':[]}
    candidate = None
    for seed in range(32):
        accepted=[]
        seen=set()
        rejected=[]
        for index in range(25):
            grid = mod.generate(seed,index)
            errors = mod.self_check(grid)
            result['self_check_calls'] += 1
            assert not errors, (seed,index,errors)
            output = mod.rule_mirror(grid)
            key = json.dumps({'input':grid,'output':output},sort_keys=True)
            if key in seen:
                rejected.append(index)
                continue
            seen.add(key)
            accepted.append({'seed':seed,'sample_index':index,'input':grid,
                'python_intended_output':output,'profile':mod.observe_overrides(grid)['scene_profile'],
                'self_check':errors})
            if len(accepted)==5:
                break
        assert len(accepted)==5
        matches={name:[rival(pair['input'],name)==pair['python_intended_output'] for pair in accepted] for name in wrong}
        result['trace'].append({'seed':seed,'indices':[p['sample_index'] for p in accepted],
            'profiles':[p['profile'] for p in accepted], 'duplicate_indices_skipped':rejected,'matches':matches})
        for name,flags in matches.items():
            if all(flags[:4]) and not flags[4]:
                candidate=(seed,name,accepted)
                break
        if candidate:
            break
    if candidate:
        seed,name,pairs=candidate
        with RacketBridge(timeout=10,startup_timeout=60) as bridge:
            identity=bridge.runtime_identity
            assert identity['protected'] is True
            for label,program in [('intended',intended),('wrong',wrong[name])]:
                bridge.eval_text('(define __peer_'+label+' '+program[7:-1]+')')
            for pair in pairs:
                bridge.define_grid('__peer_input',pair['input'])
                for label in ('intended','wrong'):
                    pair[label+'_racket_output']=bridge.eval_text('(__peer_'+label+' __peer_input)')
                    result['runtime_pair_applications']+=1
                assert pair['intended_racket_output']==pair['python_intended_output']
                assert pair['wrong_racket_output']==rival(pair['input'],name)
            assert all(p['intended_racket_output']==p['wrong_racket_output'] for p in pairs[:4])
            assert pairs[4]['intended_racket_output']!=pairs[4]['wrong_racket_output']
        result.update(outcome='blocked',finding='plausible wrong rule fits all four ordinary visible demos and differs on next generated query',
            rival=name,seed=seed,runtime_identity=identity, demonstrations=pairs[:4],query=pairs[4],
            repair_status='pending: choose diagnostic teaching profile or query-relevant rival elimination before accepting ordinary episodes')
    else:
        result['finding']='finite no-finding for two specified rivals across 32 seeds at four demonstrations'
    result['elapsed_seconds']=time.monotonic()-started
    result['probe_sha256']=sha(Path(__file__).read_bytes())
    (OUT/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ('task_id','outcome','finding','runtime_pair_applications','self_check_calls','elapsed_seconds')}))

if __name__=='__main__':
    main()
