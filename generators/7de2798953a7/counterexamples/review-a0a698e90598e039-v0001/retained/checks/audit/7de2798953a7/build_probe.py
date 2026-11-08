from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

PACKET = Path(__file__).resolve().parents[3]
GEN_PATH = PACKET / 'repo/generators/7de2798953a7/generator.py'
CANONICAL = PACKET / 'repo/shared/data/canonical/puzzles.jsonl'
OUT_DIR = Path(__file__).resolve().parent

spec = importlib.util.spec_from_file_location('audit_7de_generator', GEN_PATH)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


def rival_left_endpoint_any_two_nonzero(grid: list[list[int]]) -> list[list[int]]:
    out = [row[:] for row in grid]
    for r, row in enumerate(grid):
        positions = [c for c, value in enumerate(row) if value != 0]
        if len(positions) != 2:
            continue
        left, right = positions
        if not all(value == 0 for value in row[left + 1:right]):
            continue
        color = row[left]
        for k, c in enumerate(range(left + 1, right), start=1):
            if k % 2 == 1:
                out[r][c] = color
    return out

canonical_pairs = []
for line in CANONICAL.read_text(encoding='utf-8').splitlines():
    row = json.loads(line)
    if row.get('task_id') == '7de2798953a7':
        canonical_pairs.extend(row.get('train', []))
        canonical_pairs.extend(row.get('test', []))

canonical_fit = [
    rival_left_endpoint_any_two_nonzero(pair['input']) == pair['output']
    for pair in canonical_pairs
]

records = []
inputs = []
for difficulty in ('easy', 'medium', 'hard'):
    for sample_index in range(20):
        grid = module.generate(20261004, sample_index, difficulty=difficulty)
        records.append({
            'difficulty': difficulty,
            'seed': 20261004,
            'sample_index': sample_index,
            'self_check': module.self_check(grid, difficulty=difficulty),
        })
        inputs.append(grid)

(OUT_DIR / 'generated_inputs.json').write_text(json.dumps(inputs, indent=2) + '\n', encoding='utf-8')
(OUT_DIR / 'probe_pre_apply.json').write_text(json.dumps({
    'task_id': '7de2798953a7',
    'generator_sha256': hashlib.sha256(GEN_PATH.read_bytes()).hexdigest(),
    'seed': 20261004,
    'samples_per_band': 20,
    'generated_count': len(inputs),
    'all_generated_pass_self_check': all(not item['self_check'] for item in records),
    'canonical_pair_count': len(canonical_pairs),
    'rival_fits_all_canonical_pairs': all(canonical_fit),
    'canonical_fit_vector': canonical_fit,
    'records': records,
}, indent=2) + '\n', encoding='utf-8')
