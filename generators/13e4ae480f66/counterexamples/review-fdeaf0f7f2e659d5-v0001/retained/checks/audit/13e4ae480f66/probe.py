"""Findings-only, source-bound audit. Run from packet root; never edits sources."""
from pathlib import Path
import hashlib
import importlib.util
import json
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
OUT = HERE
if len(sys.argv) > 2:
    OUT = (HERE / sys.argv[2]).resolve()
    OUT.relative_to(HERE)
    OUT.mkdir(parents=True, exist_ok=True)
PACKET = HERE.parents[2]
REPO = PACKET / 'repo'
GEN = REPO / 'generators/13e4ae480f66/generator.py'
CANONICAL = REPO / 'shared/data/base/solutions/banks/b87bafc16aa7/S4_E6__13e4ae480f66.json'
sys.path.insert(0, str(REPO / 'shared/runtime'))
spec = importlib.util.spec_from_file_location('audit_source_generator', GEN)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def write_new(name, value):
    with (OUT / name).open('x') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')


def components(grid):
    todo = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 1}
    out = []
    while todo:
        seed = todo.pop()
        obj = {seed}
        stack = [seed]
        while stack:
            r, c = stack.pop()
            for p in ((r-1, c), (r+1, c), (r, c-1), (r, c+1)):
                if p in todo:
                    todo.remove(p)
                    obj.add(p)
                    stack.append(p)
        out.append(obj)
    return out


def counts(grid):
    objs = components(grid)
    return {'left': sum(any(c == 0 for r, c in obj) for obj in objs),
            'non_left': sum(all(c != 0 for r, c in obj) for obj in objs)}


def border_rival(grid, any_border):
    out = [row[:] for row in grid]
    h, w = len(grid), len(grid[0])
    for obj in components(grid):
        hit = any((r in (0, h-1) or c in (0, w-1)) if any_border else c == 0 for r, c in obj)
        if hit:
            for r, c in obj:
                out[r][c] = 4
    return out


def prepare():
    inputs, cases = [], []
    def add(name, grid, **meta):
        inputs.append(grid)
        cases.append({'name': name, 'index': len(inputs)-1, 'counts': counts(grid),
                      'self_check': module.self_check(grid), **meta})
    for difficulty in ('easy', 'medium', 'hard'):
        for seed in (0, 1, 17, 91):
            add(f'{difficulty}_{seed}', module.generate(seed, 0, difficulty=difficulty),
                kind='production', seed=seed, sample_index=0, difficulty=difficulty, overrides={})
    base = module.generate(0, 0, difficulty='medium')
    for kind in module.PALETTE_KINDS:
        grid = module.generate(0, 0, difficulty='medium', palette_kind=kind)
        add(f'palette_{kind}', grid, kind='override', overrides={'palette_kind': kind},
            seed=0, sample_index=0, difficulty='medium', equal_to_base=(grid == base))
    for name in module.DEGENERATE_TEXTURES:
        add(name, module.generate(0, 0, texture=name), kind='degenerate', overrides={'texture': name},
            seed=0, sample_index=0, difficulty=None)
    count_override = module.generate(0, 0, difficulty='medium', n_left=3, n_interior=3)
    add('three_left_three_interior', count_override, kind='override', seed=0, sample_index=0,
        difficulty='medium', overrides={'n_left': 3, 'n_interior': 3}, equal_to_base=(count_override == base))
    # Legitimate blue components touch top/right/bottom, but never left.
    # Left and non-left components are isolated and there is a left witness too.
    grid = [[0] * 9 for _ in range(8)]
    for r, c in ((2, 0), (3, 0), (3, 1), (0, 4), (0, 5),
                 (3, 8), (4, 8), (7, 4), (7, 5)):
        grid[r][c] = 1
    add('other_border_witness', grid, kind='handmade')
    bad_color = [[2, 0], [0, 1]]
    validation = {'unexpected_color_grid': bad_color, 'unexpected_color_errors': module.self_check(bad_color),
                  'all_background_errors': module.self_check([[0, 0], [0, 0]]),
                  'ragged_errors': module.self_check([[1, 0], [0]])}
    try:
        module.generate(0, 0, grid_h=5, grid_w=5)
    except Exception as exc:
        validation['declared_5x5_override_exception'] = f'{type(exc).__name__}: {exc}'
    write_new('input.json', {'inputs': inputs})
    write_new('cases.json', {'generator_sha256': hashlib.sha256(GEN.read_bytes()).hexdigest(),
              'canonical_record_sha256': hashlib.sha256(CANONICAL.read_bytes()).hexdigest(),
              'cases': cases, 'validation': validation})
    print(f'Saved {len(inputs)} source-bound audit inputs before reference execution.')


def analyze():
    cases = json.loads((OUT / 'cases.json').read_text())
    receipt = json.loads((OUT / 'racket.json').read_text())
    assert receipt['generator_sha256'] == cases['generator_sha256']
    assert receipt['rule_hash_matches_catalog']
    measurements = []
    for case, result in zip(cases['cases'], receipt['results'], strict=True):
        grid = result['input']
        out = result['output']
        measurements.append({**case, 'racket_error': result.get('error'),
                             'matches_left_border_semantics': out == border_rival(grid, False),
                             'matches_any_border_rival': out == border_rival(grid, True)})
    write_new('analysis.json', {'source_identity': {key: receipt[key] for key in
              ('generator_sha256', 'executed_rule_hash', 'catalog_rule_hash', 'rule_text_sha256',
               'rule_file', 'reference', 'rule_hash_matches_catalog')},
              'cases': measurements, 'validation': cases['validation'],
              'all_outputs_match_left_border_semantics': all(m['matches_left_border_semantics'] for m in measurements),
              'any_border_rival_matches_all_generated_cases': all(m['matches_any_border_rival'] for m in measurements
                                                                  if m['kind'] != 'handmade')})
    print(json.dumps({'cases': len(measurements),
                      'all_outputs_match_left_border_semantics': all(m['matches_left_border_semantics'] for m in measurements),
                      'any_border_matches_generated': all(m['matches_any_border_rival'] for m in measurements if m['kind'] != 'handmade'),
                      'handmade_matches_any_border': measurements[-1]['matches_any_border_rival']}))


if __name__ == '__main__':
    {'prepare': prepare, 'analyze': analyze}[sys.argv[1]]()
