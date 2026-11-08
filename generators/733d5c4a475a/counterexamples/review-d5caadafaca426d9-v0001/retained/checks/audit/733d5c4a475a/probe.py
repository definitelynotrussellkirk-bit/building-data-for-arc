from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

REPO = Path.cwd()
GEN_PATH = REPO / 'generators' / '733d5c4a475a' / 'generator.py'
SPEC = importlib.util.spec_from_file_location('audit_733d5c4a475a', GEN_PATH)
assert SPEC is not None and SPEC.loader is not None
GEN = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = GEN
SPEC.loader.exec_module(GEN)

counts = {
    'total': 0,
    'horizontal_dr_zero': 0,
    'vertical_dc_zero': 0,
    'diagonal_both_nonzero': 0,
    'generation_errors': 0,
}
per_band = {}
for difficulty in ('easy', 'medium', 'hard'):
    local = dict.fromkeys(counts, 0)
    for seed in range(1000):
        try:
            grid = GEN.generate(seed, 0, difficulty=difficulty)
        except Exception:
            counts['generation_errors'] += 1
            local['generation_errors'] += 1
            continue
        nines = sorted((r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 9)
        assert len(nines) == 2
        (ar, ac), (br, bc) = nines
        dr, dc = br - ar, bc - ac
        counts['total'] += 1
        local['total'] += 1
        if dr == 0:
            counts['horizontal_dr_zero'] += 1
            local['horizontal_dr_zero'] += 1
        if dc == 0:
            counts['vertical_dc_zero'] += 1
            local['vertical_dc_zero'] += 1
        if dr != 0 and dc != 0:
            counts['diagonal_both_nonzero'] += 1
            local['diagonal_both_nonzero'] += 1
    per_band[difficulty] = local

fixture = [[0] * 6 for _ in range(6)]
fixture[0][4] = 9
for r, c in ((1, 1), (1, 2), (2, 1)):
    fixture[r][c] = 4
fixture[3][4] = 9
self_check = GEN.self_check(fixture)

rival = [row[:] for row in fixture]
for r, row in enumerate(rival):
    for c, value in enumerate(row):
        if value == 9:
            rival[r][c] = 0
# Wrong but generator-consistent shortcut: only support diagonal vectors; for
# axis-aligned vectors erase markers and leave the original shape unchanged.

out_dir = REPO.parent / 'checks' / 'audit' / '733d5c4a475a'
out_dir.mkdir(parents=True, exist_ok=True)
(out_dir / 'input.json').write_text(json.dumps(fixture, indent=2) + '\n')
(out_dir / 'rival.json').write_text(json.dumps(rival, indent=2) + '\n')
report = {
    'schema': 'arcpuzzles-adversarial-audit-probe-v1',
    'task_id': '733d5c4a475a',
    'generator_path': 'generators/733d5c4a475a/generator.py',
    'generator_sha256': hashlib.sha256(GEN_PATH.read_bytes()).hexdigest(),
    'sample': {
        'seed_range': [0, 999],
        'sample_index': 0,
        'difficulties': ['easy', 'medium', 'hard'],
        'counts': counts,
        'per_band': per_band,
    },
    'fixture': {
        'dimensions': [6, 6],
        'marker_positions': [[0, 4], [3, 4]],
        'vector': [3, 0],
        'self_check': self_check,
        'rival': 'erase markers and leave original unchanged whenever the vector is axis-aligned',
        'input_path': 'checks/audit/733d5c4a475a/input.json',
        'rival_path': 'checks/audit/733d5c4a475a/rival.json',
    },
}
(out_dir / 'measurement.json').write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
print(json.dumps(report, indent=2, sort_keys=True))
