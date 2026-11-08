#!/usr/bin/env python3
"""Bind the second-component teaching shortcut to source and Racket receipts."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from reviewer_support import load_selected_generator


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--racket', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()

    gen, source, digest = load_selected_generator('b9058b6ccb82', root=args.root)
    racket = json.loads(args.racket.read_text(encoding='utf-8'))
    seed, band = 7, 'easy'
    rows = []
    for sample_index, result in enumerate(racket['results']):
        grid = gen.generate(seed, sample_index, difficulty=band)
        assert grid == result['input']
        analysis = gen._analysis(grid)
        intended = gen.rule_mirror(grid)
        rival = gen._record_mask(analysis['components'][1])
        assert intended == result['output']
        rows.append({
            'sample_index': sample_index,
            'profile': gen.schedule_profile(seed, sample_index, band),
            'input': grid,
            'racket_output': result['output'],
            'second_component_rival': rival,
            'outlier_index': analysis['outlier']['index'],
            'rival_matches_racket': rival == result['output'],
            'input_sha256': result['input_sha256'],
            'output_sha256': result['output_sha256'],
        })

    demos, query = [0, 2, 3], 1
    assert all(rows[index]['rival_matches_racket'] for index in demos)
    assert not rows[query]['rival_matches_racket']
    payload = {
        'schema': 'arc-review-audit-counterexample-v1',
        'task_id': 'b9058b6ccb82',
        'source_path': str(source),
        'generator_sha256': digest,
        'executed_rule_hash': racket['executed_rule_hash'],
        'rule_hash_matches_catalog': racket['rule_hash_matches_catalog'],
        'finding': 'undeclared second-component shortcut survives one four-pair query rotation',
        'rival_definition': 'sort colored components by (top-left cell, color), then return normalized component index 1',
        'command': [
            'python3',
            'checks/audit/b9058b6ccb82/reproduce_second_component.py',
            '--root', 'repo',
            '--racket', 'checks/audit/b9058b6ccb82/racket.json',
            '--out', 'checks/audit/b9058b6ccb82/second-component-shortcut-counterexample.json',
        ],
        'cwd': '.',
        'lesson': {
            'seed': seed,
            'difficulty': band,
            'demo_sample_indices': demos,
            'query_sample_index': query,
            'pairs': rows,
        },
        'checked_with': {
            'python_rule_mirror_matches_racket_on_all_pairs': True,
            'racket_receipt_file': 'racket.json',
            'racket_reference': racket['reference'],
            'generator_domain_all_valid': all(
                result['generator_domain']['status'] == 'valid'
                for result in racket['results']
            ),
        },
        'impact': 'Holding out profile 1 leaves three profile-0/2 demonstrations where component index 1 is always the target, but the profile-1 query target is component index 2.',
    }
    args.out.write_text(json.dumps(payload, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'generator_sha256': digest, 'matches': [r['rival_matches_racket'] for r in rows]}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
