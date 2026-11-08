from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

GENERATOR = Path('generators/50385c1a773f/generator.py')
spec = importlib.util.spec_from_file_location('audit_generator_50385c1a773f', GENERATOR)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


def fingerprint(grid):
    return hashlib.sha256(json.dumps(grid, separators=(',', ':')).encode()).hexdigest()


def canonical_output(grid):
    facts = mod._analysis(grid)
    assert not facts['errors'], facts['errors']
    out = [row[:] for row in grid]
    for row, col in facts['path']:
        out[row][col] = 8
    return out


def wall_only_rival(grid):
    facts = mod._analysis(grid)
    if facts['termination'] == 'wall':
        return canonical_output(grid)
    return [row[:] for row in grid]

records = []
first = None
for band in ('easy', 'medium', 'hard'):
    ambiguous = 0
    total = 0
    for seed in range(50):
        for start in range(24):
            grids = [mod.generate(seed, start + offset, difficulty=band) for offset in range(4)]
            facts = [mod._analysis(grid) for grid in grids]
            total += 1
            if all(item['termination'] == 'wall' for item in facts[:3]) and facts[3]['termination'] == 'boundary':
                ambiguous += 1
                if first is None:
                    demo_outputs = [canonical_output(grid) for grid in grids[:3]]
                    assert all(wall_only_rival(grid) == out for grid, out in zip(grids[:3], demo_outputs))
                    query_output = canonical_output(grids[3])
                    rival_query_output = wall_only_rival(grids[3])
                    assert query_output != rival_query_output
                    first = {
                        'band': band,
                        'seed': seed,
                        'start': start,
                        'demo_terminations': [item['termination'] for item in facts[:3]],
                        'query_termination': facts[3]['termination'],
                        'demo_fingerprints': [fingerprint(grid) for grid in grids[:3]],
                        'query_fingerprint': fingerprint(grids[3]),
                        'query_path_cells': len(facts[3]['path']),
                        'query_wall_components': facts[3]['n_wall_components'],
                        'rival_definition': 'apply the canonical painting only when the beam hits gray; return boundary-exit inputs unchanged',
                        'rival_matches_all_demos': True,
                        'rival_differs_on_query': True,
                    }
    records.append({'band': band, 'ambiguous_windows': ambiguous, 'windows_checked': total})

result = {
    'task_id': mod.TASK_ID,
    'examples_needed': mod.EXAMPLES_NEEDED,
    'first_reproduction': first,
    'window_counts': records,
}
print(json.dumps(result, indent=2, sort_keys=True))
