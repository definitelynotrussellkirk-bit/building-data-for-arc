"""Findings-only audit: source-bound ordinary parity and exact-control probes."""
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
from arcpuzzles import Catalog


def write(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + '\n')


def load(cat, task):
    path = cat.root / 'generators' / task / 'generator.py'
    spec = importlib.util.spec_from_file_location('audit_' + task, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod, hashlib.sha256(path.read_bytes()).hexdigest()


def normalize(grid):
    return [[int(c) for c in row] for row in grid]


def mode_rival(grid):
    vals = [v for row in grid for v in row if v]
    if not vals:
        return [[0]]
    color = Counter(vals).most_common(1)[0][0]
    return [[color] * len(vals)]


def overwrite_rival(grid):
    points = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 8]
    out = [row[:] for row in grid]
    if not points:
        return out
    cols = {c for _, c in points}
    vert = len(cols) == 1
    axis = points[0][1 if vert else 0]
    for r, row in enumerate(grid):
        for c, val in enumerate(row):
            rr, cc = (r, 2 * axis - c) if vert else (2 * axis - r, c)
            if val not in (0, 8) and 0 <= rr < len(grid) and 0 <= cc < len(grid[0]):
                out[rr][cc] = val
    return out


cat = Catalog()
root = cat.root.parent / 'checks' / 'audit'
canonical = {}
for line in (cat.root / 'shared/data/canonical/puzzles.jsonl').open():
    row = json.loads(line)
    if row.get('task_id') in ('0a54983176e5', 'c74ecc35f54f'):
        canonical[row['task_id']] = row

for task in ('0a54983176e5', 'c74ecc35f54f'):
    mod, sha = load(cat, task)
    outdir = root / task
    outdir.mkdir(exist_ok=True)
    coords, grids = [], []
    for band in ('easy', 'medium', 'hard'):
        for index in range(20):
            grids.append(mod.generate(18001, index, difficulty=band))
            coords.append({'difficulty': band, 'seed': 18001, 'sample_index': index, 'overrides': {}})
    receipt = cat.apply(task, grids, timeout=180)
    receipt['coordinates'] = coords
    write(outdir / 'ordinary-racket.json', receipt)
    desired = mod._mirror if task == '0a54983176e5' else lambda grid: [[next(v for row in grid for v in row if v)] * sum(v != 0 for row in grid for v in row)]
    rival = overwrite_rival if task == '0a54983176e5' else mode_rival
    pairs = canonical[task].get('train', []) + canonical[task].get('test', [])
    report = {
        'task_id': task, 'generator_sha256': sha, 'rule_hash': receipt['executed_rule_hash'],
        'rule_text_sha256': receipt['rule_text_sha256'], 'cwd': str(Path.cwd()),
        'sampling': {'seed': 18001, 'indices': '0..19 inclusive per band', 'bands': ['easy', 'medium', 'hard']},
        'ordinary_draws': 60, 'ordinary_unique_inputs': len({json.dumps(g) for g in grids}),
        'ordinary_validator_passes': sum(not mod.self_check(g) for g in grids),
        'ordinary_reference_parity': sum(a['output'] == desired(g) and not a['error'] for g, a in zip(grids, receipt['results'])),
        'rival': 'overwrite_existing_reflections' if task == '0a54983176e5' else 'most_frequent_color',
        'rival_canonical_fit': sum(rival(normalize(p['input'])) == normalize(p['output']) for p in pairs),
        'canonical_pairs': len(pairs),
        'ordinary_rival_disagreements': sum(rival(g) != a['output'] for g, a in zip(grids, receipt['results'])),
    }
    if task == '0a54983176e5':
        boundary = []
        for band in ('easy', 'medium', 'hard'):
            for name, value in [('grid_h', 5), ('grid_h', 14), ('grid_w', 7), ('grid_w', 16)]:
                row = {'seed': 18001, 'sample_index': 0, 'difficulty': band, 'overrides': {name: value}}
                try:
                    g = mod.generate(18001, 0, difficulty=band, **{name: value})
                    row.update(status='generated', shape=[len(g), len(g[0])], validator_errors=mod.self_check(g))
                except Exception as exc:
                    row.update(status='error', error=f'{type(exc).__name__}: {exc}')
                boundary.append(row)
        report['declared_boundary_controls'] = boundary
        witness = next(i for i, (g, a) in enumerate(zip(grids, receipt['results'])) if rival(g) != a['output'])
        write(outdir / 'input.json', grids[witness])
        write(outdir / 'counterexample.json', {**coords[witness], 'task_id': task, 'generator_sha256': sha,
              'rule_hash': receipt['executed_rule_hash'], 'rule_text_sha256': receipt['rule_text_sha256'],
              'input': grids[witness], 'actual_racket_output': receipt['results'][witness]['output'],
              'rival_output': rival(grids[witness]), 'validator_errors': mod.self_check(grids[witness]),
              'domain': 'ordinary generated input; refutes a shortcut already covered by this generator, not a new semantic defect'})
    else:
        cases = []
        requested = {'first_color': 9}
        for index in range(20):
            g = mod.generate(18502, index, difficulty='medium', **requested)
            first = next(v for row in g for v in row if v)
            if first != 9:
                cases.append({'kind': 'ignored_first_color', 'seed': 18502, 'sample_index': index, 'difficulty': 'medium',
                              'overrides': requested, 'observed_first_color': first, 'input': g,
                              'validator_errors': mod.self_check(g), 'in_documented_domain': True,
                              'rival_output': [[9] * sum(v != 0 for row in g for v in row)]})
                break
        g = mod.generate(18502, 0, difficulty='medium', texture='monocolor_grid')
        cases.append({'kind': 'accepted_oversized_output', 'seed': 18502, 'sample_index': 0, 'difficulty': 'medium',
                      'overrides': {'texture': 'monocolor_grid'}, 'input': g, 'validator_errors': mod.self_check(g),
                      'nonzero_count': sum(v != 0 for row in g for v in row), 'in_documented_domain': True,
                      'rival_output': [[5] * 30], 'rival_note': '30-column truncation is only a diagnostic contrast, not the correct task rule'})
        report['generated_counterexamples'] = cases
        write(outdir / 'input.json', [c['input'] for c in cases])
        write(outdir / 'counterexamples.json', {'task_id': task, 'generator_sha256': sha,
              'rule_hash': receipt['executed_rule_hash'], 'rule_text_sha256': receipt['rule_text_sha256'], 'cases': cases})
    write(outdir / 'report.json', report)
    print(task, 'ordinary parity', report['ordinary_reference_parity'], '/60; validator', report['ordinary_validator_passes'], '/60', flush=True)
