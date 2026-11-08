"""Run inside a prepared, relocated runtime. Pins and executes canonical Racket.

Copy this file, instruction_table_probe.py, and baseline_ambiguous_lesson.json
from the task workspace to the runtime root. Example:
  python3 -I reference_probe.py --out ../checks/reference_parity.json
No sibling checkout or source-tree import is required.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib
import json
from pathlib import Path
import sys
import time

ROOT=Path.cwd().resolve()
sys.path.insert(0,str(ROOT))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out',type=Path,required=True)
    p.add_argument('--seeds',type=int,default=16)
    p.add_argument('--indices',type=int,default=7)
    args=p.parse_args()
    from scripts.canonical_profile_gate import canonical_pairs, canonical_rule_source, canonical_rule_hash
    from puzzle_generators import runner
    from instruction_table_probe import analyze, predict, MATRICES
    gen=importlib.import_module('puzzle_generators.per_puzzle.72dbce4d594b.generator')
    assert Path(gen.__file__).resolve().is_relative_to(ROOT)
    assert Path(runner.__file__).resolve().is_relative_to(ROOT)
    rule_hash=canonical_rule_hash(gen.TASK_ID)
    if rule_hash != gen.RULE_HASH:
        raise ValueError(f'Rule pin mismatch: {rule_hash} != {gen.RULE_HASH}')
    bridge,name=runner._open_bridge_with_rule(runner.wrap_rule(canonical_rule_source(gen.TASK_ID)))
    rows=[]
    failures=[]
    started=time.perf_counter()
    table=('identity','rot90','rot180','flip_lr')
    def check(grid, label, expected=None):
        actual=runner._apply_rule(bridge,name,grid)
        mirror=gen.rule_mirror(grid)
        code=sum(v==3 for row in grid for v in row)
        independent=predict(grid,MATRICES[table[code-1]])
        ok=actual==mirror==independent and (expected is None or actual==expected)
        rows.append({'case':label,'passed':ok,
                     'input_sha256':hashlib.sha256(json.dumps(grid,separators=(',',':')).encode()).hexdigest()})
        if not ok:
            failures.append({'case':label,'input':grid,'racket':actual,'mirror':mirror,
                             'independent':independent,'expected':expected})
        return actual
    try:
        canonical=canonical_pairs(gen.TASK_ID)
        for i,pair in enumerate(canonical):
            check(pair['input'],f'canonical:{i}',pair['output'])
        baseline=json.loads(Path('baseline_ambiguous_lesson.json').read_text())
        for i,pair in enumerate(baseline['demos']+[baseline['query']]):
            check(pair['input'],f'baseline_counterexample:{i}',pair['output'])
        for band in ('easy','medium','hard'):
            for seed in range(args.seeds):
                for index in range(args.indices):
                    check(gen.generate(seed,index,difficulty=band),f'{band}:{seed}:{index}')
        for profile in gen._SIZE_PROFILES:
            for rank in (1,2,3):
                for transform in (1,2,3,4):
                    g=gen.generate(7001,17,grid_h=11,grid_w=12,rank=rank,
                                   transform=transform,size_profile=profile,
                                   red_layout='scattered',green_layout='scattered',target_zone='bottom_right')
                    check(g,f'override:{profile}:{rank}:{transform}')
    finally:
        bridge.shutdown()
    result={'schema':'relocated-reference-parity-v1','runtime_cwd':str(ROOT),'python':sys.version,
            'generator_module':str(Path(gen.__file__).resolve()),
            'runner_module':str(Path(runner.__file__).resolve()),
            'generator_sha256':hashlib.sha256(Path(gen.__file__).read_bytes()).hexdigest(),
            'canonical_rule_hash':rule_hash,'cases':len(rows),'failures':failures,
            'passed':not failures,'elapsed_seconds':time.perf_counter()-started,'results':rows}
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ('results','failures')},indent=2))
    return 0 if result['passed'] else 1

if __name__=='__main__':
    raise SystemExit(main())
