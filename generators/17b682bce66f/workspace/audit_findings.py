"""Findings-only probes for this packet's two immutable audit targets.

Run from packet root after staging both audit runtimes with review_probe.py.
No audit target is patched.  Outputs include input grids for counterexamples.
"""
import copy
import hashlib
import importlib
import json
from pathlib import Path
import sys


def load(runtime, task):
    sys.path.insert(0, str(Path(runtime).resolve()))
    return importlib.import_module(f'puzzle_generators.per_puzzle.{task}.generator')


def sha(module):
    return hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest()


def canon(task):
    for line in Path('repo/shared/data/canonical/puzzles.jsonl').open():
        row = json.loads(line)
        if row.get('task_id') == task:
            pairs = [*row['train']]
            pairs.extend([row['test']] if isinstance(row['test'], dict) else row['test'])
            return [{k: [[int(v) for v in r] for r in pair[k]] for k in ('input', 'output')}
                    for pair in pairs]
    raise ValueError(task)


def wall_shortcut(g, module):
    """Deliberately wrong general rule: closed-to-top/bottom implies paint."""
    out = copy.deepcopy(g)
    for cells in module._zero_components(g):
        rows = [r for r, c in cells]
        cols = [c for r, c in cells]
        if min(rows) == 0 or max(rows) == len(g)-1:
            continue
        if min(cols) == max(cols) == 0 and min(rows) < max(rows):
            continue
        for r, c in cells:
            out[r][c] = 4
    return out


def main():
    report = {}
    frames = load('.review/audit_frames_runtime', 'f2dbde875127')
    pairs = canon('f2dbde875127')
    x = {'source_sha256': sha(frames), 'canonical_pairs': len(pairs),
         'canonical_self_check': [], 'ignored_overrides': [], 'random_failures': [],
         'census': {'per_band': 100, 'seeds': [0, 99], 'sample_index': '17*seed+1'}}
    for i, pair in enumerate(pairs):
        errors = frames.self_check(pair['input'])
        x['canonical_self_check'].append({'pair_index': i, 'errors': errors, 'input': pair['input']})
    for kwargs in ({'grid_h': 9, 'grid_w': 9}, {'n_frames': 3}, {'key': 3}, {'unknown_audit_axis': 1}):
        g = frames.generate(0, 1, difficulty='easy', **kwargs)
        original = frames.generate(0, 1, difficulty='easy')
        comps = frames._color1_components(g)
        keys = []
        for cells in comps:
            r0 = min(r for r,c in cells); c0 = min(c for r,c in cells); c1 = max(c for r,c in cells)
            keys.extend(g[r0-1][c] for c in range(c0,c1+1) if g[r0-1][c] in (2,3,4,5))
        x['ignored_overrides'].append({'seed':0,'sample_index':1,'difficulty':'easy','overrides':kwargs,
                                       'observed_dimensions':[len(g),len(g[0])], 'observed_n_frames':len(comps),
                                       'keys':keys,'same_as_default':g==original,'input':g})
    for band in ('easy','medium','hard'):
        for seed in range(100):
            try:
                grid = frames.generate(seed,17*seed+1,difficulty=band)
                errs = frames.self_check(grid,difficulty=band)
                if errs:
                    x['random_failures'].append({'band':band,'seed':seed,'errors':errs,'input':grid})
            except Exception as exc:
                x['random_failures'].append({'band':band,'seed':seed,'error':str(exc)})
    report['f2dbde875127'] = x
    # Force the second module to load from its own staged package path.
    # Namespace package __path__ from the first runtime can otherwise hide it.
    for name in list(sys.modules):
        if name == 'puzzle_generators' or name.startswith('puzzle_generators.'):
            del sys.modules[name]
    walls = load('.review/audit_walls_runtime', '5f9a2df57599')
    pairs = canon('5f9a2df57599')
    y = {'source_sha256':sha(walls), 'canonical_pairs':len(pairs),
         'canonical_self_check':[], 'canonical_mirror_mismatches':[],
         'random_failures':[], 'census':{'per_band':100,'seeds':[0,99],'sample_index':'17*seed+1'},
         'general_draws':0, 'general_solid_top_row':0, 'shortcut_agreements':0,
         'shortcut_disagreements':0, 'first_shortcut_counterexample':None}
    for i,pair in enumerate(pairs):
        y['canonical_self_check'].append({'pair_index':i,'errors':walls.self_check(pair['input'])})
        if walls.rule_mirror(pair['input']) != pair['output']:
            y['canonical_mirror_mismatches'].append(i)
    for band in ('easy','medium','hard'):
        for seed in range(100):
            try:
                grid = walls.generate(seed,17*seed+1,difficulty=band)
                errs = walls.self_check(grid)
                if errs:
                    y['random_failures'].append({'band':band,'seed':seed,'errors':errs,'input':grid})
                profile = walls.observe_overrides(grid)['scene_profile']
                if profile in walls.GENERAL_PROFILES:
                    y['general_draws'] += 1
                    y['general_solid_top_row'] += all(v==5 for v in grid[0])
                expected = walls.rule_mirror(grid)
                rival = wall_shortcut(grid,walls)
                if rival == expected:
                    y['shortcut_agreements'] += 1
                else:
                    y['shortcut_disagreements'] += 1
                    if y['first_shortcut_counterexample'] is None:
                        y['first_shortcut_counterexample'] = {'band':band,'seed':seed,'sample_index':17*seed+1,
                                                             'input':grid,'mirror':expected,'rival':rival}
            except Exception as exc:
                y['random_failures'].append({'band':band,'seed':seed,'error':str(exc)})
    report['5f9a2df57599'] = y
    p=Path('checks/audit_findings.json')
    with p.open('x') as f:
        json.dump(report,f,indent=2); f.write('\n')
    print(p)


if __name__ == '__main__':
    main()
