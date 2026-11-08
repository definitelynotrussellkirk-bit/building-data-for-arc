#!/usr/bin/env python3
"""Audit-only unknown-override probe for db95939a5dd0; no target edits."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path.cwd()))

from generators.db95939a5dd0 import generator as gen

OUT = Path('../checks/audit/db95939a5dd0/unknown-override.json')


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


records = []
for band in ('easy', None, 'hard'):
    for seed in range(40):
        sample_index = seed % 7
        base = gen.generate(seed, sample_index, difficulty=band)
        entry = {
            'difficulty': band if band is not None else 'medium/default',
            'seed': seed,
            'sample_index': sample_index,
            'unknown_override': {'typo_axis': 123},
        }
        try:
            typo = gen.generate(
                seed, sample_index, difficulty=band, typo_axis=123
            )
            entry.update({
                'accepted': True,
                'changed_grid': typo != base,
                'base_profile': gen.profile_features(base),
                'typo_profile': gen.profile_features(typo),
            })
        except Exception as exc:
            entry.update({
                'accepted': False,
                'exception_type': type(exc).__name__,
                'exception': str(exc),
            })
        records.append(entry)

result = {
    'schema': 'arcpuzzles-audit-probe-v1',
    'task_id': gen.TASK_ID,
    'generator_version': gen.VERSION,
    'generator_sha256': sha256(Path(gen.__file__)),
    'probe': 'undeclared override typo_axis=123',
    'draws': len(records),
    'accepted': sum(r['accepted'] for r in records),
    'changed_grid_vs_same_coordinate_without_key': sum(
        r.get('changed_grid', False) for r in records
    ),
    'records': records,
    'source_mechanism': (
        'generate() branches to the canonical-archetype prior only when '
        '`not overrides`; an accepted unknown key therefore bypasses that prior.'
    ),
}
OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
print(json.dumps({
    'out': str(OUT),
    'generator_sha256': result['generator_sha256'],
    'draws': result['draws'],
    'accepted': result['accepted'],
    'changed_grid': result['changed_grid_vs_same_coordinate_without_key'],
}, indent=2))
