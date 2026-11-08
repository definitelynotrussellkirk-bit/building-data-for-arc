from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
REPO = ROOT / 'repo'
sys.path.insert(0, str(REPO / 'shared' / 'runtime'))

path = REPO / 'generators' / '882c01c42710' / 'generator.py'
spec = importlib.util.spec_from_file_location('audit_gen_882c01c42710', path)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

record = None
for line in (REPO / 'shared' / 'data' / 'canonical' / 'puzzles.jsonl').read_text().splitlines():
    candidate = json.loads(line)
    if candidate.get('task_id') == '882c01c42710':
        record = candidate
        break
assert record is not None

pairs = list(record['train'])
test = record['test']
if isinstance(test, list):
    pairs.extend(test)
else:
    pairs.append(test)

canonical_errors = []
for idx, pair in enumerate(pairs):
    errs = mod.self_check(pair['input'])
    canonical_errors.append({'pair_index': idx, 'errors': errs})

probes = []
base_kwargs = {'difficulty': 'medium'}
for axis, left, right in [
    ('n_h', 3, 5),
    ('n_v', 3, 5),
    ('anchor_corner', False, True),
    ('asymmetry_force', False, True),
    ('palette_kind', 'warm', 'cool'),
]:
    left_grid = mod.generate(42881, 7, **base_kwargs, **{axis: left})
    right_grid = mod.generate(42881, 7, **base_kwargs, **{axis: right})
    probes.append({
        'axis': axis,
        'left': left,
        'right': right,
        'identical_outputs': left_grid == right_grid,
        'left_grid': left_grid,
        'right_grid': right_grid,
    })

out = {
    'schema': 'arcpuzzles-audit-probe-v1',
    'task_id': '882c01c42710',
    'generator_version': getattr(mod, 'VERSION', None),
    'generator_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
    'canonical_rule_hash_reported_by_lint': '6c98f9c259fd',
    'canonical_self_check_results': canonical_errors,
    'first_canonical_pair': pairs[0],
    'override_probes': probes,
    'commands': [
        {
            'cwd': 'packet_root',
            'argv': ['python3', 'checks/audit/882c01c42710/build_probe.py'],
        }
    ],
}
(Path(__file__).with_name('counterexample.json')).write_text(json.dumps(out, indent=2) + '\n')
(Path(__file__).with_name('canonical-input.json')).write_text(json.dumps({'input': pairs[0]['input']}, indent=2) + '\n')
print(json.dumps({
    'canonical_pairs_checked': len(pairs),
    'canonical_pairs_rejected': sum(bool(x['errors']) for x in canonical_errors),
    'override_identity': {p['axis']: p['identical_outputs'] for p in probes},
    'generator_sha256': out['generator_sha256'],
}, indent=2))
