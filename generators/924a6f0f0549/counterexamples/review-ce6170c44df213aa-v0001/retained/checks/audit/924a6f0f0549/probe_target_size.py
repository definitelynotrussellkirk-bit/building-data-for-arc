#!/usr/bin/env python3
from __future__ import annotations
import argparse, json
from pathlib import Path
from reviewer_support import load_selected_generator

TASK = "924a6f0f0549"

def marker_count(grid):
    return sum(v == 1 for v in grid[0])

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    args = ap.parse_args()
    repo = Path(__file__).resolve().parents[3] / 'repo'
    gen, source_path, digest = load_selected_generator(TASK, root=repo)
    rows = []
    same = 0
    accepted = 0
    for difficulty in ('easy', 'medium', 'hard'):
        for seed in range(32):
            a = gen.generate(seed, 0, difficulty=difficulty, target_size=3)
            b = gen.generate(seed, 0, difficulty=difficulty, target_size=8)
            equal = a == b
            same += int(equal)
            errs_a = gen.self_check(a, difficulty=difficulty, meta={'overrides': {'target_size': 3}})
            errs_b = gen.self_check(b, difficulty=difficulty, meta={'overrides': {'target_size': 8}})
            accepted += int(not errs_a and not errs_b)
            rows.append({
                'difficulty': difficulty,
                'seed': seed,
                'sample_index': 0,
                'grid_equal': equal,
                'requested_a': 3,
                'requested_b': 8,
                'observed_marker_count': marker_count(a),
                'self_check_a': errs_a,
                'self_check_b': errs_b,
            })
    report = {
        'task_id': TASK,
        'generator_path': str(source_path.relative_to(repo)),
        'generator_sha256': digest,
        'probe': 'Compare target_size=3 versus target_size=8 for identical seed/sample/difficulty.',
        'seed_range_inclusive': [0, 31],
        'sample_index': 0,
        'difficulties': ['easy', 'medium', 'hard'],
        'command': ['python3', '../checks/audit/924a6f0f0549/probe_target_size.py', '--out', args.out],
        'cwd': str(Path.cwd()),
        'cases': len(rows),
        'byte_identical_pairs': same,
        'both_validator_accepted_pairs': accepted,
        'observed_marker_counts': sorted({r['observed_marker_count'] for r in rows}),
        'all_pairs_byte_identical': same == len(rows),
        'all_pairs_validator_accepted': accepted == len(rows),
        'examples': rows[:8],
        'rows': rows,
    }
    out = Path(args.out)
    if out.exists():
        raise SystemExit(f'refusing to overwrite {out}')
    out.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: report[k] for k in (
        'task_id','generator_sha256','cases','byte_identical_pairs',
        'both_validator_accepted_pairs','observed_marker_counts',
        'all_pairs_byte_identical','all_pairs_validator_accepted')}, indent=2))
    if not report['all_pairs_byte_identical'] or not report['all_pairs_validator_accepted']:
        raise SystemExit(1)

if __name__ == '__main__':
    main()
