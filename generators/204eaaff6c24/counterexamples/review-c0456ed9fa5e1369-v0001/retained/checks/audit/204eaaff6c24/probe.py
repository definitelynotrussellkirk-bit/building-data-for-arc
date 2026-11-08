"""Focused audit: a feasible diagonal/count override must grow free dimensions."""
from __future__ import annotations
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

TASK = '204eaaff6c24'
SOURCE_SHA = '9c475e402957455e63e43cc2645867c23a74b1cb0b4dcdaf54909c066072839f'
ROOT = Path.cwd()
OUT = ROOT.parent / 'checks/audit' / TASK
SOURCE = ROOT / 'generators' / TASK / 'generator.py'
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == SOURCE_SHA
spec = importlib.util.spec_from_file_location('audit_target_204eaaff6c24', SOURCE)
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)
REQUEST = {'n_cells': 8, 'fg_layout': 'diagonal', 'fg_color': 4}

if sys.argv[1:] == ['free-dimensions']:
    # This request is feasible within the declared 3..12 canvas envelope.
    # Keep the actual exception uncaught so the receipt records a true exit 1.
    grid = gen.generate(17, 0, difficulty='medium', **REQUEST)
    print(json.dumps({'unexpected_success': grid, 'self_check': gen.self_check(grid)}))
elif sys.argv[1:] == ['explicit-control']:
    controls = dict(REQUEST, grid_h=8, grid_w=8)
    grid = gen.generate(17, 0, difficulty='medium', **controls)
    errors = gen.self_check(grid)
    assert errors == [], errors
    assert gen.observe_overrides(grid) == {'fg_color': 4, 'n_cells': 8}
    assert len(grid) == len(grid[0]) == 8
    assert sum(value == 4 for row in grid for value in row) == 8
    assert all(grid[i][i] == 4 for i in range(8))
    metadata = {'task_id': TASK, 'generator_sha256': SOURCE_SHA, 'version': gen.VERSION,
                'declared_rule_hash': gen.RULE_HASH, 'seed': 17, 'sample_index': 0,
                'difficulty': 'medium', 'failing_overrides': REQUEST,
                'control_overrides': controls, 'control_self_check': errors,
                'control_observed_overrides': gen.observe_overrides(grid),
                'documented_domain': {'belongs': True, 'shape': [8, 8], 'nonzero_color': 4,
                                      'nonzero_cells': 8, 'background_cells': 56, 'layout': 'diagonal'},
                'finding_type': 'feasible override rejected before an input is returned',
                'rival_output': None,
                'rival_status': 'Not applicable: this is a construction failure, not an output-rule disagreement.'}
    (OUT / 'input.json').write_text(json.dumps(grid) + '\n')
    (OUT / 'probe-metadata.json').write_text(json.dumps(metadata, indent=2) + '\n')
    print(json.dumps(metadata))
else:
    raise SystemExit('usage: probe.py free-dimensions|explicit-control')
