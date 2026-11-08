#!/usr/bin/env python3
"""Reproduce inert exact controls for audit target c14c7af8df05."""
from __future__ import annotations
import hashlib, importlib.util, json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
REPO = ROOT / 'repo'
sys.path.insert(0, str(REPO / 'shared' / 'runtime'))
p = REPO / 'generators' / 'c14c7af8df05' / 'generator.py'
spec = importlib.util.spec_from_file_location('audit_c14', p)
assert spec is not None and spec.loader is not None
g = importlib.util.module_from_spec(spec); spec.loader.exec_module(g)
seed, sample_index = 123, 4
pairs = [
    ({'palette_kind': 'warm'}, {'palette_kind': 'cool'}),
    ({'palette_size': 1}, {'palette_size': 8}),
    ({'n_distinct_colors': 1}, {'n_distinct_colors': 8}),
    ({'texture': 'warm'}, {'texture': 'cool'}),
    ({'texture': 'default'}, {'texture': 'varied'}),
]
comparisons = []
for a, b in pairs:
    ga = g.generate(seed, sample_index, **a)
    gb = g.generate(seed, sample_index, **b)
    comparisons.append({
        'overrides_a': a, 'overrides_b': b, 'equal': ga == gb,
        'grid_a': ga, 'grid_b': gb,
        'self_check_a': g.self_check(ga), 'self_check_b': g.self_check(gb),
    })
passed = all(c['equal'] and not c['self_check_a'] and not c['self_check_b'] for c in comparisons)
out = Path(__file__).resolve().parent
report = {
    'task_id': g.TASK_ID,
    'finding': 'advertised exact controls are inert',
    'generator_sha256': hashlib.sha256(p.read_bytes()).hexdigest(),
    'seed': seed, 'sample_index': sample_index, 'difficulty': None,
    'comparisons': comparisons,
    'inert_controls_reproduced': ['palette_kind', 'palette_size', 'n_distinct_colors', 'texture (helpful values)'],
    'controls_not_claimed_inert': ['grid_h', 'grid_w', 'n_pairs', 'degenerate texture values'],
    'command': {'cwd': 'packet_root', 'argv': ['python3', 'checks/audit/c14c7af8df05/reproduce.py']},
    'domain_note': 'Every compared grid passes self_check; this is override observability, not label correctness.',
    'passed': passed,
}
(out / 'override_reproducer.json').write_text(json.dumps(report, indent=2) + '\n')
(out / 'input.json').write_text(json.dumps(comparisons[0]['grid_a'], indent=2) + '\n')
print(json.dumps({'passed': passed, 'comparisons': len(comparisons), 'generator_sha256': report['generator_sha256']}, indent=2))
raise SystemExit(0 if passed else 1)
