"""Bounded findings-only probes. Run through run_with_racket.py from packet root.
Prepare exact inputs; run the public arcpuzzles apply commands listed in README;
then finalize to compare authentic Racket labels with retained rival outputs.
"""
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from reviewer_support import canonical_pairs, find_root
ROOT = find_root(Path.cwd())
# The wrapper runs from repo/; canonical helpers bind to that explicit root.
BASE = ROOT.parent / 'checks' / 'audit'
def load(task):
    path = ROOT / 'generators' / task / 'generator.py'
    spec = importlib.util.spec_from_file_location('audit_' + task, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod, hashlib.sha256(path.read_bytes()).hexdigest()
def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + '\n')
def geometry_lookup(mod, grid):
    """Deliberately ignores every reference block: dimensions select a template.
    Only palette roles are read from the key, so palette permutations cannot
    refute this rival. It does not call _analyze or rule_mirror.
    """
    v = next(v for v in mod.VARIANTS.values()
             if (v.grid_h, v.grid_w) == (len(grid), len(grid[0])))
    colors = {}
    for r, c, role in v.key_roles:
        colors[role] = grid[v.key_top + r][v.key_left + c]
    out = [[0] * v.frame_w for _ in range(v.frame_h)]
    out[0][0] = out[-1][0] = out[0][-1] = out[-1][-1] = 4
    for r, c, role in v.key_roles:
        for dr in range(v.block_size):
            for dc in range(v.block_size):
                out[v.output_origin[0]+r*v.block_size+dr][v.output_origin[1]+c*v.block_size+dc] = colors[role]
    return out

def prepare():
    for task in ('95c6376a953c', 'ad41fc0cda2b'):
        mod, sha = load(task)
        pairs = canonical_pairs(task, root=ROOT, labeled_only=True)
        cases = []
        for p in pairs:
            case = {'kind':'canonical', 'variant':p['variant'], 'split':p['split'],
                    'pair_index':p['pair_index'], 'input':p['input'],
                    'canonical_output':p['output'], 'validator_errors':mod.self_check(p['input']),
                    'rival_output':None}
            if task == 'ad41fc0cda2b':
                case['rival_output'] = geometry_lookup(mod, p['input'])
            cases.append(case)
        if task == 'ad41fc0cda2b':
            for band in ('easy', 'medium', 'hard'):
                for i in range(8):
                    g = mod.generate(0, i, difficulty=band)
                    cases.append({'kind':'generated', 'seed':0, 'sample_index':i,
                                  'difficulty':band, 'overrides':{}, 'input':g,
                                  'validator_errors':mod.self_check(g),
                                  'rival_output':geometry_lookup(mod, g)})
            # The same 16x18 medium-hook scene, but consistent 2x2 references
            # instead of 3x3. This satisfies the broad written transformation.
            g = mod.generate(0, 0, difficulty='easy', scene_variant='medium_hook', palette_band='low')
            v = mod.VARIANTS['medium_hook']
            colors = {role:g[v.key_top+r][v.key_left+c] for r,c,role in v.key_roles}
            for r in range(v.frame_top, v.frame_top+v.frame_h):
                for c in range(v.frame_left, v.frame_left+v.frame_w):
                    if g[r][c] != 4: g[r][c] = 0
            roles = {(r,c):role for r,c,role in v.key_roles}
            for r,c in v.reference_cells:
                for dr in range(2):
                    for dc in range(2):
                        g[v.frame_top+v.output_origin[0]+2*r+dr][v.frame_left+v.output_origin[1]+2*c+dc] = colors[roles[(r,c)]]
            cases.append({'kind':'lawful_reference_scale_mutation', 'base_seed':0, 'base_sample_index':0,
                          'base_difficulty':'easy', 'base_overrides':{'scene_variant':'medium_hook','palette_band':'low'},
                          'mutation':'replace all 3x3 reference blocks by consistently aligned 2x2 blocks; keep dimensions, corners and key unchanged',
                          'input':g,'validator_errors':mod.self_check(g), 'rival_output':geometry_lookup(mod, g),
                          'documented_domain':'Matches broad INVARIANTS and Racket transformation; outside the deliberately fixed four-branch _analyze grammar.'})
        write(BASE/task/'input.json', {'inputs':[c['input'] for c in cases]})
        write(BASE/task/'cases.json', {'task_id':task,'generator_sha256':sha,'cases':cases})
        print(task, 'prepared',len(cases),'cases')
    mod, sha = load('2ab8c1aaa3e2')
    ov = dict(grid_h=4, grid_w=4, pairs=2, n_distinct_colors=2)
    grid = mod.generate(0,1,difficulty='easy',**ov)
    write(BASE/'2ab8c1aaa3e2'/'input.json',grid)
    write(BASE/'2ab8c1aaa3e2'/'cases.json', {'task_id':'2ab8c1aaa3e2','generator_sha256':sha,
          'seed':0,'sample_index':1,'difficulty':'easy','overrides':ov,'input':grid,
          'validator_errors':mod.self_check(grid),'rivals':{k:f(grid) for k,f in mod.CANONICAL_SHORTCUTS.items()}})
    print('main witness',grid)


def compare():
    for task in ('95c6376a953c', 'ad41fc0cda2b', '2ab8c1aaa3e2'):
        home = BASE/task
        data = json.loads((home/'cases.json').read_text())
        authority = json.loads((home/'racket.json').read_text())
        assert data['generator_sha256'] == authority['generator_sha256']
        report = {key:authority[key] for key in ('task_id','generator_sha256','executed_rule_hash','rule_text_sha256','command','cwd')}
        if 'cases' in data:
            assert len(data['cases']) == len(authority['results'])
            cases = []
            for case, result in zip(data['cases'],authority['results']):
                assert result['error'] is None and result['valid_output']
                assert case['input'] == result['input']
                record = dict(case, actual_racket_output=result['output'],
                              input_sha256=result['input_sha256'], output_sha256=result['output_sha256'])
                record['rival_agrees'] = None if case['rival_output'] is None else case['rival_output'] == result['output']
                record['canonical_agrees'] = None if 'canonical_output' not in case else case['canonical_output'] == result['output']
                cases.append(record)
            report['cases'] = cases
            report['summary'] = {kind:{'total':sum(c['kind']==kind for c in cases),
                'validator_accepted':sum(c['kind']==kind and not c['validator_errors'] for c in cases),
                'rival_agrees':sum(c['kind']==kind and c['rival_agrees'] is True for c in cases),
                'racket_matches_canonical':sum(c['kind']==kind and c['canonical_agrees'] is True for c in cases)}
                for kind in sorted({c['kind'] for c in cases})}
        else:
            result = authority['results'][0]
            assert result['error'] is None and result['input'] == data['input']
            report.update(data)
            report['actual_racket_output'] = result['output']
            report['rival_disagreements'] = {name:pred != result['output'] for name,pred in data['rivals'].items()}
            assert not data['validator_errors'] and all(report['rival_disagreements'].values())
        write(home/'comparison.json', report)
        print(task, report.get('summary',report.get('rival_disagreements')))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action',choices=['prepare','compare'])
    args = parser.parse_args()
    (prepare if args.action == 'prepare' else compare)()
