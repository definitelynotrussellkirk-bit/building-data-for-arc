from __future__ import annotations

from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import types

ROOT = Path('/mnt/data/arcpuzzles_review_013552/WORK/repo')
scripts_pkg = types.ModuleType('scripts')
scripts_pkg.__path__ = [str(ROOT / 'shared' / 'tools')]
sys.modules.setdefault('scripts', scripts_pkg)
from puzzle_generators import runner


def load(tid: str):
    path = ROOT / 'generators' / tid / 'generator.py'
    spec = importlib.util.spec_from_file_location(f'audit_{tid}', path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(mod)
    return mod, path


def normalize_grid(grid):
    if isinstance(grid, list) and grid and isinstance(grid[0], str):
        return [[int(cell) for cell in row] for row in grid]
    return grid


def canonical_row(tid: str):
    for line in (ROOT / 'shared/data/canonical/puzzles.jsonl').read_text().splitlines():
        row = json.loads(line)
        if row.get('task_id') == tid:
            return row
    raise KeyError(tid)


def racket_output(tid: str, grid):
    rule_source = canonical_row(tid)['program_solution']
    bridge, fn_name = runner._open_bridge_with_rule(runner.wrap_rule(rule_source))
    try:
        return runner._apply_rule(bridge, fn_name, grid)
    finally:
        bridge.shutdown()


# ------------------------------------------------------------------ 703
m703, p703 = load('703a842c8e24')
r703 = canonical_row('703a842c8e24')

def rotate(body, k):
    k %= len(body)
    return list(body) if not k else list(body[-k:]) + list(body[:-k])

def zero_first_body_rival(grid):
    out = []
    for row in grid:
        body = list(row[1:])
        body[0] = 0
        out.append([row[0], *rotate(body, row[0])])
    return out

canonical_703 = [
    {'input': normalize_grid(p['input']), 'output': normalize_grid(p['output'])}
    for p in [*r703['train'], *r703['test']]
]
canonical_fit_703 = all(zero_first_body_rival(p['input']) == p['output'] for p in canonical_703)

sampled_703 = []
for band in ('easy', 'medium', 'hard'):
    for sample_index in range(400):
        grid = m703.generate(10000 + sample_index * 37, sample_index, difficulty=band)
        sampled_703.append(grid)
assert all(row[1] == 0 for grid in sampled_703 for row in grid)
assert all(zero_first_body_rival(grid) == m703.rule_mirror(grid) for grid in sampled_703)

witness_703 = [
    [2, 5, 0, 6, 0, 0],
    [1, 0, 7, 0, 0, 8],
    [3, 0, 0, 4, 0, 9],
]
intended_703 = m703.rule_mirror(witness_703)
rival_703 = zero_first_body_rival(witness_703)
racket_703 = racket_output('703a842c8e24', witness_703)
assert m703.self_check(witness_703) == []
assert intended_703 == racket_703
assert rival_703 != intended_703

out703 = {
    'schema': 'arcpuzzles-audit-reproduction-v1',
    'task_id': '703a842c8e24',
    'generator_sha256': hashlib.sha256(p703.read_bytes()).hexdigest(),
    'finding': 'first_body_cell_is_never_foreground',
    'shortcut': 'Force the first body cell of every row to zero before applying the otherwise-correct cyclic rotation.',
    'canonical_pairs_checked': len(canonical_703),
    'shortcut_fits_all_canonical_pairs': canonical_fit_703,
    'generated_grids_checked': len(sampled_703),
    'generated_rows_checked': sum(len(g) for g in sampled_703),
    'all_generated_first_body_cells_zero': True,
    'shortcut_fits_all_generated_grids_checked': True,
    'self_check_errors_on_counterexample': m703.self_check(witness_703),
    'counterexample_input': witness_703,
    'intended_output': intended_703,
    'live_racket_output': racket_703,
    'shortcut_output': rival_703,
    'generator_emits_counterexample_class': False,
}
Path('/mnt/data/arcpuzzles_review_013552/WORK/checks/audit/703a842c8e24/first-body-padding-shortcut.json').write_text(json.dumps(out703, indent=2) + '\n')


# ------------------------------------------------------------------ 9bf
m9, p9 = load('9bfbec04496c')
r9 = canonical_row('9bfbec04496c')

def parse_mosaic(grid):
    h, w = len(grid), len(grid[0])
    sep_rows = [r for r in range(h) if len(set(grid[r])) == 1 and grid[r][0] != 0]
    sep_cols = [c for c in range(w) if len({grid[r][c] for r in range(h)}) == 1 and grid[0][c] != 0]
    tile_h, tile_w = sep_rows[0], sep_cols[0]
    row_starts = [0] + [r + 1 for r in sep_rows]
    col_starts = [0] + [c + 1 for c in sep_cols]
    values = [
        [[grid[rs + r][cs + c] for rs in row_starts for cs in col_starts]
         for c in range(tile_w)]
        for r in range(tile_h)
    ]
    return values

def intended_consensus(grid):
    values = parse_mosaic(grid)
    return [[vals[0] if len(set(vals)) == 1 else 1 for vals in row] for row in values]

def exactly_one_outlier_rival(grid):
    values = parse_mosaic(grid)
    out = []
    for row in values:
        out_row = []
        for vals in row:
            counts = Counter(vals)
            if len(counts) == 1:
                out_row.append(vals[0])
            elif sorted(counts.values()) == [1, 8]:
                out_row.append(1)
            else:
                # Shortcut treats broader disagreement as unsupported/no mutation.
                out_row.append(counts.most_common(1)[0][0])
        out.append(out_row)
    return out

canonical_9 = list(r9['train'])
assert all(exactly_one_outlier_rival(p['input']) == p['output'] for p in canonical_9)

sampled_9 = []
for sample_index in range(1200):
    grid = m9.generate(20000 + sample_index * 29, sample_index)
    sampled_9.append(grid)
    assert exactly_one_outlier_rival(grid) == intended_consensus(grid)

base = [[7, 0], [8, 8]]
sep = 3
witness_9 = [[0] * 8 for _ in range(8)]
for br in range(3):
    for bc in range(3):
        ro, co = br * 3, bc * 3
        for r in range(2):
            for c in range(2):
                witness_9[ro + r][co + c] = base[r][c]
        if bc < 2:
            for r in range(2):
                witness_9[ro + r][co + 2] = sep
    if br < 2:
        for c in range(8):
            witness_9[br * 3 + 2][c] = sep
# Two outlier tiles at the same local coordinate: a lawful disagreement the
# production generator cannot construct because local_cells are distinct and
# each selected coordinate is mutated in exactly one tile.
witness_9[0][3] = 6       # top-middle tile, local (0,0)
witness_9[6][6] = 6       # bottom-right tile, local (0,0)
intended_9 = intended_consensus(witness_9)
rival_9 = exactly_one_outlier_rival(witness_9)
racket_9 = racket_output('9bfbec04496c', witness_9)
assert m9.self_check(witness_9) == []
assert intended_9 == racket_9
assert rival_9 != intended_9

out9 = {
    'schema': 'arcpuzzles-audit-reproduction-v1',
    'task_id': '9bfbec04496c',
    'generator_sha256': hashlib.sha256(p9.read_bytes()).hexdigest(),
    'finding': 'only_exactly_one_outlier_per_disagreement_coordinate',
    'shortcut': 'Mark blue only for an 8-to-1 tile split; on broader disagreement, return the modal value.',
    'canonical_train_pairs_checked': len(canonical_9),
    'shortcut_fits_all_canonical_train_pairs': True,
    'generated_grids_checked': len(sampled_9),
    'shortcut_fits_all_generated_grids_checked': True,
    'self_check_errors_on_counterexample': m9.self_check(witness_9),
    'counterexample_input': witness_9,
    'tile_value_counts_at_local_0_0': dict(Counter(parse_mosaic(witness_9)[0][0])),
    'intended_output': intended_9,
    'live_racket_output': racket_9,
    'shortcut_output': rival_9,
    'generator_emits_counterexample_class': False,
}
Path('/mnt/data/arcpuzzles_review_013552/WORK/checks/audit/9bfbec04496c/two-outlier-shortcut.json').write_text(json.dumps(out9, indent=2) + '\n')

print(json.dumps({'703a842c8e24': out703, '9bfbec04496c': out9}, indent=2))
