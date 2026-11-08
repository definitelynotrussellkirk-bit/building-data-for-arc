"""Read-only task audits; run through run_with_racket.py from packet root."""
from pathlib import Path
from collections import Counter
import importlib.util
import hashlib
import json
from reviewer_support import canonical_pairs
from arcpuzzles import Catalog

ROOT = Path.cwd()
OUT = ROOT.parent / 'checks/audit'


def load(tid):
    source = ROOT / 'generators' / tid / 'generator.py'
    spec = importlib.util.spec_from_file_location('audit_' + tid, source)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod, hashlib.sha256(source.read_bytes()).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def largest_crop(gen, grid):
    objects = [o for o in gen._components(grid) if (0, 0) not in o['cells']]
    selected = max(objects, key=lambda o: len(o['cells']))
    r0, c0, r1, c1 = gen._bbox(selected['cells'])
    return [row[c0:c1 + 1] for row in grid[r0:r1 + 1]]


def main():
    cat = Catalog(ROOT)
    tid = 'e2eab62ba331'; gen, digest = load(tid)
    counts = Counter(); failures = []
    for band in ('easy', 'medium', 'hard'):
        for profile in gen.GENERAL_PROFILES:
            for seed in range(5):
                grid = gen.generate(42000 + seed, seed, difficulty=band, scene_profile=profile)
                errors = gen.self_check(grid, difficulty=band)
                counts['draws'] += 1; counts['valid'] += not errors
                counts['largest_matches_mirror'] += largest_crop(gen, grid) == gen.rule_mirror(grid)
                if errors: failures.append({'band':band,'profile':profile,'seed':42000+seed,'errors':errors})
    pairs = canonical_pairs(tid, root=ROOT)
    grid = [[0] * 15 for _ in range(12)]; grid[0][0] = 2
    for r in range(2, 5):
        for c in range(2, 5):
            if r in (2,4) or c in (2,4): grid[r][c] = 2
    for r in range(6,10):
        for c in range(9,13): grid[r][c] = 7
    directory = OUT / tid
    write(directory/'input.json', grid)
    write(directory/'rival.json', largest_crop(gen, grid))
    write(directory/'probe.json', {
        'task_id':tid, 'generator_sha256':digest,'rule_hash':cat.describe(tid)['rule_hash'],
        'classification':'reproduced distribution shortcut on general profiles; canonical refutes it',
        'sample_plan': {'bands':['easy','medium','hard'],'profiles':list(gen.GENERAL_PROFILES),
                        'seeds':[42000,42004],'sample_indexes':[0,4]},
        'counts':dict(counts),'failures':failures,
        'canonical_pairs':len(pairs), 'canonical_largest_fit':sum(largest_crop(gen,p['input'])==p['output'] for p in pairs),
        'witness':{'input':grid,'rival_output':largest_crop(gen,grid),'mirror_output':gen.rule_mirror(grid),
                   'validator_errors':gen.self_check(grid),'observable_profile':gen.observe_overrides(grid),
                   'generator_emits':False,'reason':'non-public distractors are only 2-cell dominoes or 3-cell Ls; witness distractor has 16 cells'},
    })
    tid = 'ea2b82cf172e'; gen,digest=load(tid);directory=OUT/tid
    calls=[]
    cases=[('medium',{'grid_h':10}),('medium',{'grid_h':25}),('medium',{'n_objects':1}),('medium',{'n_objects':9}),('easy',{'texture':'not_a_texture'}),('medium',{'unknown_axis':3})]
    for band,overrides in cases:
        entry={'seed':17,'sample_index':0,'difficulty':band,'overrides':overrides}
        try:
            grid=gen.generate(17,0,difficulty=band,**overrides)
            entry.update(returned=True,shape=[len(grid),len(grid[0])],validation_errors=gen.self_check(grid,difficulty=band))
        except Exception as exc:
            entry.update(returned=False,error_type=type(exc).__name__,error=str(exc))
        calls.append(entry)
    counts=Counter(); failures=[]
    for band in ('easy','medium','hard'):
        for i in range(20):
            grid=gen.generate(52000+i,i,difficulty=band); errors=gen.self_check(grid,difficulty=band)
            counts['draws']+=1;counts['valid']+=not errors
            if errors:failures.append({'seed':52000+i,'sample_index':i,'difficulty':band,'errors':errors})
    grid=gen.generate(17,0,difficulty='easy',texture='touching_objects')
    count=len(gen._nonzero_components(grid));rival=[[8 if r==c else 0 for c in range(count)] for r in range(count)]
    write(directory/'input.json',grid);write(directory/'rival.json',rival)
    write(directory/'probe.json',{
      'task_id':tid,'generator_sha256':digest,'rule_hash':cat.describe(tid)['rule_hash'],
      'classification':'override contract defects and optional degenerate connectivity mismatch',
      'override_calls':calls,'default_samples':{'seeds':[52000,52019],'sample_indexes':[0,19],'bands':['easy','medium','hard'],'counts':dict(counts),'failures':failures},
      'witness':{'seed':17,'sample_index':0,'difficulty':'easy','overrides':{'texture':'touching_objects'},
                 'input':grid,'rival_output':rival,'nonzero_component_count':count,
                 'validator_errors':gen.self_check(grid,difficulty='easy'),
                 'generator_emits':True,'domain':'advertised caller-opt-in degenerate, not ordinary samples'},
    })
    for tid in ('e2eab62ba331','ea2b82cf172e'):
        d=json.loads((OUT/tid/'probe.json').read_text())
        print(tid, {k:v for k,v in d.items() if k not in ('witness','sample_plan')})

if __name__=='__main__':main()
