#!/usr/bin/env python3
"""Reproduce public scalar-validation findings against one explicit source tree."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from reviewer_support import load_selected_generator


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()

    gen, source, digest = load_selected_generator('f8b3586f1d58', root=args.root)
    cases = [
        ('bool_seed', (True, 0), {'difficulty': 'easy'}),
        ('float_seed', (1.0, 0), {'difficulty': 'easy'}),
        ('negative_sample_index', (991, -1), {'difficulty': 'easy'}),
    ]
    rows = []
    for label, positional, keywords in cases:
        row = {'label': label, 'args': list(positional), 'kwargs': keywords}
        try:
            grid = gen.generate(*positional, **keywords)
            row.update(status='accepted', self_check=gen.self_check(grid), grid=grid)
        except Exception as exc:  # evidence must retain unexpected rejections too
            row.update(
                status='rejected',
                exception_type=type(exc).__name__,
                exception=str(exc),
            )
        rows.append(row)

    payload = {
        'schema': 'arc-review-audit-counterexample-v1',
        'task_id': 'f8b3586f1d58',
        'source_path': str(source),
        'source_sha256': digest,
        'rule_hash': gen.RULE_HASH,
        'finding': 'public positional scalar validation is missing',
        'command': [
            'python3',
            'checks/audit/f8b3586f1d58/reproduce_strict_scalars.py',
            '--root', 'repo',
            '--out', 'checks/audit/f8b3586f1d58/strict-scalar-counterexample.json',
        ],
        'cwd': '.',
        'cases': rows,
    }
    args.out.write_text(json.dumps(payload, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'source_sha256': digest, 'cases': [r['status'] for r in rows]}))
    return 0 if all(row['status'] == 'accepted' and row['self_check'] == [] for row in rows) else 1


if __name__ == '__main__':
    raise SystemExit(main())
