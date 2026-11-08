#!/usr/bin/env python3
"""Emit small, source-bound Racket-verified counterexamples for this assignment."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
from review_probe import ReviewContext, components
from audit_targets import snap_first_cell_to_anchor, recolor_eight_connected


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out-dir', type=Path, required=True)
    args = parser.parse_args()
    args.out_dir.mkdir(parents=True, exist_ok=True)
    command = {'cwd': 'repo', 'argv': ['python3', 'generators/05d60f5e74c6/workspace/counterexamples.py', *sys.argv[1:]]}
    with ReviewContext(['05d60f5e74c6', '24d677c76640', 'e99db35d533d']) as context:
        def save(name, task, body):
            data = {'schema': 'arcpuzzles-exact-counterexample-v1', 'source': context.identity[task],
                    'command': command, 'runtime_directory': str(context.runtime), **body}
            (args.out_dir / name).write_text(json.dumps(data, indent=2) + '\n')

        gen = context.modules['05d60f5e74c6']
        grid = gen.generate(0, 1, difficulty='easy')
        ref = context.reference('05d60f5e74c6', grid)
        rival = gen.CANONICAL_SHORTCUTS['all_component_bbox_corners'](grid)
        assert not gen.self_check(grid) and ref != rival
        save('question_counterexample.json', '05d60f5e74c6', {
            'seed': 0, 'sample_index': 1, 'difficulty': 'easy', 'overrides': {}, 'input': grid,
            'racket_output': ref, 'rival_output': rival, 'rival_name': 'all_component_bbox_corners',
            'validator_errors': [], 'in_documented_generator_domain': True})

        gen = context.modules['24d677c76640']
        pairs = [{'input': gen.generate(20, i, difficulty='easy')} for i in range(4)]
        for p in pairs:
            p['output'] = context.reference('24d677c76640', p['input'])
        assert all(snap_first_cell_to_anchor(p['input']) == p['output'] for p in pairs[:3])
        query = pairs[3]
        rival = snap_first_cell_to_anchor(query['input'])
        assert rival != query['output'] and not gen.self_check(query['input'])
        save('audit_24d677c76640_counterexample.json', '24d677c76640', {
            'seed': 20, 'sample_index': 3, 'difficulty': 'easy', 'overrides': {}, 'input': query['input'],
            'racket_output': query['output'], 'rival_output': rival, 'rival_name': 'first_cell_to_anchor',
            'demos': pairs[:3], 'validator_errors': [], 'in_documented_generator_domain': True})

        gen = context.modules['e99db35d533d']
        grid = [[0]*9 for _ in range(8)]
        for r, c in ((0, 0), (1, 0), (2, 1), (2, 2)):
            grid[r][c] = 1
        ref = context.reference('e99db35d533d', grid)
        rival = recolor_eight_connected(grid)
        assert ref != rival
        save('audit_e99db35d533d_diagonal.json', 'e99db35d533d', {
            'seed': None, 'sample_index': None, 'overrides': None, 'input': grid,
            'racket_output': ref, 'rival_output': rival, 'rival_name': 'eight_connected_top_recolor',
            'validator_available': False, 'validator_errors': None, 'in_documented_generator_domain': False,
            'domain_note': 'Within the written 4-component rule; outside the generator’s explicit 8-halo separation.'})

        overrides = {'n_top': 2, 'n_interior': 2}
        grid = gen.generate(67, 0, difficulty='easy', **overrides)
        obj = components(grid)
        actual = {'n_top': sum(o['bbox'][0] == 0 for o in obj), 'n_interior': sum(o['bbox'][0] != 0 for o in obj)}
        assert actual != overrides, 'Forced count defect no longer reproduces'
        ref = context.reference('e99db35d533d', grid)
        save('audit_e99db35d533d_forced_counts.json', 'e99db35d533d', {
            'seed': 67, 'sample_index': 0, 'difficulty': 'easy', 'overrides': overrides,
            'actual_counts': actual, 'input': grid, 'racket_output': ref,
            'rival_output': recolor_eight_connected(grid), 'rival_name': 'eight_connected_top_recolor',
            'validator_available': False, 'validator_errors': None, 'in_documented_generator_domain': True,
            'finding': 'Exact count override is not realized. Rival and reference agree here; this is a placement defect, not label disagreement.'})
    print('Wrote and independently verified four exact counterexamples.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
