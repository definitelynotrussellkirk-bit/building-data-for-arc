#!/usr/bin/env python3
from __future__ import annotations
import hashlib, importlib.util, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
REPO = ROOT / 'repo'
sys.path.insert(0, str(REPO / 'shared/runtime'))
GEN_PATH = REPO / 'generators/0cf12bd584ef/generator.py'
spec = importlib.util.spec_from_file_location('audit_0cf_generator', GEN_PATH)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)

seed = 20261003
bands = ('easy', 'medium', 'hard')
records = []
unknown_count = 0
row2_nonzero_count = 0
for band in bands:
    for sample_index in range(100):
        grid = mod.generate(seed, sample_index, difficulty=band)
        w = len(grid[0])
        legend_cols = [c for c in range(w) if grid[0][c] != 0 or grid[1][c] != 0]
        srcs = {grid[0][c] for c in legend_cols if grid[0][c] != 0 and grid[1][c] != 0}
        unknown = [(r,c,grid[r][c]) for r in range(2,len(grid)) for c in range(w)
                   if grid[r][c] != 0 and grid[r][c] not in srcs]
        row2 = [(2,c,grid[2][c]) for c in range(w) if grid[2][c] != 0]
        unknown_count += len(unknown)
        row2_nonzero_count += len(row2)
        records.append({
            'band': band,
            'sample_index': sample_index,
            'n_pairs': len(legend_cols),
            'unknown_body_cells': len(unknown),
            'row2_nonzero_cells': len(row2),
        })

counterexample = json.loads((ROOT / 'checks/audit/0cf12bd584ef/input.json').read_text())
validation = mod.self_check(counterexample)
racket = json.loads((ROOT / 'checks/audit/0cf12bd584ef/racket.json').read_text())
actual = racket['results'][0]['output']
# Plausible shortcut: normal examples contain only source-colored nonzero body
# cells, so an unmatched nonzero is (wrongly) sent to the first destination.
legend_cols = [c for c in range(len(counterexample[0]))
               if counterexample[0][c] != 0 and counterexample[1][c] != 0]
mapping = {counterexample[0][c]: counterexample[1][c] for c in legend_cols}
first_dst = counterexample[1][legend_cols[0]]
rival = [row[:] for row in counterexample]
for r in range(2, len(rival)):
    for c, v in enumerate(rival[r]):
        if v != 0:
            rival[r][c] = mapping.get(v, first_dst)

out = {
    'schema': 'arcpuzzles-audit-probe-v1',
    'task_id': mod.TASK_ID,
    'generator_sha256': hashlib.sha256(GEN_PATH.read_bytes()).hexdigest(),
    'rule_hash': racket['executed_rule_hash'],
    'sampling': {
        'seed': seed,
        'bands': list(bands),
        'sample_indices': [0, 99],
        'draws_per_band': 100,
        'total_draws': len(records),
        'unknown_body_cells_total': unknown_count,
        'row2_nonzero_cells_total': row2_nonzero_count,
        'all_normal_body_nonzero_cells_are_legend_sources': unknown_count == 0,
        'all_normal_row2_cells_are_zero': row2_nonzero_count == 0,
        'n_pairs_histogram': {str(n): sum(x['n_pairs'] == n for x in records)
                              for n in sorted({x['n_pairs'] for x in records})},
    },
    'counterexample': {
        'input_path': 'checks/audit/0cf12bd584ef/input.json',
        'passes_self_check': validation == [],
        'self_check_messages': validation,
        'actual_racket_output': actual,
        'rival_name': 'map_unmatched_nonzero_to_first_destination',
        'rival_output': rival,
        'outputs_differ': actual != rival,
        'differing_cells': [[r,c,actual[r][c],rival[r][c]]
                            for r in range(len(actual)) for c in range(len(actual[0]))
                            if actual[r][c] != rival[r][c]],
    },
    'command': ['python3', 'checks/audit/0cf12bd584ef/probe_unmapped_body.py'],
    'cwd': 'packet_root',
}
print(json.dumps(out, indent=2))
