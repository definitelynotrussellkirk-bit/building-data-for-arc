#!/usr/bin/env python3
"""Source-bound audit of canonical coverage, exact controls and branch teaching."""
import argparse
import hashlib
import json
from pathlib import Path

from arcpuzzles import Catalog
from reviewer_support import canonical_pairs, find_root, load_selected_generator

TASK = 'd03138ff3d48'


def always_original_left(grid):
    return [row + [8 if x == 0 else 0 for x in reversed(row)] for row in grid]


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--out', type=Path, required=True)
    args = p.parse_args()
    if args.out.exists():
        raise SystemExit('Choose a new output file')
    root = find_root(__file__)
    module, source, source_sha = load_selected_generator(TASK, root=root)
    pairs = canonical_pairs(TASK, root=root)
    canonical = [{'index': i, 'shape': [len(pair['input']), len(pair['input'][0])],
                  'self_check': module.self_check(pair['input'])}
                 for i, pair in enumerate(pairs)]
    override_cases = []
    for band, overrides in [('easy', {'grid_h': 8}), ('hard', {'grid_w': 8}),
                            ('medium', {'palette_size': 7, 'palette_kind': 'cool'}),
                            ('medium', {'col0_has_nonzero': 'false'})]:
        try:
            grid = module.generate(0, 0, difficulty=band, **overrides)
            result = {'status': 'accepted', 'input': grid,
                      'observed_col0_has_nonzero': any(row[0] != 0 for row in grid),
                      'foreground_palette_size': len({x for row in grid for x in row if x})}
        except Exception as exc:
            result = {'status': 'rejected', 'error': f'{type(exc).__name__}: {exc}'}
        override_cases.append({'seed': 0, 'sample_index': 0, 'difficulty': band,
                               'overrides': overrides, **result})
    malformed = []
    for name, grid in [('ragged', [[0, 1, 2], [0, 0], [0, 0, 0]]),
                       ('negative_color', [[0, -1, 2], [0, 0, 0], [0, 0, 0]]),
                       ('boolean_color', [[0, True, 2], [0, 0, 0], [0, 0, 0]])]:
        malformed.append({'name': name, 'input': grid, 'self_check': module.self_check(grid)})
    witness = None
    searched = 0
    for seed in range(200):
        grids = [module.generate(seed, i, difficulty='medium') for i in range(4)]
        states = [any(row[0] != 0 for row in grid) for grid in grids]
        searched += 1
        if states == [False, False, False, True]:
            witness = {'seed': seed, 'sample_indices': [0, 1, 2, 3],
                       'difficulty': 'medium', 'branch_states': states, 'inputs': grids}
            break
    if witness is None:
        raise RuntimeError('No branch ambiguity witness in bounded search')
    applied = Catalog(root).apply(TASK, witness['inputs'], timeout=120)
    if not applied['rule_hash_matches_catalog']:
        raise RuntimeError('Rule authority changed')
    labeled = []
    for row in applied['results']:
        if row['output'] is None:
            raise RuntimeError('Reference execution did not return an output')
        labeled.append({'input': row['input'], 'output': row['output']})
    fit = [always_original_left(pair['input']) == pair['output'] for pair in labeled]
    assert fit == [True, True, True, False], fit
    witness.update(train=labeled[:3], query=labeled[3], rival='always_original_left',
                   rival_fits_demonstrations=True, rival_query=always_original_left(labeled[3]['input']),
                   query_differs=True, normal_self_checks=[module.self_check(g) for g in witness.pop('inputs')])
    assert all(not errors for errors in witness['normal_self_checks'])
    report = {'schema': 'arcpuzzles-task-audit-v1', 'task_id': TASK,
              'generator_sha256': source_sha, 'source': str(source.relative_to(root)),
              'executed_rule_hash': applied['executed_rule_hash'],
              'rule_text_sha256': applied['rule_text_sha256'],
              'canonical_inputs_checked': len(canonical),
              'canonical_inputs_rejected': sum(bool(row['self_check']) for row in canonical),
              'canonical': canonical, 'override_cases': override_cases,
              'malformed_inputs': malformed, 'branch_search_seeds_checked': searched,
              'branch_witness': witness,
              'reference_execution': applied,
              'limits': 'One bounded production-shaped 3-demo/1-query ambiguity witness; no audit-source repair or model evaluation.'}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'out': str(args.out), 'generator_sha256': source_sha,
                      'canonical_rejected': report['canonical_inputs_rejected'],
                      'canonical_total': len(canonical), 'branch_witness_seed': witness['seed'],
                      'rival_fits': fit, 'malformed_accepted': sum(not row['self_check'] for row in malformed)}, indent=2))


if __name__ == '__main__':
    main()
