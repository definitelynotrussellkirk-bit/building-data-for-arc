#!/usr/bin/env python3
"""Replay findings-only audits against the two immutable assigned targets."""
from __future__ import annotations
import argparse
from collections import Counter
import copy
import hashlib
import json
from pathlib import Path
from topology_probe import load_generator


def header_mirror(grid):
    answer = copy.deepcopy(grid)
    for r in range(1,len(grid)):
        for c in range(1,len(grid[0])):
            if grid[r][0] == 3 and grid[0][c] == 2:
                answer[r][c] = 5
    return answer


def key_color(grid):
    a,b = grid[1][1],grid[3][3]
    return 1 if a == 5 and b == 0 else 3 if a == 0 and b == 0 else 2


def key_mirror(grid):
    color = key_color(grid)
    return [[color if grid[r+1][c+5] == 5 else 0 for c in range(3)] for r in range(3)]


def fixed_two(grid):
    return [[2 if grid[r+1][c+5] == 5 else 0 for c in range(3)] for r in range(3)]


def run(runtime,task):
    gen,path = load_generator(runtime,task)
    from scripts.canonical_profile_gate import canonical_pairs, canonical_rule_source
    from scripts.rule_smoke import rule_application
    from arc_repl.racket_bridge import RacketBridge
    result = {'task_id':task,'generator_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
              'runtime_directory':str(runtime),'generator_edits':False}
    cases = []
    if task == '0be8ff9b4144':
        endpoints = ({'grid_h':5}, {'grid_h':16}, {'grid_w':6}, {'grid_w':18},
                     {'n_top':1}, {'n_top':6}, {'n_left':1}, {'n_left':6})
        result['declared_endpoint_probes'] = []
        for kwargs in endpoints:
            try:
                grid = gen.generate(0,0,**kwargs)
                row = {'seed':0,'sample_index':0,'overrides':kwargs,'status':'accepted','input':grid}
            except ValueError as exc:
                row = {'seed':0,'sample_index':0,'overrides':kwargs,'status':'rejected','message':str(exc)}
            result['declared_endpoint_probes'].append(row)
        result['rejected_initial_hypothesis'] = (
            'Expected marker counts might silently clip on a small board; this did not reproduce '
            'because grid_h=5 was rejected first. The reproduced defect is an unreachable '
            'advertised endpoint, not proven count clipping.')
        result['unknown_override_accepted'] = gen.generate(17,0,unknown_probe=99) == gen.generate(17,0)
        result['invalid_texture_accepted'] = bool(gen.generate(17,0,texture='NOT_AN_ALLOWED_TEXTURE'))
        mirror = header_mirror
        for index in range(30):
            g=gen.generate(index,index,difficulty=('easy','medium','hard')[index%3])
            cases.append((f'default/{index}',g))
    else:
        mirror = key_mirror
        ambiguous = []
        classes = Counter()
        for seed in range(100):
            grids = [gen.generate(seed,i,difficulty='medium') for i in range(4)]
            labels = [key_color(g) for g in grids]
            classes.update(labels)
            if all(fixed_two(g) == mirror(g) for g in grids[:3]) and fixed_two(grids[3]) != mirror(grids[3]):
                ambiguous.append({'seed':seed,'sample_indices':[0,1,2,3],
                                  'difficulty':'medium','output_classes':labels})
                if 'ambiguous_witness' not in result:
                    result['ambiguous_witness'] = {'seed':seed,
                        'demos':[{'input':g,'output':mirror(g)} for g in grids[:3]],
                        'query':{'input':grids[3],'output':mirror(grids[3]),
                                 'rival_output':fixed_two(grids[3])}}
                    cases.extend((f'ambiguous/{seed}/{i}',g) for i,g in enumerate(grids))
        result['fixed_two_ambiguous_lessons'] = ambiguous
        result['lesson_count'] = 100
        result['color_classes'] = dict(classes)
        result['anti_corruption_identical_seed_count'] = sum(
            gen.generate(seed,0,anti_corruption=True) == gen.generate(seed,0,anti_corruption=False)
            for seed in range(100))
        canonical = canonical_pairs(task)
        left_patterns = {tuple(tuple(row[1:4]) for row in p['input'][1:4]) for p in canonical}
        matching = 0
        for seed in range(100):
            g = gen.generate(seed,0,difficulty='medium')
            matching += tuple(tuple(row[1:4]) for row in g[1:4]) in left_patterns
            if seed < 30:
                cases.append((f'default/{seed}',g))
        result['canonical_left_shape_matches_100'] = matching
        result['canonical_left_shape_count'] = len(left_patterns)
        result['shape_interpretation_status'] = 'domain question; selected Racket rule is explicitly a two-key classifier'
    source = canonical_rule_source(task)
    canonical = canonical_pairs(task)
    for i,p in enumerate(canonical):
        cases.append((f'canonical/{i}',p['input']))
    mismatches=[]
    checks=[]
    with RacketBridge(max_calls_before_restart=96) as bridge:
        for name,grid in cases:
            expected=mirror(grid)
            answer=bridge.eval_text(rule_application(source,grid))
            row={'case':name,'parity':expected == answer, 'self_check':gen.self_check(grid)}
            if name.startswith('canonical/'):
                row['canonical_exact'] = answer == canonical[int(name.split('/')[1])]['output']
            if answer != expected:
                mismatches.append({'case':name,'expected':expected,'actual':answer})
            checks.append(row)
    result['reference_checks']=checks
    result['reference_mismatches']=mismatches
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--runtime',required=True,type=Path)
    p.add_argument('--task',required=True,choices=('0be8ff9b4144','e2c0324ce778'))
    p.add_argument('--out',required=True,type=Path)
    a=p.parse_args()
    result=run(a.runtime.resolve(),a.task)
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in
                    ('ambiguous_witness','reference_checks')},indent=2))
    return int(bool(result['reference_mismatches']))


if __name__ == '__main__':
    raise SystemExit(main())
