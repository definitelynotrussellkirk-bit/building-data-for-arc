#!/usr/bin/env python3
"""Rebuild the review's main rule-parity and assigned audit counterexamples.

A review-time tool only: loads generators and canonical rules. Do not run during
an answer-masked solve. Output files are inputs to reference_probe.py.
"""
import argparse
from collections import Counter
import importlib.util
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from reference_probe import load_source, canonical_pairs


def dump(path, cases):
    if path.exists():
        raise ValueError(f'refusing to overwrite {path}')
    path.write_text(json.dumps({'cases': cases}, indent=2)+'\n')


def main(root, out):
    out.mkdir(parents=True, exist_ok=True)
    gen, rule, rows, identity = load_source(root, '3ab9aab86992')
    main_cases = []
    # 600 distinct seed/band requests; repeated actual inputs separately counted by the runner.
    for band in ('easy', 'medium', 'hard'):
        for seed in range(200):
            grid = gen.generate(seed, 0, difficulty=band)
            main_cases.append({'id': f'{band}-{seed}', 'seed': seed, 'sample_index': 0,
                               'difficulty': band, 'expected_output': gen.rule_mirror(grid),
                               'documented_domain': True})
    # Explicit requested cardinality, repeated colors, border/interlocking positions.
    for seed in range(100):
        overrides = {'canvas_size': 5, 'n_corners': 4, 'palette_size': 1}
        grid = gen.generate(seed, 0, difficulty='easy', **overrides)
        main_cases.append({'id': f'dense-repeat-{seed}', 'seed': seed, 'sample_index': 0,
                           'difficulty': 'easy', 'overrides': overrides,
                           'expected_output': gen.rule_mirror(grid), 'documented_domain': True})
    dump(out/'main-parity-cases.json', main_cases)
    grid = gen.generate(0, 0, canvas_size=7, bg_color=8, n_corners=1, palette_size=1)
    shortcuts = [{'id': 'missing-corners-refutes-frame-completion', 'seed': 0, 'sample_index': 0,
                  'overrides': {'canvas_size': 7, 'bg_color': 8, 'n_corners': 1, 'palette_size': 1},
                  'expected_output': gen.rule_mirror(grid),
                  'rival_output': gen.SEMANTIC_RIVALS['complete_all_corners'](grid),
                  'documented_domain': True}]
    for row in rows:
        for split, i, pair in canonical_pairs(row):
            shortcuts.append({'id': f'canonical-rival-{split}-{i}', 'input': pair['input'],
                              'expected_output': pair['output'],
                              'rival_output': gen.SEMANTIC_RIVALS['complete_all_corners'](pair['input']),
                              'documented_domain': True})
    dump(out/'main-shortcut-cases.json', shortcuts)

    # Audit A: a color-range violation accepted by both generator and validator;
    # plus the first-vs-largest ambiguity excluded by the present generator domain.
    a = '0e37f2aee589'
    agen, _, arows, _ = load_source(root, a)
    audit_a = [{'id': 'invalid-key-color-ten-is-accepted', 'seed': 0, 'sample_index': 0,
                'overrides': {'key_color': 10}, 'documented_domain': False,
                'claim': 'Invalid override should fail, and its illegal color grid should not validate.'}]
    grid = [[0]*11 for _ in range(9)]
    grid[0][0] = 4
    grid[2][2] = grid[2][3] = 4
    for r in (5, 6):
        for c in (6, 7, 8):
            grid[r][c] = 4
    audit_a.append({'id': 'first-versus-largest-key-object', 'input': grid,
                    'expected_output': [[4, 4]], 'rival_output': [[4]*3 for _ in range(2)],
                    'documented_domain': False,
                    'claim': 'Authority handles multiple key bodies; generator and validator exclude them.'})
    dump(out/'audit-0e37f2aee589-cases.json', audit_a)

    # Audit B: accepted palette pins do not affect either generated input or output.
    b = '44de940bd269'
    bgen, _, brows, _ = load_source(root, b)
    audit_b = []
    for key in ('palette_size', 'n_distinct_colors'):
        for value in (1, 8):
            audit_b.append({'id': f'ignored-{key}-{value}', 'seed': 0, 'sample_index': 0,
                            'overrides': {key: value}, 'documented_domain': True,
                            'claim': 'Pin is declared but never read by the generator.'})
    grid = [[0]*9 for _ in range(6)]
    for row in grid:
        row[4] = 5
    grid[1][1], grid[1][7], grid[3][2] = 2, 3, 6
    expected = [row[:] for row in grid]; expected[3][6] = 6
    rival = [row[:] for row in grid]
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value not in (0, 5) and 0 <= 8-c < 9:
                rival[r][8-c] = value
    audit_b.append({'id': 'occupied-mirror-preservation', 'input': grid,
                    'expected_output': expected, 'rival_output': rival,
                    'documented_domain': False,
                    'claim': 'Overwrite-all rival fits canonical train; collision branch excluded by generator.'})
    for row in brows:
        for split, i, pair in canonical_pairs(row):
            grid = pair['input']; h, w = len(grid), len(grid[0])
            axis = next(c for c in range(w) if all(grid[r][c] == 5 for r in range(h)))
            rival = [r[:] for r in grid]
            for r, row_grid in enumerate(grid):
                for c, value in enumerate(row_grid):
                    mc = 2*axis-c
                    if value not in (0, 5) and 0 <= mc < w:
                        rival[r][mc] = value
            audit_b.append({'id': f'canonical-overwrite-rival-{split}-{i}',
                            'input': grid, 'expected_output': pair['output'],
                            'rival_output': rival, 'documented_domain': True})
    dump(out/'audit-44de940bd269-cases.json', audit_b)
    print('wrote', len(main_cases), 'main parity cases plus shortcuts and both audits')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    args = p.parse_args()
    main(args.root, args.out)
